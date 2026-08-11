"""
通知通道包。

设计原因：
- 统一 NotificationChannel 协议，业务只依赖抽象
- 已实现：local / email / wecom（Webhook 或应用消息）
"""

from app.notification.base import NotificationChannel, NotificationPayload

__all__ = ["NotificationChannel", "NotificationPayload"]
