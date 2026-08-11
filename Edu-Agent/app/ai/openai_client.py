"""
OpenAI Chat Completions 客户端（httpx）。

为什么不用官方 SDK：
- 项目已依赖 httpx，减少包体积
- 便于自定义 base_url（兼容代理 / Azure / 国产兼容网关）
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from config.settings import Settings, get_settings

logger = logging.getLogger("edu_agent.openai")


class OpenAIClientError(RuntimeError):
    """OpenAI 调用失败。"""


class OpenAIClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @property
    def enabled(self) -> bool:
        return bool(self.settings.openai_api_key and self.settings.openai_api_key.strip())

    def chat_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
    ) -> str:
        """
        调用 chat/completions，返回 assistant 文本内容。
        要求模型输出 JSON；此处只负责拿到原始字符串。
        """
        if not self.enabled:
            raise OpenAIClientError("OPENAI_API_KEY 未配置")

        url = self.settings.openai_base_url.rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": self.settings.openai_model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            # 兼容支持 response_format 的模型；不支持时服务端可能忽略或报错，由上层兜底
            "response_format": {"type": "json_object"},
        }

        timeout = httpx.Timeout(self.settings.openai_timeout_seconds)
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(url, headers=headers, json=payload)
        except httpx.HTTPError as exc:
            raise OpenAIClientError(f"网络错误: {exc}") from exc

        if resp.status_code >= 400:
            # 部分兼容网关不支持 response_format，自动降级重试一次
            if resp.status_code in {400, 422} and "response_format" in payload:
                logger.warning("response_format 不被支持，降级重试")
                payload.pop("response_format", None)
                try:
                    with httpx.Client(timeout=timeout) as client:
                        resp = client.post(url, headers=headers, json=payload)
                except httpx.HTTPError as exc:
                    raise OpenAIClientError(f"网络错误: {exc}") from exc

        if resp.status_code >= 400:
            raise OpenAIClientError(f"API {resp.status_code}: {resp.text[:500]}")

        data = resp.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise OpenAIClientError(f"响应格式异常: {data!r}") from exc

        if not content or not str(content).strip():
            raise OpenAIClientError("模型返回空内容")
        return str(content)
