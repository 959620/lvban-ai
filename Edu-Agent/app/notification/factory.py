"""
通知通道工厂。

根据配置组装启用的通道列表；Step 6 起按通道名查找发送器。
"""

from app.notification.base import NotificationChannel
from app.notification.local import LocalNotifier
from config.settings import Settings, get_settings


def build_notifiers(settings: Settings | None = None) -> list[NotificationChannel]:
    """按开关返回通道实例；Email / WeCom 在对应 Step 启用。"""
    settings = settings or get_settings()
    channels: list[NotificationChannel] = []

    if settings.notify_local:
        channels.append(LocalNotifier())

    # Step 8:
    # if settings.notify_email:
    #     from app.notification.email import EmailNotifier
    #     channels.append(EmailNotifier())

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
