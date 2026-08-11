"""
本地通知（第一阶段）。

MVP：写入控制台，便于本地开发验证提醒链路。
"""

import logging

from app.notification.base import NotificationChannel, NotificationPayload

logger = logging.getLogger("edu_agent.notify.local")


class LocalNotifier(NotificationChannel):
    name = "local"

    def send(self, payload: NotificationPayload) -> None:
        logger.info("[LOCAL] %s | %s", payload.title, payload.body)
        print(f"[LOCAL NOTIFY] {payload.title}: {payload.body}")
