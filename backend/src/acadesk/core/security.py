import uuid
from enum import StrEnum

from pydantic import BaseModel


class Role(StrEnum):
    OWNER = "owner"  # 학원 관리자 (원장)
    MANAGER = "manager"  # 학원 관리자 (실장)
    TEACHER = "teacher"
    STUDENT = "student"
    PARENT = "parent"
    OPERATOR = "operator"  # 플랫폼 운영자: 커뮤니티 신고 처리. 학원 데이터 권한 없음


STAFF_ADMIN = (Role.OWNER, Role.MANAGER)  # 학원 관리자
STAFF = (Role.OWNER, Role.MANAGER, Role.TEACHER)  # 학원 직원
MEMBERS = (*STAFF, Role.STUDENT, Role.PARENT)  # 학원 구성원 전체


class CurrentUser(BaseModel):
    """요청한 사용자. 모든 조회·변경은 academy_id로 범위를 제한한다."""

    id: uuid.UUID
    academy_id: uuid.UUID
    role: Role
    name: str
    student_id: uuid.UUID | None = None  # role=student: 연결된 학생 명부
    guardian_id: uuid.UUID | None = None  # role=parent: 연결된 보호자 (자녀는 student_guardians)


DEV_USER = CurrentUser(
    id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
    academy_id=uuid.UUID("00000000-0000-0000-0000-0000000000a1"),
    role=Role.OWNER,
    name="개발용 원장",
)


def decode_access_token(token: str) -> CurrentUser | None:
    """액세스 토큰을 검증해 사용자를 돌려준다. 인증 방식이 정해지면 구현한다."""
    return None
