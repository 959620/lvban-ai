"""
任务相关 API。

Step 4：
- POST /api/tasks/parse          仅解析预览
- POST /api/tasks                结构化确认创建
- POST /api/tasks/parse-create   一键解析并创建
- GET  /api/tasks/{id}           查看刚创建的任务
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.schemas import (
    NaturalLanguageTaskRequest,
    ParsedTaskPreview,
    ParseAndCreateResponse,
    TaskCreateRequest,
    TaskResponse,
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
    """
    自然语言 → 结构化预览（不入库）。

    UX：教务老师可先看解析结果，改完再点创建，降低误解析风险。
    """
    return service.parse_natural_language(body.text)


@router.post("", response_model=TaskResponse, status_code=201)
def create_task(
    body: TaskCreateRequest,
    service: TaskService = Depends(_service),
) -> TaskResponse:
    """确认后的结构化任务创建，并写入默认提醒计划。"""
    return service.create_task(body)


@router.post("/parse-create", response_model=ParseAndCreateResponse, status_code=201)
def parse_and_create_task(
    body: NaturalLanguageTaskRequest,
    service: TaskService = Depends(_service),
) -> ParseAndCreateResponse:
    """一键：解析 + 创建（适合快速录入场景）。"""
    return service.parse_and_create(
        body.text,
        auto_create_student=body.auto_create_student,
    )


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    service: TaskService = Depends(_service),
) -> TaskResponse:
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task
