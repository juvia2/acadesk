"""강의별 QR 출결 처리."""

import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from acadesk.core import clock
from acadesk.core.config import get_settings
from acadesk.core.errors import bad_request, conflict, forbidden, not_found
from acadesk.core.schemas import Page, PageParams
from acadesk.core.security import CurrentUser, Role
from acadesk.db.tenant import get_scoped, scoped
from acadesk.modules.audit import service as audit
from acadesk.modules.lectures.models import Lecture, LectureSession
from acadesk.modules.lectures.schemas import LectureSessionOut, SessionStatus
from acadesk.modules.lectures.service import (
    can_manage,
    local_time,
    require_session,
    session_out,
    session_student_ids,
)
from acadesk.modules.notifications import service as notifications
from acadesk.modules.notifications.schemas import NotificationKind
from acadesk.modules.students.models import Student

from .models import AttendanceAlert, AttendanceRecord
from .qr import (
    CheckInOutcome,
    InvalidQrToken,
    QrError,
    classify_check_in,
    issue_token,
    verify_token,
)
from .schemas import (
    AlertAck,
    AlertKind,
    AlertStatus,
    AttendanceAlertOut,
    AttendanceCorrection,
    AttendanceOut,
    AttendanceStatus,
    CheckInBody,
    CheckInMethod,
    CheckInResult,
    ManualMark,
    QrTokenOut,
    RosterItem,
    SessionRoster,
)

STATUS_KO = {
    AttendanceStatus.PRESENT: "출석",
    AttendanceStatus.LATE: "지각",
    AttendanceStatus.ABSENT: "결석",
    AttendanceStatus.EXCUSED: "인정 결석",
    AttendanceStatus.EARLY_LEAVE: "조퇴",
}


def _lecture(db: Session, session: LectureSession) -> Lecture:
    lecture = db.get(Lecture, session.lecture_id)
    assert lecture is not None
    return lecture


def _require_manager(db: Session, user: CurrentUser, session: LectureSession) -> Lecture:
    lecture = _lecture(db, session)
    if not can_manage(user, lecture):
        raise forbidden("not_lecture_teacher", "담당 강의의 출결만 처리할 수 있습니다")
    return lecture


def _outcome(session: LectureSession, at) -> CheckInOutcome:
    s = get_settings()
    return classify_check_in(
        session.starts_at, session.ends_at, at, s.late_after_minutes, s.open_before_minutes
    )


def _out(db: Session, r: AttendanceRecord) -> AttendanceOut:
    session = db.get(LectureSession, r.session_id)
    lecture = db.get(Lecture, r.lecture_id)
    student = db.get(Student, r.student_id)
    return AttendanceOut(
        id=r.id,
        session_id=r.session_id,
        lecture_id=r.lecture_id,
        lecture_name=lecture.name if lecture else "",
        student_id=r.student_id,
        student_name=student.name if student else "",
        date=session.date if session else r.created_at.date(),
        status=r.status,
        method=r.method,
        checked_in_at=r.checked_in_at,
        note=r.note,
        recorded_by=r.recorded_by,
        corrected=r.corrected,
    )


def _notify_parents(
    db: Session, academy_id: uuid.UUID, student_ids: list[uuid.UUID], kind, title_for, body_for
) -> None:
    parents = notifications.parent_users_of(db, academy_id, student_ids)
    names = dict(
        db.execute(select(Student.id, Student.name).where(Student.id.in_(student_ids)))
        .tuples()
        .all()
    )
    for sid, user_ids in parents.items():
        notifications.notify(
            db,
            academy_id=academy_id,
            user_ids=user_ids,
            kind=kind,
            title=title_for(names.get(sid, "")),
            body=body_for(names.get(sid, "")),
            link=f"/parent/children/{sid}/attendance",
        )


# ── 교사: 출석 시작·QR·명단·수동·마감 ─────────────


