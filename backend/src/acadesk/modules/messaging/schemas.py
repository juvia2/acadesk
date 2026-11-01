import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class NoticeKind(StrEnum):
    BILLING_REMINDER = "billing_reminder"  # 수납 안내 (단계는 stage)
    ABSENCE = "absence"  # 당일 결석 확인
    REPEATED_ABSENCE = "repeated_absence"
    HOMEWORK = "homework"  # 반복 과제 미완료
    PAYMENT_CHECK = "payment_check"  # 약속일 납부 확인
    CORRECTION = "correction"  # 정정 안내
    GENERAL = "general"


class Channel(StrEnum):
    ALIMTALK = "alimtalk"
    SMS = "sms"


# ── 템플릿 ───────────────────────────────────────────


class ReviewStatus(StrEnum):
    NONE = "none"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class TemplateOut(BaseModel):
    id: uuid.UUID
    kind: NoticeKind
    stage: int | None = Field(None, description="수납 단계 1·2·3")
    name: str
    channel: Channel
    current_version: int | None = Field(None, description="승인된 최신 버전")
    archived: bool = False


class TemplateCreate(BaseModel):
    kind: NoticeKind
    stage: int | None = None
    name: str
    channel: Channel
    body: str = Field(description="{student_name}, {amount}, {due_date} 같은 자리 표시를 쓴다")


class TemplateUpdate(BaseModel):
    name: str | None = None
    archived: bool | None = None


class TemplateVersionOut(BaseModel):
    template_id: uuid.UUID
    version: int
    body: str
    variables: list[str]
    approved_by: uuid.UUID | None = None
    approved_at: datetime | None = None
    alimtalk_review: ReviewStatus = ReviewStatus.NONE
    created_at: datetime


class TemplateVersionCreate(BaseModel):
    body: str


class PreviewBody(BaseModel):
    version: int | None = Field(None, description="비우면 최신 버전")
    student_id: uuid.UUID | None = Field(None, description="실제 학생 값으로 채워 보기")
    language: str = "ko"


class PreviewOut(BaseModel):
    rendered: str
    missing_variables: list[str] = []


class TranslationStatus(StrEnum):
    GENERATING = "generating"
    DRAFT = "draft"  # AI 번역 완료, 담당자 확인 전
    APPROVED = "approved"


class TranslationOut(BaseModel):
    template_id: uuid.UUID
    version: int
    language: str
    body: str | None = None
    status: TranslationStatus
    validation_errors: list[str] = Field([], description="자리 표시 누락·변경, 원문에 없는 숫자 등")
    ai_run_id: uuid.UUID | None = None
    approved_by: uuid.UUID | None = None


class TranslationRequest(BaseModel):
    language: str = Field(examples=["en", "ko-easy"])


class TranslationUpdate(BaseModel):
    body: str | None = Field(None, description="담당자가 고친 번역")
    approve: bool = False


# ── 안내 후보 ───────────────────────────────────────


class CandidateStatus(StrEnum):
    AWAITING_APPROVAL = "awaiting_approval"
    SCHEDULED = "scheduled"  # 자동 발송 대상, 예약됨
    HELD = "held"
    CANCELLED = "cancelled"  # 발송 전 재검증에서 취소 등
    SENT = "sent"


class CandidateOut(BaseModel):
    id: uuid.UUID
    kind: NoticeKind
    stage: int | None = None
    student_ids: list[uuid.UUID]
    guardian_id: uuid.UUID
    status: CandidateStatus
    dedupe_key: str = Field(description="예: invoice:{id}:stage:2. 같은 키는 한 번만 생성")
    reason: str = Field(description="규칙이 만든 이유. 예: 납부 기한 +3일, 잔액 150,000원")
    hold_reason: str | None = None
    rule_run_id: uuid.UUID
    created_at: datetime


class CancelBody(BaseModel):
    reason: str


# ── 발송 ─────────────────────────────────────────────


class MessageStatus(StrEnum):
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MessageOut(BaseModel):
    id: uuid.UUID
    candidate_ids: list[uuid.UUID] = Field(description="형제 묶음 안내면 여러 건")
    guardian_id: uuid.UUID
    guardian_name: str
    student_ids: list[uuid.UUID]
    channel: Channel
    language: str = "ko"
    body: str
    template_version: int | None = None
    status: MessageStatus
    scheduled_at: datetime | None = None
    sent_at: datetime | None = None
    delivered_at: datetime | None = None
    failure_reason: str | None = None
    fallback_of: uuid.UUID | None = Field(
        None, description="알림톡 실패로 대신 보낸 문자면 원래 건"
    )
    approved_by: uuid.UUID | None = None


class CorrectionBody(BaseModel):
    reason: str = Field(description="오발송 원인")


# ── 회신 ─────────────────────────────────────────────


class ReplyIntent(StrEnum):
    PAID = "paid"  # 이미 납부함
    ALREADY_NOTIFIED = "already_notified"  # 미리 알렸음 (사전 신고)
    CONSULT_REQUEST = "consult_request"
    CORRECTION = "correction"  # 정정 요청
    PROMISE = "promise"  # 납부 약속
    OTHER = "other"
    UNKNOWN = "unknown"


class IntentSource(StrEnum):
    BUTTON = "button"  # 원클릭 응답
    AI = "ai"  # AI 분류 후보
    STAFF = "staff"


class ReplyStatus(StrEnum):
    OPEN = "open"
    HANDLED = "handled"


class ReplyOut(BaseModel):
    id: uuid.UUID
    message_id: uuid.UUID | None = None
    guardian_id: uuid.UUID
    guardian_name: str
    student_ids: list[uuid.UUID]
    received_at: datetime
    body: str
    language: str = "ko"
    translated_body: str | None = Field(None, description="외국어 회신의 한국어 번역")
    intent: ReplyIntent
    intent_source: IntentSource | None = None
    intent_confirmed: bool = False
    follow_up_stopped: bool = Field(description="같은 사유의 후속 안내를 멈췄는지")
    status: ReplyStatus
    handled_by: uuid.UUID | None = None


class ReplyUpdate(BaseModel):
    intent: ReplyIntent | None = Field(
        None, description="보내면 분류를 담당자가 확정한 것으로 기록"
    )
    status: ReplyStatus | None = None
    note: str | None = None
