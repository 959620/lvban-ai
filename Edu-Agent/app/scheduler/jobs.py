"""
调度器启动/停止（占位，Step 6 实现）。
"""

from apscheduler.schedulers.background import BackgroundScheduler

_scheduler: BackgroundScheduler | None = None


def start_scheduler() -> None:
    """在 FastAPI startup 时调用。"""
    global _scheduler
    # Step 6: 注册 IntervalTrigger，调用 ReminderService.process_due_reminders()
    _scheduler = None


def shutdown_scheduler() -> None:
    """在 FastAPI shutdown 时调用。"""
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