def open_attendance(db: Session, user: CurrentUser, session_id: uuid.UUID) -> LectureSessionOut:
    session = require_session(db, user, session_id)
    _require_manager(db, user, session)
    if session.status == SessionStatus.CANCELLED:
        raise conflict("session_cancelled", "휴강한 회차입니다")
    if session.status == SessionStatus.CLOSED:
        raise conflict("attendance_closed", "이미 마감한 회차입니다")
    outcome = _outcome(session, clock.now())
    if outcome == CheckInOutcome.TOO_EARLY:
        raise conflict("too_early", "수업 시작 15분 전부터 출석을 받을 수 있습니다")
    if outcome == CheckInOutcome.CLOSED:
        raise conflict("attendance_closed", "수업 시간이 끝났습니다")
    if session.status != SessionStatus.OPEN:
        session.status = SessionStatus.OPEN
        session.attendance_opened_at = clock.now()
        session.attendance_opened_by = user.id
        db.commit()
    return session_out(db, session)


def get_qr(db: Session, user: CurrentUser, session_id: uuid.UUID) -> QrTokenOut:
    session = require_session(db, user, session_id)
    _require_manager(db, user, session)
    if session.status != SessionStatus.OPEN:
        raise conflict("attendance_not_open", "먼저 출석을 시작하세요")
    s = get_settings()
    now = clock.now()
    issued = issue_token(session.id, s.qr_secret, s.qr_rotate_seconds, now)
    return QrTokenOut(
        token=issued.token,
        scan_url=f"{s.frontend_url}/student/check-in?t={issued.token}",
        expires_at=issued.expires_at,
        refresh_in_seconds=max(1, int((issued.expires_at - now).total_seconds())),
    )


def get_roster(db: Session, user: CurrentUser, session_id: uuid.UUID) -> SessionRoster:
    session = require_session(db, user, session_id)
    _require_manager(db, user, session)
    return _roster(db, session)


def _roster(db: Session, session: LectureSession) -> SessionRoster:
    lecture = _lecture(db, session)
    targets = session_student_ids(db, session)
    records = {
        r.student_id: r
        for r in db.scalars(
            select(AttendanceRecord).where(AttendanceRecord.session_id == session.id)
        )
    }
    shared = set(
        db.scalars(
            select(AttendanceRecord.device_id)
            .where(
                AttendanceRecord.session_id == session.id, AttendanceRecord.device_id.is_not(None)
            )
            .group_by(AttendanceRecord.device_id)
            .having(func.count() > 1)
        )
    )
    ids = list(dict.fromkeys([*targets, *records.keys()]))
    names = dict(
        db.execute(select(Student.id, Student.name).where(Student.id.in_(ids))).tuples().all()
    )
    items = []
    for sid in sorted(ids, key=lambda i: names.get(i, "")):
        r = records.get(sid)
        items.append(
            RosterItem(
                student_id=sid,
                student_name=names.get(sid, ""),
                status=r.status if r else None,
                method=r.method if r else None,
                checked_in_at=r.checked_in_at if r else None,
                shared_device=bool(r and r.device_id in shared),
            )
        )
    by_status = [i.status for i in items]
    return SessionRoster(
        session_id=session.id,
        lecture_name=lecture.name,
        starts_at=session.starts_at,
        ends_at=session.ends_at,
        is_open=session.status == SessionStatus.OPEN,
        present_count=by_status.count(AttendanceStatus.PRESENT),
        late_count=by_status.count(AttendanceStatus.LATE),
        absent_count=by_status.count(AttendanceStatus.ABSENT),
        pending_count=by_status.count(None),
        items=items,
    )


def mark_manually(
    db: Session, user: CurrentUser, session_id: uuid.UUID, student_id: uuid.UUID, body: ManualMark
) -> AttendanceOut:
    session = require_session(db, user, session_id)
    lecture = _require_manager(db, user, session)
    if student_id not in session_student_ids(db, session):
        raise bad_request("not_enrolled", "이 회차의 출석 대상이 아닙니다")
    record = db.scalar(
        select(AttendanceRecord).where(
            AttendanceRecord.session_id == session.id, AttendanceRecord.student_id == student_id
        )
    )
    if record is None:
        record = AttendanceRecord(
            academy_id=user.academy_id,
            session_id=session.id,
            lecture_id=lecture.id,
            student_id=student_id,
            status=body.status,
            method=CheckInMethod.MANUAL,
            checked_in_at=clock.now()
            if body.status in (AttendanceStatus.PRESENT, AttendanceStatus.LATE)
            else None,
            note=body.note,
            recorded_by=user.id,
        )
        db.add(record)
        db.flush()
    elif record.status != body.status or record.note != body.note:
        before = {"status": record.status.value, "method": record.method.value}
        record.status = body.status
        record.note = body.note
        record.recorded_by = user.id
        record.corrected = True
        audit.record(
            db,
            academy_id=user.academy_id,
            actor=user,
            action="attendance.manual_change",
            entity_type="attendance",
            entity_id=record.id,
            before=before,
            after={"status": body.status.value},
            reason=body.note,
        )
    db.commit()
    return _out(db, record)


