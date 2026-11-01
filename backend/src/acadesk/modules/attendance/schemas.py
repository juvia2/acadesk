import uuid
from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class AttendanceStatus(StrEnum):
    PRESENT = "present"
    LATE = "late"
    ABSENT = "absent"  # 무단 결석
    EXCUSED = "excused"  # 사전 신고 결석
    EARLY_LEAVE = "early_leave"
    MAKEUP = "makeup"  # 보강 출석


class AttendanceOut(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    student_name: str
    class_id: uuid.UUID
    date: date
    status: AttendanceStatus
    note: str | None = None
    recorded_at: datetime
    recorded_by: uuid.UUID | None = None
    is_late_entry: bool = Field(description="수업 시작 후 기준 시간이 지나 입력됨 → 안내 전 확인")


class AttendanceItem(BaseModel):
    student_id: uuid.UUID
    class_id: uuid.UUID
    date: date
    status: AttendanceStatus
    note: str | None = None


class AttendanceBatch(BaseModel):
    items: list[AttendanceItem] = Field(min_length=1, max_length=500)


class AttendanceCorrection(BaseModel):
    status: AttendanceStatus
    note: str | None = None
    reason: str = Field(description="정정 사유. 이미 나간 안내가 있으면 정정 안내 후보가 생긴다")


class AlertKind(StrEnum):
    UNEXCUSED_ABSENCE = "unexcused_absence"  # 당일 무단결석
    SIBLING_ABSENCE = "sibling_absence"  # 형제 동시 결석 (한 건으로 묶음)


class AlertStatus(StrEnum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"


class AttendanceAlertOut(BaseModel):
    id: uuid.UUID
    kind: AlertKind
    student_ids: list[uuid.UUID]
    student_names: list[str]
    class_id: uuid.UUID
    date: date
    status: AlertStatus
    created_at: datetime
    escalated_at: datetime | None = Field(
        None, description="담당 교사 미확인으로 실장·원장에게 다시 알린 시각"
    )
    acknowledged_by: uuid.UUID | None = None
    acknowledged_at: datetime | None = None
    note: str | None = None


class AlertAck(BaseModel):
    note: str | None = Field(None, description="예: 보호자와 통화, 병원 진료")
