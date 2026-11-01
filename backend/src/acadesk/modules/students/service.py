import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from acadesk.core.crypto import encrypt_phone, mask_phone, normalize_phone, phone_hash
from acadesk.core.errors import bad_request, not_found
from acadesk.core.schemas import Page, PageParams
from acadesk.core.security import CurrentUser
from acadesk.db.tenant import get_scoped, scoped
from acadesk.modules.academies.models import User
from acadesk.modules.audit import service as audit
from acadesk.modules.lectures.models import LectureEnrollment

from .models import Guardian, Student, StudentGuardian
from .schemas import (
    GuardianCreate,
    GuardianLink,
    GuardianLinkCreate,
    GuardianOut,
    StudentCreate,
    StudentOut,
    StudentStatus,
    StudentSummary,
)


def guardian_out(g: Guardian) -> GuardianOut:
    return GuardianOut(
        id=g.id,
        name=g.name,
        phone_masked=mask_phone(g.phone_last4),
        preferred_language=g.preferred_language,
        consent_notices=g.consent_notices,
    )


def new_guardian(academy_id: uuid.UUID, body: GuardianCreate) -> Guardian:
    digits = normalize_phone(body.phone)
    if len(digits) < 9:
        raise bad_request("invalid_phone", "연락처 형식이 올바르지 않습니다")
    return Guardian(
        academy_id=academy_id,
        name=body.name,
        phone_encrypted=encrypt_phone(digits),
        phone_hash=phone_hash(digits),
        phone_last4=digits[-4:],
        preferred_language=body.preferred_language,
        consent_notices=body.consent_notices,
    )


def _active_lecture_ids(db: Session, student_ids: list[uuid.UUID]) -> dict[uuid.UUID, list]:
    rows = db.execute(
        select(LectureEnrollment.student_id, LectureEnrollment.lecture_id).where(
            LectureEnrollment.student_id.in_(student_ids), LectureEnrollment.ended_on.is_(None)
        )
    ).all()
    out: dict[uuid.UUID, list] = {}
    for sid, lid in rows:
        out.setdefault(sid, []).append(lid)
    return out


def summary(s: Student, lecture_ids: list[uuid.UUID]) -> StudentSummary:
    return StudentSummary(
        id=s.id,
        external_id=s.external_id,
        name=s.name,
        grade=s.grade,
        status=s.status,
        household_id=s.household_id,
        lecture_ids=lecture_ids,
    )


def student_out(db: Session, s: Student) -> StudentOut:
    links = db.execute(
        select(StudentGuardian, Guardian)
        .join(Guardian, Guardian.id == StudentGuardian.guardian_id)
        .where(StudentGuardian.student_id == s.id)
        .order_by(StudentGuardian.is_primary.desc())
    ).all()
    siblings: list[uuid.UUID] = []
    if s.household_id:
        siblings = list(
            db.scalars(
                select(Student.id).where(Student.household_id == s.household_id, Student.id != s.id)
            )
        )
    has_account = db.scalar(select(func.count()).where(User.student_id == s.id)) > 0
    return StudentOut(
        **summary(s, _active_lecture_ids(db, [s.id]).get(s.id, [])).model_dump(),
        school=s.school,
        birth_date=s.birth_date,
        has_account=has_account,
        guardians=[
            GuardianLink(
                guardian=guardian_out(g),
                relation=link.relation,
                is_primary=link.is_primary,
                receives_notices=link.receives_notices,
            )
            for link, g in links
        ],
        sibling_ids=siblings,
        created_at=s.created_at,
    )


def _link(
    db: Session, user: CurrentUser, student: Student, body: GuardianLinkCreate
) -> StudentGuardian:
    if body.guardian_id:
        guardian = get_scoped(db, Guardian, body.guardian_id, user)
        if guardian is None:
            raise not_found("보호자")
    elif body.new_guardian:
        guardian = new_guardian(user.academy_id, body.new_guardian)
        db.add(guardian)
        db.flush()
    else:
        raise bad_request("guardian_required", "guardian_id나 new_guardian이 필요합니다")
    has_primary = db.scalar(
        select(func.count()).where(
            StudentGuardian.student_id == student.id, StudentGuardian.is_primary.is_(True)
        )
    )
    link = StudentGuardian(
        academy_id=user.academy_id,
        student_id=student.id,
        guardian_id=guardian.id,
        relation=body.relation,
        is_primary=body.is_primary or not has_primary,
        receives_notices=body.receives_notices,
    )
    db.add(link)
    return link


def create_student(db: Session, user: CurrentUser, body: StudentCreate) -> StudentOut:
    student = Student(
        academy_id=user.academy_id,
        external_id=body.external_id,
        name=body.name,
        grade=body.grade,
        school=body.school,
        birth_date=body.birth_date,
        status=StudentStatus.ACTIVE,
    )
    db.add(student)
    db.flush()
    for g in body.guardians:
        _link(db, user, student, g)
        db.flush()
    audit.record(
        db,
        academy_id=user.academy_id,
        actor=user,
        action="student.create",
        entity_type="student",
        entity_id=student.id,
        after={"name": student.name},
    )
    db.commit()
    return student_out(db, student)


def get_student(db: Session, user: CurrentUser, student_id: uuid.UUID) -> StudentOut:
    s = get_scoped(db, Student, student_id, user)
    if s is None:
        raise not_found("학생")
    return student_out(db, s)


def list_students(
    db: Session,
    user: CurrentUser,
    paging: PageParams,
    q: str | None,
    status: StudentStatus | None,
    lecture_id: uuid.UUID | None,
    household_id: uuid.UUID | None,
) -> Page[StudentSummary]:
    stmt = scoped(Student, user)
    if q:
        stmt = stmt.where(Student.name.ilike(f"%{q}%") | (Student.external_id == q))
    if status:
        stmt = stmt.where(Student.status == status)
    if household_id:
        stmt = stmt.where(Student.household_id == household_id)
    if lecture_id:
        stmt = stmt.where(
            Student.id.in_(
                select(LectureEnrollment.student_id).where(
                    LectureEnrollment.lecture_id == lecture_id,
                    LectureEnrollment.ended_on.is_(None),
                )
            )
        )
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = list(
        db.scalars(
            stmt.order_by(Student.name).offset((paging.page - 1) * paging.size).limit(paging.size)
        )
    )
    lectures = _active_lecture_ids(db, [s.id for s in rows])
    return Page(
        items=[summary(s, lectures.get(s.id, [])) for s in rows],
        total=total or 0,
        page=paging.page,
        size=paging.size,
    )


def link_guardian(
    db: Session, user: CurrentUser, student_id: uuid.UUID, body: GuardianLinkCreate
) -> StudentOut:
    s = get_scoped(db, Student, student_id, user)
    if s is None:
        raise not_found("학생")
    _link(db, user, s, body)
    db.commit()
    return student_out(db, s)


def create_guardian(db: Session, user: CurrentUser, body: GuardianCreate) -> GuardianOut:
    g = new_guardian(user.academy_id, body)
    db.add(g)
    db.commit()
    return guardian_out(g)
