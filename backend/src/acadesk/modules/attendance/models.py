import datetime as dt
import uuid

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from acadesk.db.base import Base, IdMixin, TenantMixin, TimestampMixin, str_enum

from .schemas import AlertKind, AlertStatus, AttendanceStatus, CheckInMethod


class AttendanceRecord(IdMixin, TenantMixin, TimestampMixin, Base):
    """강의 회차별 출결. (회차, 학생)당 1건이라 두 번 찍어도 첫 기록만 남는다."""

    __tablename__ = "attendance_records"
    __table_args__ = (
        UniqueConstraint("session_id", "student_id"),
        Index("ix_attendance_records_student_lecture", "student_id", "lecture_id"),
        Index("ix_attendance_records_device", "session_id", "device_id"),
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("lecture_sessions.id", ondelete="CASCADE")
    )
    lecture_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lectures.id", ondelete="CASCADE"))
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"))
    status: Mapped[AttendanceStatus] = mapped_column(str_enum(AttendanceStatus, 16))
    method: Mapped[CheckInMethod] = mapped_column(str_enum(CheckInMethod, 16))
    checked_in_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    device_id: Mapped[str | None] = mapped_column(String(64))
    note: Mapped[str | None] = mapped_column(Text)
    recorded_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    corrected: Mapped[bool] = mapped_column(default=False)


class AttendanceAlert(IdMixin, TenantMixin, TimestampMixin, Base):
    """마감 때 무단결석 알림. 형제 동시 결석은 한 건(student_ids 여러 명)."""

    __tablename__ = "attendance_alerts"

    kind: Mapped[AlertKind] = mapped_column(str_enum(AlertKind))
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("lecture_sessions.id", ondelete="CASCADE"), index=True
    )
    student_ids: Mapped[list[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)))
    status: Mapped[AlertStatus] = mapped_column(
        str_enum(AlertStatus, 16), default=AlertStatus.OPEN, index=True
    )
    parent_notified_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    acknowledged_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    acknowledged_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    note: Mapped[str | None] = mapped_column(Text)
