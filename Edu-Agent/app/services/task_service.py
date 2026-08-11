"""
任务服务。

Step 4 核心：
1. 解析自然语言 → 预览
2. 确认后写入 tasks，并生成 reminders
3. 自动匹配/创建学生
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.ai.parser import get_task_parser
from app.models.schemas import (
    ParsedTaskPreview,
    ParseAndCreateResponse,
    TaskCreateRequest,
    TaskResponse,
    ReminderBrief,
)
from app.models.student import Student
from app.models.task import Task
from app.services.reminder_service import ReminderService
from app.services.student_service import StudentService


class TaskService:
    """任务业务入口。"""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.students = StudentService(db)
        self.reminders = ReminderService(db)
        self.parser = get_task_parser()

    def parse_natural_language(self, text: str) -> ParsedTaskPreview:
        """只解析不入库，供前端确认卡片使用。"""
        result = self.parser.parse(text)
        deadline = result.get("deadline")
        due_at = None
        if isinstance(deadline, datetime):
            due_at = deadline
        elif isinstance(deadline, str) and deadline:
            due_at = datetime.fromisoformat(deadline)

        return ParsedTaskPreview(
            task=result.get("task") or text.strip() or "未命名任务",
            deadline=due_at,
            student=result.get("student"),
            priority=result.get("priority") or "medium",
            parse_confidence=result.get("parse_confidence") or "low",
            source_text=text,
        )

    def create_task(self, payload: TaskCreateRequest) -> TaskResponse:
        """结构化创建任务并生成默认提醒。"""
        student = None
        if payload.student_id is not None:
            student = self.db.get(Student, payload.student_id)
        elif payload.student_name:
            student = self.students.get_or_create_by_name(
                payload.student_name,
                auto_create=payload.auto_create_student,
            )

        task = Task(
            title=payload.title.strip(),
            description=payload.description,
            priority=payload.priority,
            status="pending",
            due_at=payload.due_at,
            student_id=student.id if student else None,
            source_text=payload.source_text,
            parse_confidence=payload.parse_confidence,
        )
        self.db.add(task)
        self.db.flush()

        self.reminders.create_default_reminders(
            task,
            offsets_minutes=payload.reminder_offsets_minutes,
        )
        self.db.commit()
        self.db.refresh(task)

        return self._to_response(task)

    def parse_and_create(
        self,
        text: str,
        *,
        auto_create_student: bool = True,
    ) -> ParseAndCreateResponse:
        """一键：解析自然语言并直接创建（适合快速录入）。"""
        parsed = self.parse_natural_language(text)
        task = self.create_task(
            TaskCreateRequest(
                title=parsed.task,
                student_name=parsed.student,
                priority=parsed.priority,
                due_at=parsed.deadline,
                source_text=parsed.source_text,
                parse_confidence=parsed.parse_confidence,
                reminder_offsets_minutes=parsed.reminder_offsets_minutes,
                auto_create_student=auto_create_student,
            )
        )
        return ParseAndCreateResponse(parsed=parsed, task=task)

    def get_task(self, task_id: int) -> TaskResponse | None:
        stmt = (
            select(Task)
            .options(joinedload(Task.student), joinedload(Task.reminders))
            .where(Task.id == task_id)
        )
        task = self.db.scalars(stmt).unique().first()
        if not task:
            return None
        return self._to_response(task)

    def _to_response(self, task: Task) -> TaskResponse:
        # 确保 relationship 可用
        student_name = task.student.name if task.student else None
        reminders = [
            ReminderBrief(
                id=r.id,
                remind_at=r.remind_at,
                offset_minutes=r.offset_minutes,
                status=r.status,
                channel=r.channel,
            )
            for r in sorted(task.reminders, key=lambda x: x.remind_at)
        ]
        return TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            priority=task.priority,
            status=task.status,
            due_at=task.due_at,
            student_id=task.student_id,
            student_name=student_name,
            source_text=task.source_text,
            parse_confidence=task.parse_confidence,
            created_at=task.created_at,
            reminders=reminders,
        )
