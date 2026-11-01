import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from acadesk.db.base import Base, IdMixin, TenantMixin, TimestampMixin, str_enum

from .schemas import DocumentStatus


class Document(IdMixin, TenantMixin, TimestampMixin, Base):
    """수납 안내 PDF. 파일은 비공개 저장소에, 열람은 만료되는 서명 URL로."""

    __tablename__ = "documents"

    kind: Mapped[str] = mapped_column(String(32), default="billing_notice")
    approval_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("approvals.id"), index=True)
    status: Mapped[DocumentStatus] = mapped_column(
        str_enum(DocumentStatus, 16), default=DocumentStatus.GENERATING
    )
    storage_key: Mapped[str | None] = mapped_column(String(512))
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
