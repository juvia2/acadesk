"""담당자 승인함.

엔드포인트는 모든 역할에 열려 있고, 실제 승인 가능 여부는 안내 종류별
approval_roles 설정(규칙 엔진)으로 서비스에서 검사한다. 예: 수납 3단계 = 원장·실장.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from acadesk.api.deps import MVP, CurrentUserDep, access
from acadesk.core.errors import not_implemented
from acadesk.core.schemas import BulkResult, IdsBody, Page, PageParams, page_params
from acadesk.core.security import ALL_ROLES
from acadesk.modules.messaging.schemas import NoticeKind

from .schemas import (
    ApprovalDetail,
    ApprovalStatus,
    ApprovalSummary,
    ApproveBody,
    HoldBody,
    RejectBody,
)

router = APIRouter(prefix="/approvals", tags=["승인함"])


@router.get("", summary="승인함 목록", **access(MVP, *ALL_ROLES))
def list_approvals(
    user: CurrentUserDep,
    paging: Annotated[PageParams, Depends(page_params)],
    status_: Annotated[ApprovalStatus, Query(alias="status")] = ApprovalStatus.PENDING,
    kind: NoticeKind | None = None,
    mine: Annotated[bool, Query(description="내가 승인할 수 있는 건만")] = False,
) -> Page[ApprovalSummary]:
    raise not_implemented()


@router.post(
    "/bulk-approve",
    summary="여러 건 한 번에 승인",
    description="문구 수정 없이 승인한다. 건별로 성공·실패를 돌려준다.",
    **access(MVP, *ALL_ROLES),
)
def bulk_approve(user: CurrentUserDep, body: IdsBody) -> BulkResult:
    raise not_implemented()


@router.get(
    "/{approval_id}",
    summary="승인 상세",
    description="수신자, 사실, 근거, 문구를 나란히 보여준다.",
    **access(MVP, *ALL_ROLES),
)
def get_approval(user: CurrentUserDep, approval_id: uuid.UUID) -> ApprovalDetail:
    raise not_implemented()


@router.post(
    "/{approval_id}/approve",
    summary="승인 (수정 후 승인 포함)",
    description="승인 시점의 사실을 스냅샷으로 저장한다. 발송 직전에 DB를 다시 확인해 "
    "스냅샷과 다르면(예: 그 사이 납부) 발송을 취소한다.",
    **access(MVP, *ALL_ROLES),
)
def approve(user: CurrentUserDep, approval_id: uuid.UUID, body: ApproveBody) -> ApprovalDetail:
    raise not_implemented()


@router.post("/{approval_id}/hold", summary="보류", **access(MVP, *ALL_ROLES))
def hold(user: CurrentUserDep, approval_id: uuid.UUID, body: HoldBody) -> ApprovalDetail:
    raise not_implemented()


@router.post("/{approval_id}/reject", summary="반려", **access(MVP, *ALL_ROLES))
def reject(user: CurrentUserDep, approval_id: uuid.UUID, body: RejectBody) -> ApprovalDetail:
    raise not_implemented()


routers = [router]