def close_attendance(db: Session, user: CurrentUser, session_id: uuid.UUID) -> SessionRoster:
    session = require_session(db, user, session_id)
    _require_manager(db, user, session)
    return close_session(db, session, actor=user)


def close_session(db: Session, session: LectureSession, actor: CurrentUser | None) -> SessionRoster:
    """미출석자를 결석으로 기록하고 학부모 알림·결석 알림을 만든다. 워커의 자동 마감도 이 함수를 쓴다."""
    if session.status == SessionStatus.CANCELLED:
        raise conflict("session_cancelled", "휴강한 회차입니다")
    if session.status == SessionStatus.CLOSED:
        return _roster(db, session)
    lecture = _lecture(db, session)
    checked = set(
        db.scalars(
            select(AttendanceRecord.student_id).where(AttendanceRecord.session_id == session.id)
        )
    )
    absent = [sid for sid in session_student_ids(db, session) if sid not in checked]
    for sid in absent:
        db.add(
            AttendanceRecord(
                academy_id=session.academy_id,
                session_id=session.id,
                lecture_id=lecture.id,
                student_id=sid,
                status=AttendanceStatus.ABSENT,
                method=CheckInMethod.AUTO_ABSENT,
            )
        )
    session.status = SessionStatus.CLOSED
    session.attendance_closed_at = clock.now()

    if absent:
        # 형제가 함께 결석했으면 알림 한 건으로 묶는다
        households = dict(
            db.execute(select(Student.id, Student.household_id).where(Student.id.in_(absent)))
            .tuples()
            .all()
        )
        groups: dict[object, list[uuid.UUID]] = {}
        for sid in absent:
            key = households.get(sid) or sid
            groups.setdefault(key, []).append(sid)
        now = clock.now()
        for members in groups.values():
            db.add(
                AttendanceAlert(
                    academy_id=session.academy_id,
                    kind=AlertKind.SIBLING_ABSENCE
                    if len(members) > 1
                    else AlertKind.UNEXCUSED_ABSENCE,
                    session_id=session.id,
                    student_ids=members,
                    status=AlertStatus.OPEN,
                    parent_notified_at=now,
                )
            )
        when = local_time(db, session.academy_id, session.starts_at).strftime("%H:%M")
        _notify_parents(
            db,
            session.academy_id,
            absent,
            NotificationKind.ABSENCE,
            lambda name: f"{name} 학생 결석",
            lambda name: (
                f"{lecture.name} ({when}) 수업에 출석이 확인되지 않았습니다. 사정이 있으면 학원에 알려 주세요."
            ),
        )
    db.commit()
    return _roster(db, session)


# ── 학생: QR 체크인 ─────────────────────────────────


