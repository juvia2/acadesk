"""강의 회차별 출결. (학생, 회차)당 1건."""

import uuid
from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class AttendanceStatus(StrEnum):
    PRESENT = "present"
    LATE = "late"
    ABSENT = "absent"  # 무단 결석 (마감 때 미출석)
    EXCUSED = "excused"  # 사전 신고·인정 결석
    EARLY_LEAVE = "early_leave"


class CheckInMethod(StrEnum):
    QR = "qr"
    MANUAL = "manual"  # 교사가 직접 처리
    AUTO_ABSENT = "auto_absent"  # 마감 때 자동 결석


class AttendanceOut(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    lecture_id: uuid.UUID
    lecture_name: str
    student_id: uuid.UUID
    student_name: str
    date: date
    status: AttendanceStatus
    method: CheckInMethod
    checked_in_at: datetime | None = Field(None, description="QR을 찍은 시각 = 실제 도착 시각")
    note: str | None = None
    recorded_by: uuid.UUID | None = None
    corrected: bool = Field(False, description="정정된 적이 있는지 (이력은 감사 로그)")


class QrTokenOut(BaseModel):
    token: str
    scan_url: str = Field(
        description="QR에 담는 주소. 휴대전화 기본 카메라로 찍어도 앱 출석 화면이 열림"
    )
    expires_at: datetime
    refresh_in_seconds: int = Field(description="교사 화면은 이 시간 뒤에 새 토큰을 받는다")


class CheckInBody(BaseModel):
    token: str = Field(min_length=10, max_length=200)
    device_id: str | None = Field(
        None, max_length=64, description="앱이 만든 기기 식별값 (대리 출석 감지용)"
    )


class CheckInResult(BaseModel):
    status: AttendanceStatus
    lecture_name: str
    checked_in_at: datetime
    already_checked_in: bool = Field(False, description="이미 찍었으면 첫 기록을 그대로 돌려줌")


class RosterItem(BaseModel):
    student_id: uuid.UUID
    student_name: str
    status: AttendanceStatus | None = Field(None, description="null = 아직 안 찍음")
    method: CheckInMethod | None = None
    checked_in_at: datetime | None = None
    shared_device: bool = Field(False, description="같은 기기로 다른 학생도 찍음 → 교사 확인 필요")


class SessionRoster(BaseModel):
    session_id: uuid.UUID
    lecture_name: str
    starts_at: datetime
    ends_at: datetime
    is_open: bool
    present_count: int
    late_count: int
    absent_count: int
    pending_count: int = Field(description="아직 안 찍은 학생 수")
    items: list[RosterItem]


class ManualMark(BaseModel):
    status: AttendanceStatus
    note: str | None = Field(None, description="예: 휴대전화 없음, 병원 진료 사전 연락")


class AttendanceCorrection(BaseModel):
    status: AttendanceStatus
    note: str | None = None
    reason: str = Field(description="정정 사유 (감사 로그)")


class AttendanceSummary(BaseModel):
    """기간 출결 요약. 학부모 리포트·학생 화면에서 쓴다."""

    lecture_id: uuid.UUID
    lecture_name: str
    total_sessions: int
    present: int
    late: int
    absent: int
    excused: int
    early_leave: int
    attendance_rate: float = Field(ge=0, le=1, description="(출석+지각) / (전체-인정결석)")


class AlertKind(StrEnum):
    UNEXCUSED_ABSENCE = "unexcused_absence"  # 마감 때 무단결석
    SIBLING_ABSENCE = "sibling_absence"  # 형제 동시 결석 (한 건으로 묶음)


class AlertStatus(StrEnum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"


class AttendanceAlertOut(BaseModel):
    id: uuid.UUID
    kind: AlertKind
    session_id: uuid.UUID
    lecture_name: str
    student_ids: list[uuid.UUID]
    student_names: list[str]
    status: AlertStatus
    parent_notified_at: datetime | None = Field(None, description="학부모에게 앱 푸시를 보낸 시각")
    created_at: datetime
    acknowledged_by: uuid.UUID | None = None
    acknowledged_at: datetime | None = None
    note: str | None = None


class AlertAck(BaseModel):
    note: str | None = Field(None, description="예: 보호자와 통화, 병원 진료")
