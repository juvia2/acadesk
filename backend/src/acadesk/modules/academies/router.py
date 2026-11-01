import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from acadesk.api.deps import MVP, PROPOSED, CurrentUserDep, access
from acadesk.core.errors import not_implemented
from acadesk.core.schemas import Page, PageParams, page_params
from acadesk.core.security import ALL_ROLES, STAFF_ADMIN, Role

from .schemas import (
    AcademyOut,
    AcademyUpdate,
    BranchCreate,
    BranchOut,
    BranchUpdate,
    CalendarEventCreate,
    CalendarEventOut,
    ClassCreate,
    ClassOut,
    ClassUpdate,
    EnrollBody,
    UserInvite,
    UserOut,
    UserUpdate,
)

academy_router = APIRouter(prefix="/academy", tags=["학원"])
users_router = APIRouter(prefix="/users", tags=["사용자"])
classes_router = APIRouter(prefix="/classes", tags=["반"])


# ── 학원 ─────────────────────────────────────────────


@academy_router.get("", summary="내 학원 정보", **access(MVP, *ALL_ROLES))
def get_academy(user: CurrentUserDep) -> AcademyOut:
    raise not_implemented()


@academy_router.patch("", summary="학원 정보 수정", **access(MVP, Role.OWNER))
def update_academy(user: CurrentUserDep, body: AcademyUpdate) -> AcademyOut:
    raise not_implemented()


@academy_router.get("/branches", summary="지점 목록", **access(MVP, *ALL_ROLES))
def list_branches(user: CurrentUserDep) -> list[BranchOut]:
    raise not_implemented()


@academy_router.post(
    "/branches",
    summary="지점 추가",
    status_code=status.HTTP_201_CREATED,
    **access(MVP, Role.OWNER),
)
def create_branch(user: CurrentUserDep, body: BranchCreate) -> BranchOut:
    raise not_implemented()


@academy_router.patch("/branches/{branch_id}", summary="지점 수정", **access(MVP, Role.OWNER))
def update_branch(user: CurrentUserDep, branch_id: uuid.UUID, body: BranchUpdate) -> BranchOut:
    raise not_implemented()


@academy_router.get(
    "/calendar",
    summary="휴원·방학·공휴일 목록",
    description="규칙 엔진이 쉬는 날에는 결석 후보를 만들지 않고, 수납 단계를 영업일로 셀 때 쓴다.",
    **access(PROPOSED, *ALL_ROLES),
)
def list_calendar(
    user: CurrentUserDep,
    from_: Annotated[date, Query(alias="from")],
    to: Annotated[date, Query()],
) -> list[CalendarEventOut]:
    raise not_implemented()


@academy_router.post(
    "/calendar",
    summary="휴원·방학·공휴일 등록",
    status_code=status.HTTP_201_CREATED,
    **access(PROPOSED, *STAFF_ADMIN),
)
def create_calendar_event(user: CurrentUserDep, body: CalendarEventCreate) -> CalendarEventOut:
    raise not_implemented()


@academy_router.delete(
    "/calendar/{event_id}",
    summary="휴원·방학·공휴일 삭제",
    status_code=status.HTTP_204_NO_CONTENT,
    **access(PROPOSED, *STAFF_ADMIN),
)
def delete_calendar_event(user: CurrentUserDep, event_id: uuid.UUID) -> None:
    raise not_implemented()


# ── 사용자 ───────────────────────────────────────────


@users_router.get("", summary="직원 목록", **access(MVP, *STAFF_ADMIN))
def list_users(
    user: CurrentUserDep,
    paging: Annotated[PageParams, Depends(page_params)],
    role: Role | None = None,
) -> Page[UserOut]:
    raise not_implemented()


@users_router.post(
    "/invitations",
    summary="직원 초대",
    description="초대 메일을 보내고, 수락하면 계정이 활성화된다.",
    status_code=status.HTTP_201_CREATED,
    **access(MVP, Role.OWNER),
)
def invite_user(user: CurrentUserDep, body: UserInvite) -> UserOut:
    raise not_implemented()


@users_router.patch("/{user_id}", summary="직원 역할·정보 수정", **access(MVP, Role.OWNER))
def update_user(user: CurrentUserDep, user_id: uuid.UUID, body: UserUpdate) -> UserOut:
    raise not_implemented()


@users_router.delete(
    "/{user_id}",
    summary="직원 비활성화",
    description="삭제하지 않고 비활성화한다. 승인·발송 기록의 작성자는 그대로 남는다.",
    status_code=status.HTTP_204_NO_CONTENT,
    **access(MVP, Role.OWNER),
)
def deactivate_user(user: CurrentUserDep, user_id: uuid.UUID) -> None:
    raise not_implemented()


# ── 반 ───────────────────────────────────────────────


@classes_router.get("", summary="반 목록", **access(MVP, *ALL_ROLES))
def list_classes(
    user: CurrentUserDep,
    teacher_id: uuid.UUID | None = None,
    branch_id: uuid.UUID | None = None,
) -> list[ClassOut]:
    raise not_implemented()


@classes_router.post(
    "", summary="반 만들기", status_code=status.HTTP_201_CREATED, **access(MVP, *STAFF_ADMIN)
)
def create_class(user: CurrentUserDep, body: ClassCreate) -> ClassOut:
    raise not_implemented()


@classes_router.get("/{class_id}", summary="반 상세", **access(MVP, *ALL_ROLES))
def get_class(user: CurrentUserDep, class_id: uuid.UUID) -> ClassOut:
    raise not_implemented()


@classes_router.patch("/{class_id}", summary="반 수정", **access(MVP, *STAFF_ADMIN))
def update_class(user: CurrentUserDep, class_id: uuid.UUID, body: ClassUpdate) -> ClassOut:
    raise not_implemented()


@classes_router.post("/{class_id}/students", summary="반에 학생 등록", **access(MVP, *STAFF_ADMIN))
def enroll_students(user: CurrentUserDep, class_id: uuid.UUID, body: EnrollBody) -> ClassOut:
    raise not_implemented()


@classes_router.delete(
    "/{class_id}/students/{student_id}",
    summary="반에서 학생 빼기",
    status_code=status.HTTP_204_NO_CONTENT,
    **access(MVP, *STAFF_ADMIN),
)
def unenroll_student(user: CurrentUserDep, class_id: uuid.UUID, student_id: uuid.UUID) -> None:
    raise not_implemented()


routers = [academy_router, users_router, classes_router]
