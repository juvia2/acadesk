"""계정: 학원 등록, 초대 코드, 가입, 로그인, 토큰 갱신, 학부모 자녀 연결."""

import uuid
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from acadesk.core import clock
from acadesk.core.config import get_settings
from acadesk.core.crypto import (
    code_hash,
    new_invitation_code,
    normalize_code,
    opaque_token_hash,
)
from acadesk.core.errors import AppError, bad_request, conflict, forbidden, not_found
from acadesk.core.passwords import hash_password, verify_password
from acadesk.core.schemas import Page, PageParams
from acadesk.core.security import CurrentUser, Role
from acadesk.core.tokens import create_access_token, new_refresh_token
from acadesk.db.tenant import get_scoped, scoped
from acadesk.modules.audit import service as audit
from acadesk.modules.lectures.models import Lecture, LectureEnrollment
from acadesk.modules.reports.schemas import ChildAccountStatus, ChildOut
from acadesk.modules.students.models import Student, StudentGuardian
from acadesk.modules.students.schemas import GuardianCreate
from acadesk.modules.students.service import new_guardian

from .auth_schemas import (
    AcademyRegister,
    ChildBrief,
    InvitationPreview,
    LoginBody,
    MeOut,
    SignupBody,
    SignupResult,
    TokenPair,
)
from .auth_schemas import (
    AccountStatus as ApiAccountStatus,
)
from .models import Academy, AccountStatus, Invitation, RefreshToken, User
from .schemas import (
    InvitationBulkCreate,
    InvitationCreate,
    InvitationOut,
    InvitationStatus,
)

HOME = {
    Role.OWNER: "/admin",
    Role.MANAGER: "/admin",
    Role.TEACHER: "/teacher",
    Role.STUDENT: "/student",
    Role.PARENT: "/parent",
    Role.OPERATOR: "/ops",
}
INVITABLE = {Role.MANAGER, Role.TEACHER, Role.STUDENT, Role.PARENT}
CONSENT_AGE = 14


# ── 토큰 ─────────────────────────────────────────────


def _issue_tokens(db: Session, user: User) -> TokenPair:
    access, expires_in = create_access_token(
        user_id=user.id,
        academy_id=user.academy_id,
        role=user.role.value,
        name=user.name,
        status=user.status.value,
        student_id=user.student_id,
        guardian_id=user.guardian_id,
    )
    refresh = new_refresh_token()
    db.add(
        RefreshToken(
            academy_id=user.academy_id,
            user_id=user.id,
            token_hash=opaque_token_hash(refresh),
            expires_at=clock.now() + timedelta(days=get_settings().refresh_token_days),
        )
    )
    return TokenPair(access_token=access, refresh_token=refresh, expires_in=expires_in)


def _email_taken(db: Session, email: str) -> bool:
    return db.scalar(select(func.count()).where(func.lower(User.email) == email.lower())) > 0


# ── 학원 등록 ───────────────────────────────────────


def register_academy(db: Session, body: AcademyRegister) -> TokenPair:
    if _email_taken(db, body.email):
        raise conflict("email_taken", "이미 가입된 이메일입니다")
    academy = Academy(name=body.academy_name, phone=body.academy_phone)
    db.add(academy)
    db.flush()
    owner = User(
        academy_id=academy.id,
        email=body.email.lower(),
        name=body.owner_name,
        role=Role.OWNER,
        password_hash=hash_password(body.password),
        status=AccountStatus.ACTIVE,
    )
    db.add(owner)
    db.flush()
    audit.record(
        db,
        academy_id=academy.id,
        actor=None,
        action="academy.register",
        entity_type="academy",
        entity_id=academy.id,
        after={"name": academy.name, "owner_id": str(owner.id)},
    )
    tokens = _issue_tokens(db, owner)
    db.commit()
    return tokens


# ── 초대 코드 ───────────────────────────────────────


def _invitation_out(inv: Invitation, code: str | None = None, student_name: str | None = None):
    status = inv.status
    if status == InvitationStatus.ACTIVE and inv.expires_at <= clock.now():
        status = InvitationStatus.EXPIRED
    return InvitationOut(
        id=inv.id,
        role=inv.role,
        code=code,
        code_hint=inv.code_hint,
        student_id=inv.student_id,
        student_name=student_name,
        guardian_id=inv.guardian_id,
        status=status,
        expires_at=inv.expires_at,
        used_by=inv.used_by,
        used_at=inv.used_at,
        created_at=inv.created_at,
    )


