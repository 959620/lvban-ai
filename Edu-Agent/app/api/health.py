"""
健康检查接口。

用途：确认服务已启动；附带调度器状态摘要。
"""

from fastapi import APIRouter

from app.scheduler.jobs import scheduler_status

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict:
    return {
        "status": "ok",
        "service": "Edu-Agent",
        "step": 6,
        "message": "定时提醒已就绪",
        "scheduler": scheduler_status(),
    }
