"""
通知通道包。

设计原因：
- 统一 NotificationChannel 协议，业务只依赖抽象
- 第一阶段：local / email
- 第二阶段：wecom 预留，打开开关即可挂载
"""

from app.notification.base import NotificationChannel, NotificationPayload

__all__ = ["NotificationChannel", "NotificationPayload"]
