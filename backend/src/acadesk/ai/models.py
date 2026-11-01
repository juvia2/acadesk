"""AI 실행 기록 (ai_runs, ai_steps).

RAG 문서 조각 테이블(pgvector)은 임베딩 모델과 차원이 정해지면 추가한다.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from acadesk.ai.schemas import AiRunStatus, AiTask
from acadesk.db.base import Base, IdMixin, TenantMixin, TimestampMixin, str_enum


class AiRun(IdMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "ai_runs"

    task: Mapped[AiTask] = mapped_column(str_enum(AiTask), index=True)
    status: Mapped[AiRunStatus] = mapped_column(str_enum(AiRunStatus, 16))
    target_type: Mapped[str] = mapped_column(String(32))
    target_id: Mapped[uuid.UUID | None]
    input: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    output: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    evidence_ids: Mapped[list[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)), default=list)
    validation_errors: Mapped[list[str]] = mapped_column(JSONB, default=list)
    prompt_id: Mapped[str] = mapped_column(String(64))
    prompt_version: Mapped[str] = mapped_column(String(32))
    model: Mapped[str] = mapped_column(String(64))
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # 담당자 피드백 (수정률 지표)
    feedback_accepted: Mapped[bool | None]
    feedback_edited_output: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    feedback_note: Mapped[str | None] = mapped_column(Text)


class AiStep(IdMixin, TenantMixin, Base):
    __tablename__ = "ai_steps"
    __table_args__ = (UniqueConstraint("run_id", "seq"),)

    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ai_runs.id", ondelete="CASCADE"))
    seq: Mapped[int] = mapped_column(Integer)
    node: Mapped[str] = mapped_column(String(64))
    tool: Mapped[str | None] = mapped_column(String(64))
    input_summary: Mapped[str | None] = mapped_column(Text)
    output_summary: Mapped[str | None] = mapped_column(Text)
    duration_ms: Mapped[int] = mapped_column(Integer)
    error: Mapped[str | None] = mapped_column(Text)
