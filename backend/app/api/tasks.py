from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models import User
from app.schemas.task import (
    ContactStudentOut,
    DashboardOut,
    TaskCreate,
    TaskListOut,
    TaskOut,
    TaskUpdate,
)
from app.services import tasks as task_service

router = APIRouter(prefix="/tasks", tags=["待办"])


def _to_task_out(task) -> TaskOut:
    return TaskOut.model_validate(task)


@router.get("/dashboard", response_model=DashboardOut, summary="工作台汇总")
def dashboard(
    upcoming_days: int = Query(default=3, ge=1, le=14, title="即将截止天数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardOut:
    """今日待办、需联系学生、即将截止与未完成事项。"""
    data = task_service.build_dashboard(db, current_user.id, upcoming_days=upcoming_days)
    return DashboardOut(
        today_tasks=[_to_task_out(item) for item in data["today_tasks"]],
        contact_students=[ContactStudentOut.model_validate(item) for item in data["contact_students"]],
        upcoming_tasks=[_to_task_out(item) for item in data["upcoming_tasks"]],
        incomplete_tasks=[_to_task_out(item) for item in data["incomplete_tasks"]],
        stats=data["stats"],
    )


@router.get("", response_model=TaskListOut, summary="待办列表")
def list_tasks(
    status: str | None = Query(default=None, title="状态"),
    priority: str | None = Query(default=None, title="优先级"),
    student_id: int | None = Query(default=None, title="学生 ID"),
    due_on: date | None = Query(default=None, title="截止日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskListOut:
    items = task_service.list_tasks(
        db,
        current_user.id,
        status=status,
        priority=priority,
        student_id=student_id,
        due_on=due_on,
    )
    return TaskListOut(items=[_to_task_out(item) for item in items], total=len(items))


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED, summary="新建待办")
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskOut:
    try:
        task = task_service.create_task(db, current_user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_task_out(task)


@router.patch("/{task_id}", response_model=TaskOut, summary="更新待办")
def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskOut:
    task = task_service.get_owned_task(db, task_id, current_user.id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    try:
        updated = task_service.update_task(db, task, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_task_out(updated)


@router.post("/{task_id}/toggle", response_model=TaskOut, summary="勾选完成/取消完成")
def toggle_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskOut:
    task = task_service.get_owned_task(db, task_id, current_user.id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    next_status = "done" if task.status == "todo" else "todo"
    updated = task_service.update_task(db, task, TaskUpdate(status=next_status))
    return _to_task_out(updated)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除待办")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    task = task_service.get_owned_task(db, task_id, current_user.id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    task_service.delete_task(db, task)
