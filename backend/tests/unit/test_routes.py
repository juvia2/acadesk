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
            assert op.get("x-stage") in {"MVP", "2단계", "3단계"}, f"{method} {path}"
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
    assert client.get("/api/v1/auth/invitations/ABCD1234").status_code == 501
    signup = {
        "code": "ABCD1234",
        "name": "n",
        "email": "a@b.c",
        "password": "12345678",
        "agree_terms": True,
    }
    assert client.post("/api/v1/auth/signup", json=signup).status_code == 501
    assert client.post("/api/v1/webhooks/sms/mock/delivery", json={}).status_code == 501


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("patch", "/api/v1/academy", {}),
        ("put", "/api/v1/rules/settings", {}),
        ("post", "/api/v1/invitations", {"role": "teacher", "email": "a@b.c"}),
        ("get", "/api/v1/invoices", None),
        ("get", "/api/v1/audit-logs", None),
    ],
)
def test_teacher_blocked_from_admin_endpoints(client_as, method, path, body):
    client = client_as(Role.TEACHER)
    res = client.request(method, path, json=body)
    assert res.status_code == 403


def test_teacher_can_run_attendance(client_as):
    client = client_as(Role.TEACHER)
    assert client.post(f"/api/v1/lecture-sessions/{ANY_ID}/attendance/open").status_code == 501
    assert client.get(f"/api/v1/lecture-sessions/{ANY_ID}/attendance/qr").status_code == 501


def test_only_students_check_in(client_as):
    body = {"token": "x" * 20}
    assert client_as(Role.STUDENT).post("/api/v1/attendance/check-in", json=body).status_code == 501
    for role in (Role.TEACHER, Role.PARENT, Role.OWNER):
        res = client_as(role).post("/api/v1/attendance/check-in", json=body)
        assert res.status_code == 403, role


@pytest.mark.parametrize(
    ("role", "method", "path", "expected"),
    [
        # 학원 관리자·교사는 커뮤니티 글을 볼 수 없다 (기획안 v2 8-2)
        (Role.OWNER, "get", "/api/v1/community/posts", 403),
        (Role.TEACHER, "get", "/api/v1/community/posts", 403),
        (Role.PARENT, "get", "/api/v1/community/posts", 501),
        # 학원은 건의 글과 통계만
        (Role.OWNER, "get", "/api/v1/community/academy/suggestions", 501),
        (Role.PARENT, "get", "/api/v1/community/academy/suggestions", 403),
        # 신고 처리는 플랫폼 운영자만
        (Role.OWNER, "get", "/api/v1/ops/community/queue", 403),
        (Role.OPERATOR, "get", "/api/v1/ops/community/queue", 501),
        # 운영자는 학원 데이터에 접근하지 못한다
        (Role.OPERATOR, "get", "/api/v1/students", 403),
        # 학생·학부모는 직원 화면에 접근하지 못한다
        (Role.STUDENT, "get", "/api/v1/students", 403),
        (Role.PARENT, "get", "/api/v1/attendance", 403),
        (Role.PARENT, "post", "/api/v1/emergency-messages/preview", 403),
        # 리포트는 학부모 본인, 학생 화면은 학생 본인
        (Role.PARENT, "get", f"/api/v1/children/{ANY_ID}/report", 501),
        (Role.STUDENT, "get", f"/api/v1/children/{ANY_ID}/report", 403),
        (Role.STUDENT, "get", "/api/v1/me/schedule", 501),
        # 공지·알림은 구성원 모두
        (Role.STUDENT, "get", "/api/v1/notices", 501),
        (Role.PARENT, "get", "/api/v1/notifications", 501),
    ],
)
def test_v2_role_boundaries(client_as, role, method, path, expected):
    assert client_as(role).request(method, path).status_code == expected


def test_parent_and_student_can_ask(client_as):
    body = {"title": "질문", "body": "내용"}
    for role in (Role.STUDENT, Role.PARENT):
        assert client_as(role).post("/api/v1/questions", json=body).status_code == 501
    assert client_as(Role.TEACHER).post("/api/v1/questions", json=body).status_code == 403


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
        "/api/v1/questions",
        "/api/v1/emergency-messages",
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