def _new_invitation(
    db: Session,
    user: CurrentUser,
    *,
    role: Role,
    student: Student | None,
    guardian_id: uuid.UUID | None,
    email: str | None,
    expires_in_days: int,
) -> tuple[Invitation, str]:
    code = new_invitation_code()
    inv = Invitation(
        academy_id=user.academy_id,
        code_hash=code_hash(code),
        code_hint=code[-2:],
        role=role,
        student_id=student.id if student else None,
        guardian_id=guardian_id,
        email=email,
        status=InvitationStatus.ACTIVE,
        expires_at=clock.now() + timedelta(days=expires_in_days),
        created_by=user.id,
    )
    db.add(inv)
    db.flush()
    return inv, code


def create_invitation(db: Session, user: CurrentUser, body: InvitationCreate) -> InvitationOut:
    if body.role not in INVITABLE:
        raise bad_request("role_not_invitable", "이 역할은 초대 코드로 가입할 수 없습니다")
    if body.role == Role.MANAGER and user.role != Role.OWNER:
        raise forbidden("owner_only", "실장 초대는 원장만 할 수 있습니다")
    student = None
    if body.role in (Role.STUDENT, Role.PARENT):
        if body.student_id is None:
            raise bad_request("student_required", "학생·학부모 코드에는 student_id가 필요합니다")
        student = get_scoped(db, Student, body.student_id, user)
        if student is None:
            raise not_found("학생")
    if body.guardian_id:
        linked = db.scalar(
            select(func.count()).where(
                StudentGuardian.student_id == body.student_id,
                StudentGuardian.guardian_id == body.guardian_id,
            )
        )
        if not linked:
            raise bad_request("guardian_not_linked", "이 학생의 보호자가 아닙니다")
    inv, code = _new_invitation(
        db,
        user,
        role=body.role,
        student=student,
        guardian_id=body.guardian_id,
        email=body.email,
        expires_in_days=body.expires_in_days,
    )
    db.commit()
    return _invitation_out(inv, code, student.name if student else None)


def bulk_create_invitations(
    db: Session, user: CurrentUser, body: InvitationBulkCreate
) -> list[InvitationOut]:
    students = list(db.scalars(scoped(Student, user).where(Student.id.in_(body.student_ids))))
    if len(students) != len(set(body.student_ids)):
        raise not_found("학생")
    out = []
    for s in students:
        inv, code = _new_invitation(
            db,
            user,
            role=Role.STUDENT,
            student=s,
            guardian_id=None,
            email=None,
            expires_in_days=body.expires_in_days,
        )
        out.append(_invitation_out(inv, code, s.name))
        if body.include_parents:
            primary = db.scalar(
                select(StudentGuardian.guardian_id).where(
                    StudentGuardian.student_id == s.id, StudentGuardian.is_primary.is_(True)
                )
            )
            inv, code = _new_invitation(
                db,
                user,
                role=Role.PARENT,
                student=s,
                guardian_id=primary,
                email=None,
                expires_in_days=body.expires_in_days,
            )
            out.append(_invitation_out(inv, code, s.name))
    db.commit()
    return out


def list_invitations(
    db: Session,
    user: CurrentUser,
    paging: PageParams,
    role: Role | None,
    status: InvitationStatus | None,
    student_id: uuid.UUID | None,
) -> Page[InvitationOut]:
    stmt = scoped(Invitation, user)
    if role:
        stmt = stmt.where(Invitation.role == role)
    if student_id:
        stmt = stmt.where(Invitation.student_id == student_id)
    if status == InvitationStatus.EXPIRED:
        stmt = stmt.where(
            Invitation.status == InvitationStatus.ACTIVE, Invitation.expires_at <= clock.now()
        )
    elif status == InvitationStatus.ACTIVE:
        stmt = stmt.where(
            Invitation.status == InvitationStatus.ACTIVE, Invitation.expires_at > clock.now()
        )
    elif status:
        stmt = stmt.where(Invitation.status == status)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.execute(
        stmt.add_columns(Student.name)
        .outerjoin(Student, Student.id == Invitation.student_id)
        .order_by(Invitation.created_at.desc())
        .offset((paging.page - 1) * paging.size)
        .limit(paging.size)
    ).all()
    return Page(
        items=[_invitation_out(inv, None, name) for inv, name in rows],
        total=total,
        page=paging.page,
        size=paging.size,
    )


