import uuid
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import case, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from acadesk.core import clock
from acadesk.core.errors import bad_request, forbidden, not_found
from acadesk.core.schemas import Page, PageParams
from acadesk.core.security import STAFF_ADMIN, CurrentUser, Role
from acadesk.db.tenant import get_scoped, scoped
from acadesk.modules.academies.models import Academy, User
from acadesk.modules.attendance.models import AttendanceRecord
from acadesk.modules.attendance.schemas import AttendanceStatus
from acadesk.modules.students.models import Student
from acadesk.modules.students.schemas import StudentSummary
from acadesk.modules.students.service import summary as student_summary

from .models import Lecture, LectureEnrollment, LectureSession, SessionStudent
from .schemas import (
    EnrollBody,
    LectureCreate,
    LectureOut,
    LectureSessionOut,
    LectureSlot,
    LectureUpdate,
    SessionCreate,
    SessionKind,
    SessionStatus,
    SessionUpdate,
)

AUTO_GENERATE_WEEKS = 4


def academy_tz(db: Session, academy_id: uuid.UUID) -> ZoneInfo:
    academy = db.get(Academy, academy_id)
    return ZoneInfo(academy.timezone if academy else "Asia/Seoul")


def can_manage(user: CurrentUser, lecture: Lecture) -> bool:
    return user.role in STAFF_ADMIN or lecture.teacher_id == user.id


def require_lecture(db: Session, user: CurrentUser, lecture_id: uuid.UUID) -> Lecture:
    lecture = get_scoped(db, Lecture, lecture_id, user)
    if lecture is None:
        raise not_found("강의")
    return lecture


def require_session(db: Session, user: CurrentUser, session_id: uuid.UUID) -> LectureSession:
    session = get_scoped(db, LectureSession, session_id, user)
    if session is None:
        raise not_found("강의 회차")
    return session


def _require_teacher(db: Session, user: CurrentUser, teacher_id: uuid.UUID | None) -> None:
    if teacher_id is None:
        return
    teacher = get_scoped(db, User, teacher_id, user)
    if teacher is None or teacher.role not in (Role.TEACHER, Role.OWNER, Role.MANAGER):
        raise bad_request("invalid_teacher", "이 학원의 교사가 아닙니다")


# ── 출력 변환 ───────────────────────────────────────


def lecture_out(db: Session, lecture: Lecture) -> LectureOut:
    teacher_name = db.scalar(select(User.name).where(User.id == lecture.teacher_id))
    count = db.scalar(
        select(func.count()).where(
            LectureEnrollment.lecture_id == lecture.id, LectureEnrollment.ended_on.is_(None)
        )
    )
    return LectureOut(
        id=lecture.id,
        name=lecture.name,
        subject=lecture.subject,
        grade=lecture.grade,
        room=lecture.room,
        branch_id=lecture.branch_id,
        teacher_id=lecture.teacher_id,
        teacher_name=teacher_name,
        schedule=[LectureSlot.model_validate(s) for s in lecture.schedule],
        starts_on=lecture.starts_on,
        ends_on=lecture.ends_on,
        student_count=count or 0,
        archived=lecture.archived,
    )


def session_student_ids(db: Session, session: LectureSession) -> list[uuid.UUID]:
    """이 회차의 출석 대상. 보강처럼 대상이 지정돼 있으면 그 학생만, 아니면 현재 수강생."""
    targeted = list(
        db.scalars(select(SessionStudent.student_id).where(SessionStudent.session_id == session.id))
    )
    if targeted:
        return targeted
    return list(
        db.scalars(
            select(LectureEnrollment.student_id).where(
                LectureEnrollment.lecture_id == session.lecture_id,
                LectureEnrollment.ended_on.is_(None),
            )
        )
    )


def session_out(db: Session, session: LectureSession) -> LectureSessionOut:
    lecture = db.get(Lecture, session.lecture_id)
    counts = db.execute(
        select(
            func.count(case((AttendanceRecord.status == AttendanceStatus.PRESENT, 1))),
            func.count(case((AttendanceRecord.status == AttendanceStatus.LATE, 1))),
            func.count(case((AttendanceRecord.status == AttendanceStatus.ABSENT, 1))),
        ).where(AttendanceRecord.session_id == session.id)
    ).one()
    return LectureSessionOut(
        id=session.id,
        lecture_id=session.lecture_id,
        lecture_name=lecture.name if lecture else "",
        teacher_id=lecture.teacher_id if lecture else None,
        date=session.date,
        starts_at=session.starts_at,
        ends_at=session.ends_at,
        kind=session.kind,
        status=session.status,
        attendance_opened_at=session.attendance_opened_at,
        attendance_closed_at=session.attendance_closed_at,
        present_count=counts[0],
        late_count=counts[1],
        absent_count=counts[2],
        enrolled_count=len(session_student_ids(db, session)),
        cancel_reason=session.cancel_reason,
    )


