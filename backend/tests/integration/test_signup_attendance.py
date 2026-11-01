"""가입부터 QR 출결 마감까지 실제 DB로 확인한다."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text

from acadesk.core.config import get_settings
from acadesk.modules.attendance.qr import issue_token

API = "/api/v1"


class Api:
    def __init__(self, client):
        self.c = client

    def call(self, method, path, token=None, json=None, expect=200):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        res = self.c.request(method, f"{API}{path}", json=json, headers=headers)
        assert res.status_code == expect, f"{method} {path} → {res.status_code} {res.text}"
        return res.json() if res.content else None


@pytest.fixture
def api(client):
    return Api(client)


def iso(dt: datetime) -> str:
    return dt.isoformat()


def register(api: Api, name="행복수학", email="owner@a.kr") -> str:
    res = api.call(
        "post",
        "/auth/academies",
        json={"academy_name": name, "owner_name": "원장", "email": email, "password": "password1"},
        expect=201,
    )
    return res["access_token"]


def new_student(api: Api, owner: str, name: str, birth: str, phone: str) -> str:
    res = api.call(
        "post",
        "/students",
        owner,
        json={
            "name": name,
            "grade": "중2",
            "birth_date": birth,
            "guardians": [
                {"new_guardian": {"name": f"{name} 보호자", "phone": phone}, "relation": "모"}
            ],
        },
        expect=201,
    )
    return res["id"]


def signup(api: Api, code: str, email: str, name: str, expect=201, phone=None) -> dict:
    return api.call(
        "post",
        "/auth/signup",
        json={
            "code": code,
            "name": name,
            "email": email,
            "password": "password1",
            "agree_terms": True,
            "phone": phone,
        },
        expect=expect,
    )


def codes_by(invitations: list[dict]) -> dict[tuple[str, str], str]:
    return {(i["student_id"], i["role"]): i["code"] for i in invitations}


@pytest.fixture
def academy(api: Api):
    """원장, 교사, 학생 3명(민준·하준·서연), 강의 1개를 만든다."""
    owner = register(api)
    inv = api.call(
        "post", "/invitations", owner, json={"role": "teacher", "email": "t@a.kr"}, expect=201
    )
    teacher = signup(api, inv["code"], "t@a.kr", "김선생")["access_token"]

    minjun = new_student(api, owner, "이민준", "2010-03-01", "010-1111-2222")
    hajun = new_student(api, owner, "이하준", "2016-05-05", "010-3333-4444")  # 만 14세 미만
    seoyeon = new_student(api, owner, "박서연", "2010-07-07", "010-5555-6666")
    codes = codes_by(
        api.call(
            "post",
            "/invitations/bulk",
            owner,
            json={"student_ids": [minjun, hajun, seoyeon]},
            expect=201,
        )
    )

    me = api.call("get", "/auth/me", teacher)
    lecture = api.call(
        "post",
        "/lectures",
        owner,
        json={"name": "중2 수학 A", "teacher_id": me["id"]},
        expect=201,
    )
    api.call(
        "post",
        f"/lectures/{lecture['id']}/students",
        owner,
        json={"student_ids": [minjun, hajun, seoyeon]},
    )
    return {
        "owner": owner,
        "teacher": teacher,
        "teacher_id": me["id"],
        "lecture": lecture["id"],
        "students": {"minjun": minjun, "hajun": hajun, "seoyeon": seoyeon},
        "codes": codes,
    }


def new_session(api: Api, teacher: str, lecture: str, started_min_ago=5, length=90) -> str:
    start = datetime.now(UTC) - timedelta(minutes=started_min_ago)
    res = api.call(
        "post",
        "/lecture-sessions",
        teacher,
        json={
            "lecture_id": lecture,
            "starts_at": iso(start),
            "ends_at": iso(start + timedelta(minutes=length)),
            "kind": "regular",
        },
        expect=201,
    )
    return res["id"]


def test_full_flow(api: Api, academy, engine):
    s, codes = academy["students"], academy["codes"]

    # 학생 가입: 민준은 바로 활성, 하준은 만 14세 미만이라 보호자 승인 대기
    minjun = signup(api, codes[(s["minjun"], "student")], "mj@a.kr", "이민준")
    assert minjun["status"] == "active"
    hajun = signup(api, codes[(s["hajun"], "student")], "hj@a.kr", "이하준")
    assert hajun["status"] == "pending_guardian_consent"

    # 학부모 가입 → 둘째(하준) 추가 → 하준 계정 승인
    parent = signup(api, codes[(s["minjun"], "parent")], "mom@a.kr", "민준맘")["access_token"]
    me = api.call("get", "/auth/me", parent)
    assert me["home"] == "/parent" and [c["name"] for c in me["children"]] == ["이민준"]
    child = api.call(
        "post", "/children", parent, json={"code": codes[(s["hajun"], "parent")]}, expect=201
    )
    assert child["account_status"] == "pending_consent"
    approved = api.call("post", f"/children/{s['hajun']}/approve-account", parent)
    assert approved["account_status"] == "active"
    assert {c["name"] for c in api.call("get", "/children", parent)} == {"이민준", "이하준"}

    # 출석 시작 → QR
    session = new_session(api, academy["teacher"], academy["lecture"])
    opened = api.call("post", f"/lecture-sessions/{session}/attendance/open", academy["teacher"])
    assert opened["status"] == "open" and opened["enrolled_count"] == 3
    qr = api.call("get", f"/lecture-sessions/{session}/attendance/qr", academy["teacher"])
    assert qr["scan_url"].endswith(qr["token"]) and 0 < qr["refresh_in_seconds"] <= 30

    # 민준 출석, 두 번 찍으면 첫 기록
    body = {"token": qr["token"], "device_id": "phone-mj"}
    first = api.call("post", "/attendance/check-in", minjun["access_token"], json=body)
    assert first["status"] == "present" and first["already_checked_in"] is False
    again = api.call("post", "/attendance/check-in", minjun["access_token"], json=body)
    assert again["already_checked_in"] is True and again["checked_in_at"] == first["checked_in_at"]

    # 하준의 예전 토큰은 승인 전 상태 → 거부. 토큰을 갱신하면 출석 가능
    stale = api.call(
        "post",
        "/attendance/check-in",
        hajun["access_token"],
        json={"token": qr["token"]},
        expect=403,
    )
    assert stale is not None
    fresh = api.call("post", "/auth/refresh", json={"refresh_token": hajun["refresh_token"]})
    ok = api.call(
        "post", "/attendance/check-in", fresh["access_token"], json={"token": qr["token"]}
    )
    assert ok["status"] == "present"

    roster = api.call("get", f"/lecture-sessions/{session}/attendance", academy["teacher"])
    assert (roster["present_count"], roster["pending_count"]) == (2, 1)

    # 마감 → 서연 결석, 결석 알림
    closed = api.call("post", f"/lecture-sessions/{session}/attendance/close", academy["teacher"])
    assert (closed["present_count"], closed["absent_count"], closed["pending_count"]) == (2, 1, 0)
    alerts = api.call("get", "/attendance/alerts", academy["owner"])
    assert alerts["total"] == 1 and alerts["items"][0]["student_names"] == ["박서연"]
    # 마감 뒤 QR 출석은 거부, 이미 찍은 학생은 기록 그대로
    late = api.call("post", "/attendance/check-in", minjun["access_token"], json=body)
    assert late["already_checked_in"] is True

    # 학부모 알림: 민준·하준 출석 알림 2건 (서연 보호자는 미가입)
    with engine.connect() as conn:
        kinds = conn.execute(
            text("SELECT kind, title FROM notifications ORDER BY created_at")
        ).all()
    assert [k for k, _ in kinds] == ["check_in", "check_in"]
    assert {t for _, t in kinds} == {"이민준 학생 출석", "이하준 학생 출석"}

    # 정정: 서연 결석 → 인정 결석, 감사 로그
    records = api.call("get", f"/attendance?session_id={session}&status=absent", academy["teacher"])
    absent_id = records["items"][0]["id"]
    fixed = api.call(
        "patch",
        f"/attendance/{absent_id}",
        academy["teacher"],
        json={"status": "excused", "reason": "병원 진료 사전 연락 누락"},
    )
    assert fixed["status"] == "excused" and fixed["corrected"] is True
    with engine.connect() as conn:
        actions = conn.execute(text("SELECT action FROM audit_logs")).scalars().all()
    assert "attendance.correct" in actions and "student.guardian_consent" in actions

    # 학부모는 자기 자녀 출결만
    mine = api.call("get", f"/children/{s['minjun']}/attendance", parent)
    assert len(mine) == 1 and mine[0]["checked_in_at"]
    api.call("get", f"/children/{s['seoyeon']}/attendance", parent, expect=404)


def test_qr_rejections(api: Api, academy):
    s, codes = academy["students"], academy["codes"]
    student = signup(api, codes[(s["minjun"], "student")], "mj@a.kr", "이민준")["access_token"]
    session = new_session(api, academy["teacher"], academy["lecture"])
    path = "/attendance/check-in"

    # 출석 시작 전
    token = issue_token(uuid.UUID(session), get_settings().qr_secret).token
    res = api.call("post", path, student, json={"token": token}, expect=409)
    assert res["code"] == "attendance_not_open"

    api.call("post", f"/lecture-sessions/{session}/attendance/open", academy["teacher"])
    # 위조
    res = api.call("post", path, student, json={"token": token[:-4] + "AAAA"}, expect=400)
    assert res["code"] == "invalid_qr"
    # 2분 전 사진
    old = issue_token(
        uuid.UUID(session), get_settings().qr_secret, now=datetime.now(UTC) - timedelta(minutes=2)
    ).token
    res = api.call("post", path, student, json={"token": old}, expect=400)
    assert res["code"] == "expired_qr"
    # 다른 학원 회차의 QR (서명은 맞지만 이 학원 회차가 아님)
    other = issue_token(uuid.uuid4(), get_settings().qr_secret).token
    res = api.call("post", path, student, json={"token": other}, expect=400)
    assert res["code"] == "invalid_qr"

    # 수강생이 아니면 거부
    api.call(
        "delete",
        f"/lectures/{academy['lecture']}/students/{s['minjun']}",
        academy["owner"],
        expect=204,
    )
    res = api.call("post", path, student, json={"token": token}, expect=403)
    assert res["code"] == "not_enrolled"


def test_late_check_in(api: Api, academy):
    s, codes = academy["students"], academy["codes"]
    student = signup(api, codes[(s["minjun"], "student")], "mj@a.kr", "이민준")["access_token"]
    session = new_session(api, academy["teacher"], academy["lecture"], started_min_ago=20)
    api.call("post", f"/lecture-sessions/{session}/attendance/open", academy["teacher"])
    qr = api.call("get", f"/lecture-sessions/{session}/attendance/qr", academy["teacher"])
    res = api.call("post", "/attendance/check-in", student, json={"token": qr["token"]})
    assert res["status"] == "late"


def test_too_early_and_teacher_scope(api: Api, academy):
    session = new_session(api, academy["teacher"], academy["lecture"], started_min_ago=-60)
    res = api.call(
        "post", f"/lecture-sessions/{session}/attendance/open", academy["teacher"], expect=409
    )
    assert res["code"] == "too_early"

    # 담당이 아닌 교사는 출석을 열 수 없다
    inv = api.call("post", "/invitations", academy["owner"], json={"role": "teacher"}, expect=201)
    other = signup(api, inv["code"], "t2@a.kr", "박선생")["access_token"]
    now_session = new_session(api, academy["teacher"], academy["lecture"])
    res = api.call("post", f"/lecture-sessions/{now_session}/attendance/open", other, expect=403)
    assert res["code"] == "not_lecture_teacher"


def test_invitation_rules(api: Api, academy):
    s, codes = academy["students"], academy["codes"]
    code = codes[(s["minjun"], "student")]
    preview = api.call("get", f"/auth/invitations/{code}")
    assert preview == {**preview, "role": "student", "student_name_masked": "이*준"}

    signup(api, code, "mj@a.kr", "이민준")
    again = signup(api, code, "mj2@a.kr", "이민준", expect=400)
    assert again["code"] == "invalid_code"

    # 폐기한 코드
    inv = api.call(
        "post",
        "/invitations",
        academy["owner"],
        json={"role": "parent", "student_id": s["seoyeon"]},
        expect=201,
    )
    api.call("delete", f"/invitations/{inv['id']}", academy["owner"], expect=204)
    assert signup(api, inv["code"], "x@a.kr", "x", expect=400)["code"] == "invalid_code"

    # 같은 보호자로 두 번 가입하면 '자녀 추가'로 안내
    parent_code = codes[(s["minjun"], "parent")]
    signup(api, parent_code, "mom@a.kr", "민준맘")
    inv2 = api.call(
        "post",
        "/invitations",
        academy["owner"],
        json={
            "role": "parent",
            "student_id": s["minjun"],
            "guardian_id": api.call("get", f"/students/{s['minjun']}", academy["owner"])[
                "guardians"
            ][0]["guardian"]["id"],
        },
        expect=201,
    )
    dup = signup(api, inv2["code"], "mom2@a.kr", "민준맘", expect=409)
    assert dup["code"] == "guardian_has_account"

    # 이메일 중복
    inv3 = api.call("post", "/invitations", academy["owner"], json={"role": "teacher"}, expect=201)
    assert signup(api, inv3["code"], "mj@a.kr", "x", expect=409)["code"] == "email_taken"

    # 교사는 초대 코드를 만들 수 없다
    api.call("post", "/invitations", academy["teacher"], json={"role": "teacher"}, expect=403)


def test_login_and_refresh_rotation(api: Api):
    register(api)
    bad = api.call(
        "post", "/auth/login", json={"email": "owner@a.kr", "password": "nope"}, expect=401
    )
    assert bad["code"] == "invalid_credentials"
    tokens = api.call("post", "/auth/login", json={"email": "OWNER@a.kr", "password": "password1"})
    me = api.call("get", "/auth/me", tokens["access_token"])
    assert me["role"] == "owner" and me["home"] == "/admin"

    new = api.call("post", "/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    reused = api.call(
        "post", "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}, expect=401
    )
    assert reused["code"] == "invalid_refresh_token"
    api.call(
        "post",
        "/auth/logout",
        new["access_token"],
        json={"refresh_token": new["refresh_token"]},
        expect=204,
    )
    api.call("post", "/auth/refresh", json={"refresh_token": new["refresh_token"]}, expect=401)


def test_academies_are_isolated(api: Api, academy):
    other_owner = register(api, "다른학원", "b@b.kr")
    s = academy["students"]["minjun"]
    api.call("get", f"/students/{s}", other_owner, expect=404)
    session = new_session(api, academy["teacher"], academy["lecture"])
    api.call("post", f"/lecture-sessions/{session}/attendance/open", other_owner, expect=404)
    assert api.call("get", "/students", other_owner)["total"] == 0
    # 다른 학원 학생으로 초대 코드 발급 불가
    api.call(
        "post",
        "/invitations",
        other_owner,
        json={"role": "student", "student_id": s},
        expect=404,
    )
