from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models import User
from app.schemas.follow_up import FollowUpCreate, FollowUpListOut, FollowUpOut, FollowUpUpdate
from app.services import follow_ups as follow_up_service

router = APIRouter(prefix="/follow-ups", tags=["跟进"])


@router.get("", response_model=FollowUpListOut, summary="跟进记录列表")
def list_follow_ups(
    student_id: int | None = Query(default=None, title="学生 ID"),
    contact_with: str | None = Query(default=None, title="沟通对象"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FollowUpListOut:
    """按当前老师筛选跟进记录，可按学生/对象过滤。"""
    items = follow_up_service.list_follow_ups(
        db,
        current_user.id,
        student_id=student_id,
        contact_with=contact_with,
    )
    return FollowUpListOut(
        items=[FollowUpOut.model_validate(item) for item in items],
        total=len(items),
    )


@router.post(
    "",
    response_model=FollowUpOut,
    status_code=status.HTTP_201_CREATED,
    summary="新建跟进记录",
)
def create_follow_up(
    payload: FollowUpCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FollowUpOut:
    """创建跟进；若填写下次提醒，将同步学生联系时间，并可自动生成待办。"""
    try:
        item = follow_up_service.create_follow_up(db, current_user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return FollowUpOut.model_validate(item)


@router.get("/{follow_up_id}", response_model=FollowUpOut, summary="跟进详情")
def get_follow_up(
    follow_up_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FollowUpOut:
    item = follow_up_service.get_owned_follow_up(db, follow_up_id, current_user.id)
    if item is None:
        raise HTTPException(status_code=404, detail="跟进记录不存在")
    return FollowUpOut.model_validate(item)


@router.patch("/{follow_up_id}", response_model=FollowUpOut, summary="更新跟进记录")
def update_follow_up(
    follow_up_id: int,
    payload: FollowUpUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FollowUpOut:
    item = follow_up_service.get_owned_follow_up(db, follow_up_id, current_user.id)
    if item is None:
        raise HTTPException(status_code=404, detail="跟进记录不存在")
    try:
        updated = follow_up_service.update_follow_up(db, item, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return FollowUpOut.model_validate(updated)


@router.delete("/{follow_up_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除跟进记录")
def delete_follow_up(
    follow_up_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    item = follow_up_service.get_owned_follow_up(db, follow_up_id, current_user.id)
    if item is None:
        raise HTTPException(status_code=404, detail="跟进记录不存在")
    follow_up_service.delete_follow_up(db, item)
