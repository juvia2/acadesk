"""학생 본인(/me), 학부모 자녀(/children), 직원이 보는 학생 리포트."""

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query, status

from acadesk.api.deps import MVP, CurrentUserDep, access
from acadesk.core.errors import not_implemented
from acadesk.core.security import STAFF, Role
from acadesk.modules.attendance.schemas import AttendanceOut, AttendanceSummary

from .schemas import AddChildBody, ChildOut, ChildReport, MySchedule, ReportPeriod

me_router = APIRouter(prefix="/me", tags=["학생 화면"])
children_router = APIRouter(prefix="/children", tags=["학부모 화면"])
staff_router = APIRouter(prefix="/students", tags=["학생"])

FromQ = Annotated[date | None, Query(alias="from")]


# ── 학생 본인 ───────────────────────────────────────


@me_router.get("/schedule", summary="내 시간표", **access(MVP, Role.STUDENT))
def my_schedule(user: CurrentUserDep) -> MySchedule:
    raise not_implemented()


@me_router.get("/attendance", summary="내 출결", **access(MVP, Role.STUDENT))
def my_attendance(
    user: CurrentUserDep, from_: FromQ = None, to: date | None = None
) -> list[AttendanceOut]:
    raise not_implemented()


@me_router.get("/attendance/summary", summary="내 강의별 출석률", **access(MVP, Role.STUDENT))
def my_attendance_summary(
    user: CurrentUserDep, from_: FromQ = None, to: date | None = None
) -> list[AttendanceSummary]:
    raise not_implemented()


# ── 학부모 ───────────────────────────────────────────


@children_router.get("", summary="내 자녀 목록", **access(MVP, Role.PARENT))
def list_children(user: CurrentUserDep) -> list[ChildOut]:
    raise not_implemented()


@children_router.post(
    "",
    summary="자녀 추가 (형제)",
    description="둘째 자녀의 학부모 초대 코드를 넣으면 같은 계정에 연결된다.",
    status_code=status.HTTP_201_CREATED,
    **access(MVP, Role.PARENT),
)
def add_child(user: CurrentUserDep, body: AddChildBody) -> ChildOut:
    raise not_implemented()


@children_router.post(
    "/{student_id}/approve-account",
    summary="자녀 학생 계정 승인",
    description="만 14세 미만 학생 가입에 필요한 법정대리인 동의. 승인 기록은 감사 로그에 남는다.",
    **access(MVP, Role.PARENT),
)
def approve_child_account(user: CurrentUserDep, student_id: uuid.UUID) -> ChildOut:
    raise not_implemented()


@children_router.get(
    "/{student_id}/report",
    summary="자녀 리포트",
    description="period=week|month, date가 속한 주·월. 비우면 이번 주. "
    "자녀와 교사의 질의응답은 포함하지 않는다.",
    **access(MVP, Role.PARENT),
)
def child_report(
    user: CurrentUserDep,
    student_id: uuid.UUID,
    period: ReportPeriod = ReportPeriod.WEEK,
    date_: Annotated[date | None, Query(alias="date")] = None,
) -> ChildReport:
    raise not_implemented()


@children_router.get(
    "/{student_id}/attendance",
    summary="자녀 출결 달력",
    **access(MVP, Role.PARENT),
)
def child_attendance(
    user: CurrentUserDep, student_id: uuid.UUID, from_: FromQ = None, to: date | None = None
) -> list[AttendanceOut]:
    raise not_implemented()


# ── 직원 ─────────────────────────────────────────────


@staff_router.get(
    "/{student_id}/report",
    summary="학생 리포트 (직원용)",
    description="학부모가 보는 것과 같은 리포트. 상담 준비용.",
    **access(MVP, *STAFF),
)
def student_report(
    user: CurrentUserDep,
    student_id: uuid.UUID,
    period: ReportPeriod = ReportPeriod.MONTH,
    date_: Annotated[date | None, Query(alias="date")] = None,
) -> ChildReport:
    raise not_implemented()


routers = [me_router, children_router, staff_router]
