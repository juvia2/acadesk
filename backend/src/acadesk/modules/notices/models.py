import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from acadesk.db.base import Base, IdMixin, TenantMixin, TimestampMixin, str_enum

from .schemas import NoticeAudience


class Notice(IdMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "notices"
    __table_args__ = (Index("ix_notices_academy_published", "academy_id", "published_at"),)

    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    lecture_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("lectures.id", ondelete="CASCADE"), index=True
    )  # null = 학원 전체
    audience: Mapped[NoticeAudience] = mapped_column(str_enum(NoticeAudience, 16))
    pinned: Mapped[bool] = mapped_column(default=False)
    attachment_ids: Mapped[list[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)), default=list)
    author_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class NoticeRead(TenantMixin, Base):
    __tablename__ = "notice_reads"

    notice_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("notices.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    read_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
