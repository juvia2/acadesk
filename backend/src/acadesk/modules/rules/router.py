import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from acadesk.api.deps import MVP, CurrentUserDep, access
from acadesk.core.errors import not_implemented
from acadesk.core.schemas import Page, PageParams, page_params
from acadesk.core.security import STAFF_ADMIN, Role

from .schemas import RuleRunCreate, RuleRunOut, RuleSettings

router = APIRouter(prefix="/rules", tags=["규칙 엔진"])


@router.get("/settings", summary="안내 규칙 설정 조회", **access(MVP, *STAFF_ADMIN))
def get_rule_settings(user: CurrentUserDep) -> RuleSettings:
    raise not_implemented()


@router.put(
    "/settings",
    summary="안내 규칙 설정 저장",
    description="기준값은 코드 상수가 아니라 학원별 설정이다. 변경 내역은 감사 로그에 남는다.",
    **access(MVP, Role.OWNER),
)
def put_rule_settings(user: CurrentUserDep, body: RuleSettings) -> RuleSettings:
    raise not_implemented()


@router.post(
    "/runs",
    summary="규칙 엔진 수동 실행",
    description="평소에는 Celery beat가 매일 정해진 시각에 실행한다. dry_run으로 결과를 미리 볼 수 있다.",
    status_code=status.HTTP_202_ACCEPTED,
    **access(MVP, *STAFF_ADMIN),
)
def create_run(user: CurrentUserDep, body: RuleRunCreate) -> RuleRunOut:
    raise not_implemented()


@router.get("/runs", summary="실행 기록", **access(MVP, *STAFF_ADMIN))
def list_runs(
    user: CurrentUserDep, paging: Annotated[PageParams, Depends(page_params)]
) -> Page[RuleRunOut]:
    raise not_implemented()


@router.get("/runs/{run_id}", summary="실행 결과", **access(MVP, *STAFF_ADMIN))
def get_run(user: CurrentUserDep, run_id: uuid.UUID) -> RuleRunOut:
    raise not_implemented()


routers = [router]
