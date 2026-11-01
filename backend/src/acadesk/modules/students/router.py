import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from acadesk.api.deps import MVP, STAGE2, CurrentUserDep, access
from acadesk.core.errors import not_implemented
from acadesk.core.schemas import Page, PageParams, page_params
from acadesk.core.security import STAFF, STAFF_ADMIN
from acadesk.db.session import DbDep

from . import service
from .schemas import (
    GuardianCreate,
    GuardianLinkCreate,
    GuardianLinkUpdate,
    GuardianOut,
    GuardianUpdate,
    HouseholdCreate,
    HouseholdMembersAdd,
    HouseholdOut,
    HouseholdSuggestion,
    HouseholdUpdate,
    NoteCreate,
    StudentCreate,
    StudentOut,
    StudentStatus,
    StudentSummary,
    StudentUpdate,
    SuggestionReject,
    SuggestionStatus,
    TimelineItem,
    TimelineKind,
)

students_router = APIRouter(prefix="/students", tags=["학생"])
guardians_router = APIRouter(prefix="/guardians", tags=["보호자"])
households_router = APIRouter(prefix="/households", tags=["형제 연동"])

Paging = Annotated[PageParams, Depends(page_params)]


# ── 학생 ─────────────────────────────────────────────


@students_router.get("", summary="학생 목록·검색", **access(MVP, *STAFF))
def list_students(
    db: DbDep,
    user: CurrentUserDep,
    paging: Paging,
    q: str | None = None,
    status_: Annotated[StudentStatus | None, Query(alias="status")] = None,
    lecture_id: uuid.UUID | None = None,
    household_id: uuid.UUID | None = None,
) -> Page[StudentSummary]:
    return service.list_students(db, user, paging, q, status_, lecture_id, household_id)


@students_router.post(
    "", summary="학생 등록", status_code=status.HTTP_201_CREATED, **access(MVP, *STAFF_ADMIN)
)
def create_student(db: DbDep, user: CurrentUserDep, body: StudentCreate) -> StudentOut:
    return service.create_student(db, user, body)


@students_router.get("/{student_id}", summary="학생 상세", **access(MVP, *STAFF))
def get_student(db: DbDep, user: CurrentUserDep, student_id: uuid.UUID) -> StudentOut:
    return service.get_student(db, user, student_id)


@students_router.patch("/{student_id}", summary="학생 정보·상태 수정", **access(MVP, *STAFF_ADMIN))
def update_student(user: CurrentUserDep, student_id: uuid.UUID, body: StudentUpdate) -> StudentOut:
    raise not_implemented()


@students_router.get(
    "/{student_id}/timeline",
    summary="학생별 기록",
    description="수납·출결·과제·발송·회신·승인·메모를 시간순으로 합쳐 보여준다.",
    **access(MVP, *STAFF),
)
def get_timeline(
    user: CurrentUserDep,
    student_id: uuid.UUID,
    paging: Paging,
    kinds: Annotated[list[TimelineKind] | None, Query()] = None,
) -> Page[TimelineItem]:
    raise not_implemented()


@students_router.post(
    "/{student_id}/notes",
    summary="상담·통화 메모 추가",
    status_code=status.HTTP_201_CREATED,
    **access(STAGE2, *STAFF),
)
def add_note(user: CurrentUserDep, student_id: uuid.UUID, body: NoteCreate) -> TimelineItem:
    raise not_implemented()


@students_router.post(
    "/{student_id}/guardians",
    summary="보호자 연결",
    description="기존 보호자를 연결하거나 새 보호자를 만들어 연결한다. "
    "같은 연락처가 다른 학생에도 있으면 형제 연결 후보가 생긴다.",
    status_code=status.HTTP_201_CREATED,
    **access(MVP, *STAFF_ADMIN),
)
def link_guardian(
    db: DbDep, user: CurrentUserDep, student_id: uuid.UUID, body: GuardianLinkCreate
) -> StudentOut:
    return service.link_guardian(db, user, student_id, body)


@students_router.patch(
    "/{student_id}/guardians/{guardian_id}",
    summary="보호자 관계·기본 수신자 수정",
    **access(MVP, *STAFF_ADMIN),
)
def update_guardian_link(
    user: CurrentUserDep, student_id: uuid.UUID, guardian_id: uuid.UUID, body: GuardianLinkUpdate
) -> StudentOut:
    raise not_implemented()


@students_router.delete(
    "/{student_id}/guardians/{guardian_id}",
    summary="보호자 연결 해제",
    status_code=status.HTTP_204_NO_CONTENT,
    **access(MVP, *STAFF_ADMIN),
)
def unlink_guardian(user: CurrentUserDep, student_id: uuid.UUID, guardian_id: uuid.UUID) -> None:
    raise not_implemented()