# ── 강의 ─────────────────────────────────────────────


def list_lectures(
    db: Session, user: CurrentUser, mine: bool, teacher_id: uuid.UUID | None, archived: bool
) -> list[LectureOut]:
    stmt = scoped(Lecture, user).where(Lecture.archived.is_(archived))
    if mine:
        stmt = stmt.where(Lecture.teacher_id == user.id)
    elif teacher_id:
        stmt = stmt.where(Lecture.teacher_id == teacher_id)
    return [lecture_out(db, lec) for lec in db.scalars(stmt.order_by(Lecture.name))]


def create_lecture(db: Session, user: CurrentUser, body: LectureCreate) -> LectureOut:
    _require_teacher(db, user, body.teacher_id)
    lecture = Lecture(
        academy_id=user.academy_id,
        name=body.name,
        subject=body.subject,
        grade=body.grade,
        room=body.room,
        branch_id=body.branch_id,
        teacher_id=body.teacher_id,
        schedule=[s.model_dump(mode="json") for s in body.schedule],
        starts_on=body.starts_on,
        ends_on=body.ends_on,
    )
    db.add(lecture)
    db.flush()
    if body.schedule:
        start = body.starts_on or clock.now().astimezone(academy_tz(db, user.academy_id)).date()
        _generate(db, lecture, start, start + timedelta(weeks=AUTO_GENERATE_WEEKS))
    db.commit()
    return lecture_out(db, lecture)


def get_lecture(db: Session, user: CurrentUser, lecture_id: uuid.UUID) -> LectureOut:
    return lecture_out(db, require_lecture(db, user, lecture_id))


def update_lecture(
    db: Session, user: CurrentUser, lecture_id: uuid.UUID, body: LectureUpdate
) -> LectureOut:
    lecture = require_lecture(db, user, lecture_id)
    data = body.model_dump(exclude_unset=True)
    if "teacher_id" in data:
        _require_teacher(db, user, data["teacher_id"])
    if "schedule" in data and data["schedule"] is not None:
        data["schedule"] = [
            LectureSlot.model_validate(s).model_dump(mode="json") for s in data["schedule"]
        ]
    for k, v in data.items():
        setattr(lecture, k, v)
    db.commit()
    return lecture_out(db, lecture)


def list_enrolled(db: Session, user: CurrentUser, lecture_id: uuid.UUID) -> list[StudentSummary]:
    require_lecture(db, user, lecture_id)
    students = db.scalars(
        select(Student)
        .join(LectureEnrollment, LectureEnrollment.student_id == Student.id)
        .where(LectureEnrollment.lecture_id == lecture_id, LectureEnrollment.ended_on.is_(None))
        .order_by(Student.name)
    )
    return [student_summary(s, [lecture_id]) for s in students]


def enroll(db: Session, user: CurrentUser, lecture_id: uuid.UUID, body: EnrollBody) -> LectureOut:
    lecture = require_lecture(db, user, lecture_id)
    ids = set(body.student_ids)
    found = set(
        db.scalars(
            select(Student.id).where(Student.id.in_(ids), Student.academy_id == user.academy_id)
        )
    )
    if found != ids:
        raise not_found("학생")
    today = clock.now().date()
    for sid in ids:
        existing = db.scalar(
            select(LectureEnrollment).where(
                LectureEnrollment.lecture_id == lecture.id, LectureEnrollment.student_id == sid
            )
        )
        if existing:
            existing.ended_on = None
        else:
            db.add(
                LectureEnrollment(
                    academy_id=user.academy_id,
                    lecture_id=lecture.id,
                    student_id=sid,
                    started_on=today,
                )
            )
    db.commit()
    return lecture_out(db, lecture)


def unenroll(db: Session, user: CurrentUser, lecture_id: uuid.UUID, student_id: uuid.UUID) -> None:
    require_lecture(db, user, lecture_id)
    row = db.scalar(
        select(LectureEnrollment).where(
            LectureEnrollment.lecture_id == lecture_id, LectureEnrollment.student_id == student_id
        )
    )
    if row is None or row.ended_on is not None:
        raise not_found("수강 기록")
    row.ended_on = clock.now().date()
    db.commit()


# ── 회차 ─────────────────────────────────────────────


