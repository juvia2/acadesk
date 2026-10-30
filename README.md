# acadesk — 학원 학부모 소통 자동화

기획: [docs/planning/기획안.md](docs/planning/기획안.md)

## 시작하기

```bash
# 백엔드 (Python 3.12, uv)
cd backend
uv sync                      # .venv 생성 + 의존성 설치 (uv.lock 기준)
uv run ruff check .          # 린트
uv run pytest                # 테스트

# 프론트엔드 (Node 22+)
cd frontend
npm install
npm run dev                  # http://localhost:3000
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
│   │   │   ├── academies/       # 학원·지점·테넌트
│   │   │   ├── students/        # 학생·학부모·연락처
│   │   │   ├── billing/         # 수납 (청구·납부·잔액)
│   │   │   ├── attendance/      # 출결
│   │   │   ├── homework/        # 과제
│   │   │   ├── rules/           # 규칙 엔진 (안내 후보 생성·중단 조건)
│   │   │   ├── messaging/       # 템플릿, 안내 후보, 발송 이력, 회신
│   │   │   ├── approvals/       # 담당자 검토·승인함
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
