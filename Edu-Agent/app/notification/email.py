"""
邮件通知（Step 8）。

设计原因：
- send() 保持同步，便于 APScheduler 后台线程直接调用
- 支持 SMTP 实发 + dry-run（写入 data/email_outbox/），无邮箱也能测通链路
- 配置缺失时抛出明确错误，写入 notification_logs 便于排障
"""

from __future__ import annotations

import logging
import smtplib
import ssl
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

from app.notification.base import NotificationChannel, NotificationPayload
from config.settings import BASE_DIR, Settings, get_settings

logger = logging.getLogger("edu_agent.notify.email")


class EmailNotifier(NotificationChannel):
    name = "email"

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.outbox_dir = BASE_DIR / "data" / "email_outbox"

    def send(self, payload: NotificationPayload) -> None:
        to_addr = (self.settings.notify_email_to or "").strip()
        from_addr = (self.settings.smtp_from or self.settings.smtp_user or "").strip()

        if not to_addr:
            raise ValueError("NOTIFY_EMAIL_TO 未配置")
        if not from_addr:
            raise ValueError("SMTP_FROM / SMTP_USER 未配置")

        message = self._build_message(payload, from_addr=from_addr, to_addr=to_addr)

        if self.settings.notify_email_dry_run:
            path = self._write_outbox(message, to_addr=to_addr)
            logger.info("[EMAIL-DRY-RUN] saved to %s | %s", path, payload.title)
            print(f"[EMAIL DRY-RUN] {payload.title} -> {to_addr} ({path})")
            return

        if not self.settings.smtp_host:
            raise ValueError("SMTP_HOST 未配置（或设置 NOTIFY_EMAIL_DRY_RUN=true 做本地演练）")

        self._smtp_send(message, from_addr=from_addr, to_addr=to_addr)
        logger.info("[EMAIL] sent to %s | %s", _mask_email(to_addr), payload.title)
        print(f"[EMAIL NOTIFY] {payload.title} -> {_mask_email(to_addr)}")

    def _build_message(
        self,
        payload: NotificationPayload,
        *,
        from_addr: str,
        to_addr: str,
    ) -> EmailMessage:
        msg = EmailMessage()
        msg["Subject"] = payload.title
        msg["From"] = from_addr
        msg["To"] = to_addr
        msg.set_content(payload.body)
        # 简单 HTML 提升可读性（纯文本仍保留）
        html = (
            f"<html><body>"
            f"<h2 style='font-family:sans-serif'>{_escape(payload.title)}</h2>"
            f"<p style='font-family:sans-serif;line-height:1.6'>{_escape(payload.body)}</p>"
            f"<hr><small>Edu-Agent 教务提醒</small>"
            f"</body></html>"
        )
        msg.add_alternative(html, subtype="html")
        return msg

    def _write_outbox(self, message: EmailMessage, *, to_addr: str) -> Path:
        self.outbox_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        path = self.outbox_dir / f"{stamp}_{to_addr.replace('@', '_at_')}.eml"
        path.write_bytes(message.as_bytes())
        return path

    def _smtp_send(self, message: EmailMessage, *, from_addr: str, to_addr: str) -> None:
        host = self.settings.smtp_host
        port = int(self.settings.smtp_port)
        user = self.settings.smtp_user
        password = self.settings.smtp_password
        use_ssl = bool(self.settings.smtp_use_ssl)
        use_tls = bool(self.settings.smtp_use_tls)

        context = ssl.create_default_context()
        if use_ssl:
            with smtplib.SMTP_SSL(host, port, context=context, timeout=30) as server:
                if user:
                    server.login(user, password)
                server.send_message(message, from_addr=from_addr, to_addrs=[to_addr])
            return

        with smtplib.SMTP(host, port, timeout=30) as server:
            server.ehlo()
            if use_tls:
                server.starttls(context=context)
                server.ehlo()
            if user:
                server.login(user, password)
            server.send_message(message, from_addr=from_addr, to_addrs=[to_addr])


def _mask_email(addr: str) -> str:
    if "@" not in addr:
        return addr[:2] + "***"
    name, domain = addr.split("@", 1)
    return (name[:2] + "***@" + domain) if name else "***@" + domain


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