def check_in(db: Session, user: CurrentUser, body: CheckInBody) -> CheckInResult:
    if user.role != Role.STUDENT or user.student_id is None:
        raise forbidden("students_only", "학생 계정만 출석할 수 있습니다")
    if user.status != "active":
        raise forbidden("consent_required", "보호자 승인 후 출석할 수 있습니다")
    s = get_settings()
    now = clock.now()
    try:
        session_id = verify_token(body.token, s.qr_secret, s.qr_rotate_seconds, now)
    except InvalidQrToken as e:
        if e.reason == QrError.EXPIRED:
            raise bad_request(
                "expired_qr", "QR이 바뀌었습니다. 화면의 QR을 다시 찍어 주세요"
            ) from e
        raise bad_request("invalid_qr", "출석용 QR이 아닙니다") from e

    session = get_scoped(db, LectureSession, session_id, user)
    if session is None:  # 다른 학원의 QR
        raise bad_request("invalid_qr", "출석용 QR이 아닙니다")
    lecture = _lecture(db, session)

    existing = db.scalar(
        select(AttendanceRecord).where(
            AttendanceRecord.session_id == session.id,
            AttendanceRecord.student_id == user.student_id,
        )
    )
    if existing is not None:
        return CheckInResult(
            status=existing.status,
            lecture_name=lecture.name,
            checked_in_at=existing.checked_in_at or existing.created_at,
            already_checked_in=True,
        )

    if session.status == SessionStatus.CLOSED:
        raise conflict("attendance_closed", "출석이 마감됐습니다. 선생님께 말씀하세요")
    if session.status != SessionStatus.OPEN:
        raise conflict("attendance_not_open", "아직 출석을 받지 않는 수업입니다")
    if user.student_id not in session_student_ids(db, session):
        raise forbidden("not_enrolled", "수강 중인 강의가 아닙니다")

    outcome = _outcome(session, now)
    if outcome == CheckInOutcome.TOO_EARLY:
        raise conflict("too_early", "수업 시작 15분 전부터 출석할 수 있습니다")
    if outcome == CheckInOutcome.CLOSED:
        raise conflict("attendance_closed", "수업 시간이 끝났습니다")
    status = AttendanceStatus.LATE if outcome == CheckInOutcome.LATE else AttendanceStatus.PRESENT

    record = AttendanceRecord(
        academy_id=user.academy_id,
        session_id=session.id,
        lecture_id=lecture.id,
        student_id=user.student_id,
        status=status,
        method=CheckInMethod.QR,
        checked_in_at=now,
        device_id=body.device_id,
    )
    db.add(record)
    try:
        db.flush()
    except IntegrityError:
        # 동시에 두 번 찍은 경우: 먼저 들어간 기록을 돌려준다
        db.rollback()
        first = db.scalar(
            select(AttendanceRecord).where(
                AttendanceRecord.session_id == session.id,
                AttendanceRecord.student_id == user.student_id,
            )
        )
        assert first is not None
        return CheckInResult(
            status=first.status,
            lecture_name=lecture.name,
            checked_in_at=first.checked_in_at or now,
            already_checked_in=True,
        )

    when = local_time(db, user.academy_id, now).strftime("%H:%M")
    _notify_parents(
        db,
        user.academy_id,
        [user.student_id],
        NotificationKind.CHECK_IN,
        lambda name: f"{name} 학생 {STATUS_KO[status]}",
        lambda name: f"{when} {lecture.name} 수업에 {STATUS_KO[status]}했습니다.",
    )
    db.commit()
    return CheckInResult(status=status, lecture_name=lecture.name, checked_in_at=now)


# ── 조회·정정·결석 알림 ─────────────────────────────


def list_attendance(
    db: Session,
    user: CurrentUser,
    paging: PageParams,
    lecture_id: uuid.UUID | None,
    session_id: uuid.UUID | None,
    student_id: uuid.UUID | None,
    start: date | None,
    end: date | None,
    status: AttendanceStatus | None,
) -> Page[AttendanceOut]:
    stmt = scoped(AttendanceRecord, user).join(
        LectureSession, LectureSession.id == AttendanceRecord.session_id
    )
    if user.role == Role.TEACHER:
        stmt = stmt.where(
            AttendanceRecord.lecture_id.in_(select(Lecture.id).where(Lecture.teacher_id == user.id))
        )
    if lecture_id:
        stmt = stmt.where(AttendanceRecord.lecture_id == lecture_id)
    if session_id:
        stmt = stmt.where(AttendanceRecord.session_id == session_id)
    if student_id:
        stmt = stmt.where(AttendanceRecord.student_id == student_id)
    if start:
        stmt = stmt.where(LectureSession.date >= start)
    if end:
        stmt = stmt.where(LectureSession.date <= end)
    if status:
        stmt = stmt.where(AttendanceRecord.status == status)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(LectureSession.starts_at.desc())
        .offset((paging.page - 1) * paging.size)
        .limit(paging.size)
    )
    return Page(items=[_out(db, r) for r in rows], total=total, page=paging.page, size=paging.size)


