import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from acadesk.db.base import Base, IdMixin, TenantMixin, TimestampMixin, str_enum

from .schemas import (
    CandidateStatus,
    Channel,
    EmergencyReason,
    EmergencyStatus,
    EmergencyTargetType,
    IntentSource,
    MessageStatus,
    NoticeKind,
    ReplyIntent,
    ReplyStatus,
    ReviewStatus,
    TranslationStatus,
)

# ── 템플릿 ───────────────────────────────────────────


class Template(IdMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "templates"

    kind: Mapped[NoticeKind] = mapped_column(str_enum(NoticeKind))
    stage: Mapped[int | None] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(100))
    channel: Mapped[Channel] = mapped_column(str_enum(Channel, 16))
    archived: Mapped[bool] = mapped_column(default=False)


class TemplateVersion(IdMixin, TenantMixin, TimestampMixin, Base):
    """문구를 고치면 새 버전. 발송 건은 쓴 버전을 기록한다."""

    __tablename__ = "template_versions"
    __table_args__ = (UniqueConstraint("template_id", "version"),)

    template_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("templates.id", ondelete="CASCADE"))
    version: Mapped[int] = mapped_column(Integer)
    body: Mapped[str] = mapped_column(Text)
    variables: Mapped[list[str]] = mapped_column(ARRAY(String(64)), default=list)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    alimtalk_review: Mapped[ReviewStatus] = mapped_column(
        str_enum(ReviewStatus, 16), default=ReviewStatus.NONE
    )


class TemplateTranslation(IdMixin, TenantMixin, TimestampMixin, Base):
    """템플릿 버전 × 언어 단위 번역. 담당자가 승인한 것만 발송에 쓴다."""

    __tablename__ = "template_translations"
    __table_args__ = (UniqueConstraint("template_version_id", "language"),)

    template_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("template_versions.id", ondelete="CASCADE")
    )
    language: Mapped[str] = mapped_column(String(16))
    body: Mapped[str | None] = mapped_column(Text)
    status: Mapped[TranslationStatus] = mapped_column(str_enum(TranslationStatus, 16))
    validation_errors: Mapped[list[str]] = mapped_column(JSONB, default=list)
    ai_run_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("ai_runs.id"))
    approved_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# ── 안내 후보 ───────────────────────────────────────


class NoticeCandidate(IdMixin, TenantMixin, TimestampMixin, Base):
    """규칙 엔진이 만든 안내 후보. dedupe_key가 같으면 다시 만들지 않는다 (같은 단계 1회)."""

    __tablename__ = "notice_candidates"
    __table_args__ = (UniqueConstraint("academy_id", "dedupe_key"),)

    kind: Mapped[NoticeKind] = mapped_column(str_enum(NoticeKind))
    stage: Mapped[int | None] = mapped_column(Integer)
    guardian_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("guardians.id"), index=True)
    student_ids: Mapped[list[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)))
    status: Mapped[CandidateStatus] = mapped_column(str_enum(CandidateStatus), index=True)
    dedupe_key: Mapped[str] = mapped_column(String(200))  # 예: invoice:{id}:stage:2
    reason: Mapped[str] = mapped_column(Text)
    facts: Mapped[dict[str, Any]] = mapped_column(JSONB)  # 생성 시점 사실 (금액·날짜 등)
    hold_reason: Mapped[str | None] = mapped_column(Text)
    template_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("templates.id"))
    rule_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rule_runs.id"))


# ── 발송 ─────────────────────────────────────────────


class Message(IdMixin, TenantMixin, TimestampMixin, Base):
    """발송 건. 형제 묶음 안내면 후보 여러 건이 한 메시지가 된다 (message_candidates)."""

    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_messages_academy_status_scheduled", "academy_id", "status", "scheduled_at"),
    )

    guardian_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("guardians.id"), index=True)
    student_ids: Mapped[list[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)))
    channel: Mapped[Channel] = mapped_column(str_enum(Channel, 16))
    language: Mapped[str] = mapped_column(String(16), default="ko")
    body: Mapped[str] = mapped_column(Text)  # 실제 보낸 문구 (값 채운 뒤)
    template_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("template_versions.id")
    )
    status: Mapped[MessageStatus] = mapped_column(str_enum(MessageStatus, 16))
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failure_reason: Mapped[str | None] = mapped_column(Text)
    cancel_reason: Mapped[str | None] = mapped_column(Text)
    provider: Mapped[str | None] = mapped_column(String(32))
    provider_message_id: Mapped[str | None] = mapped_column(String(128), index=True)
    # 대행사에 넘기는 멱등키. 재시도해도 1회만 나가게
    idempotency_key: Mapped[str] = mapped_column(String(64), unique=True)
    fallback_of: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("messages.id"))
    emergency_message_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("emergency_messages.id"), index=True
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))


class MessageCandidate(TenantMixin, Base):
    __tablename__ = "message_candidates"

    message_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE"), primary_key=True
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("notice_candidates.id", ondelete="CASCADE"), primary_key=True
    )


# ── 긴급 문자 ───────────────────────────────────────


class EmergencyMessage(IdMixin, TenantMixin, TimestampMixin, Base):
    """긴급 문자 1회 발송. 학부모별 문자는 messages(emergency_message_id)로 남는다."""

    __tablename__ = "emergency_messages"

    reason: Mapped[EmergencyReason] = mapped_column(str_enum(EmergencyReason, 16))
    body: Mapped[str] = mapped_column(Text)
    target_type: Mapped[EmergencyTargetType] = mapped_column(str_enum(EmergencyTargetType, 16))
    target_lecture_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("lectures.id"))
    target_student_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), default=list
    )
    sent_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    recipient_count: Mapped[int] = mapped_column(Integer, default=0)
    delivered_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[EmergencyStatus] = mapped_column(str_enum(EmergencyStatus, 16))


# ── 회신 ─────────────────────────────────────────────


class Reply(IdMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "replies"

    message_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("messages.id"), index=True)
    guardian_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("guardians.id"), index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    body: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(16), default="ko")
    translated_body: Mapped[str | None] = mapped_column(Text)
    intent: Mapped[ReplyIntent] = mapped_column(str_enum(ReplyIntent), default=ReplyIntent.UNKNOWN)
    intent_source: Mapped[IntentSource | None] = mapped_column(str_enum(IntentSource, 16))
    intent_confirmed: Mapped[bool] = mapped_column(default=False)
    follow_up_stopped: Mapped[bool] = mapped_column(default=False)
    status: Mapped[ReplyStatus] = mapped_column(
        str_enum(ReplyStatus, 16), default=ReplyStatus.OPEN, index=True
    )
    handled_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    handled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    note: Mapped[str | None] = mapped_column(Text)
    provider_event_id: Mapped[str | None] = mapped_column(String(128))


class ReplyToken(IdMixin, TenantMixin, Base):
    """원클릭 응답 링크의 일회용 토큰. 원문은 저장하지 않고 해시만."""

    __tablename__ = "reply_tokens"

    message_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE"), index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class WebhookEvent(IdMixin, Base):
    """대행사 웹훅 원문. 같은 이벤트가 여러 번 와도 한 번만 처리. 학원은 처리하면서 찾는다."""

    __tablename__ = "webhook_events"
    __table_args__ = (UniqueConstraint("provider", "event_id"),)

    provider: Mapped[str] = mapped_column(String(32))
    event_id: Mapped[str] = mapped_column(String(128))
    kind: Mapped[str] = mapped_column(String(16))  # delivery | inbound
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error: Mapped[str | None] = mapped_column(Text)
