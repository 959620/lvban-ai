"""
任务服务。

Step 4：解析 + 创建
Step 5：列表筛选 / 更新 / 状态流转（完成·取消联动提醒）
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.ai.parser import get_task_parser
from app.models.schemas import (
    ParsedTaskPreview,
    ParseAndCreateResponse,
    ReminderBrief,
    TaskCreateRequest,
    TaskListResponse,
    TaskResponse,
    TaskStatus,
    TaskUpdateRequest,
)
from app.models.student import Student
from app.models.task import Task
from app.services.reminder_service import DEFAULT_OFFSETS_MINUTES, ReminderService
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
        student = self._resolve_student(
            student_id=payload.student_id,
            student_name=payload.student_name,
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
        return self.get_task(task.id)  # type: ignore[return-value]

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
        task = self._load_task(task_id)
        if not task:
            return None
        return self._to_response(task)

    def list_tasks(
        self,
        *,
        status: str | None = None,
        student_id: int | None = None,
        student_name: str | None = None,
        priority: str | None = None,
        q: str | None = None,
        include_overdue_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> TaskListResponse:
        """
        任务列表 + 筛选。

        include_overdue_only：due_at < now 且仍为 pending/in_progress（查询态逾期，不落库改状态）。
        """
        limit = max(1, min(limit, 200))
        offset = max(0, offset)

        filters = []
        if status:
            filters.append(Task.status == status)
        if student_id is not None:
            filters.append(Task.student_id == student_id)
        if priority:
            filters.append(Task.priority == priority)
        if student_name:
            filters.append(Student.name.contains(student_name.strip()))
        if q:
            filters.append(Task.title.contains(q.strip()))
        if include_overdue_only:
            filters.append(Task.due_at.is_not(None))
            filters.append(Task.due_at < datetime.now())
            filters.append(Task.status.in_(("pending", "in_progress")))

        stmt = select(Task).outerjoin(Student)
        if filters:
            stmt = stmt.where(*filters)

        count_stmt = select(func.count(Task.id)).select_from(Task).outerjoin(Student)
        if filters:
            count_stmt = count_stmt.where(*filters)
        total = int(self.db.scalar(count_stmt) or 0)

        # SQLite 友好的 NULLS LAST：先排非空 due_at
        list_stmt = (
            stmt.options(joinedload(Task.student), joinedload(Task.reminders))
            .order_by(Task.due_at.is_(None), Task.due_at.asc(), Task.id.desc())
            .limit(limit)
            .offset(offset)
        )
        tasks = list(self.db.scalars(list_stmt).unique().all())
        return TaskListResponse(total=total, items=[self._to_response(t) for t in tasks])

    def update_task(self, task_id: int, payload: TaskUpdateRequest) -> TaskResponse | None:
        """更新任务字段；截止时间变化时重建提醒。"""
        task = self._load_task(task_id)
        if not task:
            return None

        due_changed = False
        if payload.title is not None:
            task.title = payload.title.strip()
        if payload.description is not None:
            task.description = payload.description
        if payload.priority is not None:
            task.priority = payload.priority

        if payload.clear_due_at:
            if task.due_at is not None:
                task.due_at = None
                due_changed = True
        elif payload.due_at is not None and payload.due_at != task.due_at:
            task.due_at = payload.due_at
            due_changed = True

        if payload.student_id is not None or payload.student_name is not None:
            student = self._resolve_student(
                student_id=payload.student_id,
                student_name=payload.student_name,
                auto_create=payload.auto_create_student,
            )
            task.student_id = student.id if student else None

        if due_changed:
            if task.due_at is None:
                self.reminders.cancel_pending_for_task(task.id, reason="cancelled")
            else:
                offsets = payload.reminder_offsets_minutes or DEFAULT_OFFSETS_MINUTES
                self.reminders.rebuild_reminders_for_task(task, offsets_minutes=offsets)

        self.db.commit()
        return self.get_task(task_id)

    def set_status(self, task_id: int, status: TaskStatus) -> TaskResponse | None:
        """
        状态流转。

        - done / cancelled：取消未发送提醒（完成→skipped，取消→cancelled）
        - 回到 pending / in_progress：若仍有 due_at 且无 scheduled 提醒，则重建默认提醒
        """
        task = self._load_task(task_id)
        if not task:
            return None

        old_status = task.status
        task.status = status

        if status == "done":
            task.completed_at = datetime.now()
            self.reminders.cancel_pending_for_task(task.id, reason="skipped")
        elif status == "cancelled":
            task.completed_at = None
            self.reminders.cancel_pending_for_task(task.id, reason="cancelled")
        elif status in {"pending", "in_progress"} and old_status in {"done", "cancelled"}:
            task.completed_at = None
            pending = [r for r in task.reminders if r.status == "scheduled"]
            if task.due_at and not pending:
                self.reminders.create_default_reminders(task)

        self.db.commit()
        return self.get_task(task_id)

    def _resolve_student(
        self,
        *,
        student_id: int | None,
        student_name: str | None,
        auto_create: bool,
    ) -> Student | None:
        if student_id is not None:
            return self.db.get(Student, student_id)
        if student_name:
            return self.students.get_or_create_by_name(
                student_name,
                auto_create=auto_create,
            )
        return None

    def _load_task(self, task_id: int) -> Task | None:
        stmt = (
            select(Task)
            .options(joinedload(Task.student), joinedload(Task.reminders))
            .where(Task.id == task_id)
        )
        return self.db.scalars(stmt).unique().first()

    def _to_response(self, task: Task) -> TaskResponse:
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
