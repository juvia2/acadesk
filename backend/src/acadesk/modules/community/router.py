"""학부모 익명 커뮤니티 (2단계).

학원 관리자는 글을 볼 수 없다 (기획안 v2 8-2 추천안). 학원은 건의 게시판 글과 숫자 통계만 받는다.
신고 처리는 플랫폼 운영자(role=operator)가 /ops/community에서 한다.
"""

import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Query, UploadFile, status

from acadesk.api.deps import STAGE2, CurrentUserDep, access
from acadesk.core.errors import not_implemented
from acadesk.core.schemas import Page, PageParams, page_params
from acadesk.core.security import STAFF_ADMIN, Role

from .schemas import (
    BlockBody,
    BlockOut,
    BoardOut,
    CommentCreate,
    CommentOut,
    CommunityProfile,
    CommunitySettings,
    CommunityStats,
    ModerationDecision,
    ModerationItem,
    ModerationTarget,
    PostCreate,
    PostCreateResult,
    PostDetail,
    PostOut,
    PostScope,
    PostUpdate,
    ProfileUpdate,
    ReportBody,
    ReportResult,
)

router = APIRouter(prefix="/community", tags=["학부모 커뮤니티"])
academy_router = APIRouter(prefix="/community/academy", tags=["학부모 커뮤니티 (학원)"])
ops_router = APIRouter(prefix="/ops/community", tags=["커뮤니티 신고 처리 (운영자)"])

Paging = Annotated[PageParams, Depends(page_params)]
PARENT = Role.PARENT


# ── 프로필 ───────────────────────────────────────────


@router.get("/profile", summary="내 커뮤니티 프로필", **access(STAGE2, PARENT))
def get_profile(user: CurrentUserDep) -> CommunityProfile:
    raise not_implemented()


@router.post(
    "/profile/agree-rules",
    summary="커뮤니티 이용 규칙 동의",
    description="동의해야 글·댓글을 쓸 수 있다.",
    **access(STAGE2, PARENT),
)
def agree_rules(user: CurrentUserDep) -> CommunityProfile:
    raise not_implemented()


@router.put(
    "/profile",
    summary="닉네임 설정",
    description="공개(닉네임) 글에만 쓰인다. 학원 안에서 중복 불가.",
    **access(STAGE2, PARENT),
)
def update_profile(user: CurrentUserDep, body: ProfileUpdate) -> CommunityProfile:
    raise not_implemented()


# ── 게시판·글 ───────────────────────────────────────


@router.get("/boards", summary="게시판 목록", **access(STAGE2, PARENT))
def list_boards(user: CurrentUserDep) -> list[BoardOut]:
    raise not_implemented()


@router.get(
    "/posts",
    summary="글 목록",
    description="내가 볼 수 있는 범위(학원 전체 + 내 자녀 학년·강의)의 글만. 차단한 사람의 글은 빠진다.",
    **access(STAGE2, PARENT),
)
def list_posts(
    user: CurrentUserDep,
    paging: Paging,
    board_id: uuid.UUID | None = None,
    scope: PostScope | None = None,
    q: Annotated[str | None, Query(max_length=50)] = None,
    sort: Literal["recent", "popular"] = "recent",
    mine: bool = False,
    bookmarked: bool = False,
) -> Page[PostOut]:
    raise not_implemented()


@router.post(
    "/posts/images",
    summary="글 이미지 올리기",
    description="사진 위치 정보(EXIF)는 지우고 저장한다.",
    status_code=status.HTTP_201_CREATED,
    **access(STAGE2, PARENT),
)
def upload_image(user: CurrentUserDep, file: Annotated[UploadFile, File()]) -> dict[str, str]:
    raise not_implemented()


@router.post(
    "/posts",
    summary="글쓰기",
    description="저장 전에 전화번호·실명 패턴을 가리고 결과를 check로 알려준다. 금칙어·다른 학원 홍보는 거부(422). "
    "건의 게시판 글은 학원 관리자에게 전달된다.",
    status_code=status.HTTP_201_CREATED,
    **access(STAGE2, PARENT),
)
def create_post(user: CurrentUserDep, body: PostCreate) -> PostCreateResult:
    raise not_implemented()


@router.get("/posts/{post_id}", summary="글 보기", **access(STAGE2, PARENT))
def get_post(user: CurrentUserDep, post_id: uuid.UUID) -> PostDetail:
    raise not_implemented()


@router.patch("/posts/{post_id}", summary="글 수정 (작성자)", **access(STAGE2, PARENT))
def update_post(user: CurrentUserDep, post_id: uuid.UUID, body: PostUpdate) -> PostDetail:
    raise not_implemented()


@router.delete(
    "/posts/{post_id}",
    summary="글 삭제 (작성자)",
    status_code=status.HTTP_204_NO_CONTENT,
    **access(STAGE2, PARENT),
)
def delete_post(user: CurrentUserDep, post_id: uuid.UUID) -> None:
    raise not_implemented()


@router.put(
    "/posts/{post_id}/like",
    summary="공감",
    status_code=status.HTTP_204_NO_CONTENT,
    **access(STAGE2, PARENT),
)
def like_post(user: CurrentUserDep, post_id: uuid.UUID) -> None:
    raise not_implemented()


@router.delete(
    "/posts/{post_id}/like",
    summary="공감 취소",
    status_code=status.HTTP_204_NO_CONTENT,
    **access(STAGE2, PARENT),
)
def unlike_post(user: CurrentUserDep, post_id: uuid.UUID) -> None:
    raise not_implemented()


