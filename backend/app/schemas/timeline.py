from datetime import date

from pydantic import BaseModel, Field, field_validator

EVENT_TYPES = ["portfolio_milestone", "application_milestone", "note"]
EVENT_STATUSES = ["done", "current", "upcoming"]

EVENT_TYPE_LABELS = {
    "portfolio_milestone": "作品集节点",
    "application_milestone": "申请节点",
    "note": "备注节点",
    "course_session": "课程安排",
    "application_stage": "申请阶段",
    "portfolio_status": "作品集状态",
}

EVENT_STATUS_LABELS = {
    "done": "已完成",
    "current": "进行中",
    "upcoming": "待安排/即将",
    "absent": "缺课",
    "cancelled": "已取消",
}


class TimelineEventCreate(BaseModel):
    event_type: str = Field(title="事件类型")
    title: str = Field(min_length=1, max_length=200, title="标题")
    event_date: date = Field(title="日期")
    status: str = Field(default="upcoming", title="状态")
    notes: str | None = Field(default=None, title="备注")
    related_course_id: int | None = Field(default=None, title="关联课程 ID")

    @field_validator("event_type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        if value not in EVENT_TYPES:
            raise ValueError("事件类型须为作品集/申请/备注节点")
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in EVENT_STATUSES:
            raise ValueError("状态无效")
        return value


class TimelineEventUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200, title="标题")
    event_date: date | None = Field(default=None, title="日期")
    status: str | None = Field(default=None, title="状态")
    notes: str | None = Field(default=None, title="备注")
    related_course_id: int | None = Field(default=None, title="关联课程 ID")
    clear_course: bool = Field(default=False, title="清空课程关联")

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if value not in EVENT_STATUSES:
            raise ValueError("状态无效")
        return value


class TimelineItemOut(BaseModel):
    id: str = Field(title="节点 ID", description="manual:123 或 session:45 等")
    source: str = Field(title="来源", description="manual / session / derived")
    event_type: str = Field(title="事件类型")
    event_type_label: str = Field(title="类型名称")
    title: str = Field(title="标题")
    event_date: date = Field(title="日期")
    status: str = Field(title="状态")
    status_label: str = Field(title="状态名称")
    notes: str | None = Field(default=None, title="备注")
    related_session_id: int | None = Field(default=None, title="关联排课 ID")
    related_course_id: int | None = Field(default=None, title="关联课程 ID")
    course_name: str | None = Field(default=None, title="课程名称")
    classroom: str | None = Field(default=None, title="教室")
    teacher_name: str | None = Field(default=None, title="老师")
    editable: bool = Field(title="是否可编辑")


class TimelineListOut(BaseModel):
    student_id: int = Field(title="学生 ID")
    items: list[TimelineItemOut] = Field(title="时间轴节点")
    total: int = Field(title="总数")
    summary: dict[str, int] = Field(title="统计")


class TimelineOptionsOut(BaseModel):
    event_types: list[dict[str, str]] = Field(title="事件类型选项")
    statuses: list[dict[str, str]] = Field(title="状态选项")
