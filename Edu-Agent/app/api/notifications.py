"""
通知相关 API（Step 6）。

- GET  /api/notifications          通知日志
- POST /api/notifications/run-once 立即扫描到期提醒（便于测试）
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.schemas import NotificationLogListResponse, ReminderScanResult
from app.scheduler.jobs import scheduler_status
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _service(db: Session = Depends(get_db)) -> NotificationService:
    return NotificationService(db)


@router.get("", response_model=NotificationLogListResponse)
def list_notification_logs(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    service: NotificationService = Depends(_service),
) -> NotificationLogListResponse:
    """查看通知发送历史。"""
    return service.list_logs(limit=limit, offset=offset)


@router.post("/run-once", response_model=ReminderScanResult)
def run_due_reminders_once(
    service: NotificationService = Depends(_service),
) -> ReminderScanResult:
    """
    立即扫描并发送到期提醒。

    为什么提供手动接口：本地测试不必等调度周期；生产也可作应急补发。
    """
    stats = service.run_due_now()
    return ReminderScanResult(**stats)


@router.get("/scheduler-status")
def get_scheduler_status() -> dict:
    """查看调度器是否在跑、下次触发时间。"""
    return scheduler_status()
