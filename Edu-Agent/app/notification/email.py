"""
邮件通知（第一阶段占位）。

Step 8：使用 SMTP / aiosmtplib 发送；配置来自 settings。
"""

from app.notification.base import NotificationChannel, NotificationPayload


class EmailNotifier(NotificationChannel):
    name = "email"

    def send(self, payload: NotificationPayload) -> None:
        raise NotImplementedError("Step 8 实现 SMTP 邮件发送")
