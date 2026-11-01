import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AuditLogOut(BaseModel):
    id: uuid.UUID
    at: datetime
    actor_id: uuid.UUID | None = None  # null = 시스템(규칙 엔진, 워커)
    actor_name: str | None = None
    action: str
    entity_type: str
    entity_id: uuid.UUID
    before: dict[str, Any] | None = None
    after: dict[str, Any] | None = None
    reason: str | None = None
