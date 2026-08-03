from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.schemas.student import TagOut


TASK_PRIORITIES = ["urgent", "normal", "low"]
TASK_STATUSES = ["todo", "done"]
TASK_SOURCES = ["manual", "follow_up", "match", "system"]

PRIORITY_LABELS = {
    "urgent": "紧急",
    "normal": "普通",
    "low": "低",
}


class TaskStudentBrief(BaseModel):
    id: int = Field(title="学生 ID")
    name: str = Field(title="学生姓名")

    model_config = {"from_attributes": True}


class TaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=200, title="任务名称")
    student_id: int | None = Field(default=None, title="对应学生 ID")
    due_at: datetime | None = Field(default=None, title="截止时间")
    priority: str = Field(default="normal", title="优先级")
    status: str = Field(default="todo", title="状态")
    source: str = Field(default="manual", title="来源")

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: str) -> str:
        if value not in TASK_PRIORITIES:
            raise ValueError("优先级须为 urgent / normal / low")
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in TASK_STATUSES:
            raise ValueError("状态须为 todo / done")
        return value

    @field_validator("source")
    @classmethod
    def validate_source(cls, value: str) -> str:
        if value not in TASK_SOURCES:
            raise ValueError("来源无效")
        return value


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200, title="任务名称")
    student_id: int | None = Field(default=None, title="对应学生 ID")
    due_at: datetime | None = Field(default=None, title="截止时间")
    priority: str | None = Field(default=None, title="优先级")
    status: str | None = Field(default=None, title="状态")
    clear_student: bool = Field(default=False, title="清空学生关联")
    clear_due_at: bool = Field(default=False, title="清空截止时间")

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if value not in TASK_PRIORITIES:
            raise ValueError("优先级须为 urgent / normal / low")
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if value not in TASK_STATUSES:
            raise ValueError("状态须为 todo / done")
        return value


class TaskOut(BaseModel):
    id: int = Field(title="任务 ID")
    owner_id: int = Field(title="负责教务 ID")
    title: str = Field(title="任务名称")
    student_id: int | None = Field(title="学生 ID")
    student: TaskStudentBrief | None = Field(default=None, title="对应学生")
    due_at: datetime | None = Field(title="截止时间")
    priority: str = Field(title="优先级")
    status: str = Field(title="状态")
    source: str = Field(title="来源")
    created_at: datetime = Field(title="创建时间")
    updated_at: datetime = Field(title="更新时间")

    model_config = {"from_attributes": True}


class TaskListOut(BaseModel):
    items: list[TaskOut] = Field(title="任务列表")
    total: int = Field(title="总数")


class ContactStudentOut(BaseModel):
    id: int = Field(title="学生 ID")
    name: str = Field(title="学生姓名")
    major: str | None = Field(title="专业")
    application_stage: str | None = Field(title="申请阶段")
    next_contact_at: datetime | None = Field(title="应联系时间")
    tags: list[TagOut] = Field(default_factory=list, title="标签")

    model_config = {"from_attributes": True}


class DashboardOut(BaseModel):
    today_tasks: list[TaskOut] = Field(title="今日待办")
    contact_students: list[ContactStudentOut] = Field(title="今天需要联系的学生")
    upcoming_tasks: list[TaskOut] = Field(title="即将截止任务")
    incomplete_tasks: list[TaskOut] = Field(title="未完成事项")
    stats: dict[str, int] = Field(title="统计")
