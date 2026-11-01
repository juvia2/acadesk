import uuid
from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from acadesk.core.security import Role


class AcademyOut(BaseModel):
    id: uuid.UUID
    name: str
    timezone: str = "Asia/Seoul"
    phone: str | None = None
    created_at: datetime


class AcademyUpdate(BaseModel):
    name: str | None = None
    timezone: str | None = None
    phone: str | None = None


class BranchOut(BaseModel):
    id: uuid.UUID
    name: str
    address: str | None = None


class BranchCreate(BaseModel):
    name: str
    address: str | None = None


class BranchUpdate(BaseModel):
    name: str | None = None
    address: str | None = None


class UserOut(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    role: Role
    branch_ids: list[uuid.UUID] = []
    status: str = Field(description="invited, active, pending_guardian_consent, disabled")
    student_id: uuid.UUID | None = Field(None, description="role=student")
    guardian_id: uuid.UUID | None = Field(None, description="role=parent")
    preferred_language: str = Field("ko", description="화면 언어. 외국인 강사는 en 등")


class UserUpdate(BaseModel):
    name: str | None = None
    role: Role | None = None
    branch_ids: list[uuid.UUID] | None = None
    preferred_language: str | None = None


class CalendarKind(StrEnum):
    CLOSURE = "closure"  # 학원 휴무
    VACATION = "vacation"  # 방학
    HOLIDAY = "holiday"  # 공휴일
    STUDENT_LEAVE = "student_leave"  # 학생별 휴원


class CalendarEventOut(BaseModel):
    id: uuid.UUID
    kind: CalendarKind
    start_date: date
    end_date: date
    student_id: uuid.UUID | None = None
    note: str | None = None


class CalendarEventCreate(BaseModel):
    kind: CalendarKind
    start_date: date
    end_date: date
    student_id: uuid.UUID | None = Field(None, description="kind=student_leave일 때 필수")
    note: str | None = None


# ── 초대 코드 ───────────────────────────────────────


class InvitationStatus(StrEnum):
    ACTIVE = "active"
    USED = "used"
    REVOKED = "revoked"
    EXPIRED = "expired"


class InvitationCreate(BaseModel):
    role: Role = Field(description="teacher, manager, student, parent")
    student_id: uuid.UUID | None = Field(None, description="role=student, parent일 때 대상 학생")
    guardian_id: uuid.UUID | None = Field(None, description="role=parent: 학생의 어느 보호자인지")
    email: str | None = Field(None, description="role=teacher·manager: 초대 메일 받을 주소")
    expires_in_days: int = Field(14, ge=1, le=90)


class InvitationBulkCreate(BaseModel):
    """학생 명부 업로드 뒤 한 번에 발급. 학생 코드와 기본 보호자 코드를 같이 만든다."""

    student_ids: list[uuid.UUID] = Field(min_length=1, max_length=500)
    include_parents: bool = True
    expires_in_days: int = Field(14, ge=1, le=90)


class InvitationOut(BaseModel):
    id: uuid.UUID
    role: Role
    code: str | None = Field(None, description="발급 직후 응답에만 원문이 있다. 이후에는 null")
    code_hint: str = Field(description="끝 2자리. 목록에서 구분용")
    student_id: uuid.UUID | None = None
    student_name: str | None = None
    guardian_id: uuid.UUID | None = None
    status: InvitationStatus
    expires_at: datetime
    used_by: uuid.UUID | None = None
    used_at: datetime | None = None
    created_at: datetime
