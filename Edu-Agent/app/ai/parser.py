"""
任务解析器。

Step 4：规则解析
Step 7：OpenAI 优先；失败/无 Key → 规则兜底
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Protocol
from zoneinfo import ZoneInfo

from app.ai.normalize import normalize_parsed_result
from app.ai.openai_client import OpenAIClient, OpenAIClientError
from app.ai.prompts import TASK_PARSE_SYSTEM_PROMPT, build_task_parse_user_prompt
from config.settings import get_settings

logger = logging.getLogger("edu_agent.parser")

LOCAL_TZ = ZoneInfo("Asia/Shanghai")

PRIORITY_KEYWORDS = {
    "urgent": ["紧急", "立刻", "马上", "尽快", "urgent"],
    "high": ["高优先级", "重要", "高优", "优先"],
    "low": ["不急", "有空", "低优先级", "低优"],
}

STUDENT_PATTERNS = [
    re.compile(r"(?:学生|学员)\s*([\u4e00-\u9fffA-Za-z]{1,12}同学)"),
    re.compile(r"(?:联系|催|跟进)\s*([\u4e00-\u9fffA-Za-z]{1,12}同学)"),
    re.compile(r"([\u4e00-\u9fff]{1,8}同学)"),
]

NOISE_IN_NAME = ("提醒", "联系", "催", "跟进", "下周", "明天", "后天", "上午", "下午", "晚上")


class TaskParser(Protocol):
    """自然语言 → 结构化任务字段。"""

    def parse(self, text: str) -> dict[str, Any]:
        ...


class RuleBasedTaskParser:
    """规则兜底解析：无 Key / 模型失败时保证可用。"""

    def parse(self, text: str) -> dict[str, Any]:
        raw = (text or "").strip()
        student = self._extract_student(raw)
        deadline = self._extract_deadline(raw)
        priority = self._extract_priority(raw)
        title = self._extract_title(raw, student)

        confidence = "medium" if (student or deadline) else "low"
        if student and deadline:
            confidence = "high"

        return normalize_parsed_result(
            {
                "task": title,
                "deadline": deadline,
                "student": student,
                "priority": priority,
                "parse_confidence": confidence,
            },
            source_text=raw,
            parse_source="rule",
            default_confidence=confidence,
        )

    def _extract_student(self, text: str) -> str | None:
        candidates: list[str] = []
        for pattern in STUDENT_PATTERNS:
            for match in pattern.finditer(text):
                name = match.group(1).strip()
                if any(noise in name for noise in NOISE_IN_NAME):
                    continue
                if name.endswith("同学") and len(name) <= 12:
                    candidates.append(name)
        if not candidates:
            return None
        return sorted(candidates, key=len)[0]

    def _extract_priority(self, text: str) -> str:
        lower = text.lower()
        for level, words in PRIORITY_KEYWORDS.items():
            if any(w in text or w in lower for w in words):
                return level
        return "medium"

    def _extract_deadline(self, text: str) -> datetime | None:
        now = datetime.now(LOCAL_TZ)

        iso = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})(?:[ T](\d{1,2}):(\d{2}))?", text)
        if iso:
            year, month, day = int(iso.group(1)), int(iso.group(2)), int(iso.group(3))
            hour = int(iso.group(4)) if iso.group(4) else 9
            minute = int(iso.group(5)) if iso.group(5) else 0
            return datetime(year, month, day, hour, minute)

        ymd = re.search(
            r"(?:(\d{4})[年/-])?(\d{1,2})[月/-](\d{1,2})[日号]?"
            r"(?:\s*(上午|下午|早上|晚上))?"
            r"(?:\s*(\d{1,2})\s*[点时:：](?:\s*(\d{1,2})\s*分?)?)?",
            text,
        )
        if ymd:
            year_s, month_s, day_s, meridiem, hour_s, minute_s = ymd.groups()
            year = int(year_s) if year_s else now.year
            month = int(month_s)
            day = int(day_s)
            hour = int(hour_s) if hour_s else 9
            minute = int(minute_s) if minute_s else 0
            if meridiem in {"下午", "晚上"} and hour < 12:
                hour += 12
            if meridiem == "上午" and hour == 12:
                hour = 0
            candidate = datetime(year, month, day, hour, minute)
            if not year_s and candidate < now.replace(tzinfo=None):
                candidate = datetime(year + 1, month, day, hour, minute)
            return candidate

        hour, minute = 9, 0
        hm = re.search(
            r"(上午|下午|早上|晚上)?\s*(\d{1,2})\s*[点时:：](?:\s*(\d{1,2})\s*分?)?",
            text,
        )
        if hm:
            meridiem, hour_s, minute_s = hm.groups()
            hour = int(hour_s)
            minute = int(minute_s) if minute_s else 0
            if meridiem in {"下午", "晚上"} and hour < 12:
                hour += 12

        base_day = None
        if "后天" in text:
            base_day = now.date() + timedelta(days=2)
        elif "明天" in text or "明日" in text:
            base_day = now.date() + timedelta(days=1)
        elif "下周" in text:
            days_ahead = 7 - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            base_day = now.date() + timedelta(days=days_ahead)

        if base_day:
            return datetime(base_day.year, base_day.month, base_day.day, hour, minute)
        return None

    def _extract_title(self, text: str, student: str | None) -> str:
        cleaned = text
        cleaned = re.sub(r"\d{4}-\d{1,2}-\d{1,2}(?:[ T]\d{1,2}:\d{2})?", "", cleaned)
        cleaned = re.sub(
            r"(?:(\d{4})[年/-])?\d{1,2}[月/-]\d{1,2}[日号]?"
            r"(?:\s*(上午|下午|早上|晚上))?"
            r"(?:\s*\d{1,2}\s*[点时:：](?:\s*\d{1,2}\s*分?)?)?",
            "",
            cleaned,
        )
        cleaned = re.sub(
            r"(明天|明日|后天|下周)(上午|下午|早上|晚上)?(\s*\d{1,2}\s*[点时:：](\d{1,2}\s*分?)?)?",
            "",
            cleaned,
        )
        cleaned = re.sub(r"(请)?(帮我)?(提醒我|记得|别忘了)", "", cleaned)
        cleaned = re.sub(r"(提前\d+\s*(小时|天|分钟))", "", cleaned)
        cleaned = re.sub(r"^[\s，,。；;：:]+", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" ，,。；;：:")
        if not cleaned:
            return f"跟进{student}" if student else "未命名任务"
        return cleaned[:200]


class OpenAITaskParser:
    """
    OpenAI 解析实现。

    失败策略：任意异常 / JSON 非法 → 回落 RuleBasedTaskParser，
    并标记 parse_source=openai_fallback，保证教务录入不被中断。
    """

    def __init__(
        self,
        fallback: RuleBasedTaskParser | None = None,
        client: OpenAIClient | None = None,
    ) -> None:
        self.fallback = fallback or RuleBasedTaskParser()
        self.client = client or OpenAIClient()

    def parse(self, text: str) -> dict[str, Any]:
        raw = (text or "").strip()
        try:
            content = self.client.chat_json(
                system_prompt=TASK_PARSE_SYSTEM_PROMPT,
                user_prompt=build_task_parse_user_prompt(raw),
            )
            data = _extract_json_object(content)
            return normalize_parsed_result(
                data,
                source_text=raw,
                parse_source="openai",
                default_confidence="high",
            )
        except (OpenAIClientError, json.JSONDecodeError, ValueError, TypeError) as exc:
            logger.warning("OpenAI 解析失败，回落规则解析: %s", exc)
            result = self.fallback.parse(raw)
            result["parse_source"] = "openai_fallback"
            # 回落后置信度不超过 medium，提示用户确认
            if result.get("parse_confidence") == "high":
                result["parse_confidence"] = "medium"
            return result


def _extract_json_object(content: str) -> dict[str, Any]:
    """从模型输出中提取 JSON（兼容 ```json 包裹）。"""
    text = content.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if fence:
        text = fence.group(1).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # 再尝试截取第一个 {...}
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            raise
        data = json.loads(match.group(0))

    if not isinstance(data, dict):
        raise ValueError("模型输出不是 JSON 对象")
    return data


def get_task_parser() -> TaskParser:
    """根据配置选择解析器。"""
    settings = get_settings()
    rule = RuleBasedTaskParser()
    if settings.openai_api_key and settings.openai_api_key.strip():
        return OpenAITaskParser(fallback=rule)
    return rule


def parser_status() -> dict[str, Any]:
    """供健康检查 / 前端展示当前解析引擎。"""
    settings = get_settings()
    has_key = bool(settings.openai_api_key and settings.openai_api_key.strip())
    return {
        "engine": "openai" if has_key else "rule",
        "openai_configured": has_key,
        "openai_model": settings.openai_model if has_key else None,
        "openai_base_url": settings.openai_base_url if has_key else None,
        "fallback": "rule",
    }
