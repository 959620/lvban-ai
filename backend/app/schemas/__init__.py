from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.student import (
    StudentCreate,
    StudentListOut,
    StudentOptionsOut,
    StudentOut,
    StudentSchoolIn,
    StudentSchoolOut,
    StudentUpdate,
    TagOut,
)


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64, title="用户名", description="登录用户名，至少 3 位")
    password: str = Field(min_length=6, max_length=128, title="密码", description="登录密码，至少 6 位")
    display_name: str = Field(min_length=1, max_length=64, title="显示名称", description="界面展示用的老师姓名")


class UserLogin(BaseModel):
    username: str = Field(title="用户名")
    password: str = Field(title="密码")


class UserOut(BaseModel):
    id: int = Field(title="用户 ID")
    username: str = Field(title="用户名")
    display_name: str = Field(title="显示名称")
    created_at: datetime = Field(title="创建时间")

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str = Field(title="访问令牌", description="后续请求放在 Authorization: Bearer 中")
    token_type: str = Field(default="bearer", title="令牌类型")
    user: UserOut = Field(title="用户信息")


class HealthOut(BaseModel):
    status: str = Field(title="状态", description="正常时为 ok")
    app: str = Field(title="应用名称")


class AiStatusOut(BaseModel):
    configured: bool = Field(title="是否已配置", description="是否已设置 OPENAI_API_KEY")
    model: str = Field(title="模型名称")
    base_url: str = Field(title="接口地址")
    message: str = Field(title="状态说明")


__all__ = [
    "UserCreate",
    "UserLogin",
    "UserOut",
    "TokenOut",
    "HealthOut",
    "AiStatusOut",
    "TagOut",
    "StudentSchoolIn",
    "StudentSchoolOut",
    "StudentCreate",
    "StudentUpdate",
    "StudentOut",
    "StudentListOut",
    "StudentOptionsOut",
]
