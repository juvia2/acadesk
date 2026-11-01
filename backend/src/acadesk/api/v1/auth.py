"""회원가입·로그인. 인증 방식(자체 JWT / 외부 서비스)은 킥오프에서 정한다. 계약은 자체 JWT 기준.

가입 경로는 두 가지다.
- 학원 관리자: 학원 등록과 함께 가입 (POST /auth/academies)
- 교사·학생·학부모: 학원이 발급한 일회용 초대 코드로 가입 (POST /auth/signup)
"""

import uuid
from enum import StrEnum
from typing import Annotated

from fastapi import APIRouter, Path, status
from pydantic import BaseModel, Field

from acadesk.api.deps import MVP, CurrentUserDep, access
from acadesk.core.errors import not_implemented
from acadesk.core.security import MEMBERS, CurrentUser, Role

router = APIRouter(prefix="/auth", tags=["인증"])


class LoginBody(BaseModel):
    email: str
    password: str


class RefreshBody(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class AcademyRegister(BaseModel):
    academy_name: str
    academy_phone: str | None = None
    owner_name: str
    email: str
    password: str = Field(min_length=8)


class InvitationPreview(BaseModel):
    academy_name: str
    role: Role
    student_name_masked: str | None = Field(None, description="김*준. 학부모·학생 코드일 때")
    expires_at: str


class SignupBody(BaseModel):
    code: str = Field(min_length=6, max_length=32)
    name: str
    email: str
    password: str = Field(min_length=8)
    phone: str | None = Field(None, description="학부모: 긴급 문자 받을 번호")
    agree_terms: bool
    agree_community_rules: bool = Field(False, description="학부모: 커뮤니티 이용 규칙 (2단계)")


class AccountStatus(StrEnum):
    ACTIVE = "active"
    PENDING_GUARDIAN_CONSENT = "pending_guardian_consent"  # 만 14세 미만 학생


class SignupResult(TokenPair):
    status: AccountStatus


class ChildBrief(BaseModel):
    student_id: uuid.UUID
    name: str
    grade: str | None = None
    lecture_names: list[str] = []


class MeOut(CurrentUser):
    academy_name: str
    preferred_language: str = "ko"
    status: AccountStatus = AccountStatus.ACTIVE
    children: list[ChildBrief] = Field([], description="role=parent: 연결된 자녀 (형제 포함)")
    home: str = Field(description="역할별 첫 화면 경로. 예: /admin, /teacher, /student, /parent")


@router.post(
    "/academies",
    summary="학원 등록 + 관리자 가입",
    description="학원의 첫 계정(원장)을 만든다.",
    status_code=status.HTTP_201_CREATED,
    **access(MVP),
)
def register_academy(body: AcademyRegister) -> TokenPair:
    raise not_implemented()


@router.get(
    "/invitations/{code}",
    summary="초대 코드 확인",
    description="가입 화면에서 어느 학원, 어떤 역할 코드인지 보여준다. 학생 이름은 가려서 보낸다.",
    **access(MVP),
)
def preview_invitation(
    code: Annotated[str, Path(min_length=6, max_length=32)],
) -> InvitationPreview:
    raise not_implemented()


@router.post(
    "/signup",
    summary="초대 코드로 가입 (교사·학생·학부모)",
    description="코드는 한 번 쓰면 만료된다. 학부모 코드는 보호자 기록과, 학생 코드는 학생 명부와 연결된다. "
    "만 14세 미만 학생은 보호자가 승인할 때까지 pending_guardian_consent 상태.",
    status_code=status.HTTP_201_CREATED,
    **access(MVP),
)
def signup(body: SignupBody) -> SignupResult:
    raise not_implemented()


@router.post("/login", summary="로그인", **access(MVP))
def login(body: LoginBody) -> TokenPair:
    raise not_implemented()


@router.post("/refresh", summary="토큰 갱신", **access(MVP))
def refresh(body: RefreshBody) -> TokenPair:
    raise not_implemented()


@router.post(
    "/logout",
    summary="로그아웃 (리프레시 토큰 폐기)",
    status_code=status.HTTP_204_NO_CONTENT,
    **access(MVP, *MEMBERS),
)
def logout(user: CurrentUserDep, body: RefreshBody) -> None:
    raise not_implemented()


@router.get("/me", summary="내 정보·역할·첫 화면", **access(MVP, *MEMBERS))
def me(user: CurrentUserDep) -> MeOut:
    raise not_implemented()
