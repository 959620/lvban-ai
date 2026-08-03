from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models import User
from app.schemas.schedule import (
    SESSION_TYPES,
    STATUS_LABELS,
    ClassSessionCreate,
    ClassSessionListOut,
    ClassSessionOut,
    ClassSessionUpdate,
    ScheduleOptionsOut,
)
from app.services import schedule as schedule_service
from app.services.tasks import now_cn

router = APIRouter(prefix="/schedule", tags=["日程"])


def _to_out(session, owner_id: int, db: Session) -> ClassSessionOut:
    conflicts = schedule_service.find_classroom_conflicts(
        db,
        owner_id,
        session_date=session.session_date,
        classroom=session.classroom,
        start_time=session.start_time,
        end_time=session.end_time,
        exclude_id=session.id,
    )
    data = ClassSessionOut.model_validate(session)
    data.classroom_conflict = len(conflicts) > 0
    return data


@router.get("/options", response_model=ScheduleOptionsOut, summary="排课表单选项")
def schedule_options(current_user: User = Depends(get_current_user)) -> ScheduleOptionsOut:
    _ = current_user
    return ScheduleOptionsOut(
        session_types=SESSION_TYPES,
        statuses=[{"value": key, "label": label} for key, label in STATUS_LABELS.items()],
    )


@router.get("/day", response_model=ClassSessionListOut, summary="按日查看课表")
def list_day(
    day: date | None = Query(default=None, title="日期，默认今天"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ClassSessionListOut:
    summary = schedule_service.day_summary(db, current_user.id, day)
    items = [_to_out(item, current_user.id, db) for item in summary["items"]]
    return ClassSessionListOut(
        items=items,
        total=len(items),
        query_date=summary["date"],
        occupied_classrooms=summary["occupied_classrooms"],
        absent_count=summary["absent_count"],
    )


@router.get("/week", response_model=ClassSessionListOut, summary="按周查看课表")
def list_week(
    start: date | None = Query(default=None, title="周内任意一天，默认今天"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ClassSessionListOut:
    week_start, week_end = schedule_service.week_range(start or now_cn().date())
    items_raw = schedule_service.list_sessions_by_range(
        db,
        current_user.id,
        start=week_start,
        end=week_end,
    )
    items = [_to_out(item, current_user.id, db) for item in items_raw]
    occupied = sorted(
        {
            item.classroom.strip()
            for item in items_raw
            if item.classroom and item.status != "cancelled"
        }
    )
    return ClassSessionListOut(
        items=items,
        total=len(items),
        query_date=week_start,
        occupied_classrooms=occupied,
        absent_count=sum(1 for item in items_raw if item.status == "absent"),
    )


@router.get("", response_model=ClassSessionListOut, summary="排课列表")
def list_sessions(
    start: date | None = Query(default=None, title="开始日期"),
    end: date | None = Query(default=None, title="结束日期"),
    student_id: int | None = Query(default=None, title="学生 ID"),
    status: str | None = Query(default=None, title="状态"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ClassSessionListOut:
    today = now_cn().date()
    range_start = start or today
    range_end = end or today
    items_raw = schedule_service.list_sessions_by_range(
        db,
        current_user.id,
        start=range_start,
        end=range_end,
        student_id=student_id,
        status=status,
    )
    items = [_to_out(item, current_user.id, db) for item in items_raw]
    return ClassSessionListOut(items=items, total=len(items), query_date=range_start)


@router.post(
    "",
    response_model=ClassSessionOut,
    status_code=status.HTTP_201_CREATED,
    summary="新建排课",
)
def create_session(
    payload: ClassSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ClassSessionOut:
    try:
        session = schedule_service.create_session(db, current_user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_out(session, current_user.id, db)


@router.patch("/{session_id}", response_model=ClassSessionOut, summary="更新排课")
def update_session(
    session_id: int,
    payload: ClassSessionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ClassSessionOut:
    session = schedule_service.get_owned_session(db, session_id, current_user.id)
    if session is None:
        raise HTTPException(status_code=404, detail="排课不存在")
    try:
        updated = schedule_service.update_session(db, session, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_out(updated, current_user.id, db)


@router.post("/{session_id}/absent", response_model=ClassSessionOut, summary="标记缺课")
def mark_absent(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ClassSessionOut:
    session = schedule_service.get_owned_session(db, session_id, current_user.id)
    if session is None:
        raise HTTPException(status_code=404, detail="排课不存在")
    updated = schedule_service.update_session(
        db,
        session,
        ClassSessionUpdate(status="absent"),
    )
    return _to_out(updated, current_user.id, db)


@router.post("/{session_id}/complete", response_model=ClassSessionOut, summary="标记完成")
def mark_complete(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ClassSessionOut:
    session = schedule_service.get_owned_session(db, session_id, current_user.id)
    if session is None:
        raise HTTPException(status_code=404, detail="排课不存在")
    updated = schedule_service.update_session(
        db,
        session,
        ClassSessionUpdate(status="completed"),
    )
    return _to_out(updated, current_user.id, db)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除排课")
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    session = schedule_service.get_owned_session(db, session_id, current_user.id)
    if session is None:
        raise HTTPException(status_code=404, detail="排课不存在")
    schedule_service.delete_session(db, session)
