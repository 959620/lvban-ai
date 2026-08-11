"""
学生服务。

负责学生档案匹配与简易创建（供任务关联）。
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.student import Student


class StudentService:
    """学生业务入口。"""

    def __init__(self, db: Session) -> None:
        self.db = db

    def find_by_name(self, name: str) -> Student | None:
        stmt = select(Student).where(Student.name == name).limit(1)
        return self.db.scalars(stmt).first()

    def get_or_create_by_name(self, name: str, *, auto_create: bool = True) -> Student | None:
        name = (name or "").strip()
        if not name:
            return None
        existing = self.find_by_name(name)
        if existing:
            return existing
        if not auto_create:
            return None
        student = Student(
            name=name,
            application_stage="portfolio",
            risk_level="normal",
            current_focus="待教务确认",
        )
        self.db.add(student)
        self.db.flush()
        return student
