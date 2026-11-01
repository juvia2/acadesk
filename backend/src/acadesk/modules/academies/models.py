import uuid
from datetime import date, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from acadesk.core.security import Role
from acadesk.db.base import Base, IdMixin, TenantMixin, TimestampMixin, str_enum

from .schemas import CalendarKind, InvitationStatus


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


class AccountStatus(StrEnum):
    INVITED = "invited"  # 직원 초대 메일 발송, 수락 전
    ACTIVE = "active"
    PENDING_GUARDIAN_CONSENT = "pending_guardian_consent"  # 만 14세 미만 학생
    DISABLED = "disabled"


class User(IdMixin, TenantMixin, TimestampMixin, Base):
    """모든 역할의 계정. 학생은 student_id, 학부모는 guardian_id로 명부와 연결된다."""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role <> 'student' OR student_id IS NOT NULL", name="student_linked"),
        CheckConstraint("role <> 'parent' OR guardian_id IS NOT NULL", name="parent_linked"),
    )

    email: Mapped[str] = mapped_column(String(255), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    role: Mapped[Role] = mapped_column(str_enum(Role, 16))
    password_hash: Mapped[str | None] = mapped_column(String(255))  # 초대 수락 전에는 없음
    status: Mapped[AccountStatus] = mapped_column(
        str_enum(AccountStatus, 32), default=AccountStatus.ACTIVE
    )
    student_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("students.id", ondelete="SET NULL"), unique=True
    )
    guardian_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("guardians.id", ondelete="SET NULL"), unique=True
    )
    guardian_consent_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    guardian_consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
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


class Invitation(IdMixin, TenantMixin, TimestampMixin, Base):
    """일회용 초대 코드. 원문은 발급 응답에서만 보여주고 해시만 저장한다."""

    __tablename__ = "invitations"
    __table_args__ = (
        CheckConstraint(
            "role NOT IN ('student', 'parent') OR student_id IS NOT NULL", name="target_student"
        ),
    )

    code_hash: Mapped[str] = mapped_column(String(64), unique=True)
    code_hint: Mapped[str] = mapped_column(String(4))
    role: Mapped[Role] = mapped_column(str_enum(Role, 16))
    student_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), index=True
    )
    guardian_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("guardians.id", ondelete="CASCADE")
    )
    email: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[InvitationStatus] = mapped_column(
        str_enum(InvitationStatus, 16), default=InvitationStatus.ACTIVE
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    used_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class File(IdMixin, TenantMixin, TimestampMixin, Base):
    """올린 파일 (공지 첨부, 질문 첨부, 커뮤니티 이미지). 내용은 비공개 저장소에."""

    __tablename__ = "files"

    purpose: Mapped[str] = mapped_column(String(32))  # notice | question | community
    storage_key: Mapped[str] = mapped_column(String(512), unique=True)
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100))
    size: Mapped[int] = mapped_column(Integer)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
