"""FastAPI 코드에서 API 명세서를 만든다.

    cd backend && uv run python ../scripts/export_api_spec.py

결과: docs/api/openapi.json (프론트 타입 생성용), docs/api/endpoints.md (사람이 읽는 명세서)
라우터를 고치면 다시 실행해서 같이 커밋한다.
"""

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from acadesk.main import create_app

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "api"

ROLE_KO = {"owner": "원장", "manager": "실장", "teacher": "교사"}
METHOD_ORDER = ["get", "post", "put", "patch", "delete"]


def ref_name(ref: str) -> str:
    return ref.rsplit("/", 1)[-1]


def anchor(name: str) -> str:
    return "schema-" + name.lower().replace("_", "-")


def type_str(s: dict[str, Any]) -> str:
    if "$ref" in s:
        n = ref_name(s["$ref"])
        return f"[{n}](#{anchor(n)})"
    if "anyOf" in s:
        parts = [p for p in s["anyOf"] if p.get("type") != "null"]
        nullable = len(parts) < len(s["anyOf"])
        t = " \\| ".join(type_str(p) for p in parts)
        return f"{t} \\| null" if nullable else t
    if "allOf" in s and len(s["allOf"]) == 1:
        return type_str(s["allOf"][0])
    if "enum" in s:
        return " \\| ".join(f"`{v}`" for v in s["enum"])
    t = s.get("type")
    if t == "array":
        return f"{type_str(s.get('items', {}))}[]"
    if t == "object":
        extra = s.get("additionalProperties")
        if isinstance(extra, dict) and extra:
            return f"map<string, {type_str(extra)}>"
        return "object"
    fmt = s.get("format")
    if fmt:
        return f"{t} ({fmt})"
    return t or "any"


def constraints(s: dict[str, Any]) -> str:
    keys = {
        "minimum": "≥",
        "maximum": "≤",
        "exclusiveMinimum": ">",
        "minLength": "길이 ≥",
        "maxLength": "길이 ≤",
        "minItems": "개수 ≥",
        "maxItems": "개수 ≤",
        "pattern": "형식",
    }

    def num(v: Any) -> Any:
        return int(v) if isinstance(v, float) and v.is_integer() else v

    out = [f"{label} {num(s[k])}" for k, label in keys.items() if k in s]
    if "anyOf" in s:
        for p in s["anyOf"]:
            out += [f"{label} {num(p[k])}" for k, label in keys.items() if k in p]
    return ", ".join(f"`{c}`" if "형식" in c else c for c in out)


def cell(text: Any) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ") if text not in (None, "") else ""


def default_str(s: dict[str, Any]) -> str:
    if "default" not in s:
        return ""
    d = s["default"]
    if isinstance(d, (dict, list)) and len(json.dumps(d, ensure_ascii=False)) > 40:
        return "(설정 참고)"
    return f"`{json.dumps(d, ensure_ascii=False)}`"


def roles_str(op: dict[str, Any], path: str) -> str:
    roles = op.get("x-roles") or []
    if roles:
        return ", ".join(ROLE_KO[r] for r in roles)
    if "/webhooks/" in path:
        return "공개 (서명 검증)"
    if "/public/" in path:
        return "공개 (일회용 토큰)"
    return "공개"


def body_schema(op: dict[str, Any]) -> tuple[str, str] | None:
    content = op.get("requestBody", {}).get("content", {})
    for ctype, c in content.items():
        return ctype, type_str(c.get("schema", {}))
    return None


def success_response(op: dict[str, Any]) -> tuple[str, str]:
    for code, r in op.get("responses", {}).items():
        if code.startswith("2"):
            schema = r.get("content", {}).get("application/json", {}).get("schema")
            return code, type_str(schema) if schema else "(본문 없음)"
    return "", ""


def op_anchor(method: str, path: str) -> str:
    slug = path.replace("/api/v1/", "").replace("/", "-").replace("{", "").replace("}", "")
    return f"op-{method}-{slug}".lower()


