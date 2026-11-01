"""마이그레이션 검사: 모델과 일치, 감사 로그 트리거, enum CHECK, 되돌리기."""

import uuid

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError

from acadesk.db.models import metadata

from .conftest import run_alembic


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


def test_audit_log_is_append_only(engine, clean):
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


def test_enum_check_rejects_unknown_value(engine, clean):
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
    run_alembic(db_url, "downgrade", "base")
    run_alembic(db_url, "upgrade", "head")
