"""
APScheduler：定时扫描到期提醒。

设计原因：
- 与 Web 请求同进程，MVP 部署简单
- settings.scheduler_enabled / interval 可关可调
- 真正发送逻辑在 ReminderService，调度器只负责触发
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.database import SessionLocal
from app.services.reminder_service import ReminderService
from config.settings import get_settings

logger = logging.getLogger("edu_agent.scheduler")

_scheduler: BackgroundScheduler | None = None


def run_due_reminder_job() -> dict:
    """调度任务入口：每次独立开 Session，避免跨线程共享。"""
    db = SessionLocal()
    try:
        service = ReminderService(db)
        return service.process_due_reminders()
    except Exception:
        logger.exception("due reminder job failed")
        db.rollback()
        raise
    finally:
        db.close()


def start_scheduler() -> None:
    """在 FastAPI startup 时调用。"""
    global _scheduler
    if _scheduler is not None:
        return

    settings = get_settings()
    scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
    scheduler.add_job(
        run_due_reminder_job,
        trigger=IntervalTrigger(seconds=max(10, int(settings.scheduler_interval_seconds))),
        id="due_reminders",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    _scheduler = scheduler
    logger.info(
        "scheduler started: interval=%ss",
        settings.scheduler_interval_seconds,
    )


def shutdown_scheduler() -> None:
    """在 FastAPI shutdown 时调用。"""
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("scheduler stopped")


def scheduler_status() -> dict:
    """供健康检查 / 调试使用。"""
    settings = get_settings()
    running = _scheduler is not None and _scheduler.running
    jobs = []
    if _scheduler is not None:
        for job in _scheduler.get_jobs():
            jobs.append(
                {
                    "id": job.id,
                    "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                }
            )
    return {
        "enabled": settings.scheduler_enabled,
        "running": running,
        "interval_seconds": settings.scheduler_interval_seconds,
        "jobs": jobs,
    }
