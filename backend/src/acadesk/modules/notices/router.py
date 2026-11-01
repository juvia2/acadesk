import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status

from acadesk.api.deps import MVP, CurrentUserDep, access
from acadesk.core.errors import not_implemented
from acadesk.core.schemas import Page, PageParams, page_params
from acadesk.core.security import MEMBERS, STAFF

from .schemas import (
    AttachmentOut,
    NoticeAudience,
    NoticeCreate,
    NoticeOut,
    NoticeReads,
    NoticeUpdate,
)

router = APIRouter(prefix="/notices", tags=["공지사항"])


@router.get(
    "",
    summary="공지 목록",
    description="요청한 사람에게 보이는 공지만 준다. 학생은 학원 전체·내 강의의 학생 대상 공지, "
    "학부모는 자녀 강의의 학부모 대상 공지. 고정 공지가 먼저.",
    **access(MVP, *MEMBERS),
)
def list_notices(
    user: CurrentUserDep,
    paging: Annotated[PageParams, Depends(page_params)],
    lecture_id: uuid.UUID | None = None,
    audience: NoticeAudience | None = None,
    unread: bool = False,
    student_id: uuid.UUID | None = None,
) -> Page[NoticeOut]:
    raise not_implemented()


@router.post(
    "",
    summary="공지 작성",
    description="관리자는 학원 전체·모든 강의, 교사는 자기 강의만. notify=true면 앱 푸시 (문자는 보내지 않음).",
    status_code=status.HTTP_201_CREATED,
    **access(MVP, *STAFF),
)
def create_notice(user: CurrentUserDep, body: NoticeCreate) -> NoticeOut:
    raise not_implemented()


@router.post(
    "/attachments",
    summary="첨부 파일 올리기",
    description="비공개 저장소에 저장. 공지 작성 때 attachment_ids로 연결한다. 10MB 이하.",
    status_code=status.HTTP_201_CREATED,
    **access(MVP, *STAFF),
)
def upload_attachment(user: CurrentUserDep, file: Annotated[UploadFile, File()]) -> AttachmentOut:
    raise not_implemented()


@router.get("/{notice_id}", summary="공지 상세", **access(MVP, *MEMBERS))
def get_notice(user: CurrentUserDep, notice_id: uuid.UUID) -> NoticeOut:
    raise not_implemented()


@router.post(
    "/{notice_id}/read",
    summary="읽음 표시",
    status_code=status.HTTP_204_NO_CONTENT,
    **access(MVP, *MEMBERS),
)
def mark_read(user: CurrentUserDep, notice_id: uuid.UUID) -> None:
    raise not_implemented()


@router.get(
    "/{notice_id}/reads",
    summary="읽음 현황",
    description="누가 아직 안 읽었는지. 작성자와 관리자만.",
    **access(MVP, *STAFF),
)
def get_reads(user: CurrentUserDep, notice_id: uuid.UUID) -> NoticeReads:
    raise not_implemented()


@router.patch("/{notice_id}", summary="공지 수정", **access(MVP, *STAFF))
def update_notice(user: CurrentUserDep, notice_id: uuid.UUID, body: NoticeUpdate) -> NoticeOut:
    raise not_implemented()


@router.delete(
    "/{notice_id}",
    summary="공지 삭제",
    status_code=status.HTTP_204_NO_CONTENT,
    **access(MVP, *STAFF),
)
def delete_notice(user: CurrentUserDep, notice_id: uuid.UUID) -> None:
    raise not_implemented()


routers = [router]
