import uuid
from enum import StrEnum

from pydantic import BaseModel


class Role(StrEnum):
    OWNER = "owner"  # 원장
    MANAGER = "manager"  # 실장
    TEACHER = "teacher"  # 교사


ALL_ROLES = (Role.OWNER, Role.MANAGER, Role.TEACHER)
STAFF_ADMIN = (Role.OWNER, Role.MANAGER)


class CurrentUser(BaseModel):
    """요청한 사용자. 모든 조회·변경은 academy_id로 범위를 제한한다."""

    id: uuid.UUID
    academy_id: uuid.UUID
    role: Role
    name: str


DEV_USER = CurrentUser(
    id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
    academy_id=uuid.UUID("00000000-0000-0000-0000-0000000000a1"),
    role=Role.OWNER,
    name="개발용 원장",
)


def decode_access_token(token: str) -> CurrentUser | None:
    """액세스 토큰을 검증해 사용자를 돌려준다. 인증 방식이 정해지면 구현한다."""
    return None
