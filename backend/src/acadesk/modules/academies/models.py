import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from acadesk.core.security import Role
from acadesk.db.base import Base, IdMixin, TenantMixin, TimestampMixin, str_enum

from .schemas import CalendarKind


class Academy(IdMixin, TimestampMixin, Base):
    __tablename__ = "academies"

    name: Mapped[str] = mapped_column(String(100))
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Seoul")
    phone: Mapped[str | None] = mapped_column(String(32))


class AcademySetting(IdMixin, TenantMixin, TimestampMixin, Base):
    """학원별 설정. key 예: rules(안내 규칙), sibling_discount(형제 할인)."""

    __tablename__ = "academy_settings"
    __table_args__ = (UniqueConstraint("academy_id", "key"),)

    key: Mapped[str] = mapped_column(String(64))
    value: Mapped[dict[str, Any]] = mapped_column(JSONB)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))


class Branch(IdMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "branches"

    name: Mapped[str] = mapped_column(String(100))
    address: Mapped[str | None] = mapped_column(String(255))


class User(IdMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    role: Mapped[Role] = mapped_column(str_enum(Role, 16))
    password_hash: Mapped[str | None] = mapped_column(String(255))  # 초대 수락 전에는 없음
    is_active: Mapped[bool] = mapped_column(default=True)
    preferred_language: Mapped[str] = mapped_column(String(16), default="ko")
    invited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class UserBranch(TenantMixin, Base):
    __tablename__ = "user_branches"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    branch_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("branches.id", ondelete="CASCADE"), primary_key=True
    )


class RefreshToken(IdMixin, TenantMixin, Base):
    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    token_hash: Mapped[str] = mapped_column(String(128), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Class(IdMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "classes"

    name: Mapped[str] = mapped_column(String(100))
    branch_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("branches.id"))
    teacher_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    # [{"weekday": 0, "start": "16:00", "end": "17:30"}]
    schedule: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)


class ClassEnrollment(IdMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "class_enrollments"
    __table_args__ = (UniqueConstraint("class_id", "student_id"),)

    class_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classes.id", ondelete="CASCADE"))
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), index=True
    )
    started_on: Mapped[date | None] = mapped_column(Date)
    ended_on: Mapped[date | None] = mapped_column(Date)


class CalendarEvent(IdMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "calendar_events"
    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="date_order"),
        CheckConstraint(
            "(kind = 'student_leave') = (student_id IS NOT NULL)", name="student_leave_has_student"
        ),
    )

    kind: Mapped[CalendarKind] = mapped_column(str_enum(CalendarKind))
    start_date: Mapped[date] = mapped_column(Date, index=True)
    end_date: Mapped[date] = mapped_column(Date)
    student_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE")
    )
    note: Mapped[str | None] = mapped_column(Text)
