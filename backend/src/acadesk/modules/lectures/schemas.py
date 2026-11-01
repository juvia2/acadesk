import uuid
from datetime import date, datetime, time
from enum import StrEnum

from pydantic import BaseModel, Field


class LectureSlot(BaseModel):
    weekday: int = Field(ge=0, le=6, description="0=월요일")
    start: time
    end: time


class LectureOut(BaseModel):
    id: uuid.UUID
    name: str = Field(examples=["중2 수학 A"])
    subject: str | None = None
    grade: str | None = None
    room: str | None = None
    branch_id: uuid.UUID | None = None
    teacher_id: uuid.UUID | None = None
    teacher_name: str | None = None
    schedule: list[LectureSlot] = []
    starts_on: date | None = None
    ends_on: date | None = None
    student_count: int = 0
    archived: bool = False


class LectureCreate(BaseModel):
    name: str
    subject: str | None = None
    grade: str | None = None
    room: str | None = None
    branch_id: uuid.UUID | None = None
    teacher_id: uuid.UUID | None = None
    schedule: list[LectureSlot] = []
    starts_on: date | None = None
    ends_on: date | None = None


class LectureUpdate(BaseModel):
    name: str | None = None
    subject: str | None = None
    grade: str | None = None
    room: str | None = None
    teacher_id: uuid.UUID | None = None
    schedule: list[LectureSlot] | None = Field(
        None, description="바꾸면 앞으로의 예정 회차만 다시 만든다. 지난 회차는 그대로"
    )
    ends_on: date | None = None
    archived: bool | None = None


class EnrollBody(BaseModel):
    student_ids: list[uuid.UUID] = Field(min_length=1)


class SessionStatus(StrEnum):
    SCHEDULED = "scheduled"
    OPEN = "open"  # 출석 받는 중 (QR 표시)
    CLOSED = "closed"  # 출석 마감, 미출석자는 결석 처리됨
    CANCELLED = "cancelled"  # 휴강


class SessionKind(StrEnum):
    REGULAR = "regular"
    MAKEUP = "makeup"  # 보강


class LectureSessionOut(BaseModel):
    id: uuid.UUID
    lecture_id: uuid.UUID
    lecture_name: str
    teacher_id: uuid.UUID | None = None
    date: date
    starts_at: datetime
    ends_at: datetime
    kind: SessionKind
    status: SessionStatus
    attendance_opened_at: datetime | None = None
    attendance_closed_at: datetime | None = None
    present_count: int = 0
    late_count: int = 0
    absent_count: int = 0
    enrolled_count: int = 0
    cancel_reason: str | None = None


class SessionCreate(BaseModel):
    """보강 등 시간표 밖 회차."""

    lecture_id: uuid.UUID
    starts_at: datetime
    ends_at: datetime
    kind: SessionKind = SessionKind.MAKEUP
    student_ids: list[uuid.UUID] | None = Field(None, description="보강 대상만. 비우면 수강생 전체")


class SessionUpdate(BaseModel):
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    status: SessionStatus | None = Field(None, description="cancelled로 휴강 처리")
    cancel_reason: str | None = Field(None, description="휴강 사유. 학생·학부모에게 앱 알림")


class GenerateSessionsBody(BaseModel):
    from_: date = Field(alias="from")
    to: date