def render(spec: dict[str, Any]) -> str:
    by_tag: dict[str, list[tuple[str, str, dict[str, Any]]]] = defaultdict(list)
    tag_order: list[str] = []
    for path, ops in spec["paths"].items():
        for method in METHOD_ORDER:
            if method not in ops:
                continue
            op = ops[method]
            tag = (op.get("tags") or ["기타"])[0]
            if tag not in tag_order:
                tag_order.append(tag)
            by_tag[tag].append((method, path, op))

    ops_all = [o for t in tag_order for o in by_tag[t]]
    stage_count: dict[str, int] = defaultdict(int)
    for _, _, op in ops_all:
        stage_count[op.get("x-stage", "-")] += 1

    L: list[str] = []
    L += [
        "# acadesk API 명세서",
        "",
        f"버전 {spec['info']['version']} · 엔드포인트 {len(ops_all)}개 "
        f"(MVP {stage_count['MVP']} · 확장 {stage_count['확장']} · 제안 {stage_count['제안']})",
        "",
        "> 이 문서는 `scripts/export_api_spec.py`가 백엔드 코드에서 자동으로 만든다. 직접 고치지 말고 "
        "라우터를 고친 뒤 다시 생성한다. 기계용 명세는 `docs/api/openapi.json`, "
        "서버를 켜면 `http://localhost:8000/docs`에서도 볼 수 있다.",
        "",
        "## 공통 규칙",
        "",
        "| 항목 | 내용 |",
        "|---|---|",
        "| 기본 경로 | `/api/v1` |",
        "| 인증 | `Authorization: Bearer <access_token>`. 로컬에서는 "
        "`ACADESK_AUTH_DEV_BYPASS=true`로 개발용 원장 계정 사용 |",
        "| 학원 격리 | 토큰의 `academy_id`로 모든 조회·변경 범위를 제한한다. "
        "요청 본문으로 academy_id를 받지 않는다 |",
        "| 역할 | 원장(owner) · 실장(manager) · 교사(teacher) |",
        "| 단계 | **MVP** 첫 출시 · **확장** 이후 단계 · **제안** 회의에서 채택 여부 결정 |",
        "| 목록 | `?page=1&size=20` (size 최대 100). 응답은 `{items, total, page, size}` |",
        "| 금액 | 정수(원) |",
        "| 시각 | ISO 8601, 날짜는 `YYYY-MM-DD` |",
        "| AI 작업 | 202로 `AiRun`을 돌려주고 결과는 확인 후보로만 저장. AI가 사실·발송을 확정하지 않음 |",
        "",
        "| 상태 코드 | 의미 |",
        "|---|---|",
        "| 200 / 201 / 202 / 204 | 성공 / 생성됨 / 접수됨(비동기) / 본문 없음 |",
        "| 401 | 로그인 필요, 토큰 오류 |",
        "| 403 | 역할 권한 없음 |",
        "| 404 | 없음 (다른 학원 데이터도 404) |",
        "| 409 | 상태 충돌 (예: 이미 발송된 건 취소) |",
        "| 422 | 입력 형식 오류 |",
        "| 501 | 계약만 있고 아직 구현 안 됨 |",
        "",
        "## 엔드포인트 목록",
        "",
    ]

    for tag in tag_order:
        L += [f"### {tag}", "", "| 단계 | 메서드 | 경로 | 설명 | 권한 |", "|---|---|---|---|---|"]
        for method, path, op in by_tag[tag]:
            link = f"[`{path.replace('/api/v1', '')}`](#{op_anchor(method, path)})"
            L.append(
                f"| {op.get('x-stage', '')} | {method.upper()} | {link} | "
                f"{cell(op.get('summary'))} | {roles_str(op, path)} |"
            )
        L.append("")

    L += ["## 엔드포인트 상세", ""]
    for tag in tag_order:
        L += [f"### {tag}", ""]
        for method, path, op in by_tag[tag]:
            L += [
                f'<a id="{op_anchor(method, path)}"></a>',
                "",
                f"#### {method.upper()} `{path}`",
                "",
                f"**{op.get('summary', '')}** · 단계 `{op.get('x-stage', '-')}` · "
                f"권한 {roles_str(op, path)}",
                "",
            ]
            if op.get("description"):
                L += [op["description"], ""]
            params = [p for p in op.get("parameters", []) if p.get("name") != "authorization"]
            if params:
                L += [
                    "| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |",
                    "|---|---|---|---|---|---|",
                ]
                for p in params:
                    s = p.get("schema", {})
                    desc = " ".join(x for x in [p.get("description", ""), constraints(s)] if x)
                    where = {"path": "경로", "query": "쿼리", "header": "헤더"}.get(
                        p["in"], p["in"]
                    )
                    L.append(
                        f"| `{p['name']}` | {where} | {type_str(s)} | "
                        f"{'예' if p.get('required') else ''} | {default_str(s)} | {cell(desc)} |"
                    )
                L.append("")
            b = body_schema(op)
            if b:
                ctype, t = b
                suffix = f" (`{ctype}`)" if ctype != "application/json" else ""
                L += [f"요청 본문: {t}{suffix}", ""]
            code, t = success_response(op)
            if code:
                L += [f"응답 `{code}`: {t}", ""]

    L += [
        "## 스키마",
        "",
        "요청·응답 본문의 필드. *는 필수.",
        "",
    ]
    schemas = spec.get("components", {}).get("schemas", {})
    skip = {"HTTPValidationError", "ValidationError"}
    for name in sorted(schemas, key=str.lower):
        if name in skip:
            continue
        s = schemas[name]
        L += [f'<a id="{anchor(name)}"></a>', "", f"#### {name}", ""]
        if s.get("description"):
            L += [cell(s["description"]), ""]
        if "enum" in s:
            L += ["값: " + ", ".join(f"`{v}`" for v in s["enum"]), ""]
            continue
        props = s.get("properties", {})
        if not props:
            L += [f"타입: {type_str(s)}", ""]
            continue
        req = set(s.get("required", []))
        L += ["| 필드 | 타입 | 기본값 | 설명 |", "|---|---|---|---|"]
        for field, fs in props.items():
            desc = " ".join(x for x in [fs.get("description", ""), constraints(fs)] if x)
            mark = "*" if field in req else ""
            L.append(f"| `{field}`{mark} | {type_str(fs)} | {default_str(fs)} | {cell(desc)} |")
        L.append("")
    return "\n".join(L) + "\n"


def main() -> None:
    spec = create_app().openapi()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "openapi.json").write_text(
        json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (OUT / "endpoints.md").write_text(render(spec), encoding="utf-8")
    n = sum(len(v) for v in spec["paths"].values())
    print(f"{n} operations → {OUT.relative_to(ROOT)}/endpoints.md, openapi.json")


if __name__ == "__main__":
    main()
