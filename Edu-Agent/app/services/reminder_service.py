"""
提醒服务（Step 4：创建任务时生成提醒计划；Step 5：取消/重建；Step 6：调度发送）。
"""

from datetime import datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.reminder import Reminder
from app.models.task import Task


# 默认：提前 24h / 2h / 到期
DEFAULT_OFFSETS_MINUTES = [1440, 120, 0]


class ReminderService:
    """提醒计划与发送编排。"""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_default_reminders(
        self,
        task: Task,
        offsets_minutes: list[int] | None = None,
        channel: str = "local",
    ) -> list[Reminder]:
        """
        根据 due_at 生成相对提醒。

        无 due_at 时不创建提醒（避免无意义的定时任务）。
        仅创建 remind_at > now 的提醒。
        """
        if task.due_at is None:
            return []

        offsets = offsets_minutes if offsets_minutes is not None else DEFAULT_OFFSETS_MINUTES
        now = datetime.now()
        created: list[Reminder] = []

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
                channel=channel,
            )
            self.db.add(reminder)
            created.append(reminder)

        self.db.flush()
        return created

    def cancel_pending_for_task(self, task_id: int, *, reason: str = "cancelled") -> int:
        """
        取消任务下尚未发送的提醒。

        reason:
        - cancelled：任务取消
        - skipped：任务完成（不再提醒）
        """
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
        channel: str = "local",
    ) -> list[Reminder]:
        """截止时间变更后：取消旧 scheduled，再按新 due_at 生成。"""
        self.cancel_pending_for_task(task.id, reason="cancelled")
        return self.create_default_reminders(
            task,
            offsets_minutes=offsets_minutes,
            channel=channel,
        )

    def list_by_task(self, task_id: int) -> list[Reminder]:
        stmt = select(Reminder).where(Reminder.task_id == task_id).order_by(Reminder.remind_at.asc())
        return list(self.db.scalars(stmt).all())
