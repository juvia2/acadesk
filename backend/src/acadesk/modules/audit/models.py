import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from acadesk.db.base import Base, IdMixin, TenantMixin


class AuditLog(IdMixin, TenantMixin, Base):
    """추가만 가능. UPDATE·DELETE는 마이그레이션의 DB 트리거가 막는다."""

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_entity", "academy_id", "entity_type", "entity_id"),
        Index("ix_audit_logs_academy_at", "academy_id", "at"),
    )

    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    actor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))  # null = 시스템
    action: Mapped[str] = mapped_column(String(64))
    entity_type: Mapped[str] = mapped_column(String(64))
    entity_id: Mapped[uuid.UUID]
    before: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    after: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    reason: Mapped[str | None] = mapped_column(Text)
