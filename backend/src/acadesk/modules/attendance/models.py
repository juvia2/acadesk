import datetime as dt
import uuid

from sqlalchemy import Date, DateTime, ForeignKey, Index, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from acadesk.db.base import Base, IdMixin, TenantMixin, TimestampMixin, str_enum

from .schemas import AlertKind, AlertStatus, AttendanceStatus


class AttendanceRecord(IdMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "attendance_records"
    __table_args__ = (
        UniqueConstraint("student_id", "class_id", "date"),
        Index("ix_attendance_records_academy_date", "academy_id", "date"),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"))
    class_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classes.id", ondelete="CASCADE"))
    date: Mapped[dt.date] = mapped_column(Date)
    status: Mapped[AttendanceStatus] = mapped_column(str_enum(AttendanceStatus, 16))
    note: Mapped[str | None] = mapped_column(Text)
    recorded_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))
    recorded_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    is_late_entry: Mapped[bool] = mapped_column(default=False)


class AttendanceAlert(IdMixin, TenantMixin, TimestampMixin, Base):
    """당일 무단결석 긴급 알림. 형제 동시 결석은 한 건(student_ids 여러 명)."""

    __tablename__ = "attendance_alerts"

    kind: Mapped[AlertKind] = mapped_column(str_enum(AlertKind))
    student_ids: Mapped[list[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)))
    class_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classes.id", ondelete="CASCADE"))
    date: Mapped[dt.date] = mapped_column(Date)
    status: Mapped[AlertStatus] = mapped_column(
        str_enum(AlertStatus, 16), default=AlertStatus.OPEN, index=True
    )
    escalated_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    acknowledged_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    acknowledged_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    note: Mapped[str | None] = mapped_column(Text)
