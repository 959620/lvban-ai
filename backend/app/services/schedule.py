from datetime import date, timedelta

from sqlalchemy.orm import Session, selectinload

from app.models import ClassSession, Course, Student
from app.schemas.schedule import ClassSessionCreate, ClassSessionUpdate
from app.services.tasks import now_cn


def _query(db: Session, owner_id: int):
    return (
        db.query(ClassSession)
        .options(selectinload(ClassSession.student), selectinload(ClassSession.course))
        .filter(ClassSession.owner_id == owner_id)
    )


def _ensure_student(db: Session, owner_id: int, student_id: int) -> None:
    exists = (
        db.query(Student.id)
        .filter(Student.id == student_id, Student.owner_id == owner_id)
        .first()
    )
    if exists is None:
        raise ValueError("学生不存在或不属于当前账号")


def _ensure_course(db: Session, owner_id: int, course_id: int | None) -> None:
    if course_id is None:
        return
    exists = (
        db.query(Course.id)
        .filter(Course.id == course_id, Course.owner_id == owner_id)
        .first()
    )
    if exists is None:
        raise ValueError("课程不存在或不属于当前账号")


def _overlaps(a_start: str, a_end: str, b_start: str, b_end: str) -> bool:
    return a_start < b_end and b_start < a_end


def find_classroom_conflicts(
    db: Session,
    owner_id: int,
    *,
    session_date: date,
    classroom: str | None,
    start_time: str,
    end_time: str,
    exclude_id: int | None = None,
) -> list[ClassSession]:
    if not classroom or not classroom.strip():
        return []
    room = classroom.strip()
    query = _query(db, owner_id).filter(
        ClassSession.session_date == session_date,
        ClassSession.classroom == room,
        ClassSession.status != "cancelled",
    )
    if exclude_id is not None:
        query = query.filter(ClassSession.id != exclude_id)
    conflicts = []
    for item in query.all():
        if _overlaps(start_time, end_time, item.start_time, item.end_time):
            conflicts.append(item)
    return conflicts


def list_sessions_by_date(db: Session, owner_id: int, day: date) -> list[ClassSession]:
    return (
        _query(db, owner_id)
        .filter(ClassSession.session_date == day)
        .order_by(ClassSession.start_time.asc(), ClassSession.id.asc())
        .all()
    )


def list_sessions_by_range(
    db: Session,
    owner_id: int,
    *,
    start: date,
    end: date,
    student_id: int | None = None,
    status: str | None = None,
) -> list[ClassSession]:
    query = _query(db, owner_id).filter(
        ClassSession.session_date >= start,
        ClassSession.session_date <= end,
    )
    if student_id is not None:
        query = query.filter(ClassSession.student_id == student_id)
    if status:
        query = query.filter(ClassSession.status == status)
    return query.order_by(
        ClassSession.session_date.asc(),
        ClassSession.start_time.asc(),
        ClassSession.id.asc(),
    ).all()


def get_owned_session(db: Session, session_id: int, owner_id: int) -> ClassSession | None:
    return _query(db, owner_id).filter(ClassSession.id == session_id).first()


def create_session(db: Session, owner_id: int, payload: ClassSessionCreate) -> ClassSession:
    _ensure_student(db, owner_id, payload.student_id)
    _ensure_course(db, owner_id, payload.course_id)
    data = payload.model_dump()
    if data.get("classroom"):
        data["classroom"] = data["classroom"].strip()
    session = ClassSession(owner_id=owner_id, **data)
    db.add(session)
    db.commit()
    return get_owned_session(db, session.id, owner_id)  # type: ignore[return-value]


def update_session(db: Session, session: ClassSession, payload: ClassSessionUpdate) -> ClassSession:
    data = payload.model_dump(exclude_unset=True)
    clear_course = data.pop("clear_course", False)

    if "student_id" in data and data["student_id"] is not None:
        _ensure_student(db, session.owner_id, data["student_id"])
    if "course_id" in data:
        _ensure_course(db, session.owner_id, data["course_id"])

    for key, value in data.items():
        if key == "classroom" and isinstance(value, str):
            value = value.strip() or None
        setattr(session, key, value)

    if clear_course:
        session.course_id = None

    start = session.start_time
    end = session.end_time
    if start >= end:
        raise ValueError("结束时间必须晚于开始时间")

    db.add(session)
    db.commit()
    return get_owned_session(db, session.id, session.owner_id)  # type: ignore[return-value]


def delete_session(db: Session, session: ClassSession) -> None:
    db.delete(session)
    db.commit()


def day_summary(db: Session, owner_id: int, day: date | None = None) -> dict:
    target = day or now_cn().date()
    items = list_sessions_by_date(db, owner_id, target)
    occupied = sorted(
        {
            item.classroom.strip()
            for item in items
            if item.classroom and item.status != "cancelled"
        }
    )
    absent_count = sum(1 for item in items if item.status == "absent")
    return {
        "date": target,
        "items": items,
        "occupied_classrooms": occupied,
        "absent_count": absent_count,
    }


def week_range(day: date | None = None) -> tuple[date, date]:
    target = day or now_cn().date()
    start = target - timedelta(days=target.weekday())  # Monday
    end = start + timedelta(days=6)
    return start, end
