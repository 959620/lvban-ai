from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import AiStatusOut
from app.services.ai import get_ai_status, run_assistant

router = APIRouter(prefix="/ai", tags=["AI 助手"])


class AiChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000, title="提问内容", description="发给助手的自然语言指令")
    student_id: int | None = Field(default=None, title="学生 ID", description="可选，绑定学生上下文")
    course_id: int | None = Field(default=None, title="课程 ID", description="可选，绑定课程上下文")


class AiChatResponse(BaseModel):
    engine: str = Field(title="引擎")
    reply: str = Field(title="回复内容")
    model: str = Field(title="模型")
    context: dict = Field(title="上下文摘要")


@router.get("/status", response_model=AiStatusOut, summary="AI 配置状态")
def ai_status(current_user: User = Depends(get_current_user)) -> AiStatusOut:
    """查看是否已配置 OpenAI，以及当前模型信息。"""
    _ = current_user
    return get_ai_status()


@router.post("/chat", response_model=AiChatResponse, summary="AI 对话")
def ai_chat(
    payload: AiChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AiChatResponse:
    """发送指令给 AI 助手。已配置密钥时调用 OpenAI；否则使用本地匹配/话术兜底。"""
    try:
        result = run_assistant(
            db,
            message=payload.message,
            student_id=payload.student_id,
            course_id=payload.course_id,
            owner_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return AiChatResponse(**result)
