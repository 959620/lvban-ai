"""
通知通道工厂（占位）。

根据配置组装启用的通道列表，供 ReminderService 使用。
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

    # if settings.notify_email:
    #     from app.notification.email import EmailNotifier
    #     channels.append(EmailNotifier())

    # if settings.notify_wecom:
    #     from app.notification.wecom import WeComNotifier
    #     channels.append(WeComNotifier())

    return channels
