import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from acadesk.api.deps import MVP, CurrentUserDep, access
from acadesk.core.errors import not_implemented
from acadesk.core.schemas import Page, PageParams, page_params
from acadesk.core.security import STAFF_ADMIN

from .schemas import AuditLogOut

router = APIRouter(prefix="/audit-logs", tags=["감사 로그"])


@router.get(
    "",
    summary="감사 로그 조회",
    description="추가만 가능한 기록이라 수정·삭제 엔드포인트는 없다.",
    **access(MVP, *STAFF_ADMIN),
)
def list_audit_logs(
    user: CurrentUserDep,
    paging: Annotated[PageParams, Depends(page_params)],
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    actor_id: uuid.UUID | None = None,
    from_: Annotated[datetime | None, Query(alias="from")] = None,
    to: datetime | None = None,
) -> Page[AuditLogOut]:
    raise not_implemented()


routers = [router]
