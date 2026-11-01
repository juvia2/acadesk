"""강의별 QR 출결.

흐름: 교사가 출석 시작(open) → 교실 화면이 /qr을 주기적으로 받아 QR 표시 → 학생이 찍으면
/attendance/check-in → 교사 화면은 명단(roster)을 새로 고침 → 마감(close) 때 미출석자는 결석,
학부모에게 앱 푸시.
"""

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from acadesk.api.deps import MVP, CurrentUserDep, access
from acadesk.core.errors import not_implemented
from acadesk.core.schemas import Page, PageParams, page_params
from acadesk.core.security import STAFF, Role
from acadesk.modules.lectures.schemas import LectureSessionOut

from .schemas import (
    AlertAck,
    AlertStatus,
    AttendanceAlertOut,
    AttendanceCorrection,
    AttendanceOut,
    AttendanceStatus,
    CheckInBody,
    CheckInResult,
    ManualMark,
    QrTokenOut,
    SessionRoster,
)

session_router = APIRouter(prefix="/lecture-sessions/{session_id}/attendance", tags=["출결"])
router = APIRouter(prefix="/attendance", tags=["출결"])

Paging = Annotated[PageParams, Depends(page_params)]


# ── 회차 출석 (교사) ────────────────────────────────


@session_router.post(
    "/open",
    summary="출석 시작",
    description="회차를 open으로 바꾸고 QR 발급을 시작한다. 출석 가능 시간(시작 15분 전 ~ 종료) 안에서만.",
    **access(MVP, *STAFF),
)
def open_attendance(user: CurrentUserDep, session_id: uuid.UUID) -> LectureSessionOut:
    raise not_implemented()


@session_router.get(
    "/qr",
    summary="현재 QR 토큰",
    description="토큰은 30초마다 바뀐다. 교실 화면은 refresh_in_seconds마다 다시 요청한다. "
    "토큰은 저장하지 않는 서명 값이라 사진으로 공유해도 곧 무효가 된다.",
    **access(MVP, *STAFF),
)
def get_qr(user: CurrentUserDep, session_id: uuid.UUID) -> QrTokenOut:
    raise not_implemented()


@session_router.get("", summary="실시간 출석 명단", **access(MVP, *STAFF))
def get_roster(user: CurrentUserDep, session_id: uuid.UUID) -> SessionRoster:
    raise not_implemented()


@session_router.put(
    "/{student_id}",
    summary="수동 출결 처리",
    description="휴대전화가 없는 학생, 사전 연락된 결석 등. method=manual로 기록된다.",
    **access(MVP, *STAFF),
)
def mark_manually(
    user: CurrentUserDep, session_id: uuid.UUID, student_id: uuid.UUID, body: ManualMark
) -> AttendanceOut:
    raise not_implemented()


@session_router.post(
    "/close",
    summary="출석 마감",
    description="안 찍은 학생은 결석(auto_absent)으로 기록하고 학부모에게 앱 푸시, 관리자에게 결석 알림을 만든다. "
    "교사가 마감하지 않으면 회차 종료 시각에 워커가 자동 마감한다.",
    **access(MVP, *STAFF),
)
def close_attendance(user: CurrentUserDep, session_id: uuid.UUID) -> SessionRoster:
    raise not_implemented()


# ── 체크인 (학생) ───────────────────────────────────


@router.post(
    "/check-in",
    summary="QR 출석 (학생)",
    description="토큰 서명·유효 시간, 수강생 여부, 출석 가능 시간을 확인한다. 같은 회차에 두 번 찍으면 첫 기록을 돌려준다. "
    "실패 사유: 400 expired_qr · 403 not_enrolled · 409 attendance_closed / too_early",
    **access(MVP, Role.STUDENT),
)
def check_in(user: CurrentUserDep, body: CheckInBody) -> CheckInResult:
    raise not_implemented()


# ── 조회·정정 (직원) ────────────────────────────────


@router.get("", summary="출결 조회", **access(MVP, *STAFF))
def list_attendance(
    user: CurrentUserDep,
    paging: Paging,
    lecture_id: uuid.UUID | None = None,
    session_id: uuid.UUID | None = None,
    student_id: uuid.UUID | None = None,
    from_: Annotated[date | None, Query(alias="from")] = None,
    to: date | None = None,
    status_: Annotated[AttendanceStatus | None, Query(alias="status")] = None,
) -> Page[AttendanceOut]:
    raise not_implemented()


@router.get(
    "/alerts",
    summary="결석 알림",
    description="마감 때 무단결석이면 생긴다. 형제가 같은 날 함께 결석하면 한 건으로 묶는다.",
    **access(MVP, *STAFF),
)
def list_alerts(
    user: CurrentUserDep,
    paging: Paging,
    status_: Annotated[AlertStatus, Query(alias="status")] = AlertStatus.OPEN,
) -> Page[AttendanceAlertOut]:
    raise not_implemented()


@router.post("/alerts/{alert_id}/ack", summary="결석 알림 확인", **access(MVP, *STAFF))
def ack_alert(user: CurrentUserDep, alert_id: uuid.UUID, body: AlertAck) -> AttendanceAlertOut:
    raise not_implemented()


@router.patch(
    "/{attendance_id}",
    summary="출결 정정",
    description="결석 → 출석으로 정정하면 학부모에게 정정 알림(앱 푸시)이 간다. 이력은 감사 로그에 남는다.",
    **access(MVP, *STAFF),
)
def correct_attendance(
    user: CurrentUserDep, attendance_id: uuid.UUID, body: AttendanceCorrection
) -> AttendanceOut:
    raise not_implemented()


routers = [session_router, router]
