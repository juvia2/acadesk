"""마이그레이션을 실제 Postgres에 적용해 본다.

DB가 없으면 건너뛴다. 로컬에서는:
    docker compose -f infra/docker/docker-compose.yml up -d
테스트는 같은 서버에 acadesk_test DB를 새로 만들어 쓴다 (개발 DB는 건드리지 않음).
"""

import uuid
from pathlib import Path

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError, IntegrityError, OperationalError

from acadesk.core.config import get_settings
from acadesk.db.models import metadata

BACKEND = Path(__file__).resolve().parents[2]
TEST_DB = "acadesk_test"


@pytest.fixture(scope="module")
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
    yield url
    admin = create_engine(base, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB} WITH (FORCE)"))
    admin.dispose()


def alembic(url: str, *args: str) -> None:
    cfg = Config(str(BACKEND / "alembic.ini"))
    cfg.cmd_opts = type("Opts", (), {"x": [f"url={url}"]})()  # env.py의 -x url=
    getattr(command, args[0])(cfg, *args[1:])


@pytest.fixture(scope="module")
def engine(db_url):
    alembic(db_url, "upgrade", "head")
    eng = create_engine(db_url)
    yield eng
    eng.dispose()


def test_models_match_migrations(engine):
    with engine.connect() as conn:
        diff = compare_metadata(MigrationContext.configure(conn), metadata)
    assert diff == [], f"모델과 마이그레이션이 다름. alembic revision --autogenerate 필요: {diff}"


def seed_academy(conn) -> uuid.UUID:
    academy = uuid.uuid4()
    conn.execute(
        text("INSERT INTO academies (id, name, timezone) VALUES (:id, 'T', 'Asia/Seoul')"),
        {"id": academy},
    )
    return academy


def test_audit_log_is_append_only(engine):
    with engine.begin() as conn:
        academy = seed_academy(conn)
        log_id = uuid.uuid4()
        conn.execute(
            text(
                "INSERT INTO audit_logs (id, academy_id, action, entity_type, entity_id) "
                "VALUES (:id, :a, 'create', 'student', :e)"
            ),
            {"id": log_id, "a": academy, "e": uuid.uuid4()},
        )
    for sql in (
        "UPDATE audit_logs SET action = 'x' WHERE id = :id",
        "DELETE FROM audit_logs WHERE id = :id",
    ):
        with pytest.raises(DBAPIError, match="수정·삭제할 수 없습니다"), engine.begin() as conn:
            conn.execute(text(sql), {"id": log_id})


def test_enum_check_rejects_unknown_value(engine):
    with pytest.raises(IntegrityError), engine.begin() as conn:
        academy = seed_academy(conn)
        conn.execute(
            text(
                "INSERT INTO students (id, academy_id, name, status) "
                "VALUES (:id, :a, '학생', 'graduated')"
            ),
            {"id": uuid.uuid4(), "a": academy},
        )


def test_downgrade_to_base_and_back(db_url, engine):
    engine.dispose()
    alembic(db_url, "downgrade", "base")
    alembic(db_url, "upgrade", "head")
