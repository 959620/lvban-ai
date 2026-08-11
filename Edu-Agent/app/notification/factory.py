"""
通知通道工厂。

根据配置组装启用的通道列表；对外提供通道状态（不含密钥）。
"""

from __future__ import annotations

from app.notification.base import NotificationChannel
from app.notification.email import EmailNotifier
from app.notification.local import LocalNotifier
from app.notification.wecom import WeComNotifier
from config.settings import Settings, get_settings


def build_notifiers(settings: Settings | None = None) -> list[NotificationChannel]:
    """按开关返回通道实例。"""
    settings = settings or get_settings()
    channels: list[NotificationChannel] = []

    if settings.notify_local:
        channels.append(LocalNotifier())

    if settings.notify_email:
        channels.append(EmailNotifier(settings))

    if settings.notify_wecom:
        channels.append(WeComNotifier(settings))

    return channels


def get_notifier_by_name(
    name: str,
    channels: list[NotificationChannel] | None = None,
) -> NotificationChannel | None:
    """按通道名查找；找不到返回 None。"""
    channels = channels if channels is not None else build_notifiers()
    for channel in channels:
        if channel.name == name:
            return channel
    return None


def enabled_channel_names(settings: Settings | None = None) -> list[str]:
    """创建提醒时使用的通道名列表。"""
    return [c.name for c in build_notifiers(settings)]


def _mask_secret(value: str, keep: int = 4) -> str | None:
    text = (value or "").strip()
    if not text:
        return None
    if len(text) <= keep:
        return "***"
    return text[:keep] + "***"


def channels_status(settings: Settings | None = None) -> dict:
    """
    通道就绪状态（供前端 / 健康检查）。

    不返回密码等敏感信息。
    """
    settings = settings or get_settings()
    email_to = (settings.notify_email_to or "").strip()
    masked_to = ""
    if email_to and "@" in email_to:
        name, domain = email_to.split("@", 1)
        masked_to = (name[:2] + "***@" + domain) if name else "***@" + domain

    wecom = WeComNotifier(settings) if settings.notify_wecom else None
    wecom_mode = wecom.mode if wecom else "disabled"
    wecom_ready = bool(
        settings.notify_wecom
        and (
            settings.notify_wecom_dry_run
            or wecom_mode in {"webhook", "app"}
        )
    )

    return {
        "local": {
            "enabled": settings.notify_local,
            "ready": settings.notify_local,
        },
        "email": {
            "enabled": settings.notify_email,
            "dry_run": settings.notify_email_dry_run,
            "smtp_host": settings.smtp_host or None,
            "smtp_port": settings.smtp_port,
            "to": masked_to or None,
            "ready": bool(
                settings.notify_email
                and (
                    settings.notify_email_dry_run
                    or (settings.smtp_host and settings.notify_email_to)
                )
            ),
        },
        "wecom": {
            "enabled": settings.notify_wecom,
            "dry_run": settings.notify_wecom_dry_run,
            "mode": wecom_mode,
            "msg_type": settings.wecom_msg_type,
            "webhook_configured": bool((settings.wecom_webhook_url or "").strip()),
            "app_configured": bool(
                (settings.wecom_corp_id or "").strip()
                and (settings.wecom_agent_id or "").strip()
                and (settings.wecom_secret or "").strip()
            ),
            "corp_id": _mask_secret(settings.wecom_corp_id),
            "ready": wecom_ready,
            "reserved": False,
        },
        "active": enabled_channel_names(settings),
    }
