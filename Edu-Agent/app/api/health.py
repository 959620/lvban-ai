"""
健康检查接口。

用途：确认服务已启动；附带调度器与 AI 解析引擎状态。
"""

from fastapi import APIRouter

from app.ai.parser import parser_status
from app.scheduler.jobs import scheduler_status

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict:
    return {
        "status": "ok",
        "service": "Edu-Agent",
        "step": 7,
        "message": "AI 自然语言解析已接入（无 Key 时规则兜底）",
        "scheduler": scheduler_status(),
        "parser": parser_status(),
    }
