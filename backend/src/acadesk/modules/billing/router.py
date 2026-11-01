import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from acadesk.api.deps import STAGE2, STAGE3, CurrentUserDep, access
from acadesk.core.errors import not_implemented
from acadesk.core.schemas import Page, PageParams, page_params
from acadesk.core.security import STAFF, STAFF_ADMIN, Role

from .schemas import (
    DepositMatchConfirm,
    DepositMatchOut,
    DepositMatchReject,
    DepositMatchStatus,
    HoldCreate,
    HoldReason,
    InvoiceCreate,
    InvoiceOut,
    InvoiceStatus,
    InvoiceUpdate,
    PaymentCreate,
    PaymentOut,
    PromiseCreate,
    PromiseOut,
    SiblingDiscountSettings,
    VoidBody,
)

invoices_router = APIRouter(prefix="/invoices", tags=["수납"])
payments_router = APIRouter(prefix="/payments", tags=["수납"])
matches_router = APIRouter(prefix="/deposit-matches", tags=["수납"])
billing_router = APIRouter(prefix="/billing", tags=["수납"])

Paging = Annotated[PageParams, Depends(page_params)]


# ── 청구 ─────────────────────────────────────────────


@invoices_router.get("", summary="청구 목록", **access(STAGE2, *STAFF_ADMIN))
def list_invoices(
    user: CurrentUserDep,
    paging: Paging,
    status_: Annotated[InvoiceStatus | None, Query(alias="status")] = None,
    student_id: uuid.UUID | None = None,
    household_id: uuid.UUID | None = None,
    billing_month: Annotated[str | None, Query(pattern=r"^\d{4}-\d{2}$")] = None,
    overdue: bool | None = None,
    on_hold: bool | None = None,
) -> Page[InvoiceOut]:
    raise not_implemented()


@invoices_router.post(
    "",
    summary="청구 직접 등록",
    status_code=status.HTTP_201_CREATED,
    **access(STAGE2, *STAFF_ADMIN),
)
def create_invoice(user: CurrentUserDep, body: InvoiceCreate) -> InvoiceOut:
    raise not_implemented()


@invoices_router.get("/{invoice_id}", summary="청구 상세", **access(STAGE2, *STAFF_ADMIN))
def get_invoice(user: CurrentUserDep, invoice_id: uuid.UUID) -> InvoiceOut:
    raise not_implemented()


@invoices_router.patch(
    "/{invoice_id}",
    summary="청구 수정·취소",
    description="금액이 바뀌거나 취소되면 예약된 수납 안내를 다시 검사한다.",
    **access(STAGE2, *STAFF_ADMIN),
)
def update_invoice(user: CurrentUserDep, invoice_id: uuid.UUID, body: InvoiceUpdate) -> InvoiceOut:
    raise not_implemented()


@invoices_router.post(
    "/{invoice_id}/holds",
    summary="자동 안내 보류 걸기",
    description="보류가 하나라도 있으면 이 청구의 자동 안내는 만들어지지 않고 예약 건도 취소된다.",
    **access(STAGE3, *STAFF_ADMIN),
)
def add_hold(user: CurrentUserDep, invoice_id: uuid.UUID, body: HoldCreate) -> InvoiceOut:
    raise not_implemented()


@invoices_router.delete(
    "/{invoice_id}/holds/{reason}", summary="보류 해제", **access(STAGE3, *STAFF_ADMIN)
)
def remove_hold(user: CurrentUserDep, invoice_id: uuid.UUID, reason: HoldReason) -> InvoiceOut:
    raise not_implemented()


@invoices_router.get(
    "/{invoice_id}/promises", summary="납부 약속 목록", **access(STAGE3, *STAFF_ADMIN)
)
def list_promises(user: CurrentUserDep, invoice_id: uuid.UUID) -> list[PromiseOut]:
    raise not_implemented()


