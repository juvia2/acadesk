import datetime as dt
import uuid
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from acadesk.db.base import Base, IdMixin, TenantMixin, TimestampMixin, str_enum

from .schemas import SessionKind, SessionStatus


class Lecture(IdMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "lectures"

    name: Mapped[str] = mapped_column(String(100))
    subject: Mapped[str | None] = mapped_column(String(50))
    grade: Mapped[str | None] = mapped_column(String(32))
    room: Mapped[str | None] = mapped_column(String(50))
    branch_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("branches.id"))
    teacher_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    # [{"weekday": 0, "start": "16:00", "end": "17:30"}]
    schedule: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    starts_on: Mapped[dt.date | None] = mapped_column(Date)
    ends_on: Mapped[dt.date | None] = mapped_column(Date)
    archived: Mapped[bool] = mapped_column(default=False)


class LectureEnrollment(IdMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "lecture_enrollments"
    __table_args__ = (UniqueConstraint("lecture_id", "student_id"),)

    lecture_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lectures.id", ondelete="CASCADE"))
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), index=True
    )
    started_on: Mapped[dt.date | None] = mapped_column(Date)
    ended_on: Mapped[dt.date | None] = mapped_column(Date)  # 수강 종료. 지난 출결은 남는다


class LectureSession(IdMixin, TenantMixin, TimestampMixin, Base):
    """강의 회차. 출결의 단위."""

    __tablename__ = "lecture_sessions"
    __table_args__ = (
        UniqueConstraint("lecture_id", "starts_at"),
        Index("ix_lecture_sessions_academy_date", "academy_id", "date"),
        CheckConstraint("ends_at > starts_at", name="time_order"),
    )

    lecture_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lectures.id", ondelete="CASCADE"))
    date: Mapped[dt.date] = mapped_column(Date)
    starts_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))
    kind: Mapped[SessionKind] = mapped_column(
        str_enum(SessionKind, 16), default=SessionKind.REGULAR
    )
    status: Mapped[SessionStatus] = mapped_column(
        str_enum(SessionStatus, 16), default=SessionStatus.SCHEDULED
    )
    attendance_opened_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    attendance_opened_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    attendance_closed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    cancel_reason: Mapped[str | None] = mapped_column(Text)


class SessionStudent(TenantMixin, Base):
    """보강처럼 일부 학생만 듣는 회차의 대상. 행이 없으면 강의 수강생 전체."""

    __tablename__ = "session_students"

    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("lecture_sessions.id", ondelete="CASCADE"), primary_key=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), primary_key=True
    )
