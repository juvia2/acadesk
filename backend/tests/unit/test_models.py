"""DB 모델 규칙 검사 (DB 없이 메타데이터만 본다)."""

import pytest
from sqlalchemy import CheckConstraint, Integer, UniqueConstraint
from sqlalchemy.orm import configure_mappers

from acadesk.db.models import metadata

NO_TENANT = {"academies", "webhook_events"}


def test_mappers_configure():
    configure_mappers()


@pytest.mark.parametrize("table", sorted(metadata.tables.values(), key=lambda t: t.name), ids=str)
def test_tenant_column(table):
    if table.name in NO_TENANT:
        return
    col = table.c.get("academy_id")
    assert col is not None, f"{table.name}에 academy_id 없음"
    assert not col.nullable
    assert {fk.column.table.name for fk in col.foreign_keys} == {"academies"}


def test_money_columns_are_integers():
    money = {
        "invoices": ["amount", "discount", "paid"],
        "payments": ["amount"],
        "payment_allocations": ["amount"],
        "bank_deposits": ["amount"],
    }
    for table, cols in money.items():
        for c in cols:
            assert isinstance(metadata.tables[table].c[c].type, Integer), f"{table}.{c}"


def unique_sets(table_name):
    t = metadata.tables[table_name]
    sets = [
        {c.name for c in con.columns} for con in t.constraints if isinstance(con, UniqueConstraint)
    ]
    sets += [{c.name for c in col_set} for col_set in ([c] for c in t.columns if c.unique)]
    return sets


@pytest.mark.parametrize(
    ("table", "cols"),
    [
        ("notice_candidates", {"academy_id", "dedupe_key"}),  # 같은 단계 안내 1회
        ("messages", {"idempotency_key"}),  # 대행사 재시도 중복 방지
        ("approvals", {"candidate_id"}),
        ("attendance_records", {"session_id", "student_id"}),  # 회차당 1건
        ("invitations", {"code_hash"}),
        ("community_reports", {"target_type", "target_id", "reporter_id"}),  # 1인 1신고
        ("community_anon_numbers", {"post_id", "number"}),
        ("users", {"student_id"}),
        ("household_suggestions", {"academy_id", "student_key"}),
        ("webhook_events", {"provider", "event_id"}),
        ("template_translations", {"template_version_id", "language"}),
    ],
)
def test_unique_rules(table, cols):
    assert cols in unique_sets(table)


def test_enum_columns_have_check_constraints():
    names = {
        con.name
        for t in metadata.tables.values()
        for con in t.constraints
        if isinstance(con, CheckConstraint)
    }
    assert any("invoicestatus" in str(n) for n in names)
    assert any("role" in str(n) for n in names)
