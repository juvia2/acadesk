"""학부모 익명 커뮤니티 (기획안 v2 8장).

익명성 원칙
- 응답에는 작성자 user_id를 절대 넣지 않는다. 내 글인지는 is_mine으로만 알려준다.
- 같은 글 안의 익명 댓글은 "익명1, 익명2"처럼 글마다 따로 번호를 매긴다 (다른 글과 연결 불가).
- "중2 학부모" 같은 소속 표시는 그 그룹 학부모가 min_group_size(기본 5) 이상일 때만 붙인다.
- 서버는 실제 작성자를 알고 있다. 신고 처리·법적 요청에만 쓰고 학원에는 보여주지 않는다.
"""

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class BoardKind(StrEnum):
    FREE = "free"
    QUESTION = "question"
    INFO = "info"  # 정보 공유
    MARKET = "market"  # 나눔·거래 (결제 없음)
    SUGGESTION = "suggestion"  # 학원에 건의 (학원이 볼 수 있는 유일한 게시판)


class BoardOut(BaseModel):
    id: uuid.UUID
    kind: BoardKind
    name: str
    description: str | None = None
    visible_to_academy: bool = Field(description="학원 관리자가 볼 수 있는지 (건의 게시판만 true)")


class AuthorDisplay(StrEnum):
    ANONYMOUS = "anonymous"
    NICKNAME = "nickname"


class PostScope(StrEnum):
    ACADEMY = "academy"  # 학원 전체 학부모
    GRADE = "grade"  # 같은 학년 학부모
    LECTURE = "lecture"  # 같은 강의 학부모


class ContentStatus(StrEnum):
    ACTIVE = "active"
    BLINDED = "blinded"  # 신고 누적으로 임시 블라인드 (운영자 검토 대기)
    REMOVED = "removed"  # 운영자 삭제
    DELETED = "deleted"  # 작성자 삭제


class MarketType(StrEnum):
    SHARE = "share"  # 나눔
    SELL = "sell"


class MarketStatus(StrEnum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    DONE = "done"


class MarketInfo(BaseModel):
    type: MarketType
    price: int | None = Field(None, ge=0, description="원. 나눔이면 null")
    status: MarketStatus = MarketStatus.AVAILABLE


class PostOut(BaseModel):
    id: uuid.UUID
    board_id: uuid.UUID
    board_kind: BoardKind
    title: str
    preview: str = Field(description="본문 앞부분")
    author_label: str = Field(description="익명 / 중2 학부모 / 닉네임")
    scope: PostScope
    scope_label: str = Field(description="학원 전체 / 중2 / 중2 수학 A")
    status: ContentStatus
    market: MarketInfo | None = None
    like_count: int = 0
    comment_count: int = 0
    liked: bool = False
    bookmarked: bool = False
    is_mine: bool = False
    forwarded_to_academy: bool = False
    image_urls: list[str] = []
    created_at: datetime
    edited_at: datetime | None = None


class PostDetail(PostOut):
    body: str


class PostCreate(BaseModel):
    board_id: uuid.UUID
    title: str = Field(min_length=2, max_length=100)
    body: str = Field(min_length=2, max_length=5000)
    author_display: AuthorDisplay = AuthorDisplay.ANONYMOUS
    show_group_label: bool = Field(True, description="익명일 때 '중2 학부모' 표시를 붙일지")
    scope: PostScope = PostScope.ACADEMY
    scope_grade: str | None = Field(None, description="scope=grade: 내 자녀 학년 중 하나")
    scope_lecture_id: uuid.UUID | None = Field(
        None, description="scope=lecture: 내 자녀 강의 중 하나"
    )
    market: MarketInfo | None = Field(None, description="나눔·거래 게시판만")
    image_ids: list[uuid.UUID] = Field([], max_length=5)


class PostUpdate(BaseModel):
    title: str | None = Field(None, min_length=2, max_length=100)
    body: str | None = Field(None, min_length=2, max_length=5000)
    market_status: MarketStatus | None = None


class MaskResult(BaseModel):
    """글 저장 전 검사 결과. 전화번호·실명 패턴은 가려서 저장하고 작성자에게 알려준다."""

    masked: bool
    warnings: list[str] = Field(
        [], description="예: 전화번호가 가려졌습니다, 교사 이름이 포함돼 있습니다"
    )


class PostCreateResult(BaseModel):
    post: PostDetail
    check: MaskResult


class CommentOut(BaseModel):
    id: uuid.UUID
    post_id: uuid.UUID
    parent_id: uuid.UUID | None = None
    author_label: str = Field(description="글쓴이 / 익명1 / 닉네임")
    body: str
    status: ContentStatus
    is_mine: bool = False
    created_at: datetime


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=1000)
    parent_id: uuid.UUID | None = Field(None, description="대댓글")
    author_display: AuthorDisplay = AuthorDisplay.ANONYMOUS