@router.put(
    "/posts/{post_id}/bookmark",
    summary="북마크",
    status_code=status.HTTP_204_NO_CONTENT,
    **access(STAGE2, PARENT),
)
def bookmark_post(user: CurrentUserDep, post_id: uuid.UUID) -> None:
    raise not_implemented()


@router.delete(
    "/posts/{post_id}/bookmark",
    summary="북마크 취소",
    status_code=status.HTTP_204_NO_CONTENT,
    **access(STAGE2, PARENT),
)
def unbookmark_post(user: CurrentUserDep, post_id: uuid.UUID) -> None:
    raise not_implemented()


# ── 댓글 ─────────────────────────────────────────────


@router.get("/posts/{post_id}/comments", summary="댓글 목록", **access(STAGE2, PARENT))
def list_comments(user: CurrentUserDep, post_id: uuid.UUID) -> list[CommentOut]:
    raise not_implemented()


@router.post(
    "/posts/{post_id}/comments",
    summary="댓글 쓰기",
    description="익명 댓글은 이 글 안에서만 쓰는 번호(익명1, 익명2)가 붙는다. 글쓴이는 '글쓴이'로 표시.",
    status_code=status.HTTP_201_CREATED,
    **access(STAGE2, PARENT),
)
def create_comment(user: CurrentUserDep, post_id: uuid.UUID, body: CommentCreate) -> CommentOut:
    raise not_implemented()


@router.delete(
    "/comments/{comment_id}",
    summary="댓글 삭제 (작성자)",
    status_code=status.HTTP_204_NO_CONTENT,
    **access(STAGE2, PARENT),
)
def delete_comment(user: CurrentUserDep, comment_id: uuid.UUID) -> None:
    raise not_implemented()


# ── 신고·차단 ───────────────────────────────────────


@router.post(
    "/posts/{post_id}/reports",
    summary="글 신고",
    description="한 사람이 같은 글을 한 번만 신고할 수 있다. 서로 다른 3명이 신고하면 임시 블라인드되고 운영자 검토로 간다.",
    **access(STAGE2, PARENT),
)
def report_post(user: CurrentUserDep, post_id: uuid.UUID, body: ReportBody) -> ReportResult:
    raise not_implemented()


@router.post("/comments/{comment_id}/reports", summary="댓글 신고", **access(STAGE2, PARENT))
def report_comment(user: CurrentUserDep, comment_id: uuid.UUID, body: ReportBody) -> ReportResult:
    raise not_implemented()


@router.get("/blocks", summary="차단 목록", **access(STAGE2, PARENT))
def list_blocks(user: CurrentUserDep) -> list[BlockOut]:
    raise not_implemented()


@router.post(
    "/blocks",
    summary="작성자 차단",
    description="글이나 댓글 ID로 차단한다. 그 사람의 글·댓글이 내 화면에서 사라진다.",
    status_code=status.HTTP_201_CREATED,
    **access(STAGE2, PARENT),
)
def block_author(user: CurrentUserDep, body: BlockBody) -> BlockOut:
    raise not_implemented()


@router.delete(
    "/blocks/{block_id}",
    summary="차단 해제",
    status_code=status.HTTP_204_NO_CONTENT,
    **access(STAGE2, PARENT),
)
def unblock(user: CurrentUserDep, block_id: uuid.UUID) -> None:
    raise not_implemented()


# ── 학원 관리자 ─────────────────────────────────────


@academy_router.get(
    "/suggestions",
    summary="학원에 건의 글",
    description="학원이 볼 수 있는 유일한 커뮤니티 글. 작성자는 익명 표시 그대로.",
    **access(STAGE2, *STAFF_ADMIN),
)
def list_suggestions(user: CurrentUserDep, paging: Paging) -> Page[PostDetail]:
    raise not_implemented()


@academy_router.get("/stats", summary="커뮤니티 통계 (숫자만)", **access(STAGE2, *STAFF_ADMIN))
def get_stats(user: CurrentUserDep) -> CommunityStats:
    raise not_implemented()


@academy_router.get("/settings", summary="커뮤니티 설정 조회", **access(STAGE2, *STAFF_ADMIN))
def get_community_settings(user: CurrentUserDep) -> CommunitySettings:
    raise not_implemented()


@academy_router.put(
    "/settings",
    summary="커뮤니티 켜기·끄기, 소속 표시 최소 인원",
    **access(STAGE2, Role.OWNER),
)
def put_community_settings(user: CurrentUserDep, body: CommunitySettings) -> CommunitySettings:
    raise not_implemented()


# ── 플랫폼 운영자 ───────────────────────────────────


@ops_router.get(
    "/queue",
    summary="신고 검토 대기열",
    description="임시 블라인드된 글·댓글과 신고 사유. 학원을 가리지 않고 본다.",
    **access(STAGE2, Role.OPERATOR),
)
def moderation_queue(
    user: CurrentUserDep, paging: Paging, academy_id: uuid.UUID | None = None
) -> Page[ModerationItem]:
    raise not_implemented()


@ops_router.post(
    "/{target_type}/{target_id}/decision",
    summary="신고 처리 (복구·삭제·제재)",
    description="제재는 익명 뒤의 실제 계정에 적용된다. 처리 기록은 감사 로그에 남는다.",
    **access(STAGE2, Role.OPERATOR),
)
def decide(
    user: CurrentUserDep,
    target_type: ModerationTarget,
    target_id: uuid.UUID,
    body: ModerationDecision,
) -> ModerationItem:
    raise not_implemented()


routers = [router, academy_router, ops_router]
