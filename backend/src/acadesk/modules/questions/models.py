import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from acadesk.core.security import Role
from acadesk.db.base import Base, IdMixin, TenantMixin, TimestampMixin, str_enum

from .schemas import QuestionCategory, QuestionStatus, QuestionVisibility


class Question(IdMixin, TenantMixin, TimestampMixin, Base):
    """질문 스레드. author_role=student인 스레드는 학부모에게 보이지 않는다."""

    __tablename__ = "questions"
    __table_args__ = (Index("ix_questions_assignee_status", "assignee_id", "status"),)

    title: Mapped[str] = mapped_column(String(200))
    category: Mapped[QuestionCategory] = mapped_column(str_enum(QuestionCategory, 16))
    status: Mapped[QuestionStatus] = mapped_column(
        str_enum(QuestionStatus, 16), default=QuestionStatus.OPEN
    )
    visibility: Mapped[QuestionVisibility] = mapped_column(
        str_enum(QuestionVisibility, 16), default=QuestionVisibility.PRIVATE
    )
    author_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    author_role: Mapped[Role] = mapped_column(str_enum(Role, 16))
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"))
    lecture_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("lectures.id"))
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    last_message_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class QuestionMessage(IdMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "question_messages"

    question_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), index=True
    )
    author_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(Text)
    attachment_ids: Mapped[list[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)), default=list)


class QuestionRead(TenantMixin, Base):
    """사용자별 마지막으로 읽은 시각 → 안 읽은 메시지 수 계산."""

    __tablename__ = "question_reads"

    question_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    last_read_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
