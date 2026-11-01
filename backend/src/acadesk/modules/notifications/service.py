"""알림 만들기. 지금은 알림함(notifications)에 저장만 하고, Web Push 발송은 워커가 붙으면 보낸다."""

import uuid
from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from acadesk.modules.academies.models import AccountStatus, User
from acadesk.modules.notifications.models import Notification
from acadesk.modules.notifications.schemas import NotificationKind
from acadesk.modules.students.models import StudentGuardian


def parent_users_of(
    db: Session, academy_id: uuid.UUID, student_ids: Iterable[uuid.UUID]
) -> dict[uuid.UUID, list[uuid.UUID]]:
    """학생별로 알림을 받을 학부모 계정 ID. 수신 설정을 끈 보호자는 뺀다."""
    rows = db.execute(
        select(StudentGuardian.student_id, User.id)
        .join(User, User.guardian_id == StudentGuardian.guardian_id)
        .where(
            StudentGuardian.academy_id == academy_id,
            StudentGuardian.student_id.in_(list(student_ids)),
            StudentGuardian.receives_notices.is_(True),
            User.status == AccountStatus.ACTIVE,
        )
    ).all()
    out: dict[uuid.UUID, list[uuid.UUID]] = {}
    for student_id, user_id in rows:
        out.setdefault(student_id, []).append(user_id)
    return out


def notify(
    db: Session,
    *,
    academy_id: uuid.UUID,
    user_ids: Iterable[uuid.UUID],
    kind: NotificationKind,
    title: str,
    body: str,
    link: str,
) -> int:
    count = 0
    for uid in set(user_ids):
        db.add(
            Notification(
                academy_id=academy_id, user_id=uid, kind=kind, title=title, body=body, link=link
            )
        )
        count += 1
    return count
