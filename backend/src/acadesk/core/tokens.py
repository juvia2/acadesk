"""액세스 토큰(JWT)과 리프레시 토큰(불투명 값, DB에는 해시만)."""

import secrets
import uuid
from datetime import timedelta

import jwt

from acadesk.core import clock
from acadesk.core.config import get_settings

ALGORITHM = "HS256"


def create_access_token(
    *,
    user_id: uuid.UUID,
    academy_id: uuid.UUID,
    role: str,
    name: str,
    status: str,
    student_id: uuid.UUID | None,
    guardian_id: uuid.UUID | None,
) -> tuple[str, int]:
    settings = get_settings()
    issued = clock.now()
    lifetime = timedelta(minutes=settings.access_token_minutes)
    claims = {
        "type": "access",
        "sub": str(user_id),
        "aid": str(academy_id),
        "role": role,
        "name": name,
        "st": status,
        "sid": str(student_id) if student_id else None,
        "gid": str(guardian_id) if guardian_id else None,
        "iat": issued,
        "exp": issued + lifetime,
    }
    token = jwt.encode(claims, settings.jwt_secret, algorithm=ALGORITHM)
    return token, int(lifetime.total_seconds())


def decode_access_claims(token: str) -> dict | None:
    try:
        claims = jwt.decode(token, get_settings().jwt_secret, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None
    return claims if claims.get("type") == "access" else None


def new_refresh_token() -> str:
    return secrets.token_urlsafe(32)
