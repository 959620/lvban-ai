from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.constants import APPLICATION_STAGES, MAJORS, SCHOOL_PRIORITIES


class TagOut(BaseModel):
    id: int = Field(title="标签 ID")
    name: str = Field(title="标签名称")
    category: str = Field(title="分类")

    model_config = {"from_attributes": True}


class StudentSchoolIn(BaseModel):
    school_name: str = Field(min_length=1, max_length=128, title="院校名称")
    priority: str | None = Field(default=None, title="优先级", description="主申 / 冲刺 / 保底")

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        if value not in SCHOOL_PRIORITIES:
            raise ValueError(f"优先级须为：{' / '.join(SCHOOL_PRIORITIES)}")
        return value


class StudentSchoolOut(StudentSchoolIn):
    id: int = Field(title="记录 ID")

    model_config = {"from_attributes": True}


class StudentBase(BaseModel):
    name: str = Field(min_length=1, max_length=64, title="学生姓名")
    grade: str | None = Field(default=None, max_length=32, title="年级")
    phone: str | None = Field(default=None, max_length=64, title="学生联系方式")
    parent_phone: str | None = Field(default=None, max_length=64, title="家长联系方式")

    major: str | None = Field(default=None, title="艺术专业方向")
    target_country: str | None = Field(default=None, max_length=64, title="目标国家")
    target_major: str | None = Field(default=None, max_length=128, title="目标专业")
    intake_year: int | None = Field(default=None, ge=2020, le=2040, title="入学年份")
    application_stage: str | None = Field(default=None, title="当前申请阶段")

    portfolio_started: bool = Field(default=False, title="是否开始作品集")
    portfolio_project_count: int = Field(default=0, ge=0, title="当前项目数量")
    portfolio_progress: int = Field(default=0, ge=0, le=100, title="作品集完成度")

    personality_notes: str | None = Field(default=None, title="学生性格")
    family_notes: str | None = Field(default=None, title="家庭情况")
    communication_notes: str | None = Field(default=None, title="沟通习惯")
    important_events: str | None = Field(default=None, title="重要事件")
    next_contact_at: datetime | None = Field(default=None, title="下次应联系时间")

    @field_validator("major")
    @classmethod
    def validate_major(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        if value not in MAJORS:
            raise ValueError(f"专业须为预设选项之一")
        return value

    @field_validator("application_stage")
    @classmethod
    def validate_stage(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        if value not in APPLICATION_STAGES:
            raise ValueError("申请阶段须为预设选项之一")
        return value


class StudentCreate(StudentBase):
    schools: list[StudentSchoolIn] = Field(default_factory=list, title="目标院校")
    tag_ids: list[int] = Field(default_factory=list, title="标签 ID 列表")


class StudentUpdate(StudentBase):
    schools: list[StudentSchoolIn] = Field(default_factory=list, title="目标院校")
    tag_ids: list[int] = Field(default_factory=list, title="标签 ID 列表")


class StudentOut(StudentBase):
    id: int = Field(title="学生 ID")
    owner_id: int = Field(title="负责教务 ID")
    schools: list[StudentSchoolOut] = Field(default_factory=list, title="目标院校")
    tags: list[TagOut] = Field(default_factory=list, title="标签")
    created_at: datetime = Field(title="创建时间")
    updated_at: datetime = Field(title="更新时间")

    model_config = {"from_attributes": True}


class StudentListOut(BaseModel):
    items: list[StudentOut] = Field(title="学生列表")
    total: int = Field(title="总数")


class StudentOptionsOut(BaseModel):
    majors: list[str] = Field(title="专业方向选项")
    application_stages: list[str] = Field(title="申请阶段选项")
    school_priorities: list[str] = Field(title="院校优先级选项")
    tags: list[TagOut] = Field(title="可用标签")
