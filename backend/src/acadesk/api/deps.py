"""라우터가 같이 쓰는 의존성.

모든 라우터는 `CurrentUserDep`로 academy_id와 역할을 받고,
엔드포인트마다 `access(단계, *역할)`로 허용 역할과 출시 단계를 한 곳에 적는다.
"""

from collections.abc import Callable
from typing import Annotated, Any, Literal

from fastapi import Depends, Header, HTTPException, Request, status

from acadesk.core.config import get_settings
from acadesk.core.security import DEV_USER, CurrentUser, Role, decode_access_token

Stage = Literal["MVP", "확장", "제안"]
MVP: Stage = "MVP"
EXT: Stage = "확장"
PROPOSED: Stage = "제안"  # features.md "제안 기능": 회의에서 MVP/확장/보류를 정함


def get_current_user(authorization: Annotated[str | None, Header()] = None) -> CurrentUser:
    if get_settings().auth_dev_bypass:
        return DEV_USER
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "로그인이 필요합니다")
    user = decode_access_token(authorization.removeprefix("Bearer "))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "토큰이 유효하지 않습니다")
    return user


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]


def require_roles(*roles: Role) -> Callable[[CurrentUser], CurrentUser]:
    def checker(user: CurrentUserDep) -> CurrentUser:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "권한이 없습니다")
        return user

    return checker


def access(stage: Stage, *roles: Role) -> dict[str, Any]:
    """엔드포인트 데코레이터에 펼쳐 넣는다: `@router.get("/x", **access(MVP, Role.OWNER))`.

    역할을 비우면 인증 없이 열린 엔드포인트(공개 링크, 웹훅)다.
    단계와 역할은 OpenAPI의 x-stage, x-roles로도 나가서 명세서에 표시된다.
    """
    extra: dict[str, Any] = {"x-stage": stage, "x-roles": [r.value for r in roles]}
    deps = [Depends(require_roles(*roles))] if roles else []
    return {"openapi_extra": extra, "dependencies": deps}


async def verify_webhook_signature(request: Request, provider: str) -> None:
    """발송 대행사 웹훅 서명 검증. 대행사가 정해지면 integrations/sms의 구현체로 넘긴다."""
    if get_settings().env == "local":
        return
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "서명을 확인할 수 없습니다")