# ── 보호자 ───────────────────────────────────────────


@guardians_router.get(
    "",
    summary="보호자 검색",
    description="이름이나 연락처 뒷자리로 찾는다. 응답의 연락처는 항상 마스킹한다.",
    **access(MVP, *STAFF_ADMIN),
)
def search_guardians(
    user: CurrentUserDep, paging: Paging, q: str | None = None
) -> Page[GuardianOut]:
    raise not_implemented()


@guardians_router.post(
    "", summary="보호자 등록", status_code=status.HTTP_201_CREATED, **access(MVP, *STAFF_ADMIN)
)
def create_guardian(db: DbDep, user: CurrentUserDep, body: GuardianCreate) -> GuardianOut:
    return service.create_guardian(db, user, body)


@guardians_router.get("/{guardian_id}", summary="보호자 상세", **access(MVP, *STAFF))
def get_guardian(user: CurrentUserDep, guardian_id: uuid.UUID) -> GuardianOut:
    raise not_implemented()


@guardians_router.patch(
    "/{guardian_id}",
    summary="보호자 연락처·수신 언어·동의 수정",
    description="연결된 모든 학생(형제)에 한 번에 반영된다.",
    **access(MVP, *STAFF_ADMIN),
)
def update_guardian(
    user: CurrentUserDep, guardian_id: uuid.UUID, body: GuardianUpdate
) -> GuardianOut:
    raise not_implemented()


# ── 형제 연동 ───────────────────────────────────────
# 정적 경로(/suggestions)를 /{household_id}보다 먼저 선언한다.


@households_router.get(
    "/suggestions",
    summary="형제 연결 후보 목록",
    description="업로드나 보호자 연결 때 같은 연락처·입금자명이 발견되면 생긴다. 자동 확정하지 않는다.",
    **access(MVP, *STAFF_ADMIN),
)
def list_suggestions(
    user: CurrentUserDep,
    paging: Paging,
    status_: Annotated[SuggestionStatus, Query(alias="status")] = SuggestionStatus.PENDING,
) -> Page[HouseholdSuggestion]:
    raise not_implemented()


@households_router.post(
    "/suggestions/{suggestion_id}/accept",
    summary="형제 연결 후보 수락",
    description="가구를 만들거나 기존 가구에 합친다. 감사 로그에 기록된다.",
    **access(MVP, *STAFF_ADMIN),
)
def accept_suggestion(user: CurrentUserDep, suggestion_id: uuid.UUID) -> HouseholdOut:
    raise not_implemented()


@households_router.post(
    "/suggestions/{suggestion_id}/reject",
    summary="형제 연결 후보 거절",
    description="같은 학생 조합으로는 다시 제안하지 않는다.",
    status_code=status.HTTP_204_NO_CONTENT,
    **access(MVP, *STAFF_ADMIN),
)
def reject_suggestion(
    user: CurrentUserDep, suggestion_id: uuid.UUID, body: SuggestionReject
) -> None:
    raise not_implemented()


@households_router.get("", summary="가구 목록", **access(MVP, *STAFF_ADMIN))
def list_households(user: CurrentUserDep, paging: Paging) -> Page[HouseholdOut]:
    raise not_implemented()


@households_router.post(
    "",
    summary="가구 직접 만들기",
    status_code=status.HTTP_201_CREATED,
    **access(MVP, *STAFF_ADMIN),
)
def create_household(user: CurrentUserDep, body: HouseholdCreate) -> HouseholdOut:
    raise not_implemented()


@households_router.get("/{household_id}", summary="가구 상세", **access(MVP, *STAFF))
def get_household(user: CurrentUserDep, household_id: uuid.UUID) -> HouseholdOut:
    raise not_implemented()


@households_router.patch("/{household_id}", summary="가구 이름 수정", **access(MVP, *STAFF_ADMIN))
def update_household(
    user: CurrentUserDep, household_id: uuid.UUID, body: HouseholdUpdate
) -> HouseholdOut:
    raise not_implemented()


@households_router.post(
    "/{household_id}/members", summary="가구에 형제 추가", **access(MVP, *STAFF_ADMIN)
)
def add_members(
    user: CurrentUserDep, household_id: uuid.UUID, body: HouseholdMembersAdd
) -> HouseholdOut:
    raise not_implemented()


@households_router.delete(
    "/{household_id}/members/{student_id}",
    summary="가구에서 학생 빼기",
    description="형제 할인을 쓰는 학원이면 할인 재계산 후보가 생긴다.",
    status_code=status.HTTP_204_NO_CONTENT,
    **access(MVP, *STAFF_ADMIN),
)
def remove_member(user: CurrentUserDep, household_id: uuid.UUID, student_id: uuid.UUID) -> None:
    raise not_implemented()


routers = [students_router, guardians_router, households_router]
