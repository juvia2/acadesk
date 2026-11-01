"""여러 모듈이 같이 쓰는 응답 형식."""

import uuid
from typing import Annotated

from fastapi import Query
from pydantic import BaseModel, Field


class Page[T](BaseModel):
    items: list[T]
    total: int
    page: int
    size: int


class PageParams(BaseModel):
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)


def page_params(
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PageParams:
    return PageParams(page=page, size=size)


class ErrorBody(BaseModel):
    detail: str
    code: str | None = Field(
        None, description="프론트 분기용 오류 코드. 예: expired_qr, not_enrolled"
    )


class IdsBody(BaseModel):
    ids: list[uuid.UUID] = Field(min_length=1, max_length=200)


class BulkResult(BaseModel):
    succeeded: list[uuid.UUID]
    failed: dict[uuid.UUID, str] = Field(default_factory=dict, description="ID → 실패 사유")
