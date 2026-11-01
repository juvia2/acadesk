"""금액은 모두 정수(원)."""

import uuid
from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class InvoiceStatus(StrEnum):
    OPEN = "open"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    CANCELLED = "cancelled"


class HoldReason(StrEnum):
    DEPOSITOR_MISMATCH = "depositor_mismatch"  # 입금자명 불일치
    PARTIAL_PAYMENT = "partial_payment"
    INSTALLMENT_PROMISE = "installment_promise"  # 분납·납부 약속
    REFUND = "refund"
    LEAVE_OR_WITHDRAWAL = "leave_or_withdrawal"  # 휴원·퇴원
    DISPUTE = "dispute"  # 청구 이의
    MANUAL = "manual"


class HoldOut(BaseModel):
    reason: HoldReason
    note: str | None = None
    created_by: uuid.UUID | None = Field(None, description="규칙 엔진이 건 보류면 null")
    created_at: datetime


class HoldCreate(BaseModel):
    reason: HoldReason
    note: str | None = None


class InvoiceOut(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    student_name: str
    household_id: uuid.UUID | None = None
    billing_month: str = Field(pattern=r"^\d{4}-\d{2}$", examples=["2026-11"])
    due_date: date
    amount: int = Field(ge=0)
    discount: int = Field(0, ge=0)
    paid: int = Field(0, ge=0)
    balance: int = Field(description="amount - discount - paid")
    status: InvoiceStatus
    overdue_days: int = 0
    holds: list[HoldOut] = []


class InvoiceCreate(BaseModel):
    student_id: uuid.UUID
    billing_month: str = Field(pattern=r"^\d{4}-\d{2}$")
    due_date: date
    amount: int = Field(ge=0)
    discount: int = Field(0, ge=0)
    memo: str | None = None


class InvoiceUpdate(BaseModel):
    due_date: date | None = None
    amount: int | None = Field(None, ge=0)
    discount: int | None = Field(None, ge=0)
    status: InvoiceStatus | None = Field(None, description="cancelled로만 직접 변경 가능")
    reason: str = Field(description="변경 사유 (감사 로그)")


class PaymentMethod(StrEnum):
    BANK_TRANSFER = "bank_transfer"
    CARD = "card"
    CASH = "cash"
    OTHER = "other"


class Allocation(BaseModel):
    invoice_id: uuid.UUID
    amount: int = Field(gt=0)


class PaymentOut(BaseModel):
    id: uuid.UUID
    amount: int
    paid_at: datetime
    method: PaymentMethod
    payer_name: str | None = None
    allocations: list[Allocation]
    voided: bool = False
    created_by: uuid.UUID


class PaymentCreate(BaseModel):
    amount: int = Field(gt=0)
    paid_at: datetime
    method: PaymentMethod
    payer_name: str | None = None
    allocations: list[Allocation] = Field(
        min_length=1, description="형제 청구서 여러 건에 나눠 반영 가능. 합계 = amount"
    )


class VoidBody(BaseModel):
    reason: str


class DepositMatchStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class Deposit(BaseModel):
    payer_name: str
    amount: int
    deposited_at: datetime
    import_batch_id: uuid.UUID


class MatchCandidate(BaseModel):
    student_id: uuid.UUID
    student_name: str
    household_id: uuid.UUID | None = None
    invoice_ids: list[uuid.UUID]
    score: float = Field(ge=0, le=1)
    reasons: list[str] = Field(description="예: 보호자 이름 일치, 금액이 형제 청구 합계와 같음")


class DepositMatchOut(BaseModel):
    id: uuid.UUID
    deposit: Deposit
    candidates: list[MatchCandidate]
    status: DepositMatchStatus


class DepositMatchConfirm(BaseModel):
    allocations: list[Allocation] = Field(min_length=1)
    remember_payer_name: bool = Field(True, description="다음 달부터 이 입금자명을 자동 매칭")


class DepositMatchReject(BaseModel):
    note: str | None = None


class PromiseStatus(StrEnum):
    ACTIVE = "active"
    KEPT = "kept"
    BROKEN = "broken"
    CANCELLED = "cancelled"


class PromiseOut(BaseModel):
    id: uuid.UUID
    invoice_id: uuid.UUID
    promised_date: date
    amount: int | None = None
    note: str | None = None
    status: PromiseStatus
    source_reply_id: uuid.UUID | None = None


class PromiseCreate(BaseModel):
    promised_date: date
    amount: int | None = Field(None, gt=0, description="일부만 약속한 경우")
    note: str | None = None
    source_reply_id: uuid.UUID | None = None


class SiblingDiscountRule(BaseModel):
    nth_child: int = Field(ge=2, description="몇째부터")
    percent: int | None = Field(None, ge=0, le=100)
    fixed_amount: int | None = Field(None, ge=0)


class SiblingDiscountSettings(BaseModel):
    enabled: bool = False
    rules: list[SiblingDiscountRule] = []
