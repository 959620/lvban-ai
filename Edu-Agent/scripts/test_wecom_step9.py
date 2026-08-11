"""
Step 9 企业微信通知本地验证（dry-run + mock webhook）。

运行：
  cd Edu-Agent
  .venv/bin/python scripts/test_wecom_step9.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.notification.base import NotificationPayload
from app.notification.factory import build_notifiers, channels_status
from app.notification.wecom import WeComNotifier
from config.settings import Settings, get_settings


def test_wecom_dry_run_webhook() -> None:
    settings = Settings(
        notify_wecom=True,
        notify_wecom_dry_run=True,
        wecom_webhook_url="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=demo",
        wecom_msg_type="markdown",
    )
    notifier = WeComNotifier(settings)
    assert notifier.mode == "webhook"
    notifier.send(NotificationPayload(title="教务提醒", body="请跟进王同学作品集"))
    files = list((ROOT / "data" / "wecom_outbox").glob("*_webhook.json"))
    assert files, "dry-run 应写出 webhook json"
    data = json.loads(files[-1].read_text(encoding="utf-8"))
    assert data["msgtype"] == "markdown"
    print("dry_run_webhook_ok", files[-1].name)


def test_wecom_dry_run_app() -> None:
    settings = Settings(
        notify_wecom=True,
        notify_wecom_dry_run=True,
        wecom_webhook_url="",  # 明确关闭 webhook，验证应用消息模式
        wecom_corp_id="wwcorp",
        wecom_agent_id="1000002",
        wecom_secret="secret",
    )
    notifier = WeComNotifier(settings)
    assert notifier.mode == "app"
    notifier.send(NotificationPayload(title="应用消息", body="催李同学交稿"))
    files = list((ROOT / "data" / "wecom_outbox").glob("*_app.json"))
    assert files
    print("dry_run_app_ok", files[-1].name)


def test_wecom_webhook_http_mocked() -> None:
    settings = Settings(
        notify_wecom=True,
        notify_wecom_dry_run=False,
        wecom_webhook_url="https://example.test/webhook",
    )
    notifier = WeComNotifier(settings)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"errcode": 0, "errmsg": "ok"}

    with patch("app.notification.wecom.httpx.Client") as client_cls:
        client = client_cls.return_value.__enter__.return_value
        client.post.return_value = mock_resp
        notifier.send(NotificationPayload(title="HTTP测试", body="hello wecom"))
        assert client.post.called
    print("webhook_http_ok")


def test_factory_includes_wecom() -> None:
    settings = Settings(
        notify_local=True,
        notify_email=False,
        notify_wecom=True,
        notify_wecom_dry_run=True,
        wecom_webhook_url="https://example.test/webhook",
    )
    names = [c.name for c in build_notifiers(settings)]
    assert "wecom" in names
    status = channels_status(settings)
    assert status["wecom"]["ready"] is True
    assert status["wecom"]["mode"] == "webhook"
    print("factory_ok", status["active"])


if __name__ == "__main__":
    get_settings.cache_clear()
    test_wecom_dry_run_webhook()
    test_wecom_dry_run_app()
    test_wecom_webhook_http_mocked()
    test_factory_includes_wecom()
    print("ALL_PASSED")
