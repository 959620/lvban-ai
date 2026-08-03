from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(32), default="其他")

    students: Mapped[list["Student"]] = relationship(
        secondary="student_tags",
        back_populates="tags",
    )


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    name: Mapped[str] = mapped_column(String(64), index=True)
    grade: Mapped[str | None] = mapped_column(String(32), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    parent_phone: Mapped[str | None] = mapped_column(String(64), nullable=True)

    major: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    target_country: Mapped[str | None] = mapped_column(String(64), nullable=True)
    target_major: Mapped[str | None] = mapped_column(String(128), nullable=True)
    intake_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    application_stage: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    portfolio_started: Mapped[bool] = mapped_column(Boolean, default=False)
    portfolio_project_count: Mapped[int] = mapped_column(Integer, default=0)
    portfolio_progress: Mapped[int] = mapped_column(Integer, default=0)

    personality_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    family_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    communication_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    important_events: Mapped[str | None] = mapped_column(Text, nullable=True)

    next_contact_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    schools: Mapped[list["StudentSchool"]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
        order_by="StudentSchool.id",
    )
    tags: Mapped[list[Tag]] = relationship(
        secondary="student_tags",
        back_populates="students",
    )


class StudentSchool(Base):
    __tablename__ = "student_schools"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    school_name: Mapped[str] = mapped_column(String(128))
    priority: Mapped[str | None] = mapped_column(String(16), nullable=True)

    student: Mapped[Student] = relationship(back_populates="schools")


class StudentTag(Base):
    __tablename__ = "student_tags"
    __table_args__ = (UniqueConstraint("student_id", "tag_id", name="uq_student_tag"),)

    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), primary_key=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
