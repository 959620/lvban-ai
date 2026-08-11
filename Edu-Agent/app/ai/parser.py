"""
任务解析器。

Step 4：规则解析已可用（提取学生、时间、优先级、任务名）
Step 7：接入 OpenAI；无 Key 时仍回落到本规则实现
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any, Protocol
from zoneinfo import ZoneInfo

from config.settings import get_settings

# 教务场景常见时区；后续可配置化
LOCAL_TZ = ZoneInfo("Asia/Shanghai")

PRIORITY_KEYWORDS = {
    "urgent": ["紧急", "立刻", "马上", "尽快", "urgent"],
    "high": ["高优先级", "重要", "高优", "优先"],
    "low": ["不急", "有空", "低优先级", "低优"],
}

# 学生名模式：优先「学生X同学」，再回落短「X同学」
STUDENT_PATTERNS = [
    re.compile(r"(?:学生|学员)\s*([\u4e00-\u9fffA-Za-z]{1,12}同学)"),
    re.compile(r"(?:联系|催|跟进)\s*([\u4e00-\u9fffA-Za-z]{1,12}同学)"),
    re.compile(r"([\u4e00-\u9fff]{1,8}同学)"),
]

NOISE_IN_NAME = ("提醒", "联系", "催", "跟进", "下周", "明天", "后天", "上午", "下午", "晚上")


class TaskParser(Protocol):
    """自然语言 → 结构化任务字段。"""

    def parse(self, text: str) -> dict[str, Any]:
        """解析用户输入，返回标准化字典。"""
        ...


class RuleBasedTaskParser:
    """
    规则兜底解析。

    为什么 Step 4 先做规则版：
    - 无 OpenAI Key 也能演示「自然语言 → 结构化」闭环
    - 作为 Step 7 模型失败时的安全网
    """

    def parse(self, text: str) -> dict[str, Any]:
        raw = (text or "").strip()
        student = self._extract_student(raw)
        deadline = self._extract_deadline(raw)
        priority = self._extract_priority(raw)
        title = self._extract_title(raw, student)

        confidence = "medium" if (student or deadline) else "low"
        if student and deadline:
            confidence = "high"

        return {
            "task": title,
            "deadline": deadline.isoformat() if deadline else None,
            "student": student,
            "priority": priority,
            "parse_confidence": confidence,
        }

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
        # 取最短合理名（避免吞掉前后文）
        return sorted(candidates, key=len)[0]

    def _extract_priority(self, text: str) -> str:
        lower = text.lower()
        for level, words in PRIORITY_KEYWORDS.items():
            if any(w in text or w in lower for w in words):
                return level
        return "medium"

    def _extract_deadline(self, text: str) -> datetime | None:
        now = datetime.now(LOCAL_TZ)

        # ISO：2026-09-01 15:00 / 2026-09-01T15:00
        iso = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})(?:[ T](\d{1,2}):(\d{2}))?", text)
        if iso:
            year, month, day = int(iso.group(1)), int(iso.group(2)), int(iso.group(3))
            hour = int(iso.group(4)) if iso.group(4) else 9
            minute = int(iso.group(5)) if iso.group(5) else 0
            return datetime(year, month, day, hour, minute)

        # 中文日期：8月20日下午3点 / 2026年8月20日15:00
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

        # 相对日期：明天 / 后天 / 下周
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
            # 简单策略：下周一（Step 7 可用模型精化）
            days_ahead = 7 - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            base_day = now.date() + timedelta(days=days_ahead)

        if base_day:
            return datetime(base_day.year, base_day.month, base_day.day, hour, minute)
        return None

    def _extract_title(self, text: str, student: str | None) -> str:
        """去掉时间与提醒套话，留下任务核心描述。"""
        cleaned = text
        # 先去日期时间，再去提醒套话（套话常在日期后面）
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
    """OpenAI 解析实现（Step 7；当前占位并回落规则）。"""

    def __init__(self, fallback: RuleBasedTaskParser | None = None) -> None:
        self.fallback = fallback or RuleBasedTaskParser()

    def parse(self, text: str) -> dict[str, Any]:
        # Step 7 将调用 OpenAI；当前先回落，保证创建链路可测
        return self.fallback.parse(text)


def get_task_parser() -> TaskParser:
    """根据配置选择解析器。"""
    settings = get_settings()
    rule = RuleBasedTaskParser()
    if settings.openai_api_key:
        return OpenAITaskParser(fallback=rule)
    return rule
