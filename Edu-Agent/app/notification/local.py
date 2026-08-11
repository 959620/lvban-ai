"""
本地通知（第一阶段 / Step 8 增强）。

除控制台输出外，追加写入 data/local_notifications.log，便于网页侧回顾。
"""

from __future__ import annotations

import logging
from datetime import datetime

from app.notification.base import NotificationChannel, NotificationPayload
from config.settings import BASE_DIR

logger = logging.getLogger("edu_agent.notify.local")


class LocalNotifier(NotificationChannel):
    name = "local"

    def __init__(self) -> None:
        self.log_path = BASE_DIR / "data" / "local_notifications.log"

    def send(self, payload: NotificationPayload) -> None:
        line = f"{datetime.now().isoformat(timespec='seconds')} | {payload.title} | {payload.body}"
        logger.info("[LOCAL] %s", line)
        print(f"[LOCAL NOTIFY] {payload.title}: {payload.body}")

        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as fp:
            fp.write(line + "\n")
