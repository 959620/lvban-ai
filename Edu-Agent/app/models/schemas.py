"""
任务相关 Pydantic Schema。

设计原因：
- API 入参/出参与 ORM 解耦，前端确认卡片可独立演进
- 自然语言解析结果先以 ParsedTask 展示，用户可改后再入库
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Priority = Literal["low", "medium", "high", "urgent"]
TaskStatus = Literal["pending", "in_progress", "done", "cancelled"]
ParseConfidence = Literal["high", "medium", "low", "manual"]


class NaturalLanguageTaskRequest(BaseModel):
    """自然语言创建请求。"""

    text: str = Field(..., min_length=1, max_length=1000, description="自然语言任务描述")
    auto_create_student: bool = Field(
        default=True,
        description="解析到学生名但库中不存在时，是否自动创建简易学生档案",
    )


class ParsedTaskPreview(BaseModel):
    """AI/规则解析预览（尚未入库）。"""

    task: str
    deadline: datetime | None = None
    student: str | None = None
    priority: Priority = "medium"
    parse_confidence: ParseConfidence = "low"
    source_text: str
    reminder_offsets_minutes: list[int] = Field(
        default_factory=lambda: [1440, 120, 0],
        description="默认提醒：提前24h / 2h / 到期",
    )


class TaskCreateRequest(BaseModel):
    """确认后的结构化创建请求（可来自预览编辑）。"""

    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    student_name: str | None = Field(default=None, max_length=100)
    student_id: int | None = None
    priority: Priority = "medium"
    due_at: datetime | None = None
    source_text: str | None = None
    parse_confidence: ParseConfidence = "manual"
    reminder_offsets_minutes: list[int] = Field(default_factory=lambda: [1440, 120, 0])
    auto_create_student: bool = True


class ReminderBrief(BaseModel):
    id: int
    remind_at: datetime
    offset_minutes: int | None
    status: str
    channel: str

    model_config = {"from_attributes": True}


class TaskResponse(BaseModel):
    """任务创建/查询响应。"""

    id: int
    title: str
    description: str | None
    priority: str
    status: str
    due_at: datetime | None
    student_id: int | None
    student_name: str | None = None
    source_text: str | None
    parse_confidence: str | None
    created_at: datetime | None = None
    reminders: list[ReminderBrief] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ParseAndCreateResponse(BaseModel):
    """一键：解析并创建。"""

    parsed: ParsedTaskPreview
    task: TaskResponse
