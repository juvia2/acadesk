"""엔드포인트 계약 테스트: 인증·역할·경로 충돌·명세 메타데이터.

서비스가 아직 없으므로 인증·권한을 통과한 요청은 501을 기대한다.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from acadesk.api.deps import get_current_user
from acadesk.core.security import CurrentUser, Role
from acadesk.main import create_app

ACADEMY = uuid.uuid4()
ANY_ID = "00000000-0000-0000-0000-000000000000"


def user_with(role: Role) -> CurrentUser:
    return CurrentUser(id=uuid.uuid4(), academy_id=ACADEMY, role=role, name="테스트")


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client_as(app):
    def make(role: Role) -> TestClient:
        app.dependency_overrides[get_current_user] = lambda: user_with(role)
        return TestClient(app)

    yield make
    app.dependency_overrides.clear()


def test_openapi_operations_have_stage(app):
    spec = app.openapi()
    for path, ops in spec["paths"].items():
        if not path.startswith("/api/v1"):
            continue
        for method, op in ops.items():
            assert op.get("x-stage") in {"MVP", "확장", "제안"}, f"{method} {path}"
            assert op.get("summary"), f"{method} {path} 요약 없음"


def test_operation_ids_unique(app):
    ids = [op["operationId"] for ops in app.openapi()["paths"].values() for op in ops.values()]
    assert len(ids) == len(set(ids))


def test_requires_login(app):
    client = TestClient(app)
    assert client.get("/api/v1/students").status_code == 401
    bad = client.get("/api/v1/students", headers={"Authorization": "Bearer nope"})
    assert bad.status_code == 401


def test_open_endpoints_skip_login(app):
    client = TestClient(app)
    assert client.get("/health").status_code == 200
    assert (
        client.post("/api/v1/auth/login", json={"email": "a", "password": "b"}).status_code == 501
    )
    token = "t" * 32
    assert client.get(f"/api/v1/public/replies/{token}").status_code == 501
    assert client.post("/api/v1/webhooks/sms/mock/delivery", json={}).status_code == 501


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("patch", "/api/v1/academy", {}),
        ("put", "/api/v1/rules/settings", {}),
        ("post", "/api/v1/users/invitations", {"email": "a@b.c", "name": "n", "role": "teacher"}),
        ("get", "/api/v1/invoices", None),
        ("get", "/api/v1/audit-logs", None),
    ],
)
def test_teacher_blocked_from_admin_endpoints(client_as, method, path, body):
    client = client_as(Role.TEACHER)
    res = client.request(method, path, json=body)
    assert res.status_code == 403


def test_teacher_can_record_attendance(client_as):
    client = client_as(Role.TEACHER)
    body = {
        "items": [
            {"student_id": ANY_ID, "class_id": ANY_ID, "date": "2026-11-02", "status": "absent"}
        ]
    }
    assert client.post("/api/v1/attendance/batch", json=body).status_code == 501


def test_owner_passes_role_checks(client_as):
    client = client_as(Role.OWNER)
    assert client.get("/api/v1/rules/settings").status_code == 501
    assert client.get("/api/v1/audit-logs").status_code == 501


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/households/suggestions",
        "/api/v1/attendance/alerts",
        "/api/v1/deposit-matches",
        "/api/v1/imports/kinds/students/fields",
    ],
)
def test_static_paths_not_captured_by_id_paths(client_as, path):
    # /{id} 경로가 먼저 잡으면 UUID 검증 실패로 422가 난다
    assert client_as(Role.OWNER).get(path).status_code == 501


def test_validation_rejects_bad_input(client_as):
    client = client_as(Role.OWNER)
    bad_month = {
        "student_id": ANY_ID,
        "billing_month": "2026/11",
        "due_date": "2026-11-10",
        "amount": 100,
    }
    assert client.post("/api/v1/invoices", json=bad_month).status_code == 422
    one_student = {"student_ids": [ANY_ID]}
    assert client.post("/api/v1/households", json=one_student).status_code == 422
