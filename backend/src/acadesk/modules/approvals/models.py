import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from acadesk.db.base import Base, IdMixin, TenantMixin, TimestampMixin, str_enum

from .schemas import ApprovalStatus


class Approval(IdMixin, TenantMixin, TimestampMixin, Base):
    """승인함 항목. 후보 1건당 1개.

    facts_snapshot은 승인 시점의 사실이다. 발송 직전에 DB를 다시 읽어 이 값과 다르면 취소한다.
    """

    __tablename__ = "approvals"

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("notice_candidates.id", ondelete="CASCADE"), unique=True
    )
    status: Mapped[ApprovalStatus] = mapped_column(
        str_enum(ApprovalStatus, 16), default=ApprovalStatus.PENDING, index=True
    )
    body_template: Mapped[str] = mapped_column(Text)  # 자리 표시가 남은 문구
    edited_body: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(16), default="ko")
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    facts_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    ai_run_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("ai_runs.id"))
    decided_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    hold_until: Mapped[date | None] = mapped_column(Date)
    decision_reason: Mapped[str | None] = mapped_column(Text)


class ApprovalEvent(IdMixin, TenantMixin, Base):
    __tablename__ = "approval_events"

    approval_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("approvals.id", ondelete="CASCADE"), index=True
    )
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    actor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(32))
    note: Mapped[str | None] = mapped_column(Text)
