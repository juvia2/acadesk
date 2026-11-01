# acadesk — 학원 학부모 소통 자동화

기획: [docs/planning/기획안_v2.md](docs/planning/기획안_v2.md) (이전: [기획안.md](docs/planning/기획안.md)) · 작업 기준: [HANDOFF.md](HANDOFF.md)

## 시작하기

```bash
# 로컬 DB·Redis (Docker). Postgres 5433, Redis 6380
docker compose -f infra/docker/docker-compose.yml up -d

# 백엔드 (Python 3.12, uv)
cd backend
uv sync                      # .venv 생성 + 의존성 설치 (uv.lock 기준)
uv run alembic upgrade head  # DB 테이블 생성·갱신
uv run ruff check .          # 린트
uv run pytest                # 테스트
ACADESK_AUTH_DEV_BYPASS=true uv run uvicorn acadesk.main:app --reload
                             # http://localhost:8000/docs (Swagger), 개발용 원장 계정으로 로그인 생략
uv run python ../scripts/export_api_spec.py
                             # 라우터를 고친 뒤 API 명세서(docs/api/) 다시 생성

# 프론트엔드 (Node 22+)
cd frontend
npm install
npm run dev                  # http://localhost:3000
```

API 명세서: [docs/api/endpoints.md](docs/api/endpoints.md) (PDF: `docs/api/endpoints.pdf`, 기계용: `docs/api/openapi.json`)

모델을 고쳤으면 마이그레이션을 만들고 내용을 확인한 뒤 같이 커밋합니다.

```bash
cd backend
uv run alembic revision --autogenerate -m "무엇을 바꿨는지"
uv run alembic upgrade head
uv run pytest tests/integration   # 모델과 마이그레이션이 같은지 확인
```

의존성 추가는 `uv add <패키지>` / `uv add --dev <패키지>`로 하고, `uv.lock`도 함께 커밋합니다.

## 폴더 구조

```
acadesk/
├── backend/                     # Python · FastAPI (uv로 관리)
│   ├── src/acadesk/
│   │   ├── api/v1/              # 라우터 (HTTP 진입점)
│   │   ├── core/                # 설정, 인증·RBAC, 로깅
│   │   ├── db/                  # DB 세션, Base, pgvector 설정
│   │   ├── modules/             # 업무 도메인 (각 폴더에 models/schemas/service/router)
│   │   │   ├── academies/       # 학원·지점·계정·초대 코드
│   │   │   ├── lectures/        # 강의·수강·강의 회차
│   │   │   ├── students/        # 학생·보호자·형제(가구)
│   │   │   ├── billing/         # 수납 기록 (2단계), 자동 안내 관련은 3단계
│   │   │   ├── attendance/      # 강의별 QR 출결 (qr.py: 토큰·판정)
│   │   │   ├── notices/         # 공지사항
│   │   │   ├── questions/       # 질의응답·상담
│   │   │   ├── notifications/   # 앱 알림·푸시 구독
│   │   │   ├── reports/         # 학생 화면·학부모 자녀 리포트
│   │   │   ├── community/       # 학부모 익명 커뮤니티 (2단계)
│   │   │   ├── homework/        # 과제
│   │   │   ├── rules/           # 규칙 엔진 (3단계)
│   │   │   ├── messaging/       # 긴급 문자, 발송 이력 / 템플릿·안내 후보·회신(3단계)
│   │   │   ├── approvals/       # 승인함 (3단계)
│   │   │   ├── imports/         # CSV/엑셀 업로드, 데이터 검증
│   │   │   ├── documents/       # 수납 안내 PDF 생성
│   │   │   └── audit/           # 감사 로그
│   │   ├── ai/                  # 제한된 AI 에이전트
│   │   │   ├── orchestrator/    # LangGraph 상태 흐름
│   │   │   ├── tools/           # 허용 목록 기반 도구
│   │   │   ├── rag/             # 검색 계층 (academy_id 필터)
│   │   │   └── prompts/
│   │   ├── workers/             # Celery 작업 (예약·재시도·발송 직전 재검증)
│   │   └── integrations/
│   │       ├── sms/             # 문자·알림톡 발송 대행 API, 웹훅
│   │       └── storage/         # 비공개 객체 저장소
│   ├── migrations/              # Alembic
│   └── tests/                   # unit / integration / fixtures
├── frontend/                    # Next.js · React · TypeScript · Tailwind (담당자 웹 앱)
├── infra/docker/                # Dockerfile, docker-compose (Postgres, Redis)
├── data/samples/                # 가상·익명화 샘플 데이터만 (실데이터 금지)
├── docs/
│   ├── planning/                # 기획 문서
│   └── adr/                     # 설계 결정 기록
├── scripts/                     # 시드·유틸 스크립트
└── .github/workflows/           # GitHub Actions CI
```
