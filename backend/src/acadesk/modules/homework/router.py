import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from acadesk.api.deps import STAGE2, CurrentUserDep, access
from acadesk.core.errors import not_implemented
from acadesk.core.schemas import Page, PageParams, page_params
from acadesk.core.security import STAFF

from .schemas import (
    HomeworkCreate,
    HomeworkOut,
    HomeworkUpdate,
    SubmissionBatch,
    SubmissionOut,
)

router = APIRouter(prefix="/homework", tags=["과제"])

Paging = Annotated[PageParams, Depends(page_params)]


@router.get("", summary="과제 목록", **access(STAGE2, *STAFF))
def list_homework(
    user: CurrentUserDep,
    paging: Paging,
    lecture_id: uuid.UUID | None = None,
    due_from: Annotated[date | None, Query()] = None,
    due_to: Annotated[date | None, Query()] = None,
) -> Page[HomeworkOut]:
    raise not_implemented()


@router.post("", summary="과제 등록", status_code=status.HTTP_201_CREATED, **access(STAGE2, *STAFF))
def create_homework(user: CurrentUserDep, body: HomeworkCreate) -> HomeworkOut:
    raise not_implemented()


@router.patch("/{homework_id}", summary="과제 수정", **access(STAGE2, *STAFF))
def update_homework(
    user: CurrentUserDep, homework_id: uuid.UUID, body: HomeworkUpdate
) -> HomeworkOut:
    raise not_implemented()


@router.get("/{homework_id}/submissions", summary="제출 현황", **access(STAGE2, *STAFF))
def list_submissions(user: CurrentUserDep, homework_id: uuid.UUID) -> list[SubmissionOut]:
    raise not_implemented()


@router.put(
    "/{homework_id}/submissions",
    summary="제출 기록 일괄 입력",
    description="과제 모듈은 사실만 기록한다. 반복 미완료 판단은 규칙 엔진이 한다.",
    **access(STAGE2, *STAFF),
)
def upsert_submissions(
    user: CurrentUserDep, homework_id: uuid.UUID, body: SubmissionBatch
) -> list[SubmissionOut]:
    raise not_implemented()


routers = [router]
