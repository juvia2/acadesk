import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class StudentStatus(StrEnum):
    ACTIVE = "active"
    ON_LEAVE = "on_leave"  # 휴원
    WITHDRAWN = "withdrawn"  # 퇴원


class GuardianOut(BaseModel):
    id: uuid.UUID
    name: str
    phone_masked: str = Field(description="010-****-1234. 원문은 발송 시점에만 복호화")
    preferred_language: str = Field("ko", description="수신 언어: ko, en, ko-easy 등")
    consent_notices: bool = Field(description="안내 수신 동의")


class GuardianCreate(BaseModel):
    name: str
    phone: str
    preferred_language: str = "ko"
    consent_notices: bool = True


class GuardianUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    preferred_language: str | None = None
    consent_notices: bool | None = None


class GuardianLink(BaseModel):
    guardian: GuardianOut
    relation: str = Field(description="모, 부, 조모 등")
    is_primary: bool = Field(description="기본 수신자")
    receives_notices: bool


class GuardianLinkCreate(BaseModel):
    guardian_id: uuid.UUID | None = Field(None, description="기존 보호자 연결. 없으면 new_guardian")
    new_guardian: GuardianCreate | None = None
    relation: str
    is_primary: bool = False
    receives_notices: bool = True


class GuardianLinkUpdate(BaseModel):
    relation: str | None = None
    is_primary: bool | None = None
    receives_notices: bool | None = None


class StudentSummary(BaseModel):
    id: uuid.UUID
    external_id: str | None = Field(None, description="학원이 쓰는 학생 번호 (업로드 upsert 키)")
    name: str
    grade: str | None = None
    status: StudentStatus
    household_id: uuid.UUID | None = None
    class_ids: list[uuid.UUID] = []


class StudentOut(StudentSummary):
    school: str | None = None
    guardians: list[GuardianLink] = []
    sibling_ids: list[uuid.UUID] = Field([], description="같은 가구의 다른 학생")
    created_at: datetime


class StudentCreate(BaseModel):
    external_id: str | None = None
    name: str
    grade: str | None = None
    school: str | None = None
    class_ids: list[uuid.UUID] = []
    guardians: list[GuardianLinkCreate] = []


class StudentUpdate(BaseModel):
    external_id: str | None = None
    name: str | None = None
    grade: str | None = None
    school: str | None = None
    status: StudentStatus | None = Field(
        None, description="휴원·퇴원으로 바꾸면 예약 안내가 보류된다"
    )


class TimelineKind(StrEnum):
    INVOICE = "invoice"
    PAYMENT = "payment"
    ATTENDANCE = "attendance"
    HOMEWORK = "homework"
    MESSAGE = "message"
    REPLY = "reply"
    APPROVAL = "approval"
    NOTE = "note"


class TimelineItem(BaseModel):
    at: datetime
    kind: TimelineKind
    title: str
    detail: str | None = None
    ref_id: uuid.UUID
    actor_name: str | None = None


class NoteCreate(BaseModel):
    body: str = Field(min_length=1, max_length=2000, description="상담·통화 메모")


# ── 형제 연동 (가구) ────────────────────────────────


class HouseholdOut(BaseModel):
    id: uuid.UUID
    name: str | None = Field(None, description="예: 김민준·김서연 가구")
    students: list[StudentSummary]
    guardians: list[GuardianOut]
    open_balance: int = Field(0, description="가구 전체 미납 잔액(원)")


class HouseholdCreate(BaseModel):
    student_ids: list[uuid.UUID] = Field(min_length=2)
    name: str | None = None


class HouseholdUpdate(BaseModel):
    name: str | None = None


class HouseholdMembersAdd(BaseModel):
    student_ids: list[uuid.UUID] = Field(min_length=1)


class SuggestionReason(StrEnum):
    SHARED_GUARDIAN_PHONE = "shared_guardian_phone"
    SHARED_PAYER_NAME = "shared_payer_name"


class SuggestionStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class HouseholdSuggestion(BaseModel):
    id: uuid.UUID
    students: list[StudentSummary]
    reason: SuggestionReason
    evidence: str = Field(description="예: 보호자 연락처 010-****-1234 공유")
    status: SuggestionStatus
    created_at: datetime


class SuggestionReject(BaseModel):
    note: str | None = None
