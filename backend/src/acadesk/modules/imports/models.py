import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from acadesk.db.base import Base, IdMixin, TenantMixin, TimestampMixin, str_enum

from .schemas import ImportKind, ImportStatus, RowStatus


class ImportBatch(IdMixin, TenantMixin, TimestampMixin, Base):
    """업로드 1회 = 1건. 원본 파일은 비공개 저장소(storage_key)에 둔다."""

    __tablename__ = "import_batches"

    kind: Mapped[ImportKind] = mapped_column(str_enum(ImportKind))
    source: Mapped[str] = mapped_column(String(16), default="file")
    filename: Mapped[str | None] = mapped_column(String(255))
    storage_key: Mapped[str | None] = mapped_column(String(512))
    status: Mapped[ImportStatus] = mapped_column(
        str_enum(ImportStatus), default=ImportStatus.UPLOADED, index=True
    )
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    ok_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    warning_count: Mapped[int] = mapped_column(Integer, default=0)
    duplicate_count: Mapped[int] = mapped_column(Integer, default=0)
    column_mapping: Mapped[dict[str, str] | None] = mapped_column(JSONB)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    committed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ImportRow(IdMixin, TenantMixin, Base):
    __tablename__ = "import_rows"
    __table_args__ = (UniqueConstraint("batch_id", "row_number"),)

    batch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("import_batches.id", ondelete="CASCADE"))
    row_number: Mapped[int] = mapped_column(Integer)
    status: Mapped[RowStatus] = mapped_column(str_enum(RowStatus, 16), index=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSONB)
    messages: Mapped[list[str]] = mapped_column(JSONB, default=list)


class ColumnMapping(IdMixin, TenantMixin, TimestampMixin, Base):
    """학원이 한 번 맞춘 열 매핑. 같은 열 구성으로 다시 올리면 자동 적용."""

    __tablename__ = "column_mappings"
    __table_args__ = (UniqueConstraint("academy_id", "kind", "header_signature"),)

    kind: Mapped[ImportKind] = mapped_column(str_enum(ImportKind))
    header_signature: Mapped[str] = mapped_column(String(64))  # 정렬한 열 이름의 해시
    mapping: Mapped[dict[str, str]] = mapped_column(JSONB)
