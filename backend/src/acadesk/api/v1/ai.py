"""AI 보조 작업. 모두 비동기(202)로 ai_run을 만들고, 결과는 '확인 후보'로만 저장한다.

AI는 사실을 만들거나 발송을 결정하지 않는다. 번역 요청은 /templates 아래에 있다.
"""

import uuid
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from acadesk.ai.schemas import AiRunStatus, AiTask
from acadesk.api.deps import EXT, CurrentUserDep, access
from acadesk.core.errors import not_implemented
from acadesk.core.schemas import Page, PageParams, page_params
from acadesk.core.security import ALL_ROLES, STAFF_ADMIN

router = APIRouter(prefix="/ai", tags=["AI 보조"])


class AiRunOut(BaseModel):
    id: uuid.UUID
    task: AiTask
    status: AiRunStatus
    target_type: str
    target_id: uuid.UUID | None = None
    output: dict[str, Any] | None = None
    evidence_ids: list[uuid.UUID] = Field([], description="근거로 쓴 기록·문서 조각")
    validation_errors: list[str] = []
    prompt_id: str
    prompt_version: str
    model: str
    created_by: uuid.UUID
    created_at: datetime
    finished_at: datetime | None = None


class AiStepOut(BaseModel):
    seq: int
    node: str = Field(description="fetch_facts, retrieve, draft, validate 등")
    tool: str | None = None
    input_summary: str | None = None
    output_summary: str | None = None
    duration_ms: int
    error: str | None = None


class MismatchScanBody(BaseModel):
    scopes: list[str] = Field(["billing", "attendance"], description="검사할 기록 종류")


class FeedbackBody(BaseModel):
    accepted: bool
    edited_output: dict[str, Any] | None = Field(
        None, description="담당자가 고친 결과 (수정률 측정)"
    )
    note: str | None = None


@router.post(
    "/replies/{reply_id}/classify",
    summary="회신 분류·후속 업무 제안",
    status_code=status.HTTP_202_ACCEPTED,
    **access(EXT, *ALL_ROLES),
)
def classify_reply(user: CurrentUserDep, reply_id: uuid.UUID) -> AiRunOut:
    raise not_implemented()


@router.post(
    "/candidates/{candidate_id}/draft",
    summary="안내문 초안",
    description="자리 표시가 남은 문구를 만든다. 숫자·날짜는 코드가 채운다. 결과는 승인함으로 간다.",
    status_code=status.HTTP_202_ACCEPTED,
    **access(EXT, *STAFF_ADMIN),
)
def draft(user: CurrentUserDep, candidate_id: uuid.UUID) -> AiRunOut:
    raise not_implemented()


@router.post(
    "/students/{student_id}/summary",
    summary="상담 전 연락 이력 요약",
    status_code=status.HTTP_202_ACCEPTED,
    **access(EXT, *ALL_ROLES),
)
def consult_summary(user: CurrentUserDep, student_id: uuid.UUID) -> AiRunOut:
    raise not_implemented()


@router.post(
    "/mismatch-scans",
    summary="수납·출결 불일치 후보 찾기",
    description="찾은 후보는 확인 필요함(ai_mismatch)에 올라간다.",
    status_code=status.HTTP_202_ACCEPTED,
    **access(EXT, *STAFF_ADMIN),
)
def mismatch_scan(user: CurrentUserDep, body: MismatchScanBody) -> AiRunOut:
    raise not_implemented()


@router.get("/runs", summary="AI 실행 기록", **access(EXT, *STAFF_ADMIN))
def list_runs(
    user: CurrentUserDep,
    paging: Annotated[PageParams, Depends(page_params)],
    task: AiTask | None = None,
) -> Page[AiRunOut]:
    raise not_implemented()


@router.get("/runs/{run_id}", summary="AI 실행 결과", **access(EXT, *ALL_ROLES))
def get_run(user: CurrentUserDep, run_id: uuid.UUID) -> AiRunOut:
    raise not_implemented()


@router.get("/runs/{run_id}/steps", summary="AI 실행 단계별 기록", **access(EXT, *STAFF_ADMIN))
def list_steps(user: CurrentUserDep, run_id: uuid.UUID) -> list[AiStepOut]:
    raise not_implemented()


@router.post(
    "/runs/{run_id}/feedback",
    summary="AI 결과 채택·수정 기록",
    status_code=status.HTTP_204_NO_CONTENT,
    **access(EXT, *ALL_ROLES),
)
def feedback(user: CurrentUserDep, run_id: uuid.UUID, body: FeedbackBody) -> None:
    raise not_implemented()
