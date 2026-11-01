import uuid
from datetime import date, datetime, time
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
    is_active: bool
    preferred_language: str = Field("ko", description="화면 언어. 외국인 강사는 en 등")


class UserInvite(BaseModel):
    email: str
    name: str
    role: Role
    branch_ids: list[uuid.UUID] = []


class UserUpdate(BaseModel):
    name: str | None = None
    role: Role | None = None
    branch_ids: list[uuid.UUID] | None = None
    preferred_language: str | None = None


class ClassSlot(BaseModel):
    weekday: int = Field(ge=0, le=6, description="0=월요일")
    start: time
    end: time


class ClassOut(BaseModel):
    id: uuid.UUID
    name: str
    branch_id: uuid.UUID | None = None
    teacher_id: uuid.UUID | None = None
    schedule: list[ClassSlot] = []
    student_count: int = 0


class ClassCreate(BaseModel):
    name: str
    branch_id: uuid.UUID | None = None
    teacher_id: uuid.UUID | None = None
    schedule: list[ClassSlot] = []


class ClassUpdate(BaseModel):
    name: str | None = None
    teacher_id: uuid.UUID | None = None
    schedule: list[ClassSlot] | None = None


class EnrollBody(BaseModel):
    student_ids: list[uuid.UUID] = Field(min_length=1)


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