def records_for_student(
    db: Session, academy_id: uuid.UUID, student_id: uuid.UUID, start: date | None, end: date | None
) -> list[AttendanceOut]:
    """학생 본인·학부모 화면용. 권한 확인은 호출한 쪽에서."""
    stmt = (
        select(AttendanceRecord)
        .join(LectureSession, LectureSession.id == AttendanceRecord.session_id)
        .where(AttendanceRecord.academy_id == academy_id, AttendanceRecord.student_id == student_id)
    )
    if start:
        stmt = stmt.where(LectureSession.date >= start)
    if end:
        stmt = stmt.where(LectureSession.date <= end)
    return [_out(db, r) for r in db.scalars(stmt.order_by(LectureSession.starts_at.desc()))]


def correct(
    db: Session, user: CurrentUser, attendance_id: uuid.UUID, body: AttendanceCorrection
) -> AttendanceOut:
    record = get_scoped(db, AttendanceRecord, attendance_id, user)
    if record is None:
        raise not_found("출결 기록")
    session = db.get(LectureSession, record.session_id)
    assert session is not None
    _require_manager(db, user, session)
    if record.status == body.status and record.note == body.note:
        return _out(db, record)
    before = {"status": record.status.value, "note": record.note}
    was_absent = record.status == AttendanceStatus.ABSENT
    record.status = body.status
    record.note = body.note
    record.corrected = True
    record.recorded_by = user.id
    audit.record(
        db,
        academy_id=user.academy_id,
        actor=user,
        action="attendance.correct",
        entity_type="attendance",
        entity_id=record.id,
        before=before,
        after={"status": body.status.value, "note": body.note},
        reason=body.reason,
    )
    if was_absent and body.status != AttendanceStatus.ABSENT:
        lecture = _lecture(db, session)
        new = STATUS_KO[body.status]
        _notify_parents(
            db,
            user.academy_id,
            [record.student_id],
            NotificationKind.ATTENDANCE_CORRECTED,
            lambda name: f"{name} 학생 출결 정정",
            lambda name: f"{session.date:%m/%d} {lecture.name} 결석이 '{new}'(으)로 정정됐습니다.",
        )
    db.commit()
    return _out(db, record)


def _alert_out(db: Session, a: AttendanceAlert) -> AttendanceAlertOut:
    session = db.get(LectureSession, a.session_id)
    lecture = db.get(Lecture, session.lecture_id) if session else None
    names = dict(
        db.execute(select(Student.id, Student.name).where(Student.id.in_(a.student_ids)))
        .tuples()
        .all()
    )
    return AttendanceAlertOut(
        id=a.id,
        kind=a.kind,
        session_id=a.session_id,
        lecture_name=lecture.name if lecture else "",
        student_ids=a.student_ids,
        student_names=[names.get(i, "") for i in a.student_ids],
        status=a.status,
        parent_notified_at=a.parent_notified_at,
        created_at=a.created_at,
        acknowledged_by=a.acknowledged_by,
        acknowledged_at=a.acknowledged_at,
        note=a.note,
    )


def list_alerts(
    db: Session, user: CurrentUser, paging: PageParams, status: AlertStatus
) -> Page[AttendanceAlertOut]:
    stmt = scoped(AttendanceAlert, user).where(AttendanceAlert.status == status)
    if user.role == Role.TEACHER:
        mine = (
            select(LectureSession.id)
            .join(Lecture, Lecture.id == LectureSession.lecture_id)
            .where(Lecture.teacher_id == user.id)
        )
        stmt = stmt.where(AttendanceAlert.session_id.in_(mine))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(AttendanceAlert.created_at.desc())
        .offset((paging.page - 1) * paging.size)
        .limit(paging.size)
    )
    return Page(
        items=[_alert_out(db, a) for a in rows], total=total, page=paging.page, size=paging.size
    )


def ack_alert(
    db: Session, user: CurrentUser, alert_id: uuid.UUID, body: AlertAck
) -> AttendanceAlertOut:
    alert = get_scoped(db, AttendanceAlert, alert_id, user)
    if alert is None:
        raise not_found("결석 알림")
    if alert.status != AlertStatus.ACKNOWLEDGED:
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_by = user.id
        alert.acknowledged_at = clock.now()
        alert.note = body.note
        db.commit()
    return _alert_out(db, alert)
