from datetime import date, datetime, timedelta, timezone

from sqlalchemy import case
from sqlalchemy.orm import Session, selectinload

from app.models import Student, Task
from app.schemas.task import TaskCreate, TaskUpdate

CN_TZ = timezone(timedelta(hours=8))

PRIORITY_ORDER = case(
    (Task.priority == "urgent", 0),
    (Task.priority == "normal", 1),
    (Task.priority == "low", 2),
    else_=3,
)


def now_cn() -> datetime:
    return datetime.now(CN_TZ)


def as_aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=CN_TZ)
    return value.astimezone(CN_TZ)


def day_bounds(day: date | None = None) -> tuple[datetime, datetime]:
    target = day or now_cn().date()
    start = datetime.combine(target, datetime.min.time(), tzinfo=CN_TZ)
    end = start + timedelta(days=1)
    return start, end


def _task_query(db: Session, owner_id: int):
    return db.query(Task).options(selectinload(Task.student)).filter(Task.owner_id == owner_id)


def list_tasks(
    db: Session,
    owner_id: int,
    *,
    status: str | None = None,
    priority: str | None = None,
    student_id: int | None = None,
    due_on: date | None = None,
) -> list[Task]:
    query = _task_query(db, owner_id)
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    if student_id is not None:
        query = query.filter(Task.student_id == student_id)
    if due_on is not None:
        start, end = day_bounds(due_on)
        query = query.filter(Task.due_at.is_not(None), Task.due_at >= start, Task.due_at < end)
    return query.order_by(
        Task.status.asc(),
        PRIORITY_ORDER,
        Task.due_at.asc().nulls_last(),
        Task.id.desc(),
    ).all()


def get_owned_task(db: Session, task_id: int, owner_id: int) -> Task | None:
    return _task_query(db, owner_id).filter(Task.id == task_id).first()


def _ensure_student(db: Session, owner_id: int, student_id: int | None) -> None:
    if student_id is None:
        return
    exists = (
        db.query(Student.id)
        .filter(Student.id == student_id, Student.owner_id == owner_id)
        .first()
    )
    if exists is None:
        raise ValueError("学生不存在或不属于当前账号")


def create_task(db: Session, owner_id: int, payload: TaskCreate) -> Task:
    _ensure_student(db, owner_id, payload.student_id)
    task = Task(owner_id=owner_id, **payload.model_dump())
    db.add(task)
    db.commit()
    return get_owned_task(db, task.id, owner_id)  # type: ignore[return-value]


def update_task(db: Session, task: Task, payload: TaskUpdate) -> Task:
    data = payload.model_dump(exclude_unset=True)
    clear_student = data.pop("clear_student", False)
    clear_due_at = data.pop("clear_due_at", False)

    if "student_id" in data:
        _ensure_student(db, task.owner_id, data["student_id"])

    for key, value in data.items():
        setattr(task, key, value)

    if clear_student:
        task.student_id = None
    if clear_due_at:
        task.due_at = None

    db.add(task)
    db.commit()
    return get_owned_task(db, task.id, task.owner_id)  # type: ignore[return-value]


def delete_task(db: Session, task: Task) -> None:
    db.delete(task)
    db.commit()


def list_contact_students_today(db: Session, owner_id: int) -> list[Student]:
    start, end = day_bounds()
    return (
        db.query(Student)
        .options(selectinload(Student.tags))
        .filter(
            Student.owner_id == owner_id,
            Student.next_contact_at.is_not(None),
            Student.next_contact_at >= start,
            Student.next_contact_at < end,
        )
        .order_by(Student.next_contact_at.asc())
        .all()
    )


def build_dashboard(db: Session, owner_id: int, upcoming_days: int = 3) -> dict:
    today = now_cn().date()
    start_today, end_today = day_bounds(today)
    upcoming_end = day_bounds(today + timedelta(days=upcoming_days))[1]

    all_todo = (
        _task_query(db, owner_id)
        .filter(Task.status == "todo")
        .order_by(PRIORITY_ORDER, Task.due_at.asc().nulls_last(), Task.id.desc())
        .all()
    )

    today_tasks: list[Task] = []
    upcoming_tasks: list[Task] = []
    incomplete_tasks: list[Task] = []

    for task in all_todo:
        due = as_aware(task.due_at)
        if due is None:
            incomplete_tasks.append(task)
            continue
        if start_today <= due < end_today:
            today_tasks.append(task)
        elif end_today <= due < upcoming_end:
            upcoming_tasks.append(task)
        elif due < start_today:
            incomplete_tasks.append(task)
        else:
            # 更远的未来任务也算未完成事项的一部分，但提醒区优先展示逾期/无截止
            pass

    # 未完成事项：逾期 + 无截止 + 今日未完成（去重后按紧急程度）
    seen: set[int] = set()
    merged_incomplete: list[Task] = []
    for task in incomplete_tasks + today_tasks:
        if task.id in seen:
            continue
        seen.add(task.id)
        merged_incomplete.append(task)

    contact_students = list_contact_students_today(db, owner_id)

    return {
        "today_tasks": today_tasks,
        "contact_students": contact_students,
        "upcoming_tasks": upcoming_tasks,
        "incomplete_tasks": merged_incomplete,
        "stats": {
            "today_count": len(today_tasks),
            "contact_count": len(contact_students),
            "upcoming_count": len(upcoming_tasks),
            "incomplete_count": len(merged_incomplete),
            "todo_total": len(all_todo),
        },
    }
