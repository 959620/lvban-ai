"""
Step 8 邮件通知本地验证（dry-run，不连真实 SMTP）。

运行：
  cd Edu-Agent
  .venv/bin/python scripts/test_email_step8.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.notification.base import NotificationPayload
from app.notification.email import EmailNotifier
from app.notification.factory import build_notifiers, channels_status, enabled_channel_names
from config.settings import Settings, get_settings


def test_email_dry_run() -> None:
    settings = Settings(
        notify_email=True,
        notify_email_dry_run=True,
        notify_email_to="teacher@example.com",
        smtp_from="edu-agent@example.com",
    )
    notifier = EmailNotifier(settings)
    notifier.send(
        NotificationPayload(
            title="教务提醒测试",
            body="提醒：明天下午3点需要跟进王同学作品集修改，请提前准备。",
        )
    )
    outbox = ROOT / "data" / "email_outbox"
    files = list(outbox.glob("*.eml"))
    assert files, "dry-run 应写出 .eml 文件"
    print("dry_run_ok", files[-1].name)


def test_factory_with_email() -> None:
    settings = Settings(
        notify_local=True,
        notify_email=True,
        notify_email_dry_run=True,
        notify_email_to="teacher@example.com",
        smtp_from="edu-agent@example.com",
    )
    channels = build_notifiers(settings)
    names = [c.name for c in channels]
    assert names == ["local", "email"]
    status = channels_status(settings)
    assert status["email"]["ready"] is True
    assert enabled_channel_names(settings) == ["local", "email"]
    print("factory_ok", status["active"])


def test_email_missing_to_raises() -> None:
    settings = Settings(notify_email=True, notify_email_dry_run=True, notify_email_to="")
    notifier = EmailNotifier(settings)
    try:
        notifier.send(NotificationPayload(title="x", body="y"))
        raise AssertionError("should raise")
    except ValueError as exc:
        assert "NOTIFY_EMAIL_TO" in str(exc)
        print("validation_ok", exc)


if __name__ == "__main__":
    # 避免污染进程内 settings 缓存影响其他测试
    get_settings.cache_clear()
    test_email_dry_run()
    test_factory_with_email()
    test_email_missing_to_raises()
    print("ALL_PASSED")
