"""
通知服务：日志查询、通道状态、测试发送、手动扫描。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.notification_log import NotificationLog
from app.models.schemas import (
    NotificationLogListResponse,
    NotificationLogResponse,
    NotificationTestRequest,
    NotificationTestResponse,
)
from app.notification.base import NotificationPayload
from app.notification.factory import build_notifiers, channels_status, get_notifier_by_name
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

    def get_channels_status(self) -> dict:
        return channels_status()

    def send_test(self, payload: NotificationTestRequest) -> NotificationTestResponse:
        """
        向指定/全部已启用通道发送测试通知，并写入 notification_logs。
        """
        notifiers = build_notifiers()
        targets = notifiers
        if payload.channel:
            found = get_notifier_by_name(payload.channel, notifiers)
            if found is None:
                return NotificationTestResponse(
                    ok=False,
                    results=[{"channel": payload.channel, "status": "failed", "error": "通道未启用"}],
                )
            targets = [found]

        title = payload.title or "Edu-Agent 测试通知"
        body = payload.body or f"这是一条测试消息（{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}）"
        results: list[dict] = []

        for notifier in targets:
            try:
                notifier.send(NotificationPayload(title=title, body=body, meta={"test": True}))
                self.db.add(
                    NotificationLog(
                        reminder_id=None,
                        student_id=None,
                        channel=notifier.name,
                        title=title,
                        body=body,
                        status="success",
                        error_message=None,
                    )
                )
                results.append({"channel": notifier.name, "status": "success"})
            except Exception as exc:  # noqa: BLE001
                self.db.add(
                    NotificationLog(
                        reminder_id=None,
                        student_id=None,
                        channel=notifier.name,
                        title=title,
                        body=body,
                        status="failed",
                        error_message=str(exc)[:1000],
                    )
                )
                results.append({"channel": notifier.name, "status": "failed", "error": str(exc)})

        self.db.commit()
        ok = bool(results) and all(r.get("status") == "success" for r in results)
        return NotificationTestResponse(ok=ok, results=results)
