import json
from datetime import datetime

from pydantic import BaseModel, Field


class MatchStudentBrief(BaseModel):
    id: int = Field(title="学生 ID")
    name: str = Field(title="学生姓名")
    major: str | None = Field(title="专业")
    application_stage: str | None = Field(title="申请阶段")
    portfolio_progress: int = Field(title="作品集完成度")
    target_country: str | None = Field(default=None, title="目标国家")

    model_config = {"from_attributes": True}


class MatchCourseBrief(BaseModel):
    id: int = Field(title="课程 ID")
    name: str = Field(title="课程名称")
    course_type: str = Field(title="课程类型")
    goal: str | None = Field(title="课程目标")

    model_config = {"from_attributes": True}


class MatchResultOut(BaseModel):
    id: int = Field(title="匹配结果 ID")
    student_id: int = Field(title="学生 ID")
    student: MatchStudentBrief | None = Field(default=None, title="学生")
    score: float = Field(title="匹配分")
    rank: int = Field(title="排名")
    reasons: list[str] = Field(default_factory=list, title="推荐理由")
    schools: list[str] = Field(default_factory=list, title="目标院校")
    tags: list[str] = Field(default_factory=list, title="标签")


class MatchRunOut(BaseModel):
    id: int = Field(title="匹配批次 ID")
    course_id: int = Field(title="课程 ID")
    course: MatchCourseBrief | None = Field(default=None, title="课程")
    engine_version: str = Field(title="引擎版本")
    created_at: datetime = Field(title="创建时间")
    results: list[MatchResultOut] = Field(default_factory=list, title="推荐名单")
    total: int = Field(title="推荐人数")


class MatchRunRequest(BaseModel):
    course_id: int = Field(title="课程 ID")
    min_score: float = Field(default=25, ge=0, le=100, title="最低匹配分")


class ScriptBundleOut(BaseModel):
    student_id: int = Field(title="学生 ID")
    course_id: int = Field(title="课程 ID")
    engine_version: str = Field(title="引擎版本")
    wechat_student: str = Field(title="给学生微信话术")
    parent: str = Field(title="给家长沟通话术")
    phone_outline: str = Field(title="电话沟通提纲")


class ScriptRequest(BaseModel):
    course_id: int = Field(title="课程 ID")
    student_id: int = Field(title="学生 ID")
    match_result_id: int | None = Field(default=None, title="匹配结果 ID")


class CreateMatchTaskRequest(BaseModel):
    course_id: int = Field(title="课程 ID")
    student_id: int = Field(title="学生 ID")
    title: str | None = Field(default=None, title="任务标题")


def parse_reasons(raw: str | list[str] | None) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(item) for item in raw]
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return [str(item) for item in data]
    except json.JSONDecodeError:
        pass
    return [raw] if raw else []
