"""
企业微信通知（第二阶段预留）。

扩展点说明：
1. 群机器人：使用 WECOM_WEBHOOK_URL 推送 markdown/text
2. 应用消息：使用 corp_id / agent_id / secret 调企业微信 API

当前仅保留接口，避免业务层出现 if wecom 分支膨胀。
启用方式（未来）：
- settings.notify_wecom = True
- 在通知工厂中注册 WeComNotifier
"""

from app.notification.base import NotificationChannel, NotificationPayload


class WeComNotifier(NotificationChannel):
    """企业微信通道占位实现。"""

    name = "wecom"

    def send(self, payload: NotificationPayload) -> None:
        # TODO(Step 9):
        # - webhook: POST WECOM_WEBHOOK_URL {"msgtype":"text","text":{"content":...}}
        # - 或获取 access_token 后调用消息推送 API
        raise NotImplementedError(
            "企业微信通知预留中：请配置 WECOM_* 并在 Step 9 实现 send()"
        )
