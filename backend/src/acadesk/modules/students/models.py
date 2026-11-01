import uuid
from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from acadesk.db.base import Base, IdMixin, TenantMixin, TimestampMixin, str_enum

from .schemas import StudentStatus, SuggestionReason, SuggestionStatus


class Household(IdMixin, TenantMixin, TimestampMixin, Base):
    """형제를 묶는 가구. 담당자가 확인해야 만들어진다."""

    __tablename__ = "households"

    name: Mapped[str | None] = mapped_column(String(100))


class Student(IdMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "students"
    __table_args__ = (UniqueConstraint("academy_id", "external_id"),)

    external_id: Mapped[str | None] = mapped_column(String(64))  # 학원 학생 번호, 업로드 upsert 키
    name: Mapped[str] = mapped_column(String(100))
    grade: Mapped[str | None] = mapped_column(String(32))
    school: Mapped[str | None] = mapped_column(String(100))
    birth_date: Mapped[date | None] = mapped_column(Date)  # 만 14세 미만 가입 동의 판단
    status: Mapped[StudentStatus] = mapped_column(
        str_enum(StudentStatus, 16), default=StudentStatus.ACTIVE
    )
    household_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("households.id", ondelete="SET NULL"), index=True
    )


class Guardian(IdMixin, TenantMixin, TimestampMixin, Base):
    """보호자. 연락처는 암호화해 저장하고, 검색·중복 확인은 해시로 한다."""

    __tablename__ = "guardians"
    __table_args__ = (Index("ix_guardians_academy_phone_hash", "academy_id", "phone_hash"),)

    name: Mapped[str] = mapped_column(String(100))
    phone_encrypted: Mapped[bytes] = mapped_column(LargeBinary)
    phone_hash: Mapped[str] = mapped_column(String(64))  # 정규화한 번호의 HMAC-SHA256
    phone_last4: Mapped[str] = mapped_column(String(4))  # 마스킹 표시·검색용
    preferred_language: Mapped[str] = mapped_column(String(16), default="ko")
    consent_notices: Mapped[bool] = mapped_column(default=True)


class StudentGuardian(IdMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "student_guardians"
    __table_args__ = (UniqueConstraint("student_id", "guardian_id"),)

    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"))
    guardian_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("guardians.id", ondelete="CASCADE"), index=True
    )
    relation: Mapped[str] = mapped_column(String(32))
    is_primary: Mapped[bool] = mapped_column(default=False)
    receives_notices: Mapped[bool] = mapped_column(default=True)


class HouseholdSuggestion(IdMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "household_suggestions"
    # 같은 학생 조합은 한 번만 제안 (거절했으면 다시 제안하지 않음)
    __table_args__ = (UniqueConstraint("academy_id", "student_key"),)

    student_ids: Mapped[list[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)))
    student_key: Mapped[str] = mapped_column(String(512))  # 정렬한 student_ids를 이은 값
    reason: Mapped[SuggestionReason] = mapped_column(str_enum(SuggestionReason))
    evidence: Mapped[str] = mapped_column(String(255))
    status: Mapped[SuggestionStatus] = mapped_column(
        str_enum(SuggestionStatus, 16), default=SuggestionStatus.PENDING, index=True
    )
    decided_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    note: Mapped[str | None] = mapped_column(Text)


class StudentNote(IdMixin, TenantMixin, TimestampMixin, Base):
    """상담·통화 메모."""

    __tablename__ = "student_notes"

    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), index=True
    )
    author_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(Text)
