"""관리자·교사 대시보드와 확인 필요함. 여러 모듈의 데이터를 모아 보여주는 읽기 전용."""

import uuid
from datetime import date, datetime
from enum import StrEnum
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from acadesk.api.deps import MVP, STAGE3, CurrentUserDep, access
from acadesk.core.errors import not_implemented
from acadesk.core.schemas import Page, PageParams, page_params
from acadesk.core.security import STAFF

router = APIRouter(tags=["대시보드"])


class TodaySummary(BaseModel):
    date: date
    sessions_today: int = Field(description="오늘 강의 회차 수 (휴강 제외)")
    sessions_open: int = Field(description="지금 출석 받는 중")
    attendance_rate_today: float | None = Field(None, ge=0, le=1, description="마감된 회차 기준")
    absent_today: int
    open_alerts: int = Field(description="확인 안 한 결석 알림")
    unanswered_questions: int
    emergency_sent_today: int
    review_items: int
    community_reports_7d: int | None = Field(None, description="2단계: 커뮤니티를 켠 학원만")


class ReviewKind(StrEnum):
    IMPORT_ERROR = "import_error"
    HOUSEHOLD_SUGGESTION = "household_suggestion"
    SHARED_DEVICE_CHECK_IN = "shared_device_check_in"  # 한 기기로 여러 학생 출석
    PENDING_CHILD_CONSENT = "pending_child_consent"  # 학부모 승인 대기 학생 계정
    DEPOSIT_MATCH = "deposit_match"  # 3단계
    DISCOUNT_RECALC = "discount_recalc"  # 3단계
    AI_MISMATCH = "ai_mismatch"  # 3단계


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


@router.get("/dashboard/today", summary="관리자·교사 대시보드 요약", **access(MVP, *STAFF))
def today(user: CurrentUserDep) -> TodaySummary:
    raise not_implemented()


@router.get("/dashboard/briefing", summary="담당자 아침 브리핑", **access(STAGE3, *STAFF))
def briefing(user: CurrentUserDep) -> Briefing:
    raise not_implemented()


@router.get(
    "/review-items",
    summary="확인 필요함",
    description="업로드 오류, 형제 연결 후보, 같은 기기 출석 등 사람이 봐야 할 것을 한 목록으로.",
    tags=["확인 필요함"],
    **access(MVP, *STAFF),
)
def review_items(
    user: CurrentUserDep,
    paging: Annotated[PageParams, Depends(page_params)],
    kind: ReviewKind | None = None,
) -> Page[ReviewItem]:
    raise not_implemented()
