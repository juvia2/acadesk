"""가입·로그인 요청과 응답."""

import uuid
from enum import StrEnum

from pydantic import BaseModel, Field

from acadesk.core.security import CurrentUser, Role


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
