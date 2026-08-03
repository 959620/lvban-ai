from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.constants import COURSE_SUITABLE_STAGES, COURSE_TYPES, MAJORS


class CourseBase(BaseModel):
    name: str = Field(min_length=1, max_length=128, title="课程名称")
    course_type: str = Field(default="其他", title="课程类型")
    suitable_majors: list[str] = Field(default_factory=list, title="适合专业")
    suitable_stages: list[str] = Field(default_factory=list, title="适合阶段")
    goal: str | None = Field(default=None, title="课程目标")
    price: Decimal | None = Field(default=None, ge=0, title="价格")
    teacher_name: str | None = Field(default=None, max_length=64, title="授课老师")
    description: str | None = Field(default=None, title="补充说明")

    @field_validator("course_type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        if value not in COURSE_TYPES:
            raise ValueError("课程类型无效")
        return value

    @field_validator("suitable_majors")
    @classmethod
    def validate_majors(cls, value: list[str]) -> list[str]:
        invalid = [item for item in value if item not in MAJORS]
        if invalid:
            raise ValueError(f"存在无效专业：{', '.join(invalid)}")
        return value

    @field_validator("suitable_stages")
    @classmethod
    def validate_stages(cls, value: list[str]) -> list[str]:
        invalid = [item for item in value if item not in COURSE_SUITABLE_STAGES]
        if invalid:
            raise ValueError(f"存在无效阶段：{', '.join(invalid)}")
        return value


class CourseCreate(CourseBase):
    pass


class CourseUpdate(CourseBase):
    pass


class CourseOut(CourseBase):
    id: int = Field(title="课程 ID")
    owner_id: int = Field(title="负责教务 ID")
    created_at: datetime = Field(title="创建时间")
    updated_at: datetime = Field(title="更新时间")

    model_config = {"from_attributes": True}


class CourseListOut(BaseModel):
    items: list[CourseOut] = Field(title="课程列表")
    total: int = Field(title="总数")


class CourseOptionsOut(BaseModel):
    course_types: list[str] = Field(title="课程类型选项")
    majors: list[str] = Field(title="适合专业选项")
    suitable_stages: list[str] = Field(title="适合阶段选项")
