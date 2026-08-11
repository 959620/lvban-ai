"""
学生 ORM 模型。

对应表：students（Step 2 设计）
"""

from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    target_schools: Mapped[str | None] = mapped_column(String(500), nullable=True)
    major: Mapped[str | None] = mapped_column(String(200), nullable=True)
    application_stage: Mapped[str] = mapped_column(String(50), nullable=False, default="inquiry")
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False, default="normal")
    current_focus: Mapped[str | None] = mapped_column(String(300), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    tasks = relationship("Task", back_populates="student")