def _generate(db: Session, lecture: Lecture, start: date, end: date) -> list[uuid.UUID]:
    tz = academy_tz(db, lecture.academy_id)
    slots = [LectureSlot.model_validate(s) for s in lecture.schedule]
    rows = []
    day = start
    while day <= end:
        if lecture.ends_on and day > lecture.ends_on:
            break
        for slot in slots:
            if slot.weekday == day.weekday():
                rows.append(
                    {
                        "id": uuid.uuid4(),
                        "academy_id": lecture.academy_id,
                        "lecture_id": lecture.id,
                        "date": day,
                        "starts_at": datetime.combine(day, slot.start, tz),
                        "ends_at": datetime.combine(day, slot.end, tz),
                        "kind": SessionKind.REGULAR.value,
                        "status": SessionStatus.SCHEDULED.value,
                    }
                )
        day += timedelta(days=1)
    if not rows:
        return []
    stmt = (
        insert(LectureSession)
        .values(rows)
        .on_conflict_do_nothing(index_elements=["lecture_id", "starts_at"])
        .returning(LectureSession.id)
    )
    return list(db.scalars(stmt))


def generate_sessions(
    db: Session, user: CurrentUser, lecture_id: uuid.UUID, start: date, end: date
) -> list[LectureSessionOut]:
    lecture = require_lecture(db, user, lecture_id)
    if end < start or (end - start).days > 120:
        raise bad_request("invalid_range", "기간은 120일 이내로 지정하세요")
    _generate(db, lecture, start, end)
    db.commit()
    sessions = db.scalars(
        select(LectureSession)
        .where(LectureSession.lecture_id == lecture.id, LectureSession.date.between(start, end))
        .order_by(LectureSession.starts_at)
    )
    return [session_out(db, s) for s in sessions]


def list_sessions(
    db: Session,
    user: CurrentUser,
    paging: PageParams,
    on: date | None,
    start: date | None,
    end: date | None,
    lecture_id: uuid.UUID | None,
    mine: bool,
    status: SessionStatus | None,
) -> Page[LectureSessionOut]:
    stmt = scoped(LectureSession, user)
    if start or end:
        if start:
            stmt = stmt.where(LectureSession.date >= start)
        if end:
            stmt = stmt.where(LectureSession.date <= end)
    else:
        day = on or clock.now().astimezone(academy_tz(db, user.academy_id)).date()
        stmt = stmt.where(LectureSession.date == day)
    if lecture_id:
        stmt = stmt.where(LectureSession.lecture_id == lecture_id)
    if mine:
        stmt = stmt.where(
            LectureSession.lecture_id.in_(select(Lecture.id).where(Lecture.teacher_id == user.id))
        )
    if status:
        stmt = stmt.where(LectureSession.status == status)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(LectureSession.starts_at)
        .offset((paging.page - 1) * paging.size)
        .limit(paging.size)
    )
    return Page(
        items=[session_out(db, s) for s in rows], total=total, page=paging.page, size=paging.size
    )


def create_session(db: Session, user: CurrentUser, body: SessionCreate) -> LectureSessionOut:
    lecture = require_lecture(db, user, body.lecture_id)
    if not can_manage(user, lecture):
        raise forbidden("not_lecture_teacher", "담당 강의만 관리할 수 있습니다")
    if body.ends_at <= body.starts_at:
        raise bad_request("invalid_time", "종료 시각이 시작보다 늦어야 합니다")
    tz = academy_tz(db, user.academy_id)
    session = LectureSession(
        academy_id=user.academy_id,
        lecture_id=lecture.id,
        date=body.starts_at.astimezone(tz).date(),
        starts_at=body.starts_at,
        ends_at=body.ends_at,
        kind=body.kind,
        status=SessionStatus.SCHEDULED,
    )
    db.add(session)
    db.flush()
    for sid in set(body.student_ids or []):
        db.add(SessionStudent(academy_id=user.academy_id, session_id=session.id, student_id=sid))
    db.commit()
    return session_out(db, session)


def get_session(db: Session, user: CurrentUser, session_id: uuid.UUID) -> LectureSessionOut:
    return session_out(db, require_session(db, user, session_id))


def update_session(
    db: Session, user: CurrentUser, session_id: uuid.UUID, body: SessionUpdate
) -> LectureSessionOut:
    session = require_session(db, user, session_id)
    lecture = db.get(Lecture, session.lecture_id)
    if lecture is None or not can_manage(user, lecture):
        raise forbidden("not_lecture_teacher", "담당 강의만 관리할 수 있습니다")
    if session.status == SessionStatus.CLOSED:
        raise bad_request("session_closed", "마감된 회차는 바꿀 수 없습니다")
    if body.starts_at:
        session.starts_at = body.starts_at
        session.date = body.starts_at.astimezone(academy_tz(db, user.academy_id)).date()
    if body.ends_at:
        session.ends_at = body.ends_at
    if body.status == SessionStatus.CANCELLED:
        session.status = SessionStatus.CANCELLED
        session.cancel_reason = body.cancel_reason
    db.commit()
    return session_out(db, session)


def local_time(db: Session, academy_id: uuid.UUID, at: datetime) -> time:
    return at.astimezone(academy_tz(db, academy_id)).time()
