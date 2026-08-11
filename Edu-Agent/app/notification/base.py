"""
通知通道抽象基类。

所有通道实现同一接口，ReminderService 无需关心具体投递方式。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class NotificationPayload:
    """一次通知的标准载荷。"""

    title: str
    body: str
    meta: dict[str, Any] = field(default_factory=dict)


class NotificationChannel(ABC):
    """通知通道协议。"""

    name: str = "base"

    @abstractmethod
    def send(self, payload: NotificationPayload) -> None:
        """发送通知；失败应抛出异常，由上层写入 notification_logs。"""