class ReportReason(StrEnum):
    ABUSE = "abuse"  # 욕설·비방
    PERSONAL_INFO = "personal_info"  # 아이·교사 실명, 연락처
    DEFAMATION = "defamation"  # 명예훼손 (임시조치 요청)
    AD = "ad"  # 광고·다른 학원 홍보
    SPAM = "spam"
    ILLEGAL = "illegal"
    OTHER = "other"


class ReportBody(BaseModel):
    reason: ReportReason
    detail: str | None = Field(None, max_length=500)


class ReportResult(BaseModel):
    accepted: bool = True
    blinded: bool = Field(description="이번 신고로 임시 블라인드됐는지 (신고 3건)")


class BlockBody(BaseModel):
    """글이나 댓글을 기준으로 작성자를 차단한다. 차단해도 상대가 누군지는 알려주지 않는다."""

    post_id: uuid.UUID | None = None
    comment_id: uuid.UUID | None = None


class BlockOut(BaseModel):
    id: uuid.UUID
    label: str = Field(description="차단할 때 본 표시. 예: '익명 (자유게시판 글)'")
    created_at: datetime


class CommunityProfile(BaseModel):
    nickname: str | None = None
    agreed_rules_at: datetime | None = Field(None, description="이용 규칙 동의 전에는 글쓰기 불가")
    muted_until: datetime | None = Field(None, description="제재 중이면 글쓰기 정지 종료 시각")


class ProfileUpdate(BaseModel):
    nickname: str = Field(min_length=2, max_length=12)


# ── 학원 관리자 쪽 ─────────────────────────────────


class CommunitySettings(BaseModel):
    enabled: bool = True
    min_group_size: int = Field(5, ge=3, le=20, description="소속 표시를 붙이는 최소 인원")
    market_enabled: bool = True


class CommunityStats(BaseModel):
    """학원이 볼 수 있는 숫자. 글 내용과 작성자는 포함하지 않는다."""

    joined_parents: int
    active_parents_7d: int
    posts_7d: int
    reports_7d: int
    blinded_now: int


# ── 플랫폼 운영자 (신고 처리) ──────────────────────


class ModerationTarget(StrEnum):
    POST = "post"
    COMMENT = "comment"


class ModerationItem(BaseModel):
    target_type: ModerationTarget
    target_id: uuid.UUID
    academy_id: uuid.UUID
    academy_name: str
    content: str
    status: ContentStatus
    report_count: int
    reasons: dict[ReportReason, int]
    author_prior_sanctions: int = Field(description="익명 뒤 실제 계정의 이전 제재 횟수")
    first_reported_at: datetime


class Sanction(StrEnum):
    NONE = "none"
    WARN = "warn"
    MUTE_7D = "mute_7d"
    MUTE_30D = "mute_30d"
    BAN = "ban"  # 커뮤니티 영구 이용 정지


class ModerationDecision(BaseModel):
    action: str = Field(
        pattern="^(restore|remove)$", description="restore=블라인드 해제, remove=삭제"
    )
    sanction: Sanction = Sanction.NONE
    note: str = Field(description="처리 사유 (기록용)")