def revoke_invitation(db: Session, user: CurrentUser, invitation_id: uuid.UUID) -> None:
    inv = get_scoped(db, Invitation, invitation_id, user)
    if inv is None:
        raise not_found("초대 코드")
    if inv.status == InvitationStatus.USED:
        raise conflict("already_used", "이미 사용된 코드입니다")
    inv.status = InvitationStatus.REVOKED
    db.commit()


def _find_usable_invitation(db: Session, code: str) -> Invitation:
    inv = db.scalar(select(Invitation).where(Invitation.code_hash == code_hash(code)))
    if inv is None or inv.status != InvitationStatus.ACTIVE:
        raise bad_request("invalid_code", "사용할 수 없는 초대 코드입니다")
    if inv.expires_at <= clock.now():
        raise bad_request("expired_code", "만료된 초대 코드입니다. 학원에 새 코드를 요청하세요")
    return inv


def _mask_name(name: str) -> str:
    if len(name) <= 1:
        return name
    if len(name) == 2:
        return name[0] + "*"
    return name[0] + "*" * (len(name) - 2) + name[-1]


def preview_invitation(db: Session, code: str) -> InvitationPreview:
    inv = _find_usable_invitation(db, normalize_code(code))
    academy = db.get(Academy, inv.academy_id)
    student = db.get(Student, inv.student_id) if inv.student_id else None
    return InvitationPreview(
        academy_name=academy.name if academy else "",
        role=inv.role,
        student_name_masked=_mask_name(student.name) if student else None,
        expires_at=inv.expires_at.isoformat(),
    )


# ── 가입 ─────────────────────────────────────────────


def _age_on(birth: date, today: date) -> int:
    return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))


def signup(db: Session, body: SignupBody) -> SignupResult:
    if not body.agree_terms:
        raise bad_request("terms_required", "이용약관 동의가 필요합니다")
    inv = _find_usable_invitation(db, body.code)
    if _email_taken(db, body.email):
        raise conflict("email_taken", "이미 가입된 이메일입니다")

    user = User(
        academy_id=inv.academy_id,
        email=body.email.lower(),
        name=body.name,
        role=inv.role,
        password_hash=hash_password(body.password),
        status=AccountStatus.ACTIVE,
    )

    if inv.role == Role.STUDENT:
        student = db.get(Student, inv.student_id)
        if student is None:
            raise bad_request("invalid_code", "사용할 수 없는 초대 코드입니다")
        if db.scalar(select(func.count()).where(User.student_id == student.id)):
            raise conflict("student_has_account", "이 학생은 이미 가입했습니다")
        user.student_id = student.id
        if student.birth_date and _age_on(student.birth_date, clock.now().date()) < CONSENT_AGE:
            user.status = AccountStatus.PENDING_GUARDIAN_CONSENT

    elif inv.role == Role.PARENT:
        guardian_id = inv.guardian_id
        if guardian_id is None:
            # 보호자 기록 없이 발급된 코드: 가입 정보로 보호자를 만들어 학생과 연결
            if not body.phone:
                raise bad_request("phone_required", "긴급 연락을 받을 휴대전화 번호가 필요합니다")
            guardian = new_guardian(
                inv.academy_id, GuardianCreate(name=body.name, phone=body.phone)
            )
            db.add(guardian)
            db.flush()
            has_primary = db.scalar(
                select(func.count()).where(
                    StudentGuardian.student_id == inv.student_id,
                    StudentGuardian.is_primary.is_(True),
                )
            )
            db.add(
                StudentGuardian(
                    academy_id=inv.academy_id,
                    student_id=inv.student_id,
                    guardian_id=guardian.id,
                    relation="보호자",
                    is_primary=not has_primary,
                )
            )
            guardian_id = guardian.id
        elif db.scalar(select(func.count()).where(User.guardian_id == guardian_id)):
            raise conflict(
                "guardian_has_account",
                "이 보호자는 이미 가입했습니다. 기존 계정에서 '자녀 추가'로 연결하세요",
            )
        user.guardian_id = guardian_id

    db.add(user)
    try:
        db.flush()
    except IntegrityError as e:
        db.rollback()
        raise conflict("signup_conflict", "가입 정보가 이미 사용 중입니다") from e

    inv.status = InvitationStatus.USED
    inv.used_by = user.id
    inv.used_at = clock.now()
    audit.record(
        db,
        academy_id=inv.academy_id,
        actor=None,
        action="user.signup",
        entity_type="user",
        entity_id=user.id,
        after={"role": user.role.value, "invitation_id": str(inv.id)},
    )
    tokens = _issue_tokens(db, user)
    db.commit()
    return SignupResult(**tokens.model_dump(), status=ApiAccountStatus(user.status.value))


