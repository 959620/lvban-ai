"""
提醒文案渲染。

设计原因：文案与发送通道解耦，后续可按任务类型/学生定制模板。
"""

from __future__ import annotations

from datetime import datetime

from app.models.reminder import Reminder
from app.models.task import Task


def _format_due_cn(due_at: datetime | None) -> str:
    if due_at is None:
        return "稍后"
    return due_at.strftime("%m月%d日 %H:%M")


def _relative_hint(offset_minutes: int | None, due_at: datetime | None) -> str:
    """根据提前量生成口语化时间描述。"""
    if offset_minutes is None:
        return _format_due_cn(due_at)
    if offset_minutes == 0:
        return f"现在（{_format_due_cn(due_at)}）"
    if offset_minutes == 120:
        return f"两小时后（{_format_due_cn(due_at)}）"
    if offset_minutes == 1440:
        return f"明天（{_format_due_cn(due_at)}）"
    if offset_minutes % 1440 == 0:
        days = offset_minutes // 1440
        return f"{days} 天后（{_format_due_cn(due_at)}）"
    if offset_minutes % 60 == 0:
        hours = offset_minutes // 60
        return f"{hours} 小时后（{_format_due_cn(due_at)}）"
    return f"{offset_minutes} 分钟后（{_format_due_cn(due_at)}）"


def render_reminder_message(task: Task, reminder: Reminder) -> tuple[str, str]:
    """
    返回 (title, body)。

    示例：
    提醒：明天下午3点需要跟进王同学作品集修改，请提前准备。
    """
    if reminder.message_template:
        body = reminder.message_template
        return ("教务提醒", body)

    student_name = task.student.name if task.student else "相关学生"
    when = _relative_hint(reminder.offset_minutes, task.due_at)
    title = "教务提醒"
    body = f"提醒：{when}需要跟进{student_name}——{task.title}，请提前准备。"
    return title, body
