import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from acadesk.api.deps import MVP, STAGE2, CurrentUserDep, access
from acadesk.core.errors import not_implemented
from acadesk.core.schemas import Page, PageParams, page_params
from acadesk.core.security import STAFF, STAFF_ADMIN, Role
from acadesk.db.session import DbDep

from . import accounts
from .schemas import (
    AcademyOut,
    AcademyUpdate,
    BranchCreate,
    BranchOut,
    BranchUpdate,
    CalendarEventCreate,
    CalendarEventOut,
    InvitationBulkCreate,
    InvitationCreate,
    InvitationOut,
    InvitationStatus,
    UserOut,
    UserUpdate,
)

academy_router = APIRouter(prefix="/academy", tags=["학원"])
users_router = APIRouter(prefix="/users", tags=["사용자"])
invitations_router = APIRouter(prefix="/invitations", tags=["초대 코드"])


# ── 학원 ─────────────────────────────────────────────


@academy_router.get("", summary="내 학원 정보", **access(MVP, *STAFF))
def get_academy(user: CurrentUserDep) -> AcademyOut:
    raise not_implemented()


@academy_router.patch("", summary="학원 정보 수정", **access(MVP, Role.OWNER))
def update_academy(user: CurrentUserDep, body: AcademyUpdate) -> AcademyOut:
    raise not_implemented()


@academy_router.get("/branches", summary="지점 목록", **access(MVP, *STAFF))
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
    **access(STAGE2, *STAFF),
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
    **access(STAGE2, *STAFF_ADMIN),
)
def create_calendar_event(user: CurrentUserDep, body: CalendarEventCreate) -> CalendarEventOut:
    raise not_implemented()


@academy_router.delete(
    "/calendar/{event_id}",
    summary="휴원·방학·공휴일 삭제",
    status_code=status.HTTP_204_NO_CONTENT,
    **access(STAGE2, *STAFF_ADMIN),
)
def delete_calendar_event(user: CurrentUserDep, event_id: uuid.UUID) -> None:
    raise not_implemented()


# ── 사용자 ───────────────────────────────────────────


@users_router.get("", summary="계정 목록", **access(MVP, *STAFF_ADMIN))
def list_users(
    user: CurrentUserDep,
    paging: Annotated[PageParams, Depends(page_params)],
    role: Role | None = None,
) -> Page[UserOut]:
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


# ── 초대 코드 ───────────────────────────────────────


@invitations_router.post(
    "",
    summary="초대 코드 발급",
    description="교사·학생·학부모 가입용 일회용 코드. 코드 원문은 이 응답에서만 보인다 (DB에는 해시).",
    status_code=status.HTTP_201_CREATED,
    **access(MVP, *STAFF_ADMIN),
)
def create_invitation(db: DbDep, user: CurrentUserDep, body: InvitationCreate) -> InvitationOut:
    return accounts.create_invitation(db, user, body)


@invitations_router.post(
    "/bulk",
    summary="학생·학부모 초대 코드 일괄 발급",
    description="명부 업로드 뒤 학생별 코드와 기본 보호자 코드를 한 번에 만든다. 안내문 인쇄용.",
    status_code=status.HTTP_201_CREATED,
    **access(MVP, *STAFF_ADMIN),
)
def bulk_create_invitations(
    db: DbDep, user: CurrentUserDep, body: InvitationBulkCreate
) -> list[InvitationOut]:
    return accounts.bulk_create_invitations(db, user, body)


@invitations_router.get("", summary="초대 코드 목록", **access(MVP, *STAFF_ADMIN))
def list_invitations(
    db: DbDep,
    user: CurrentUserDep,
    paging: Annotated[PageParams, Depends(page_params)],
    role: Role | None = None,
    status_: Annotated[InvitationStatus | None, Query(alias="status")] = None,
    student_id: uuid.UUID | None = None,
) -> Page[InvitationOut]:
    return accounts.list_invitations(db, user, paging, role, status_, student_id)


@invitations_router.delete(
    "/{invitation_id}",
    summary="초대 코드 폐기",
    status_code=status.HTTP_204_NO_CONTENT,
    **access(MVP, *STAFF_ADMIN),
)
def revoke_invitation(db: DbDep, user: CurrentUserDep, invitation_id: uuid.UUID) -> None:
    accounts.revoke_invitation(db, user, invitation_id)


routers = [academy_router, users_router, invitations_router]
