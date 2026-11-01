"""실제 Postgres에서 도는 통합 테스트 공통 준비.

DB가 없으면 건너뛴다. 로컬에서는:
    docker compose -f infra/docker/docker-compose.yml up -d
같은 서버에 acadesk_test DB를 새로 만들어 마이그레이션을 적용한다 (개발 DB는 건드리지 않음).
"""

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

from acadesk.core.config import get_settings
from acadesk.db.models import metadata
from acadesk.db.session import get_db
from acadesk.main import create_app

BACKEND = Path(__file__).resolve().parents[2]
TEST_DB = "acadesk_test"


def run_alembic(url: str, *args: str) -> None:
    cfg = Config(str(BACKEND / "alembic.ini"))
    cfg.cmd_opts = type("Opts", (), {"x": [f"url={url}"]})()  # env.py의 -x url=
    getattr(command, args[0])(cfg, *args[1:])


@pytest.fixture(scope="session")
def db_url():
    base = make_url(get_settings().database_url)
    admin = create_engine(base, isolation_level="AUTOCOMMIT")
    try:
        with admin.connect() as conn:
            conn.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB} WITH (FORCE)"))
            conn.execute(text(f"CREATE DATABASE {TEST_DB}"))
    except OperationalError:
        pytest.skip("Postgres에 연결할 수 없음 (docker compose up 필요)")
    finally:
        admin.dispose()
    url = base.set(database=TEST_DB).render_as_string(hide_password=False)
    run_alembic(url, "upgrade", "head")
    yield url
    admin = create_engine(base, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB} WITH (FORCE)"))
    admin.dispose()


@pytest.fixture(scope="session")
def engine(db_url):
    eng = create_engine(db_url)
    yield eng
    eng.dispose()


@pytest.fixture
def clean(engine):
    """테스트마다 모든 테이블을 비운다. TRUNCATE는 감사 로그 행 트리거에 걸리지 않는다."""
    names = ", ".join(t.name for t in metadata.sorted_tables)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {names} RESTART IDENTITY CASCADE"))
    yield


@pytest.fixture
def client(engine, clean):
    app = create_app()
    make_session = sessionmaker(bind=engine, expire_on_commit=False)

    def test_db():
        s = make_session()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = test_db
    with TestClient(app) as c:
        yield c
