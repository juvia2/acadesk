"""학생 본인 화면과 학부모 자녀 리포트 (기획안 v2 6장). 읽기 전용 모음."""

import uuid
from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from acadesk.modules.attendance.schemas import AttendanceStatus, AttendanceSummary
from acadesk.modules.lectures.schemas import LectureOut, LectureSessionOut
from acadesk.modules.messaging.schemas import EmergencyReason


class ChildAccountStatus(StrEnum):
    NO_ACCOUNT = "no_account"  # 학생이 아직 가입 안 함
    PENDING_CONSENT = "pending_consent"  # 만 14세 미만, 학부모 승인 대기
    ACTIVE = "active"


class ChildOut(BaseModel):
    student_id: uuid.UUID
    name: str
    grade: str | None = None
    lecture_names: list[str] = []
    account_status: ChildAccountStatus
    relation: str


class AddChildBody(BaseModel):
    code: str = Field(min_length=6, max_length=32, description="둘째 자녀의 학부모 초대 코드")


class MySchedule(BaseModel):
    lectures: list[LectureOut]
    upcoming_sessions: list[LectureSessionOut] = Field(description="오늘부터 7일. 휴강·보강 포함")


class ReportPeriod(StrEnum):
    WEEK = "week"
    MONTH = "month"


class CheckInRow(BaseModel):
    date: date
    lecture_name: str
    status: AttendanceStatus
    checked_in_at: datetime | None = Field(None, description="QR 찍은 시각 = 교실 도착 시각")


class MissingHomework(BaseModel):
    title: str
    lecture_name: str
    due_date: date


class HomeworkSummary(BaseModel):
    total: int
    submitted: int
    missing: list[MissingHomework]


class NoticeBrief(BaseModel):
    id: uuid.UUID
    title: str
    lecture_name: str | None = None
    published_at: datetime
    read: bool


class BillingSummary(BaseModel):
    billing_month: str
    billed: int
    paid: int
    balance: int
    household_balance: int | None = Field(None, description="형제 합산 잔액")


class EmergencyBrief(BaseModel):
    id: uuid.UUID
    reason: EmergencyReason
    body: str
    sent_at: datetime


class ChildReport(BaseModel):
    student: ChildOut
    period: ReportPeriod
    from_: date = Field(alias="from")
    to: date
    attendance_rate: float = Field(ge=0, le=1, description="전체 강의 합산 출석률")
    attendance_by_lecture: list[AttendanceSummary]
    recent_check_ins: list[CheckInRow] = Field(description="기간 안 회차별 출결, 최신순")
    upcoming_sessions: list[LectureSessionOut] = Field(
        description="다음 7일 시간표 (휴강·보강 포함)"
    )
    notices: list[NoticeBrief]
    emergency_messages: list[EmergencyBrief]
    homework: HomeworkSummary | None = Field(None, description="2단계: 과제 기능을 켠 학원만")
    billing: BillingSummary | None = Field(None, description="2단계: 수납 기록을 쓰는 학원만")

    model_config = {"populate_by_name": True}
