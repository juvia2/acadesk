import uuid
from datetime import date, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from acadesk.modules.messaging.schemas import NoticeKind


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    EDITED_APPROVED = "edited_approved"  # 문구 수정 후 승인
    HELD = "held"
    REJECTED = "rejected"
    EXPIRED = "expired"  # 사실이 바뀌어 더 이상 유효하지 않음 (예: 승인 전 납부됨)


class EvidenceRef(BaseModel):
    kind: str = Field(description="invoice, payment, attendance, reply, rag_chunk 등")
    ref_id: uuid.UUID
    label: str


class ApprovalEvent(BaseModel):
    at: datetime
    actor_id: uuid.UUID | None = None
    action: str
    note: str | None = None


class ApprovalSummary(BaseModel):
    id: uuid.UUID
    candidate_id: uuid.UUID
    kind: NoticeKind
    stage: int | None = None
    student_names: list[str]
    guardian_name: str
    status: ApprovalStatus
    reason: str
    can_approve: bool = Field(description="요청한 사용자의 역할로 승인할 수 있는지")
    created_at: datetime


class ApprovalDetail(ApprovalSummary):
    facts: dict[str, Any] = Field(
        description="승인 화면에 보여줄 사실. 금액·날짜 등. 승인 시 스냅샷으로 저장"
    )
    evidence: list[EvidenceRef] = []
    body_template: str = Field(description="자리 표시가 남아 있는 문구 ({amount} 등)")
    rendered_body: str = Field(description="사실 값으로 채운 미리 보기")
    language: str = "ko"
    translated_body: str | None = None
    ai_run_id: uuid.UUID | None = Field(None, description="AI가 초안을 쓴 경우")
    history: list[ApprovalEvent] = []


class ApproveBody(BaseModel):
    edited_body: str | None = Field(
        None, description="문구를 고친 경우. 자리 표시 밖에 숫자를 직접 쓰면 거절된다"
    )
    scheduled_at: datetime | None = Field(None, description="비우면 다음 발송 가능 시간대")


class HoldBody(BaseModel):
    reason: str
    until: date | None = None


class RejectBody(BaseModel):
    reason: str
