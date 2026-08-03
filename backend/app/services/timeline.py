"""学生时间轴：聚合排课 + 手工节点 + 派生状态。"""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session, selectinload

from app.models import ClassSession, Course, Student, TimelineEvent
from app.schemas.timeline import (
    EVENT_STATUS_LABELS,
    EVENT_TYPE_LABELS,
    TimelineEventCreate,
    TimelineEventUpdate,
    TimelineItemOut,
)
from app.services.tasks import now_cn


def _ensure_student(db: Session, student_id: int, owner_id: int) -> Student:
    student = (
        db.query(Student)
        .filter(Student.id == student_id, Student.owner_id == owner_id)
        .first()
    )
    if student is None:
        raise ValueError("学生不存在或不属于当前账号")
    return student


def _ensure_course(db: Session, course_id: int | None, owner_id: int) -> None:
    if course_id is None:
        return
    exists = (
        db.query(Course.id)
        .filter(Course.id == course_id, Course.owner_id == owner_id)
        .first()
    )
    if exists is None:
        raise ValueError("课程不存在或不属于当前账号")


def _session_status(session: ClassSession, today: date) -> str:
    if session.status == "completed":
        return "done"
    if session.status == "absent":
        return "absent"
    if session.status == "cancelled":
        return "cancelled"
    # scheduled
    if session.session_date < today:
        return "done"  # 过期未标记，按已发生展示，前端可再核对
    if session.session_date == today:
        return "current"
    return "upcoming"


def _item(
    *,
    id: str,
    source: str,
    event_type: str,
    title: str,
    event_date: date,
    status: str,
    notes: str | None = None,
    related_session_id: int | None = None,
    related_course_id: int | None = None,
    course_name: str | None = None,
    classroom: str | None = None,
    teacher_name: str | None = None,
    editable: bool = False,
) -> TimelineItemOut:
    return TimelineItemOut(
        id=id,
        source=source,
        event_type=event_type,
        event_type_label=EVENT_TYPE_LABELS.get(event_type, event_type),
        title=title,
        event_date=event_date,
        status=status,
        status_label=EVENT_STATUS_LABELS.get(status, status),
        notes=notes,
        related_session_id=related_session_id,
        related_course_id=related_course_id,
        course_name=course_name,
        classroom=classroom,
        teacher_name=teacher_name,
        editable=editable,
    )


def build_timeline(db: Session, student_id: int, owner_id: int) -> list[TimelineItemOut]:
    student = _ensure_student(db, student_id, owner_id)
    today = now_cn().date()
    items: list[TimelineItemOut] = []

    # 1) 排课 → 课程节点
    sessions = (
        db.query(ClassSession)
        .options(selectinload(ClassSession.course))
        .filter(ClassSession.owner_id == owner_id, ClassSession.student_id == student_id)
        .order_by(ClassSession.session_date.asc(), ClassSession.start_time.asc())
        .all()
    )
    for session in sessions:
        course_name = session.course.name if session.course else None
        title = course_name or session.session_type
        title = f"{title}（{session.start_time}-{session.end_time}）"
        note_parts = []
        if session.notes:
            note_parts.append(session.notes)
        if session.classroom:
            note_parts.append(f"教室 {session.classroom}")
        items.append(
            _item(
                id=f"session:{session.id}",
                source="session",
                event_type="course_session",
                title=title,
                event_date=session.session_date,
                status=_session_status(session, today),
                notes=" · ".join(note_parts) or None,
                related_session_id=session.id,
                related_course_id=session.course_id,
                course_name=course_name,
                classroom=session.classroom,
                teacher_name=session.teacher_name,
                editable=False,
            )
        )

    # 2) 手工节点
    manuals = (
        db.query(TimelineEvent)
        .filter(TimelineEvent.owner_id == owner_id, TimelineEvent.student_id == student_id)
        .order_by(TimelineEvent.event_date.asc(), TimelineEvent.id.asc())
        .all()
    )
    for event in manuals:
        course_name = None
        if event.related_course_id:
            course = db.query(Course).filter(Course.id == event.related_course_id).first()
            course_name = course.name if course else None
        items.append(
            _item(
                id=f"manual:{event.id}",
                source="manual",
                event_type=event.event_type,
                title=event.title,
                event_date=event.event_date,
                status=event.status,
                notes=event.notes,
                related_session_id=event.related_session_id,
                related_course_id=event.related_course_id,
                course_name=course_name,
                editable=True,
            )
        )

    # 3) 派生：当前申请阶段
    if student.application_stage:
        items.append(
            _item(
                id="derived:application_stage",
                source="derived",
                event_type="application_stage",
                title=f"当前申请阶段：{student.application_stage}",
                event_date=today,
                status="current",
                notes="来自学生档案，可在编辑页更新",
                editable=False,
            )
        )

    # 4) 派生：作品集状态
    if student.portfolio_started or (student.portfolio_progress or 0) > 0:
        items.append(
            _item(
                id="derived:portfolio_status",
                source="derived",
                event_type="portfolio_status",
                title=f"作品集进度 {student.portfolio_progress}%（项目 {student.portfolio_project_count}）",
                event_date=today,
                status="current" if student.portfolio_progress < 100 else "done",
                notes="来自学生档案作品集字段",
                editable=False,
            )
        )

    items.sort(key=lambda item: (item.event_date, item.id))
    return items


def timeline_summary(items: list[TimelineItemOut]) -> dict[str, int]:
    return {
        "total": len(items),
        "done": sum(1 for i in items if i.status == "done"),
        "current": sum(1 for i in items if i.status == "current"),
        "upcoming": sum(1 for i in items if i.status == "upcoming"),
        "absent": sum(1 for i in items if i.status == "absent"),
        "course_sessions": sum(1 for i in items if i.event_type == "course_session"),
        "manual": sum(1 for i in items if i.source == "manual"),
    }


def create_event(
    db: Session,
    owner_id: int,
    student_id: int,
    payload: TimelineEventCreate,
) -> TimelineEvent:
    _ensure_student(db, student_id, owner_id)
    _ensure_course(db, payload.related_course_id, owner_id)
    event = TimelineEvent(
        owner_id=owner_id,
        student_id=student_id,
        **payload.model_dump(),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_owned_event(db: Session, event_id: int, owner_id: int) -> TimelineEvent | None:
    return (
        db.query(TimelineEvent)
        .filter(TimelineEvent.id == event_id, TimelineEvent.owner_id == owner_id)
        .first()
    )


def update_event(db: Session, event: TimelineEvent, payload: TimelineEventUpdate) -> TimelineEvent:
    data = payload.model_dump(exclude_unset=True)
    clear_course = data.pop("clear_course", False)
    if "related_course_id" in data:
        _ensure_course(db, data["related_course_id"], event.owner_id)
    for key, value in data.items():
        setattr(event, key, value)
    if clear_course:
        event.related_course_id = None
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def delete_event(db: Session, event: TimelineEvent) -> None:
    db.delete(event)
    db.commit()
