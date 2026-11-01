from collections.abc import Iterator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from acadesk.core.config import get_settings


@lru_cache
def get_engine() -> Engine:
    return create_engine(get_settings().database_url, pool_pre_ping=True)


@lru_cache
def get_sessionmaker() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """요청마다 세션 하나. 예외가 나면 롤백한다. 커밋은 서비스가 명시적으로 한다."""
    session = get_sessionmaker()()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


DbDep = Annotated[Session, Depends(get_db)]
