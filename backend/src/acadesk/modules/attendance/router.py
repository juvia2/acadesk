import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from acadesk.api.deps import MVP, CurrentUserDep, access
from acadesk.core.errors import not_implemented
from acadesk.core.schemas import Page, PageParams, page_params
from acadesk.core.security import ALL_ROLES

from .schemas import (
    AlertAck,
    AlertStatus,
    AttendanceAlertOut,
    AttendanceBatch,
    AttendanceCorrection,
    AttendanceOut,
    AttendanceStatus,
)

router = APIRouter(prefix="/attendance", tags=["출결"])

Paging = Annotated[PageParams, Depends(page_params)]


@router.get("", summary="출결 조회", **access(MVP, *ALL_ROLES))
def list_attendance(
    user: CurrentUserDep,
    paging: Paging,
    date_: Annotated[date | None, Query(alias="date")] = None,
    class_id: uuid.UUID | None = None,
    student_id: uuid.UUID | None = None,
    status_: Annotated[AttendanceStatus | None, Query(alias="status")] = None,
) -> Page[AttendanceOut]:
    raise not_implemented()


@router.post(
    "/batch",
    summary="출결 일괄 입력",
    description="(학생, 반, 날짜)로 upsert한다. 당일 무단결석은 예약 안내 대신 담당자 긴급 알림을 만든다.",
    **access(MVP, *ALL_ROLES),
)
def upsert_attendance(user: CurrentUserDep, body: AttendanceBatch) -> list[AttendanceOut]:
    raise not_implemented()


@router.get(
    "/alerts",
    summary="긴급 결석 알림",
    description="형제가 같은 날 함께 결석하면 한 건으로 묶는다.",
    **access(MVP, *ALL_ROLES),
)
def list_alerts(
    user: CurrentUserDep,
    paging: Paging,
    status_: Annotated[AlertStatus, Query(alias="status")] = AlertStatus.OPEN,
) -> Page[AttendanceAlertOut]:
    raise not_implemented()


@router.post("/alerts/{alert_id}/ack", summary="긴급 알림 확인", **access(MVP, *ALL_ROLES))
def ack_alert(user: CurrentUserDep, alert_id: uuid.UUID, body: AlertAck) -> AttendanceAlertOut:
    raise not_implemented()


@router.patch(
    "/{attendance_id}",
    summary="출결 정정",
    description="예약된 결석 안내는 취소되고, 이미 나간 안내가 있으면 정정 안내 후보가 승인함에 생긴다.",
    **access(MVP, *ALL_ROLES),
)
def correct_attendance(
    user: CurrentUserDep, attendance_id: uuid.UUID, body: AttendanceCorrection
) -> AttendanceOut:
    raise not_implemented()


routers = [router]
