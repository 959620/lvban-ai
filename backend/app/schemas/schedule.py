from datetime import date

from pydantic import BaseModel, Field, field_validator, model_validator

SESSION_STATUSES = ["scheduled", "completed", "cancelled", "absent"]
SESSION_TYPES = ["一对一", "小班", "作品集辅导", "文书辅导", "模拟面试", "其他"]

STATUS_LABELS = {
    "scheduled": "已安排",
    "completed": "已完成",
    "cancelled": "已取消",
    "absent": "缺课",
}


def _valid_hhmm(value: str) -> str:
    parts = value.split(":")
    if len(parts) != 2:
        raise ValueError("时间格式须为 HH:MM")
    hour, minute = parts
    if not (hour.isdigit() and minute.isdigit()):
        raise ValueError("时间格式须为 HH:MM")
    h, m = int(hour), int(minute)
    if not (0 <= h <= 23 and 0 <= m <= 59):
        raise ValueError("时间超出有效范围")
    return f"{h:02d}:{m:02d}"


class SessionStudentBrief(BaseModel):
    id: int = Field(title="学生 ID")
    name: str = Field(title="学生姓名")

    model_config = {"from_attributes": True}


class SessionCourseBrief(BaseModel):
    id: int = Field(title="课程 ID")
    name: str = Field(title="课程名称")

    model_config = {"from_attributes": True}


class ClassSessionBase(BaseModel):
    student_id: int = Field(title="学生 ID")
    course_id: int | None = Field(default=None, title="关联课程 ID")
    session_date: date = Field(title="上课日期")
    start_time: str = Field(title="开始时间")
    end_time: str = Field(title="结束时间")
    classroom: str | None = Field(default=None, max_length=64, title="教室")
    teacher_name: str | None = Field(default=None, max_length=64, title="老师")
    session_type: str = Field(default="一对一", title="课程类型")
    status: str = Field(default="scheduled", title="状态")
    notes: str | None = Field(default=None, title="备注")

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_time(cls, value: str) -> str:
        return _valid_hhmm(value.strip())

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in SESSION_STATUSES:
            raise ValueError("状态无效")
        return value

    @field_validator("session_type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        if value not in SESSION_TYPES:
            raise ValueError("课程类型无效")
        return value

    @model_validator(mode="after")
    def validate_range(self):
        if self.start_time >= self.end_time:
            raise ValueError("结束时间必须晚于开始时间")
        return self


class ClassSessionCreate(ClassSessionBase):
    pass


class ClassSessionUpdate(BaseModel):
    student_id: int | None = Field(default=None, title="学生 ID")
    course_id: int | None = Field(default=None, title="关联课程 ID")
    clear_course: bool = Field(default=False, title="清空课程关联")
    session_date: date | None = Field(default=None, title="上课日期")
    start_time: str | None = Field(default=None, title="开始时间")
    end_time: str | None = Field(default=None, title="结束时间")
    classroom: str | None = Field(default=None, title="教室")
    teacher_name: str | None = Field(default=None, title="老师")
    session_type: str | None = Field(default=None, title="课程类型")
    status: str | None = Field(default=None, title="状态")
    notes: str | None = Field(default=None, title="备注")

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_time(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return _valid_hhmm(value.strip())

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if value not in SESSION_STATUSES:
            raise ValueError("状态无效")
        return value

    @field_validator("session_type")
    @classmethod
    def validate_type(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if value not in SESSION_TYPES:
            raise ValueError("课程类型无效")
        return value


class ClassSessionOut(BaseModel):
    id: int = Field(title="排课 ID")
    owner_id: int = Field(title="负责教务 ID")
    student_id: int = Field(title="学生 ID")
    student: SessionStudentBrief | None = Field(default=None, title="学生")
    course_id: int | None = Field(title="课程 ID")
    course: SessionCourseBrief | None = Field(default=None, title="课程")
    session_date: date = Field(title="上课日期")
    start_time: str = Field(title="开始时间")
    end_time: str = Field(title="结束时间")
    classroom: str | None = Field(title="教室")
    teacher_name: str | None = Field(title="老师")
    session_type: str = Field(title="课程类型")
    status: str = Field(title="状态")
    notes: str | None = Field(title="备注")
    classroom_conflict: bool = Field(default=False, title="是否教室冲突")

    model_config = {"from_attributes": True}


class ClassSessionListOut(BaseModel):
    items: list[ClassSessionOut] = Field(title="排课列表")
    total: int = Field(title="总数")
    query_date: date | None = Field(default=None, title="查询日期")
    occupied_classrooms: list[str] = Field(default_factory=list, title="当日占用教室")
    absent_count: int = Field(default=0, title="缺课数")


class ScheduleOptionsOut(BaseModel):
    session_types: list[str] = Field(title="课程类型选项")
    statuses: list[dict[str, str]] = Field(title="状态选项")