# ── 로그인 ───────────────────────────────────────────


def login(db: Session, body: LoginBody) -> TokenPair:
    user = db.scalar(select(User).where(func.lower(User.email) == body.email.lower()))
    if (
        user is None
        or not user.password_hash
        or not verify_password(user.password_hash, body.password)
    ):
        raise AppError(401, "invalid_credentials", "이메일 또는 비밀번호가 올바르지 않습니다")
    if user.status == AccountStatus.DISABLED:
        raise forbidden("account_disabled", "사용이 중지된 계정입니다")
    user.last_login_at = clock.now()
    tokens = _issue_tokens(db, user)
    db.commit()
    return tokens


def _valid_refresh(db: Session, token: str) -> RefreshToken:
    row = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == opaque_token_hash(token)))
    if row is None or row.revoked_at is not None or row.expires_at <= clock.now():
        raise AppError(401, "invalid_refresh_token", "다시 로그인하세요")
    return row


def refresh(db: Session, token: str) -> TokenPair:
    """리프레시 토큰은 한 번 쓰면 폐기하고 새로 준다 (회전)."""
    row = _valid_refresh(db, token)
    user = db.get(User, row.user_id)
    if user is None or user.status == AccountStatus.DISABLED:
        raise AppError(401, "invalid_refresh_token", "다시 로그인하세요")
    row.revoked_at = clock.now()
    tokens = _issue_tokens(db, user)
    db.commit()
    return tokens


def logout(db: Session, user: CurrentUser, token: str) -> None:
    row = db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == opaque_token_hash(token), RefreshToken.user_id == user.id
        )
    )
    if row and row.revoked_at is None:
        row.revoked_at = clock.now()
        db.commit()


# ── 내 정보·자녀 ────────────────────────────────────


def _child_rows(db: Session, guardian_id: uuid.UUID) -> list[tuple[Student, str]]:
    return list(
        db.execute(
            select(Student, StudentGuardian.relation)
            .join(StudentGuardian, StudentGuardian.student_id == Student.id)
            .where(StudentGuardian.guardian_id == guardian_id)
            .order_by(Student.name)
        ).tuples()
    )


def _lecture_names(db: Session, student_ids: list[uuid.UUID]) -> dict[uuid.UUID, list[str]]:
    rows = db.execute(
        select(LectureEnrollment.student_id, Lecture.name)
        .join(Lecture, Lecture.id == LectureEnrollment.lecture_id)
        .where(LectureEnrollment.student_id.in_(student_ids), LectureEnrollment.ended_on.is_(None))
    ).all()
    out: dict[uuid.UUID, list[str]] = {}
    for sid, name in rows:
        out.setdefault(sid, []).append(name)
    return out


def _child_status(db: Session, student_id: uuid.UUID) -> ChildAccountStatus:
    status = db.scalar(select(User.status).where(User.student_id == student_id))
    if status is None:
        return ChildAccountStatus.NO_ACCOUNT
    if status == AccountStatus.PENDING_GUARDIAN_CONSENT:
        return ChildAccountStatus.PENDING_CONSENT
    return ChildAccountStatus.ACTIVE


def list_children(db: Session, user: CurrentUser) -> list[ChildOut]:
    if user.guardian_id is None:
        return []
    rows = _child_rows(db, user.guardian_id)
    names = _lecture_names(db, [s.id for s, _ in rows])
    return [
        ChildOut(
            student_id=s.id,
            name=s.name,
            grade=s.grade,
            lecture_names=names.get(s.id, []),
            account_status=_child_status(db, s.id),
            relation=relation,
        )
        for s, relation in rows
    ]