@invoices_router.post(
    "/{invoice_id}/promises",
    summary="납부 약속 등록",
    description="약속일까지 수납 안내를 보류하고, 약속일 다음 날 납부 확인 후보를 만든다.",
    status_code=status.HTTP_201_CREATED,
    **access(STAGE3, *STAFF_ADMIN),
)
def create_promise(user: CurrentUserDep, invoice_id: uuid.UUID, body: PromiseCreate) -> PromiseOut:
    raise not_implemented()


@invoices_router.delete(
    "/{invoice_id}/promises/{promise_id}",
    summary="납부 약속 취소",
    status_code=status.HTTP_204_NO_CONTENT,
    **access(STAGE3, *STAFF_ADMIN),
)
def cancel_promise(user: CurrentUserDep, invoice_id: uuid.UUID, promise_id: uuid.UUID) -> None:
    raise not_implemented()


# ── 납부 ─────────────────────────────────────────────


@payments_router.get("", summary="납부 기록", **access(STAGE2, *STAFF_ADMIN))
def list_payments(
    user: CurrentUserDep,
    paging: Paging,
    student_id: uuid.UUID | None = None,
    household_id: uuid.UUID | None = None,
) -> Page[PaymentOut]:
    raise not_implemented()


@payments_router.post(
    "",
    summary="납부 등록",
    description="여러 청구(형제 포함)에 나눠 반영할 수 있다. 완납된 청구의 예약 안내는 취소된다.",
    status_code=status.HTTP_201_CREATED,
    **access(STAGE2, *STAFF_ADMIN),
)
def create_payment(user: CurrentUserDep, body: PaymentCreate) -> PaymentOut:
    raise not_implemented()


@payments_router.post(
    "/{payment_id}/void",
    summary="납부 취소",
    description="삭제하지 않고 취소 표시만 한다. 잔액이 다시 생기면 규칙 엔진이 다음 실행에서 판단한다.",
    **access(STAGE2, Role.OWNER, Role.MANAGER),
)
def void_payment(user: CurrentUserDep, payment_id: uuid.UUID, body: VoidBody) -> PaymentOut:
    raise not_implemented()


# ── 입금자명 매칭 ───────────────────────────────────


@matches_router.get(
    "",
    summary="입금자명 매칭 후보",
    description="통장 입금 내역 업로드 후 생긴다. 가구 단위로 찾아 형 이름으로 낸 동생 학원비도 잡는다.",
    **access(STAGE3, *STAFF_ADMIN),
)
def list_matches(
    user: CurrentUserDep,
    paging: Paging,
    status_: Annotated[DepositMatchStatus, Query(alias="status")] = DepositMatchStatus.PENDING,
) -> Page[DepositMatchOut]:
    raise not_implemented()


@matches_router.post(
    "/{match_id}/confirm",
    summary="매칭 확정 → 납부 등록",
    **access(STAGE3, *STAFF_ADMIN),
)
def confirm_match(
    user: CurrentUserDep, match_id: uuid.UUID, body: DepositMatchConfirm
) -> PaymentOut:
    raise not_implemented()


@matches_router.post(
    "/{match_id}/reject",
    summary="매칭 거절",
    status_code=status.HTTP_204_NO_CONTENT,
    **access(STAGE3, *STAFF_ADMIN),
)
def reject_match(user: CurrentUserDep, match_id: uuid.UUID, body: DepositMatchReject) -> None:
    raise not_implemented()


# ── 형제 할인 설정 ─────────────────────────────────


@billing_router.get("/sibling-discount", summary="형제 할인 규칙 조회", **access(STAGE3, *STAFF))
def get_sibling_discount(user: CurrentUserDep) -> SiblingDiscountSettings:
    raise not_implemented()


@billing_router.put(
    "/sibling-discount",
    summary="형제 할인 규칙 저장",
    description="청구 생성 때 할인 줄로 기록한다. 바꾼 뒤 이미 만든 청구는 바뀌지 않는다.",
    **access(STAGE3, Role.OWNER),
)
def set_sibling_discount(
    user: CurrentUserDep, body: SiblingDiscountSettings
) -> SiblingDiscountSettings:
    raise not_implemented()


routers = [invoices_router, payments_router, matches_router, billing_router]
