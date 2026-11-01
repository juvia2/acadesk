"""수납. 금액은 정수(원)."""

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from acadesk.db.base import Base, IdMixin, TenantMixin, TimestampMixin, str_enum

from .schemas import DepositMatchStatus, HoldReason, InvoiceStatus, PaymentMethod, PromiseStatus


class Invoice(IdMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint("academy_id", "external_key"),
        Index("ix_invoices_student_month", "student_id", "billing_month"),
        CheckConstraint("amount >= 0", name="amount_non_negative"),
        CheckConstraint("discount >= 0 AND discount <= amount", name="discount_range"),
        CheckConstraint("paid >= 0", name="paid_non_negative"),
        CheckConstraint("billing_month ~ '^[0-9]{4}-[0-9]{2}$'", name="billing_month_format"),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id", ondelete="RESTRICT"))
    external_key: Mapped[str | None] = mapped_column(String(128))  # 업로드 upsert 키
    billing_month: Mapped[str] = mapped_column(String(7))
    due_date: Mapped[date] = mapped_column(Date, index=True)
    amount: Mapped[int] = mapped_column(Integer)
    discount: Mapped[int] = mapped_column(Integer, default=0)
    # 납부 배분 합계. 배분이 바뀔 때 같은 트랜잭션에서 갱신한다. 잔액 = amount - discount - paid
    paid: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[InvoiceStatus] = mapped_column(
        str_enum(InvoiceStatus, 16), default=InvoiceStatus.OPEN, index=True
    )
    memo: Mapped[str | None] = mapped_column(Text)


class InvoiceHold(IdMixin, TenantMixin, Base):
    """보류가 하나라도 열려 있으면 그 청구의 자동 안내를 만들지 않는다. 해제해도 기록은 남긴다."""

    __tablename__ = "invoice_holds"
    __table_args__ = (
        Index(
            "uq_invoice_holds_open",
            "invoice_id",
            "reason",
            unique=True,
            postgresql_where=text("released_at IS NULL"),
        ),
    )

    invoice_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"))
    reason: Mapped[HoldReason] = mapped_column(str_enum(HoldReason))
    note: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))  # null=규칙 엔진
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    released_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))


class Payment(IdMixin, TenantMixin, TimestampMixin, Base):
    """삭제하지 않고 voided_at으로 취소한다."""

    __tablename__ = "payments"
    __table_args__ = (CheckConstraint("amount > 0", name="amount_positive"),)

    amount: Mapped[int] = mapped_column(Integer)
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    method: Mapped[PaymentMethod] = mapped_column(str_enum(PaymentMethod, 16))
    payer_name: Mapped[str | None] = mapped_column(String(100))
    voided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    void_reason: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    import_batch_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("import_batches.id"))


class PaymentAllocation(IdMixin, TenantMixin, Base):
    """납부 1건을 여러 청구(형제 포함)에 나눠 반영."""

    __tablename__ = "payment_allocations"
    __table_args__ = (
        UniqueConstraint("payment_id", "invoice_id"),
        CheckConstraint("amount > 0", name="amount_positive"),
    )

    payment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("payments.id", ondelete="CASCADE"))
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("invoices.id", ondelete="RESTRICT"), index=True
    )
    amount: Mapped[int] = mapped_column(Integer)


class BankDeposit(IdMixin, TenantMixin, TimestampMixin, Base):
    """통장 입금 내역 업로드의 한 줄."""

    __tablename__ = "bank_deposits"
    __table_args__ = (UniqueConstraint("academy_id", "external_key"),)

    import_batch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("import_batches.id"))
    external_key: Mapped[str] = mapped_column(String(128))  # 날짜+금액+입금자+순번 해시
    payer_name: Mapped[str] = mapped_column(String(100))
    amount: Mapped[int] = mapped_column(Integer)
    deposited_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class DepositMatch(IdMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "deposit_matches"

    deposit_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("bank_deposits.id", ondelete="CASCADE"), unique=True
    )
    # [{"student_id", "household_id", "invoice_ids", "score", "reasons"}]
    candidates: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    status: Mapped[DepositMatchStatus] = mapped_column(
        str_enum(DepositMatchStatus, 16), default=DepositMatchStatus.PENDING, index=True
    )
    payment_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("payments.id"))
    decided_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    note: Mapped[str | None] = mapped_column(Text)


class PayerAlias(IdMixin, TenantMixin, TimestampMixin, Base):
    """담당자가 한 번 연결한 입금자명 → 다음 달부터 자동 매칭."""

    __tablename__ = "payer_aliases"
    __table_args__ = (
        UniqueConstraint("academy_id", "payer_name"),
        CheckConstraint("household_id IS NOT NULL OR student_id IS NOT NULL", name="has_target"),
    )

    payer_name: Mapped[str] = mapped_column(String(100))
    household_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("households.id", ondelete="CASCADE")
    )
    student_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE")
    )
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))


class PaymentPromise(IdMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "payment_promises"

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("invoices.id", ondelete="CASCADE"), index=True
    )
    promised_date: Mapped[date] = mapped_column(Date, index=True)
    amount: Mapped[int | None] = mapped_column(Integer)
    note: Mapped[str | None] = mapped_column(Text)
    status: Mapped[PromiseStatus] = mapped_column(
        str_enum(PromiseStatus, 16), default=PromiseStatus.ACTIVE
    )
    source_reply_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("replies.id"))
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
