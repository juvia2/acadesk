"""오늘의 소통함과 확인 필요함. 여러 모듈의 데이터를 모아 보여주는 읽기 전용 화면용."""

import uuid
from datetime import date, datetime
from enum import StrEnum
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from acadesk.api.deps import MVP, PROPOSED, CurrentUserDep, access
from acadesk.core.errors import not_implemented
from acadesk.core.schemas import Page, PageParams, page_params
from acadesk.core.security import ALL_ROLES

router = APIRouter(tags=["오늘의 소통함"])


class TodaySummary(BaseModel):
    date: date
    pending_approvals: int
    my_pending_approvals: int = Field(description="내가 승인할 수 있는 건")
    scheduled_today: int
    sent_today: int
    failed_today: int
    cancelled_by_recheck_today: int = Field(description="발송 직전 재검증으로 막은 건")
    open_alerts: int
    open_replies: int
    review_items: int


class ReviewKind(StrEnum):
    IMPORT_ERROR = "import_error"
    DEPOSIT_MATCH = "deposit_match"
    HOUSEHOLD_SUGGESTION = "household_suggestion"
    UNCLASSIFIED_REPLY = "unclassified_reply"
    LATE_ATTENDANCE_ENTRY = "late_attendance_entry"
    DISCOUNT_RECALC = "discount_recalc"
    AI_MISMATCH = "ai_mismatch"


class ReviewItem(BaseModel):
    id: uuid.UUID
    kind: ReviewKind
    title: str
    detail: str | None = None
    ref_id: uuid.UUID = Field(description="처리할 대상 ID (업로드, 매칭 후보 등)")
    created_at: datetime


class Briefing(BaseModel):
    date: date
    summary: TodaySummary
    held_reasons: dict[str, int] = Field(description="보류 사유별 건수")
    overnight_replies: int
    reply_digest: str | None = Field(None, description="AI 요약 (선택)")


@router.get("/dashboard/today", summary="오늘의 소통함 요약", **access(MVP, *ALL_ROLES))
def today(user: CurrentUserDep) -> TodaySummary:
    raise not_implemented()


@router.get("/dashboard/briefing", summary="담당자 아침 브리핑", **access(PROPOSED, *ALL_ROLES))
def briefing(user: CurrentUserDep) -> Briefing:
    raise not_implemented()


@router.get(
    "/review-items",
    summary="확인 필요함",
    description="업로드 오류, 매칭 후보, 형제 연결 후보, 미분류 회신 등 사람이 봐야 할 것을 한 목록으로.",
    tags=["확인 필요함"],
    **access(MVP, *ALL_ROLES),
)
def review_items(
    user: CurrentUserDep,
    paging: Annotated[PageParams, Depends(page_params)],
    kind: ReviewKind | None = None,
) -> Page[ReviewItem]:
    raise not_implemented()
