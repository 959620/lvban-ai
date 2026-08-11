"""
企业微信通知（Step 9）。

支持两种模式（按配置自动选择）：
1. 群机器人 Webhook：WECOM_WEBHOOK_URL（教务群最快落地）
2. 应用消息 API：WECOM_CORP_ID + WECOM_AGENT_ID + WECOM_SECRET

另提供 dry-run：写入 data/wecom_outbox/，无需真实企业微信即可验证链路。
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

from app.notification.base import NotificationChannel, NotificationPayload
from config.settings import BASE_DIR, Settings, get_settings

logger = logging.getLogger("edu_agent.notify.wecom")


class WeComNotifier(NotificationChannel):
    """企业微信通道。"""

    name = "wecom"

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.outbox_dir = BASE_DIR / "data" / "wecom_outbox"

    @property
    def mode(self) -> str:
        """webhook | app | unconfigured"""
        if (self.settings.wecom_webhook_url or "").strip():
            return "webhook"
        if (
            (self.settings.wecom_corp_id or "").strip()
            and (self.settings.wecom_agent_id or "").strip()
            and (self.settings.wecom_secret or "").strip()
        ):
            return "app"
        return "unconfigured"

    def send(self, payload: NotificationPayload) -> None:
        mode = self.mode
        body = self._build_payload(payload, mode=mode if mode != "unconfigured" else "webhook")

        if self.settings.notify_wecom_dry_run:
            path = self._write_outbox(body, mode=mode)
            logger.info("[WECOM-DRY-RUN] mode=%s saved=%s | %s", mode, path, payload.title)
            print(f"[WECOM DRY-RUN] mode={mode} -> {path}")
            return

        if mode == "webhook":
            self._send_webhook(body)
            logger.info("[WECOM] webhook ok | %s", payload.title)
            print(f"[WECOM NOTIFY] webhook | {payload.title}")
            return

        if mode == "app":
            self._send_app_message(payload)
            logger.info("[WECOM] app message ok | %s", payload.title)
            print(f"[WECOM NOTIFY] app | {payload.title}")
            return

        raise ValueError(
            "企业微信未配置：请设置 WECOM_WEBHOOK_URL，"
            "或 WECOM_CORP_ID + WECOM_AGENT_ID + WECOM_SECRET；"
            "本地演练可设 NOTIFY_WECOM_DRY_RUN=true"
        )

    def _build_payload(self, payload: NotificationPayload, *, mode: str) -> dict[str, Any]:
        msg_type = (self.settings.wecom_msg_type or "markdown").strip().lower()
        content = f"{payload.title}\n{payload.body}".strip()

        if mode == "app":
            # 应用消息结构在 _send_app_message 中组装；此处仅给 dry-run 预览
            return {
                "mode": "app",
                "touser": self.settings.wecom_touser or "@all",
                "agentid": self._agent_id_int(),
                "msgtype": msg_type,
                "content": content,
            }

        if msg_type == "text":
            return {"msgtype": "text", "text": {"content": content}}

        # 默认 markdown，更适合教务群可读性
        md = f"**{payload.title}**\n{payload.body}"
        return {"msgtype": "markdown", "markdown": {"content": md}}

    def _write_outbox(self, body: dict[str, Any], *, mode: str) -> Path:
        self.outbox_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        path = self.outbox_dir / f"{stamp}_{mode or 'unknown'}.json"
        path.write_text(json.dumps(body, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def _send_webhook(self, body: dict[str, Any]) -> None:
        url = self.settings.wecom_webhook_url.strip()
        timeout = httpx.Timeout(self.settings.wecom_timeout_seconds)
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, json=body)
        self._raise_for_wecom_response(resp, context="webhook")

    def _send_app_message(self, payload: NotificationPayload) -> None:
        token = self._get_access_token()
        msg_type = (self.settings.wecom_msg_type or "text").strip().lower()
        content = f"{payload.title}\n{payload.body}".strip()
        agent_id = self._agent_id_int()

        if msg_type == "markdown":
            body: dict[str, Any] = {
                "touser": self.settings.wecom_touser or "@all",
                "msgtype": "markdown",
                "agentid": agent_id,
                "markdown": {"content": f"**{payload.title}**\n{payload.body}"},
            }
        else:
            body = {
                "touser": self.settings.wecom_touser or "@all",
                "msgtype": "text",
                "agentid": agent_id,
                "text": {"content": content},
                "safe": 0,
            }

        api = self.settings.wecom_api_base.rstrip("/")
        url = f"{api}/cgi-bin/message/send"
        timeout = httpx.Timeout(self.settings.wecom_timeout_seconds)
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, params={"access_token": token}, json=body)
        self._raise_for_wecom_response(resp, context="app_message")

    def _get_access_token(self) -> str:
        api = self.settings.wecom_api_base.rstrip("/")
        url = f"{api}/cgi-bin/gettoken"
        params = {
            "corpid": self.settings.wecom_corp_id.strip(),
            "corpsecret": self.settings.wecom_secret.strip(),
        }
        timeout = httpx.Timeout(self.settings.wecom_timeout_seconds)
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(url, params=params)
        data = self._raise_for_wecom_response(resp, context="gettoken")
        token = data.get("access_token")
        if not token:
            raise RuntimeError(f"企业微信 gettoken 未返回 access_token: {data}")
        return str(token)

    def _agent_id_int(self) -> int:
        raw = str(self.settings.wecom_agent_id).strip()
        try:
            return int(raw)
        except ValueError as exc:
            raise ValueError(f"WECOM_AGENT_ID 必须是数字，当前={raw!r}") from exc

    def _raise_for_wecom_response(self, resp: httpx.Response, *, context: str) -> dict[str, Any]:
        try:
            data = resp.json()
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                f"企业微信 {context} 响应非 JSON: HTTP {resp.status_code} {resp.text[:300]}"
            ) from exc

        # HTTP 层错误
        if resp.status_code >= 400:
            raise RuntimeError(f"企业微信 {context} HTTP {resp.status_code}: {data}")

        # 企业微信业务错误码
        errcode = data.get("errcode", 0)
        if errcode not in (0, "0", None):
            raise RuntimeError(
                f"企业微信 {context} 失败 errcode={errcode} errmsg={data.get('errmsg')}"
            )
        return data if isinstance(data, dict) else {"raw": data}