def me(db: Session, user: CurrentUser) -> MeOut:
    academy = db.get(Academy, user.academy_id)
    db_user = db.get(User, user.id)
    children = []
    if user.role == Role.PARENT and user.guardian_id:
        rows = _child_rows(db, user.guardian_id)
        names = _lecture_names(db, [s.id for s, _ in rows])
        children = [
            ChildBrief(
                student_id=s.id, name=s.name, grade=s.grade, lecture_names=names.get(s.id, [])
            )
            for s, _ in rows
        ]
    return MeOut(
        **user.model_dump(exclude={"status"}),
        academy_name=academy.name if academy else "",
        preferred_language=db_user.preferred_language if db_user else "ko",
        status=ApiAccountStatus(db_user.status.value if db_user else user.status),
        children=children,
        home=HOME[user.role],
    )


def _require_child(db: Session, user: CurrentUser, student_id: uuid.UUID) -> Student:
    if user.guardian_id is None:
        raise not_found("자녀")
    student = db.scalar(
        select(Student)
        .join(StudentGuardian, StudentGuardian.student_id == Student.id)
        .where(
            Student.id == student_id,
            Student.academy_id == user.academy_id,
            StudentGuardian.guardian_id == user.guardian_id,
        )
    )
    if student is None:
        raise not_found("자녀")
    return student


def require_child(db: Session, user: CurrentUser, student_id: uuid.UUID) -> Student:
    """학부모가 자기 자녀에만 접근하는지 확인. 다른 서비스(리포트 등)에서도 쓴다."""
    return _require_child(db, user, student_id)


def add_child(db: Session, user: CurrentUser, code: str) -> ChildOut:
    inv = _find_usable_invitation(db, code)
    if inv.role != Role.PARENT or inv.academy_id != user.academy_id or user.guardian_id is None:
        raise bad_request("invalid_code", "이 계정에 연결할 수 없는 코드입니다")
    exists = db.scalar(
        select(StudentGuardian).where(
            StudentGuardian.student_id == inv.student_id,
            StudentGuardian.guardian_id == user.guardian_id,
        )
    )
    if exists is None:
        relation = "보호자"
        if inv.guardian_id:
            relation = (
                db.scalar(
                    select(StudentGuardian.relation).where(
                        StudentGuardian.student_id == inv.student_id,
                        StudentGuardian.guardian_id == inv.guardian_id,
                    )
                )
                or relation
            )
        db.add(
            StudentGuardian(
                academy_id=user.academy_id,
                student_id=inv.student_id,
                guardian_id=user.guardian_id,
                relation=relation,
                is_primary=False,
            )
        )
    inv.status = InvitationStatus.USED
    inv.used_by = user.id
    inv.used_at = clock.now()
    audit.record(
        db,
        academy_id=user.academy_id,
        actor=user,
        action="guardian.add_child",
        entity_type="student",
        entity_id=inv.student_id,
        after={"guardian_id": str(user.guardian_id)},
    )
    db.commit()
    child = next(c for c in list_children(db, user) if c.student_id == inv.student_id)
    return child


def approve_child_account(db: Session, user: CurrentUser, student_id: uuid.UUID) -> ChildOut:
    _require_child(db, user, student_id)
    child_user = db.scalar(select(User).where(User.student_id == student_id))
    if child_user is None or child_user.status != AccountStatus.PENDING_GUARDIAN_CONSENT:
        raise conflict("nothing_to_approve", "승인 대기 중인 학생 계정이 없습니다")
    child_user.status = AccountStatus.ACTIVE
    child_user.guardian_consent_by = user.id
    child_user.guardian_consent_at = clock.now()
    audit.record(
        db,
        academy_id=user.academy_id,
        actor=user,
        action="student.guardian_consent",
        entity_type="user",
        entity_id=child_user.id,
        before={"status": AccountStatus.PENDING_GUARDIAN_CONSENT.value},
        after={"status": AccountStatus.ACTIVE.value},
    )
    db.commit()
    return next(c for c in list_children(db, user) if c.student_id == student_id)
