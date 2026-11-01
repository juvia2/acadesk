import uuid
from typing import Any

from sqlalchemy.orm import Session

from acadesk.core.security import CurrentUser
from acadesk.modules.audit.models import AuditLog


def record(
    db: Session,
    *,
    academy_id: uuid.UUID,
    actor: CurrentUser | None,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    reason: str | None = None,
) -> None:
    """감사 로그 한 줄. 호출한 서비스의 트랜잭션에 같이 커밋된다."""
    db.add(
        AuditLog(
            academy_id=academy_id,
            actor_id=actor.id if actor else None,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            before=before,
            after=after,
            reason=reason,
        )
    )
