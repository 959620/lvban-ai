from datetime import datetime

from pydantic import BaseModel, Field, field_validator

CONTACT_WITH_OPTIONS = ["student", "parent"]
CONTACT_WITH_LABELS = {"student": "学生", "parent": "家长"}


class FollowUpStudentBrief(BaseModel):
    id: int = Field(title="学生 ID")
    name: str = Field(title="学生姓名")

    model_config = {"from_attributes": True}


class FollowUpBase(BaseModel):
    student_id: int = Field(title="学生 ID")
    contact_date: datetime = Field(title="沟通日期")
    contact_with: str = Field(default="student", title="沟通对象")
    content: str = Field(min_length=1, title="沟通内容")
    result: str | None = Field(default=None, title="结果")
    next_action: str | None = Field(default=None, title="下一步")
    next_remind_at: datetime | None = Field(default=None, title="下次提醒时间")
    create_task: bool = Field(
        default=True,
        title="自动创建待办",
        description="填写下次提醒时，是否自动生成工作台待办",
    )

    @field_validator("contact_with")
    @classmethod
    def validate_contact_with(cls, value: str) -> str:
        if value not in CONTACT_WITH_OPTIONS:
            raise ValueError("沟通对象须为 student 或 parent")
        return value


class FollowUpCreate(FollowUpBase):
    pass


class FollowUpUpdate(BaseModel):
    contact_date: datetime | None = Field(default=None, title="沟通日期")
    contact_with: str | None = Field(default=None, title="沟通对象")
    content: str | None = Field(default=None, min_length=1, title="沟通内容")
    result: str | None = Field(default=None, title="结果")
    next_action: str | None = Field(default=None, title="下一步")
    next_remind_at: datetime | None = Field(default=None, title="下次提醒时间")
    clear_next_remind_at: bool = Field(default=False, title="清空下次提醒")
    create_task: bool = Field(default=True, title="自动创建待办")

    @field_validator("contact_with")
    @classmethod
    def validate_contact_with(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if value not in CONTACT_WITH_OPTIONS:
            raise ValueError("沟通对象须为 student 或 parent")
        return value


class FollowUpOut(BaseModel):
    id: int = Field(title="跟进 ID")
    owner_id: int = Field(title="负责教务 ID")
    student_id: int = Field(title="学生 ID")
    student: FollowUpStudentBrief | None = Field(default=None, title="学生")
    contact_date: datetime = Field(title="沟通日期")
    contact_with: str = Field(title="沟通对象")
    content: str = Field(title="沟通内容")
    result: str | None = Field(title="结果")
    next_action: str | None = Field(title="下一步")
    next_remind_at: datetime | None = Field(title="下次提醒时间")
    created_task_id: int | None = Field(title="关联待办 ID")
    created_at: datetime = Field(title="创建时间")
    updated_at: datetime = Field(title="更新时间")

    model_config = {"from_attributes": True}


class FollowUpListOut(BaseModel):
    items: list[FollowUpOut] = Field(title="跟进列表")
    total: int = Field(title="总数")
