"""
提醒服务（Step 4–6）。

Step 6：扫描到期提醒 → 渲染文案 → 通知通道发送 → 写 notification_logs
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from sqlalchemy import and_, or_, select, update
from sqlalchemy.orm import Session, joinedload

from app.models.notification_log import NotificationLog
from app.models.reminder import Reminder
from app.models.task import Task
from app.notification.base import NotificationChannel, NotificationPayload
from app.notification.factory import build_notifiers, enabled_channel_names, get_notifier_by_name
from app.services.message_templates import render_reminder_message

logger = logging.getLogger("edu_agent.reminder")

# 默认：提前 24h / 2h / 到期
DEFAULT_OFFSETS_MINUTES = [1440, 120, 0]
MAX_RETRY = 3
BATCH_LIMIT = 100


class ReminderService:
    """提醒计划与发送编排。"""

    def __init__(self, db: Session, notifiers: list[NotificationChannel] | None = None) -> None:
        self.db = db
        self.notifiers = notifiers if notifiers is not None else build_notifiers()

    def create_default_reminders(
        self,
        task: Task,
        offsets_minutes: list[int] | None = None,
        channel: str | None = None,
        channels: list[str] | None = None,
    ) -> list[Reminder]:
        """
        根据 due_at 生成相对提醒。

        Step 8：默认按已启用通知通道各生成一套提醒（local / email ...）。
        仍兼容单 channel 参数。
        """
        if task.due_at is None:
            return []

        if channels is None:
            if channel:
                channels = [channel]
            else:
                channels = enabled_channel_names() or ["local"]

        offsets = offsets_minutes if offsets_minutes is not None else DEFAULT_OFFSETS_MINUTES
        now = datetime.now()
        created: list[Reminder] = []

        for ch in channels:
            for offset in offsets:
                remind_at = task.due_at - timedelta(minutes=offset)
                if remind_at <= now:
                    continue
                reminder = Reminder(
                    task_id=task.id,
                    remind_at=remind_at,
                    remind_type="relative",
                    offset_minutes=offset,
                    status="scheduled",
                    channel=ch,
                )
                self.db.add(reminder)
                created.append(reminder)

        self.db.flush()
        return created

    def cancel_pending_for_task(self, task_id: int, *, reason: str = "cancelled") -> int:
        """取消任务下尚未发送的提醒。"""
        status = "cancelled" if reason == "cancelled" else "skipped"
        stmt = (
            update(Reminder)
            .where(Reminder.task_id == task_id, Reminder.status == "scheduled")
            .values(status=status)
        )
        result = self.db.execute(stmt)
        self.db.flush()
        return int(result.rowcount or 0)

    def rebuild_reminders_for_task(
        self,
        task: Task,
        offsets_minutes: list[int] | None = None,
        channel: str | None = None,
        channels: list[str] | None = None,
    ) -> list[Reminder]:
        """截止时间变更后：取消旧 scheduled，再按新 due_at 生成。"""
        self.cancel_pending_for_task(task.id, reason="cancelled")
        return self.create_default_reminders(
            task,
            offsets_minutes=offsets_minutes,
            channel=channel,
            channels=channels,
        )

    def list_by_task(self, task_id: int) -> list[Reminder]:
        stmt = select(Reminder).where(Reminder.task_id == task_id).order_by(Reminder.remind_at.asc())
        return list(self.db.scalars(stmt).all())

    def process_due_reminders(self, *, now: datetime | None = None, limit: int = BATCH_LIMIT) -> dict:
        """
        处理到期提醒（供调度器与手动触发共用）。

        规则：
        1. 拉取 status=scheduled（或 failed 且未超重试）且 remind_at <= now
        2. 任务已 done/cancelled → 标记 skipped，不发送
        3. 发送成功 → sent + notification_logs(success)
        4. 发送失败 → failed + retry_count+1 + notification_logs(failed)
        """
        now = now or datetime.now()
        due = self._fetch_due_reminders(now=now, limit=limit)

        stats = {"scanned": len(due), "sent": 0, "failed": 0, "skipped": 0}
        for reminder in due:
            result = self._process_one(reminder, now=now)
            stats[result] = stats.get(result, 0) + 1

        self.db.commit()
        logger.info("process_due_reminders: %s", stats)
        return stats

    def _fetch_due_reminders(self, *, now: datetime, limit: int) -> list[Reminder]:
        stmt = (
            select(Reminder)
            .options(
                joinedload(Reminder.task).joinedload(Task.student),
            )
            .where(
                Reminder.remind_at <= now,
                or_(
                    Reminder.status == "scheduled",
                    and_(Reminder.status == "failed", Reminder.retry_count < MAX_RETRY),
                ),
            )
            .order_by(Reminder.remind_at.asc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).unique().all())

    def _process_one(self, reminder: Reminder, *, now: datetime) -> str:
        task = reminder.task
        if task is None or task.status in {"done", "cancelled"}:
            reminder.status = "skipped"
            reminder.updated_at = now
            return "skipped"

        title, body = render_reminder_message(task, reminder)
        channel_name = reminder.channel or "local"
        notifier = get_notifier_by_name(channel_name, self.notifiers)

        if notifier is None:
            # 通道未启用时：有本地通道则降级，否则记失败
            notifier = get_notifier_by_name("local", self.notifiers)
            if notifier is None and self.notifiers:
                notifier = self.notifiers[0]

        if notifier is None:
            return self._mark_failed(
                reminder,
                now=now,
                title=title,
                body=body,
                channel=channel_name,
                error=f"通知通道未配置: {channel_name}",
            )

        try:
            notifier.send(
                NotificationPayload(
                    title=title,
                    body=body,
                    meta={
                        "reminder_id": reminder.id,
                        "task_id": task.id,
                        "student_id": task.student_id,
                        "offset_minutes": reminder.offset_minutes,
                    },
                )
            )
        except Exception as exc:  # noqa: BLE001 - 需记录任意发送失败
            logger.exception("reminder %s send failed", reminder.id)
            return self._mark_failed(
                reminder,
                now=now,
                title=title,
                body=body,
                channel=notifier.name,
                error=str(exc),
            )

        reminder.status = "sent"
        reminder.sent_at = now
        reminder.updated_at = now
        self.db.add(
            NotificationLog(
                reminder_id=reminder.id,
                student_id=task.student_id,
                channel=notifier.name,
                title=title,
                body=body,
                status="success",
                error_message=None,
            )
        )
        return "sent"

    def _mark_failed(
        self,
        reminder: Reminder,
        *,
        now: datetime,
        title: str,
        body: str,
        channel: str,
        error: str,
    ) -> str:
        reminder.status = "failed"
        reminder.retry_count = int(reminder.retry_count or 0) + 1
        reminder.updated_at = now
        self.db.add(
            NotificationLog(
                reminder_id=reminder.id,
                student_id=reminder.task.student_id if reminder.task else None,
                channel=channel,
                title=title,
                body=body,
                status="failed",
                error_message=error[:1000],
            )
        )
        return "failed"
