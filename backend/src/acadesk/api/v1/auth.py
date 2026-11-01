"""로그인. 인증 방식(자체 JWT / 외부 서비스)은 킥오프에서 정한다. 계약은 자체 JWT 기준."""

from fastapi import APIRouter, status
from pydantic import BaseModel

from acadesk.api.deps import MVP, CurrentUserDep, access
from acadesk.core.errors import not_implemented
from acadesk.core.security import ALL_ROLES, CurrentUser

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


class MeOut(CurrentUser):
    academy_name: str
    preferred_language: str = "ko"


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
    **access(MVP, *ALL_ROLES),
)
def logout(user: CurrentUserDep, body: RefreshBody) -> None:
    raise not_implemented()


@router.get("/me", summary="내 정보·역할", **access(MVP, *ALL_ROLES))
def me(user: CurrentUserDep) -> MeOut:
    raise not_implemented()
