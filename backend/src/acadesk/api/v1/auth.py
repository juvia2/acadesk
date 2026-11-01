"""회원가입·로그인. 인증 방식(자체 JWT / 외부 서비스)은 킥오프에서 정한다. 계약은 자체 JWT 기준.

가입 경로는 두 가지다.
- 학원 관리자: 학원 등록과 함께 가입 (POST /auth/academies)
- 교사·학생·학부모: 학원이 발급한 일회용 초대 코드로 가입 (POST /auth/signup)
"""

from typing import Annotated

from fastapi import APIRouter, Path, status

from acadesk.api.deps import MVP, CurrentUserDep, access
from acadesk.core.security import MEMBERS
from acadesk.db.session import DbDep
from acadesk.modules.academies import accounts
from acadesk.modules.academies.auth_schemas import (
    AcademyRegister,
    InvitationPreview,
    LoginBody,
    MeOut,
    RefreshBody,
    SignupBody,
    SignupResult,
    TokenPair,
)

router = APIRouter(prefix="/auth", tags=["인증"])


@router.post(
    "/academies",
    summary="학원 등록 + 관리자 가입",
    description="학원의 첫 계정(원장)을 만든다.",
    status_code=status.HTTP_201_CREATED,
    **access(MVP),
)
def register_academy(db: DbDep, body: AcademyRegister) -> TokenPair:
    return accounts.register_academy(db, body)


@router.get(
    "/invitations/{code}",
    summary="초대 코드 확인",
    description="가입 화면에서 어느 학원, 어떤 역할 코드인지 보여준다. 학생 이름은 가려서 보낸다.",
    **access(MVP),
)
def preview_invitation(
    db: DbDep,
    code: Annotated[str, Path(min_length=6, max_length=32)],
) -> InvitationPreview:
    return accounts.preview_invitation(db, code)


@router.post(
    "/signup",
    summary="초대 코드로 가입 (교사·학생·학부모)",
    description="코드는 한 번 쓰면 만료된다. 학부모 코드는 보호자 기록과, 학생 코드는 학생 명부와 연결된다. "
    "만 14세 미만 학생은 보호자가 승인할 때까지 pending_guardian_consent 상태.",
    status_code=status.HTTP_201_CREATED,
    **access(MVP),
)
def signup(db: DbDep, body: SignupBody) -> SignupResult:
    return accounts.signup(db, body)


@router.post("/login", summary="로그인", **access(MVP))
def login(db: DbDep, body: LoginBody) -> TokenPair:
    return accounts.login(db, body)


@router.post("/refresh", summary="토큰 갱신", **access(MVP))
def refresh(db: DbDep, body: RefreshBody) -> TokenPair:
    return accounts.refresh(db, body.refresh_token)


@router.post(
    "/logout",
    summary="로그아웃 (리프레시 토큰 폐기)",
    status_code=status.HTTP_204_NO_CONTENT,
    **access(MVP, *MEMBERS),
)
def logout(db: DbDep, user: CurrentUserDep, body: RefreshBody) -> None:
    accounts.logout(db, user, body.refresh_token)


@router.get("/me", summary="내 정보·역할·첫 화면", **access(MVP, *MEMBERS))
def me(db: DbDep, user: CurrentUserDep) -> MeOut:
    return accounts.me(db, user)
