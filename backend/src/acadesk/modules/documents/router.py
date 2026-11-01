import uuid

from fastapi import APIRouter, status

from acadesk.api.deps import EXT, CurrentUserDep, access
from acadesk.core.errors import not_implemented
from acadesk.core.security import STAFF_ADMIN

from .schemas import BillingNoticeCreate, DocumentLink, DocumentOut

router = APIRouter(prefix="/documents", tags=["수납 안내 PDF"])


@router.post(
    "/billing-notices",
    summary="수납 안내 PDF 생성",
    description="수납 3단계 승인이 끝난 건만 가능하다. 생성 시점 DB 값이 아니라 승인 스냅샷 값으로 만든다.",
    status_code=status.HTTP_202_ACCEPTED,
    **access(EXT, *STAFF_ADMIN),
)
def create_billing_notice(user: CurrentUserDep, body: BillingNoticeCreate) -> DocumentOut:
    raise not_implemented()


@router.get("/{document_id}", summary="PDF 상태", **access(EXT, *STAFF_ADMIN))
def get_document(user: CurrentUserDep, document_id: uuid.UUID) -> DocumentOut:
    raise not_implemented()


@router.post(
    "/{document_id}/links",
    summary="만료되는 열람 링크 발급",
    description="비공개 저장소의 서명 URL. 발급 기록이 감사 로그에 남는다.",
    **access(EXT, *STAFF_ADMIN),
)
def create_link(user: CurrentUserDep, document_id: uuid.UUID) -> DocumentLink:
    raise not_implemented()


routers = [router]
