"""
健康检查接口。

用途：确认服务已启动；附带调度器、解析引擎、通知通道状态。
"""

from fastapi import APIRouter

from app.ai.parser import parser_status
from app.notification.factory import channels_status
from app.scheduler.jobs import scheduler_status

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict:
    return {
        "status": "ok",
        "service": "Edu-Agent",
        "step": 8,
        "message": "本地 + 邮件通知已就绪（邮件支持 dry-run）",
        "scheduler": scheduler_status(),
        "parser": parser_status(),
        "channels": channels_status(),
    }
