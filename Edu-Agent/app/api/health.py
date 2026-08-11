"""
健康检查接口。

用途：确认服务已启动；后续可扩展为检查数据库 / 调度器状态。
"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict:
    return {
        "status": "ok",
        "service": "Edu-Agent",
        "step": 4,
        "message": "任务创建功能已就绪",
    }
