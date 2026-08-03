from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models import User
from app.schemas.timeline import (
    EVENT_STATUSES,
    EVENT_TYPES,
    EVENT_STATUS_LABELS,
    EVENT_TYPE_LABELS,
    TimelineEventCreate,
    TimelineEventUpdate,
    TimelineItemOut,
    TimelineListOut,
    TimelineOptionsOut,
)
from app.services import timeline as timeline_service

router = APIRouter(tags=["时间轴"])


@router.get("/timeline/options", response_model=TimelineOptionsOut, summary="时间轴表单选项")
def timeline_options(current_user: User = Depends(get_current_user)) -> TimelineOptionsOut:
    _ = current_user
    return TimelineOptionsOut(
        event_types=[
            {"value": key, "label": EVENT_TYPE_LABELS[key]}
            for key in EVENT_TYPES
        ],
        statuses=[
            {"value": key, "label": EVENT_STATUS_LABELS[key]}
            for key in EVENT_STATUSES
        ],
    )


@router.get(
    "/students/{student_id}/timeline",
    response_model=TimelineListOut,
    summary="学生时间轴",
)
def get_student_timeline(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TimelineListOut:
    """聚合排课、手工节点与档案派生状态。"""
    try:
        items = timeline_service.build_timeline(db, student_id, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return TimelineListOut(
        student_id=student_id,
        items=items,
        total=len(items),
        summary=timeline_service.timeline_summary(items),
    )


@router.post(
    "/students/{student_id}/timeline",
    response_model=TimelineItemOut,
    status_code=status.HTTP_201_CREATED,
    summary="新增时间轴节点",
)
def create_timeline_event(
    student_id: int,
    payload: TimelineEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TimelineItemOut:
    try:
        event = timeline_service.create_event(db, current_user.id, student_id, payload)
        items = timeline_service.build_timeline(db, student_id, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    for item in items:
        if item.id == f"manual:{event.id}":
            return item
    raise HTTPException(status_code=500, detail="创建成功但读取失败")


@router.patch(
    "/timeline/events/{event_id}",
    response_model=TimelineItemOut,
    summary="更新时间轴节点",
)
def update_timeline_event(
    event_id: int,
    payload: TimelineEventUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TimelineItemOut:
    event = timeline_service.get_owned_event(db, event_id, current_user.id)
    if event is None:
        raise HTTPException(status_code=404, detail="节点不存在")
    try:
        updated = timeline_service.update_event(db, event, payload)
        items = timeline_service.build_timeline(db, updated.student_id, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    for item in items:
        if item.id == f"manual:{updated.id}":
            return item
    raise HTTPException(status_code=500, detail="更新成功但读取失败")


@router.delete(
    "/timeline/events/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除时间轴节点",
)
def delete_timeline_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    event = timeline_service.get_owned_event(db, event_id, current_user.id)
    if event is None:
        raise HTTPException(status_code=404, detail="节点不存在")
    timeline_service.delete_event(db, event)
