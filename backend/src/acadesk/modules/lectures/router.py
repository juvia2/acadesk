import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from acadesk.api.deps import MVP, CurrentUserDep, access
from acadesk.core.errors import not_implemented
from acadesk.core.schemas import Page, PageParams, page_params
from acadesk.core.security import STAFF, STAFF_ADMIN
from acadesk.modules.students.schemas import StudentSummary

from .schemas import (
    EnrollBody,
    GenerateSessionsBody,
    LectureCreate,
    LectureOut,
    LectureSessionOut,
    LectureUpdate,
    SessionCreate,
    SessionStatus,
    SessionUpdate,
)

lectures_router = APIRouter(prefix="/lectures", tags=["강의"])
sessions_router = APIRouter(prefix="/lecture-sessions", tags=["강의 회차"])

Paging = Annotated[PageParams, Depends(page_params)]


# ── 강의 ─────────────────────────────────────────────


@lectures_router.get(
    "",
    summary="강의 목록",
    description="교사는 mine=true로 내 강의만 본다.",
    **access(MVP, *STAFF),
)
def list_lectures(
    user: CurrentUserDep,
    mine: bool = False,
    teacher_id: uuid.UUID | None = None,
    archived: bool = False,
) -> list[LectureOut]:
    raise not_implemented()


@lectures_router.post(
    "",
    summary="강의 개설",
    description="시간표(schedule)가 있으면 개강일부터 4주치 회차를 자동으로 만든다.",
    status_code=status.HTTP_201_CREATED,
    **access(MVP, *STAFF_ADMIN),
)
def create_lecture(user: CurrentUserDep, body: LectureCreate) -> LectureOut:
    raise not_implemented()


@lectures_router.get("/{lecture_id}", summary="강의 상세", **access(MVP, *STAFF))
def get_lecture(user: CurrentUserDep, lecture_id: uuid.UUID) -> LectureOut:
    raise not_implemented()


@lectures_router.patch("/{lecture_id}", summary="강의 수정·종강", **access(MVP, *STAFF_ADMIN))
def update_lecture(user: CurrentUserDep, lecture_id: uuid.UUID, body: LectureUpdate) -> LectureOut:
    raise not_implemented()


@lectures_router.get("/{lecture_id}/students", summary="수강생 목록", **access(MVP, *STAFF))
def list_enrolled(user: CurrentUserDep, lecture_id: uuid.UUID) -> list[StudentSummary]:
    raise not_implemented()


@lectures_router.post("/{lecture_id}/students", summary="수강생 등록", **access(MVP, *STAFF_ADMIN))
def enroll_students(user: CurrentUserDep, lecture_id: uuid.UUID, body: EnrollBody) -> LectureOut:
    raise not_implemented()


@lectures_router.delete(
    "/{lecture_id}/students/{student_id}",
    summary="수강 종료",
    description="지난 출결 기록은 남고, 앞으로의 회차에서만 빠진다.",
    status_code=status.HTTP_204_NO_CONTENT,
    **access(MVP, *STAFF_ADMIN),
)
def unenroll_student(user: CurrentUserDep, lecture_id: uuid.UUID, student_id: uuid.UUID) -> None:
    raise not_implemented()


@lectures_router.post(
    "/{lecture_id}/sessions/generate",
    summary="시간표로 회차 만들기",
    description="기간 안의 회차를 만든다. 이미 있는 회차는 건너뛴다. 평소에는 워커가 매주 자동 실행.",
    **access(MVP, *STAFF_ADMIN),
)
def generate_sessions(
    user: CurrentUserDep, lecture_id: uuid.UUID, body: GenerateSessionsBody
) -> list[LectureSessionOut]:
    raise not_implemented()


# ── 강의 회차 ───────────────────────────────────────


@sessions_router.get(
    "",
    summary="회차 목록 (오늘의 강의)",
    description="date를 비우면 오늘. 교사는 mine=true로 내 강의 회차만.",
    **access(MVP, *STAFF),
)
def list_sessions(
    user: CurrentUserDep,
    paging: Paging,
    date_: Annotated[date | None, Query(alias="date")] = None,
    from_: Annotated[date | None, Query(alias="from")] = None,
    to: date | None = None,
    lecture_id: uuid.UUID | None = None,
    mine: bool = False,
    status_: Annotated[SessionStatus | None, Query(alias="status")] = None,
) -> Page[LectureSessionOut]:
    raise not_implemented()


@sessions_router.post(
    "",
    summary="보강 회차 추가",
    status_code=status.HTTP_201_CREATED,
    **access(MVP, *STAFF),
)
def create_session(user: CurrentUserDep, body: SessionCreate) -> LectureSessionOut:
    raise not_implemented()


@sessions_router.get("/{session_id}", summary="회차 상세", **access(MVP, *STAFF))
def get_session(user: CurrentUserDep, session_id: uuid.UUID) -> LectureSessionOut:
    raise not_implemented()


@sessions_router.patch(
    "/{session_id}",
    summary="회차 시간 변경·휴강",
    description="휴강하면 수강생과 학부모에게 앱 알림이 간다.",
    **access(MVP, *STAFF),
)
def update_session(
    user: CurrentUserDep, session_id: uuid.UUID, body: SessionUpdate
) -> LectureSessionOut:
    raise not_implemented()


routers = [lectures_router, sessions_router]
