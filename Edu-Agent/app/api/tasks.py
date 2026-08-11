"""
任务相关 API。

Step 4：parse / create / parse-create / get
Step 5：list / update / status（完成·取消联动提醒）
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.schemas import (
    NaturalLanguageTaskRequest,
    ParsedTaskPreview,
    ParseAndCreateResponse,
    TaskCreateRequest,
    TaskListResponse,
    TaskResponse,
    TaskStatusUpdateRequest,
    TaskUpdateRequest,
)
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _service(db: Session = Depends(get_db)) -> TaskService:
    return TaskService(db)


@router.post("/parse", response_model=ParsedTaskPreview)
def parse_task(
    body: NaturalLanguageTaskRequest,
    service: TaskService = Depends(_service),
) -> ParsedTaskPreview:
    """自然语言 → 结构化预览（不入库）。"""
    return service.parse_natural_language(body.text)


@router.post("/parse-create", response_model=ParseAndCreateResponse, status_code=201)
def parse_and_create_task(
    body: NaturalLanguageTaskRequest,
    service: TaskService = Depends(_service),
) -> ParseAndCreateResponse:
    """一键：解析 + 创建。"""
    return service.parse_and_create(
        body.text,
        auto_create_student=body.auto_create_student,
    )


@router.get("", response_model=TaskListResponse)
def list_tasks(
    status: str | None = Query(default=None, description="pending/in_progress/done/cancelled"),
    student_id: int | None = Query(default=None),
    student_name: str | None = Query(default=None, description="按学生姓名模糊筛选"),
    priority: str | None = Query(default=None),
    q: str | None = Query(default=None, description="按标题关键词搜索"),
    overdue: bool = Query(default=False, description="仅看逾期未完成任务"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    service: TaskService = Depends(_service),
) -> TaskListResponse:
    """任务列表与筛选（Step 5）。"""
    return service.list_tasks(
        status=status,
        student_id=student_id,
        student_name=student_name,
        priority=priority,
        q=q,
        include_overdue_only=overdue,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=TaskResponse, status_code=201)
def create_task(
    body: TaskCreateRequest,
    service: TaskService = Depends(_service),
) -> TaskResponse:
    """确认后的结构化任务创建，并写入默认提醒计划。"""
    return service.create_task(body)


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    service: TaskService = Depends(_service),
) -> TaskResponse:
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    body: TaskUpdateRequest,
    service: TaskService = Depends(_service),
) -> TaskResponse:
    """部分更新；截止时间变更会重建未发送提醒。"""
    task = service.update_task(task_id, body)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.patch("/{task_id}/status", response_model=TaskResponse)
def update_task_status(
    task_id: int,
    body: TaskStatusUpdateRequest,
    service: TaskService = Depends(_service),
) -> TaskResponse:
    """
    状态流转。

    done/cancelled 会跳过或取消未发送提醒，避免完成后仍打扰。
    """
    task = service.set_status(task_id, body.status)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task
