"""학원 격리 쿼리 헬퍼.

서비스는 학원 데이터를 조회할 때 반드시 이 함수를 거친다. 다른 학원 ID로 조회하면
결과가 비어서 404가 된다 (존재 여부도 드러내지 않음). 다지점 단계에서 Postgres RLS를 추가한다.
"""

import uuid
from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from acadesk.core.security import CurrentUser


def scoped[T](model: type[T], user: CurrentUser) -> Select[tuple[T]]:
    academy_col: Any = model.academy_id  # type: ignore[attr-defined]
    return select(model).where(academy_col == user.academy_id)


def get_scoped[T](db: Session, model: type[T], obj_id: uuid.UUID, user: CurrentUser) -> T | None:
    id_col: Any = model.id  # type: ignore[attr-defined]
    return db.scalars(scoped(model, user).where(id_col == obj_id)).first()
