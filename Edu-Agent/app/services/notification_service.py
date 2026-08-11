"""
通知服务：日志查询与手动触发扫描。
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.notification_log import NotificationLog
from app.models.schemas import NotificationLogListResponse, NotificationLogResponse
from app.services.reminder_service import ReminderService


class NotificationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_logs(self, *, limit: int = 50, offset: int = 0) -> NotificationLogListResponse:
        limit = max(1, min(limit, 200))
        offset = max(0, offset)
        total = int(self.db.scalar(select(func.count(NotificationLog.id))) or 0)
        stmt = (
            select(NotificationLog)
            .order_by(NotificationLog.created_at.desc(), NotificationLog.id.desc())
            .limit(limit)
            .offset(offset)
        )
        items = list(self.db.scalars(stmt).all())
        return NotificationLogListResponse(
            total=total,
            items=[NotificationLogResponse.model_validate(i) for i in items],
        )

    def run_due_now(self) -> dict:
        """手动立即扫描（测试与应急）。"""
        return ReminderService(self.db).process_due_reminders()
