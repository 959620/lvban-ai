"""
通知通道工厂。

根据配置组装启用的通道列表；对外提供通道状态（不含密钥）。
"""

from __future__ import annotations

from app.notification.base import NotificationChannel
from app.notification.email import EmailNotifier
from app.notification.local import LocalNotifier
from config.settings import Settings, get_settings


def build_notifiers(settings: Settings | None = None) -> list[NotificationChannel]:
    """按开关返回通道实例。"""
    settings = settings or get_settings()
    channels: list[NotificationChannel] = []

    if settings.notify_local:
        channels.append(LocalNotifier())

    if settings.notify_email:
        channels.append(EmailNotifier(settings))

    # Step 9:
    # if settings.notify_wecom:
    #     from app.notification.wecom import WeComNotifier
    #     channels.append(WeComNotifier())

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
            "ready": False,
            "reserved": True,
        },
        "active": enabled_channel_names(settings),
    }
