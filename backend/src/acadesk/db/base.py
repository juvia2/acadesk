"""모든 모델의 공통 기반.

규칙
- 기본 키는 UUID.
- 학원 데이터 테이블은 `TenantMixin`으로 academy_id를 반드시 가진다 (academies 자신과 웹훅 원문 제외).
- 상태 값은 VARCHAR + CHECK로 저장한다 (값 추가가 쉬움). 파이썬 쪽 값은 각 모듈 schemas의 StrEnum.
- 금액은 정수(원).
"""

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, ForeignKey, MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

NAMING = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING)


class IdMixin:
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class TenantMixin:
    @declared_attr
    def academy_id(cls) -> Mapped[uuid.UUID]:
        return mapped_column(ForeignKey("academies.id", ondelete="RESTRICT"), index=True)


def str_enum(enum_cls: type[StrEnum], length: int = 32) -> Enum:
    """StrEnum을 VARCHAR + CHECK 제약으로 저장한다."""
    return Enum(
        enum_cls,
        native_enum=False,
        create_constraint=True,
        length=length,
        values_callable=lambda e: [m.value for m in e],
        name=enum_cls.__name__.lower(),
        validate_strings=True,
    )
