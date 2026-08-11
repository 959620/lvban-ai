"""
解析结果规范化。

设计原因：OpenAI / 规则解析输出格式可能不一致，入库前统一字段与类型。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

ALLOWED_PRIORITIES = {"low", "medium", "high", "urgent"}


def normalize_parsed_result(
    data: dict[str, Any],
    *,
    source_text: str,
    parse_source: str,
    default_confidence: str = "medium",
) -> dict[str, Any]:
    """将任意解析字典规范为 TaskService 可用结构。"""
    task = str(data.get("task") or data.get("title") or source_text).strip()
    if not task:
        task = "未命名任务"
    task = task[:200]

    student = data.get("student")
    if student is not None:
        student = str(student).strip() or None

    priority = str(data.get("priority") or "medium").strip().lower()
    if priority not in ALLOWED_PRIORITIES:
        priority = "medium"

    deadline = _normalize_deadline(data.get("deadline") or data.get("due_at"))

    confidence = str(data.get("parse_confidence") or default_confidence).strip().lower()
    if confidence not in {"high", "medium", "low", "manual"}:
        confidence = default_confidence

    # OpenAI 成功时默认高置信；缺字段则降级
    if parse_source == "openai":
        if student and deadline:
            confidence = "high"
        elif student or deadline:
            confidence = "medium"
        else:
            confidence = "medium"

    return {
        "task": task,
        "deadline": deadline.isoformat() if isinstance(deadline, datetime) else deadline,
        "student": student,
        "priority": priority,
        "parse_confidence": confidence,
        "parse_source": parse_source,
    }


def _normalize_deadline(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=None) if value.tzinfo else value
    text = str(value).strip()
    if not text or text.lower() in {"null", "none"}:
        return None
    # 兼容 Z / 带时区
    text = text.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        # 常见兜底：2026-08-20 15:00:00
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M"):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue
        return None
    if dt.tzinfo:
        dt = dt.replace(tzinfo=None)
    return dt
