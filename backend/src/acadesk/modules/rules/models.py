"""규칙 엔진 실행 기록. 기준값 설정은 academy_settings(key='rules')에 있다."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from acadesk.db.base import Base, IdMixin, TenantMixin, TimestampMixin, str_enum

from .schemas import RuleRunStatus


class RuleRun(IdMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "rule_runs"

    status: Mapped[RuleRunStatus] = mapped_column(
        str_enum(RuleRunStatus, 16), default=RuleRunStatus.QUEUED
    )
    dry_run: Mapped[bool] = mapped_column(default=False)
    trigger: Mapped[str] = mapped_column(String(16))  # schedule | manual
    kinds: Mapped[list[str] | None] = mapped_column(ARRAY(String(32)))
    requested_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_count: Mapped[int] = mapped_column(Integer, default=0)
    held_count: Mapped[int] = mapped_column(Integer, default=0)
    skipped_duplicate_count: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text)
