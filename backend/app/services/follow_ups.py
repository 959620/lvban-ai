from sqlalchemy.orm import Session, selectinload

from app.models import FollowUp, Student, Task
from app.schemas.follow_up import FollowUpCreate, FollowUpUpdate
from app.schemas.task import TaskCreate
from app.services import tasks as task_service


def _query(db: Session, owner_id: int):
    return (
        db.query(FollowUp)
        .options(selectinload(FollowUp.student))
        .filter(FollowUp.owner_id == owner_id)
    )


def list_follow_ups(
    db: Session,
    owner_id: int,
    *,
    student_id: int | None = None,
    contact_with: str | None = None,
) -> list[FollowUp]:
    query = _query(db, owner_id)
    if student_id is not None:
        query = query.filter(FollowUp.student_id == student_id)
    if contact_with:
        query = query.filter(FollowUp.contact_with == contact_with)
    return query.order_by(FollowUp.contact_date.desc(), FollowUp.id.desc()).all()


def get_owned_follow_up(db: Session, follow_up_id: int, owner_id: int) -> FollowUp | None:
    return _query(db, owner_id).filter(FollowUp.id == follow_up_id).first()


def _get_owned_student(db: Session, student_id: int, owner_id: int) -> Student:
    student = (
        db.query(Student)
        .filter(Student.id == student_id, Student.owner_id == owner_id)
        .first()
    )
    if student is None:
        raise ValueError("学生不存在或不属于当前账号")
    return student


def _build_task_title(student: Student, next_action: str | None, contact_with: str) -> str:
    target = "家长" if contact_with == "parent" else "学生"
    action = (next_action or "").strip() or f"跟进{target}"
    return f"跟进提醒 · {student.name} · {action}"


def _maybe_create_or_sync_task(
    db: Session,
    *,
    owner_id: int,
    student: Student,
    follow_up: FollowUp,
    create_task: bool,
) -> None:
    if follow_up.next_remind_at is None:
        return

    if follow_up.created_task_id:
        task = (
            db.query(Task)
            .filter(Task.id == follow_up.created_task_id, Task.owner_id == owner_id)
            .first()
        )
        if task is not None:
            task.due_at = follow_up.next_remind_at
            task.title = _build_task_title(student, follow_up.next_action, follow_up.contact_with)
            if task.status == "done":
                task.status = "todo"
            db.add(task)
            db.commit()
            return

    if not create_task:
        return

    task = task_service.create_task(
        db,
        owner_id,
        TaskCreate(
            title=_build_task_title(student, follow_up.next_action, follow_up.contact_with),
            student_id=student.id,
            due_at=follow_up.next_remind_at,
            priority="normal",
            status="todo",
            source="follow_up",
        ),
    )
    follow_up.created_task_id = task.id
    db.add(follow_up)
    db.commit()


def create_follow_up(db: Session, owner_id: int, payload: FollowUpCreate) -> FollowUp:
    student = _get_owned_student(db, payload.student_id, owner_id)
    data = payload.model_dump(exclude={"create_task"})
    follow_up = FollowUp(owner_id=owner_id, **data)
    db.add(follow_up)

    if payload.next_remind_at is not None:
        student.next_contact_at = payload.next_remind_at
        db.add(student)

    db.commit()
    db.refresh(follow_up)

    _maybe_create_or_sync_task(
        db,
        owner_id=owner_id,
        student=student,
        follow_up=follow_up,
        create_task=payload.create_task,
    )
    return get_owned_follow_up(db, follow_up.id, owner_id)  # type: ignore[return-value]


def update_follow_up(db: Session, follow_up: FollowUp, payload: FollowUpUpdate) -> FollowUp:
    student = _get_owned_student(db, follow_up.student_id, follow_up.owner_id)
    data = payload.model_dump(exclude_unset=True)
    create_task = data.pop("create_task", True)
    clear_next = data.pop("clear_next_remind_at", False)

    for key, value in data.items():
        setattr(follow_up, key, value)

    if clear_next:
        follow_up.next_remind_at = None
        student.next_contact_at = None
    elif "next_remind_at" in data:
        student.next_contact_at = follow_up.next_remind_at

    db.add(follow_up)
    db.add(student)
    db.commit()

    _maybe_create_or_sync_task(
        db,
        owner_id=follow_up.owner_id,
        student=student,
        follow_up=follow_up,
        create_task=create_task,
    )
    return get_owned_follow_up(db, follow_up.id, follow_up.owner_id)  # type: ignore[return-value]


def delete_follow_up(db: Session, follow_up: FollowUp) -> None:
    db.delete(follow_up)
    db.commit()
