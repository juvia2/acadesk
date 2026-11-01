"""학부모 익명 커뮤니티.

author_id(실제 작성자)는 저장하지만 API 응답에는 내보내지 않는다. 학원 직원 계정은
이 테이블을 조회하는 API가 없다 (건의 게시판 제외).
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from acadesk.db.base import Base, IdMixin, TenantMixin, TimestampMixin, str_enum

from .schemas import (
    AuthorDisplay,
    BoardKind,
    ContentStatus,
    ModerationTarget,
    PostScope,
    ReportReason,
    Sanction,
)


class CommunityBoard(IdMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "community_boards"
    __table_args__ = (UniqueConstraint("academy_id", "kind"),)

    kind: Mapped[BoardKind] = mapped_column(str_enum(BoardKind, 16))
    name: Mapped[str] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(String(200))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class CommunityProfile(IdMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "community_profiles"
    __table_args__ = (UniqueConstraint("academy_id", "nickname"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    nickname: Mapped[str | None] = mapped_column(String(12))
    agreed_rules_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    muted_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    banned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    access_ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )  # 자녀 퇴원 30일 뒤


class CommunityPost(IdMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "community_posts"
    __table_args__ = (
        Index("ix_community_posts_board_created", "board_id", "created_at"),
        CheckConstraint(
            "(scope = 'academy') OR (scope = 'grade' AND scope_grade IS NOT NULL) "
            "OR (scope = 'lecture' AND scope_lecture_id IS NOT NULL)",
            name="scope_target",
        ),
    )

    board_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("community_boards.id"))
    author_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)  # 비공개
    author_display: Mapped[AuthorDisplay] = mapped_column(str_enum(AuthorDisplay, 16))
    group_label: Mapped[str | None] = mapped_column(String(50))  # 작성 시점에 계산 ("중2 학부모")
    scope: Mapped[PostScope] = mapped_column(str_enum(PostScope, 16))
    scope_grade: Mapped[str | None] = mapped_column(String(32))
    scope_lecture_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("lectures.id"))
    title: Mapped[str] = mapped_column(String(100))
    body: Mapped[str] = mapped_column(Text)  # 전화번호·실명 가림 처리 후 저장
    image_ids: Mapped[list[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)), default=list)
    market: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    status: Mapped[ContentStatus] = mapped_column(
        str_enum(ContentStatus, 16), default=ContentStatus.ACTIVE, index=True
    )
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    comment_count: Mapped[int] = mapped_column(Integer, default=0)
    report_count: Mapped[int] = mapped_column(Integer, default=0)
    edited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CommunityComment(IdMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "community_comments"

    post_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("community_posts.id", ondelete="CASCADE"), index=True
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("community_comments.id", ondelete="CASCADE")
    )
    author_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))  # 비공개
    author_display: Mapped[AuthorDisplay] = mapped_column(str_enum(AuthorDisplay, 16))
    anon_number: Mapped[int | None] = mapped_column(Integer)  # 이 글 안의 "익명N"
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[ContentStatus] = mapped_column(
        str_enum(ContentStatus, 16), default=ContentStatus.ACTIVE
    )
    report_count: Mapped[int] = mapped_column(Integer, default=0)


class CommunityAnonNumber(TenantMixin, Base):
    """글마다 따로 매기는 익명 번호. 같은 사람은 그 글 안에서 항상 같은 번호."""

    __tablename__ = "community_anon_numbers"
    __table_args__ = (UniqueConstraint("post_id", "number"),)

    post_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("community_posts.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    number: Mapped[int] = mapped_column(Integer)


class CommunityLike(TenantMixin, Base):
    __tablename__ = "community_likes"

    post_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("community_posts.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class CommunityBookmark(TenantMixin, Base):
    __tablename__ = "community_bookmarks"

    post_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("community_posts.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class CommunityReport(IdMixin, TenantMixin, Base):
    """한 사람이 같은 대상을 한 번만 신고. 서로 다른 3명이면 임시 블라인드."""

    __tablename__ = "community_reports"
    __table_args__ = (UniqueConstraint("target_type", "target_id", "reporter_id"),)

    target_type: Mapped[ModerationTarget] = mapped_column(str_enum(ModerationTarget, 16))
    target_id: Mapped[uuid.UUID] = mapped_column(index=True)
    reporter_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    reason: Mapped[ReportReason] = mapped_column(str_enum(ReportReason, 16))
    detail: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CommunityBlock(IdMixin, TenantMixin, Base):
    """차단. blocked_user_id는 서버 안에서만 쓰고 차단한 사람에게도 보여주지 않는다."""

    __tablename__ = "community_blocks"
    __table_args__ = (UniqueConstraint("blocker_id", "blocked_user_id"),)

    blocker_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    blocked_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    label: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class CommunitySanction(IdMixin, TenantMixin, Base):
    __tablename__ = "community_sanctions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    sanction: Mapped[Sanction] = mapped_column(str_enum(Sanction, 16))
    target_type: Mapped[ModerationTarget | None] = mapped_column(str_enum(ModerationTarget, 16))
    target_id: Mapped[uuid.UUID | None]
    until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    note: Mapped[str] = mapped_column(Text)
    decided_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
