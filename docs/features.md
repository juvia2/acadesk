# acadesk 기능 정리

## 인증 / 권한 / 테넌트

`MVP` · 담당: 미정

<aside>
📁

- backend/src/acadesk/core/security.py
- backend/src/acadesk/core/config.py
- backend/src/acadesk/api/deps.py
</aside>

<aside>
💡 기획 요구: 원장·실장·교사 권한 분리, 학원별 데이터 격리
</aside>

<aside>
➡️

- 로그인 사용자에서 academy_id와 역할을 꺼내는 의존성 하나를 모든 라우터가 쓰게 함
- 단계별 승인 권한(3단계 수납 = 원장·실장)을 역할 검사 함수로 한 곳에 모음
</aside>

## 기록 업로드 / 검증

`MVP` · 담당: Olivia (제안)

<aside>
📁

- backend/src/acadesk/modules/imports/
- backend/src/acadesk/integrations/storage/
- backend/src/acadesk/api/v1/imports.py
</aside>

<aside>
💡 기획 요구: CSV·엑셀 입력, 기록 갱신이 늦거나 틀린 데이터로 오발송 방지
</aside>

<aside>
➡️

- 업로드 1회 = import_batch 1건, 행마다 오류를 모아 '확인 필요함'으로 보냄 (전체 실패 X)
- 원본 파일은 비공개 저장소에 두고 만료 정책 적용
- 같은 파일 재업로드 시 중복 생성 안 되게 외부 키(학생번호+청구월 등)로 upsert
</aside>

## 학원 / 학생 / 학부모

`MVP` · 담당: Olivia (제안)

<aside>
📁

- backend/src/acadesk/modules/academies/
- backend/src/acadesk/modules/students/
</aside>

<aside>
💡 기획 요구: 수신자 정보는 원본 데이터에서만, 연락처는 개인정보
</aside>

<aside>
➡️

- 모든 테이블에 academy_id 필수
- 학생–보호자 1:N, 수신 동의와 기본 수신자 표시
- 연락처 컬럼 암호화, 화면에는 마스킹
- 보호자마다 수신 언어(preferred_language, 기본 ko)를 MVP부터 둠 → 다국어 안내 연결
</aside>

## 형제 연동

`MVP (연결·묶음 안내) · 확장 (할인·합산 수납)` · 담당: lshee9008 (제안)

<aside>
📁

- backend/src/acadesk/modules/students/households.py
- backend/src/acadesk/modules/imports/ (형제 연결 후보)
- backend/src/acadesk/modules/billing/discounts.py
- backend/src/acadesk/modules/billing/allocation.py
- backend/src/acadesk/workers/send.py (발송 전 묶기 단계)
- frontend/src/app/students/[id]/ (형제 표시)
- frontend/src/app/review/ (연결 후보 확인)
</aside>

<aside>
💡 기획 요구: 학생–보호자 1:N, 학부모 1인당 하루 발송 상한, 입금자명 불일치 보류. 형제가 같이 다니는 학원이 많아 안내·수납이 학생 단위로 흩어짐
</aside>

<aside>
➡️

- 가구(household) 테이블로 형제를 묶음. 학생은 household_id를 가지고, 보호자는 학생–보호자 연결로 공유
- 연결은 자동 확정하지 않음: 업로드 때 같은 보호자 연락처가 여러 학생에 있으면 '형제로 연결할까요?' 후보 → 담당자 확인. 연결·해제는 감사 로그에 기록
- 묶음 안내 (MVP): 같은 보호자에게 같은 날 가는 안내를 한 통으로 합침. 각 건의 발송 직전 재검증은 따로 하고, 취소된 줄만 빼고 발송
- 입금자명 매칭: 가구 단위로 찾음 (형 이름으로 동생 학원비를 내는 경우)
- 합산 수납 (확장): 한 번 입금으로 형제 청구서 여러 건을 낼 때 오래된 청구부터 나눠 반영. 금액이 딱 맞지 않으면 보류하고 담당자가 배분
- 형제 할인 (확장): 학원별 규칙(예: 둘째 10%)을 청구 생성 때 할인 줄로 기록. 형제가 퇴원·휴원하면 할인 재계산 후보를 만들고 담당자가 확인
- 형제가 같은 날 함께 결석하면 결석 확인 알림을 한 건으로 (가족 일정일 가능성)
- 학생 화면·상담 전 요약에 형제 목록과 가구 전체 수납 상태를 표시
- 개인정보: 보호자가 다른 형제(재혼·조부모 양육 등)는 자동 연결하지 않음. 한 보호자에게는 그 보호자와 연결된 학생 정보만 보냄
</aside>

## 수납

`MVP` · 담당: Olivia (제안)

<aside>
📁

- backend/src/acadesk/modules/billing/
</aside>

<aside>
💡 기획 요구: 잔액 = 청구 − 납부 − 할인, 부분 납부·분납·환불·이의 시 자동 발송 보류
</aside>

<aside>
➡️

- 금액은 정수(원), 잔액은 저장하지 않고 계산하거나 납부 반영 시 함께 갱신
- 보류 사유를 enum 플래그로 저장해 규칙 엔진이 읽게 함
- 납부가 확인되면 예약된 후속 안내 취소 이벤트 발행
</aside>

## 출결

`MVP` · 담당: Olivia (제안)

<aside>
📁

- backend/src/acadesk/modules/attendance/
</aside>

<aside>
💡 기획 요구: 지각·결석·보강·사전 신고 구분, 입력 지연 가능성
</aside>

<aside>
➡️

- 상태 enum + 입력 시각(recorded_at) 저장 → 수업 시작 후 몇 분 지났는지로 '입력 지연' 판단
- 당일 무단결석은 예약 발송 말고 담당자 즉시 알림으로 분기
</aside>

## 과제

`확장` · 담당: Olivia (제안)

<aside>
📁

- backend/src/acadesk/modules/homework/
</aside>

<aside>
💡 기획 요구: 1회 미완료는 내부 기록, 반복 시에만 안내 후보
</aside>

<aside>
➡️

- 과제(마감일)와 제출 기록을 분리
- 반복 판단은 규칙 엔진에서, 과제 모듈은 사실만 기록
</aside>

## 규칙 엔진

`MVP` · 담당: lshee9008 (제안)

<aside>
📁

- backend/src/acadesk/modules/rules/engine.py
- backend/src/acadesk/modules/rules/policies/
- backend/src/acadesk/modules/rules/settings.py
</aside>

<aside>
💡 기획 요구: 상황별 발송 조건·중단 조건, 학원별로 기준 조정
</aside>

<aside>
➡️

- 사실을 넣으면 후보 목록이 나오는 순수 함수로 작성 → DB 없이 테스트
- 기준값(2주 3회 등)은 코드 상수가 아니라 학원별 설정 테이블
- 후보마다 dedupe_key(예: invoice_id+단계)를 유니크로 → 같은 단계 1회만
</aside>

## 메시지 / 템플릿 / 이력

`MVP` · 담당: lshee9008 (제안)

<aside>
📁

- backend/src/acadesk/modules/messaging/
</aside>

<aside>
💡 기획 요구: 승인된 템플릿과 변수 치환, 하루 발송 상한, 회신 시 후속 중단
</aside>

<aside>
➡️

- 템플릿은 버전 관리, 발송 건에 사용한 버전 기록
- 변수 치환은 코드가 DB 값으로 수행 (AI가 숫자를 쓰지 않음)
- 회신·정정·상담 중 상태가 생기면 같은 사유 후보를 일괄 중단
</aside>

## 담당자 승인함

`MVP` · 담당: lshee9008 (제안)

<aside>
📁

- backend/src/acadesk/modules/approvals/
- backend/src/acadesk/api/v1/approvals.py
</aside>

<aside>
💡 기획 요구: 수신자·사실·근거 확인 후 수정·보류·승인
</aside>

<aside>
➡️

- 상태: 대기 → 승인 / 수정 후 승인 / 보류 / 반려
- 승인 시점의 사실(금액·날짜)을 스냅샷으로 저장 → 발송 직전 비교 기준
- 누가 무엇을 바꿨는지 audit에 기록
</aside>

## 예약 / 발송 워커

`MVP` · 담당: lshee9008 (제안)

<aside>
📁

- backend/src/acadesk/workers/celery_app.py
- backend/src/acadesk/workers/schedule.py
- backend/src/acadesk/workers/send.py
</aside>

<aside>
💡 기획 요구: 발송 직전 최신 상태 재검증, 재시도, 중복 방지
</aside>

<aside>
➡️

- 매일 정해진 시각에 후보 생성 작업 실행 (Celery beat)
- 발송 직전 DB 재조회 → 잔액 0 또는 보류 사유가 생기면 취소
- 발송 건 ID를 멱등키로 대행사에 전달, 재시도해도 1회만 나가게
</aside>

## 문자 / 알림톡 연동

`MVP` · 담당: lshee9008 (제안)

<aside>
📁

- backend/src/acadesk/integrations/sms/base.py
- backend/src/acadesk/integrations/sms/mock.py
- backend/src/acadesk/api/v1/webhooks.py
</aside>

<aside>
💡 기획 요구: 발송 결과·회신 웹훅, 채널별 템플릿 심사
</aside>

<aside>
➡️

- 어댑터 인터페이스 + 모의 구현 먼저 → 대행사 정해지면 구현체만 추가
- 웹훅은 서명 검증 후 발송 이력 상태 갱신
</aside>

## 수납 안내 PDF

`확장` · 담당: 미정

<aside>
📁

- backend/src/acadesk/modules/documents/
</aside>

<aside>
💡 기획 요구: 3단계 승인 후에만 생성, 접근 제한 링크
</aside>

<aside>
➡️

- 승인 스냅샷 값으로 생성 (생성 시점 DB 값 X)
- 비공개 저장 + 만료되는 링크
</aside>

## 감사 로그

`MVP` · 담당: 미정

<aside>
📁

- backend/src/acadesk/modules/audit/
</aside>

<aside>
💡 기획 요구: 연락 이력 인수인계, 오발송 추적
</aside>

<aside>
➡️

- 추가만 가능한 테이블 (수정·삭제 없음)
- 누가 / 언제 / 무엇을 / 이전 값 → 이후 값
</aside>

## AI 에이전트

`확장` · 담당: lshee9008

<aside>
📁

- backend/src/acadesk/ai/orchestrator/
- backend/src/acadesk/ai/tools/
- backend/src/acadesk/workers/ (AI 작업)
</aside>

<aside>
💡 기획 요구: 제한된 에이전트, 허용 도구만, 단계별 기록. 회신 분류·후속 업무 제안, 안내문 초안, 상담 전 연락 이력 요약, 수납·출결 불일치 후보 (HANDOFF)
</aside>

<aside>
➡️

- 상태 흐름: 사실 조회 → 검색 → 초안 → 검증 → 승인함
- 작업 4종을 같은 흐름 위에 둠: 회신 분류, 안내문 초안, 상담 전 요약, 불일치 후보
- 결과는 모두 '확인 후보'로 저장하고 근거 기록 ID와 검토 상태를 함께 남김 (AI가 확정·발송하지 않음)
- 도구는 읽기 전용, academy_id는 상태에서 자동 주입
- ai_runs / ai_steps 테이블에 단계별 기록, 담당자 수정률을 지표로 남김
</aside>

## LLM / 프롬프트

`확장` · 담당: Olivia

<aside>
📁

- backend/src/acadesk/ai/prompts/
- backend/src/acadesk/ai/llm.py
- backend/src/acadesk/ai/orchestrator/validators.py
</aside>

<aside>
💡 기획 요구: AI는 사실을 정중한 문장으로 다듬기만, 민감 사유 추론 금지
</aside>

<aside>
➡️

- 프롬프트 파일마다 입력 변수와 출력 스키마를 함께 둠
- 검증: 자리 표시가 아닌 숫자·날짜, 금지어, 홍보 문구
- 평가 데이터셋으로 프롬프트 버전 비교
</aside>

## 다국어 안내 / 번역

`확장` · 담당: Olivia (번역 프롬프트·검증), lshee9008 (발송 흐름)

<aside>
📁

- backend/src/acadesk/modules/students/ (preferred_language)
- backend/src/acadesk/modules/messaging/translations.py
- backend/src/acadesk/ai/prompts/translate/
- backend/src/acadesk/ai/orchestrator/validators.py
- frontend/src/i18n/ (강사용 화면 문구)
</aside>

<aside>
💡 기획 요구: 외국인·다문화 가정 학부모와 외국인 강사. 영어 먼저 (2026-10-30 합의)
</aside>

<aside>
➡️

- 번역 단위는 발송 건이 아니라 '승인된 템플릿 버전 × 언어'. 한 번 번역하고 담당자가 확인하면 재사용 → 비용과 오역 위험 감소
- {amount} 같은 자리 표시는 번역하지 않고 그대로 두고, 값은 코드가 채움. 날짜·금액 형식만 언어별로 바꿈
- 검증: 자리 표시 개수·이름이 원문과 같은지, 원문에 없는 숫자가 생기지 않았는지
- 기본 발송은 번역문 + 한국어 원문 함께 (학원이 정확한 원문을 증명할 수 있게)
- 학부모 회신은 원문을 저장하고 한국어 번역을 승인함·학생 기록에 같이 표시
- 알림톡은 언어별 템플릿 심사가 필요한지 확인 필요
</aside>

## RAG 검색

`확장` · 담당: lshee9008

<aside>
📁

- backend/src/acadesk/ai/rag/ingest.py
- backend/src/acadesk/ai/rag/retrieve.py
</aside>

<aside>
💡 기획 요구: 학원 승인 템플릿·운영 규정·권한 있는 연락 이력만 근거로
</aside>

<aside>
➡️

- pgvector, 검색은 academy_id 필터가 강제된 함수 하나만 공개
- 근거 조각 ID를 초안과 함께 저장 → 승인함에 출처 표시
</aside>

## 담당자 웹 화면

`MVP` · 담당: Olivia (제안)

<aside>
📁

- frontend/src/app/today/
- frontend/src/app/approvals/
- frontend/src/app/review/
- frontend/src/app/students/[id]/
- frontend/src/app/settings/
</aside>

<aside>
💡 기획 요구: 오늘의 소통함, 승인함, 확인 필요함, 학생별 기록, 운영 설정
</aside>

<aside>
➡️

- API 타입은 FastAPI OpenAPI에서 자동 생성
- 승인 화면에 사실·근거·문구를 나란히 보여줌
- MVP 화면: 오늘의 소통함, 승인함, 확인 필요함, 업로드
</aside>

# 제안 기능 (회의에서 MVP / 확장 / 보류 결정)

## 학부모 원클릭 응답

`제안 · MVP 추천` · 담당: 미정

<aside>
📁

- backend/src/acadesk/modules/messaging/replies.py
- backend/src/acadesk/api/v1/public_replies.py
- frontend/src/app/r/[token]/
</aside>

<aside>
💡 기획 요구: 회신·정정이 오면 후속 발송 중단. 자유 문장 회신은 분류가 틀릴 수 있음
</aside>

<aside>
➡️

- 안내 끝에 버튼 링크: "이미 납부했어요" / "미리 알렸어요" / "상담 원해요"
- 누르면 AI 분류 없이 정확한 의도가 기록되고, 같은 사유 후속 발송 즉시 중단 + 담당자 확인 작업 생성
- 링크는 발송 건별 일회용 토큰, 로그인 없음, 개인정보 표시 없음
</aside>

## 입금자명 매칭 보조

`제안 · MVP 추천` · 담당: 미정

<aside>
📁

- backend/src/acadesk/modules/billing/matching.py
- backend/src/acadesk/modules/imports/
</aside>

<aside>
💡 기획 요구: 입금자명 불일치는 자동 발송 보류 조건. 미납이 아닌데 미납 안내가 나가는 게 가장 큰 오발송
</aside>

<aside>
➡️

- 통장 입금 내역 CSV 업로드 → 보호자 이름·형제·금액·날짜로 학생 매칭 후보 제시
- 확실하지 않으면 '확인 필요함'으로, 담당자가 한 번 연결하면 다음 달부터 자동 매칭
</aside>

## 휴원·방학 캘린더

`제안 · MVP 추천` · 담당: 미정

<aside>
📁

- backend/src/acadesk/modules/academies/calendar.py
- backend/src/acadesk/modules/rules/
</aside>

<aside>
💡 기획 요구: 휴원·퇴원 시 보류, 학원별 기준 조정
</aside>

<aside>
➡️

- 학원 휴무일·방학·공휴일과 학생별 휴원 기간을 등록
- 쉬는 날엔 결석 후보를 만들지 않음, 수납 단계(+1/+3/+7일)는 영업일 기준 옵션
</aside>

## 납부 약속 추적

`제안 · 확장` · 담당: 미정

<aside>
📁

- backend/src/acadesk/modules/billing/promises.py
- backend/src/acadesk/modules/rules/
</aside>

<aside>
💡 기획 요구: 분납 약속이 있으면 자동 발송 보류
</aside>

<aside>
➡️

- "25일에 낼게요" 같은 회신을 담당자가 약속으로 등록 (AI는 날짜 후보만 제안)
- 약속일까지 수납 안내 보류, 약속일 다음 날 납부 확인 후보 생성
</aside>

## 긴급 알림 에스컬레이션

`제안 · 확장` · 담당: 미정

<aside>
📁

- backend/src/acadesk/workers/
- backend/src/acadesk/modules/attendance/
</aside>

<aside>
💡 기획 요구: 당일 무단결석은 담당자 즉시 알림
</aside>

<aside>
➡️

- 담당 교사가 N분 안에 확인하지 않으면 실장·원장에게 다시 알림
- 확인한 사람과 시각을 감사 로그에 기록
</aside>

## 오발송 정정 안내

`제안 · 확장` · 담당: 미정

<aside>
📁

- backend/src/acadesk/modules/messaging/
- backend/src/acadesk/modules/approvals/
</aside>

<aside>
💡 기획 요구: 정정 요청 처리, 오발송 추적
</aside>

<aside>
➡️

- 발송 이력에서 건을 고르면 정정 안내 초안 + 같은 사유 후속 중단 + 원인 기록을 한 번에
- 정정 안내도 승인함을 거침
</aside>

## 담당자 아침 브리핑

`제안 · 확장` · 담당: 미정

<aside>
📁

- frontend/src/app/today/
- backend/src/acadesk/ai/ (회신 요약, 선택)
</aside>

<aside>
💡 기획 요구: 담당자 처리 시간 절감
</aside>

<aside>
➡️

- 오늘 승인할 것, 보류된 이유, 어제 들어온 회신, 확인 필요한 업로드 오류를 한 화면으로
- 처음엔 숫자·목록만, AI 요약은 나중에 추가
</aside>

## 쉬운 한국어 모드

`제안 · 확장` · 담당: Olivia (제안)

<aside>
📁

- backend/src/acadesk/ai/prompts/translate/
</aside>

<aside>
💡 기획 요구: 한국어가 서툰 보호자 (다국어 안내와 같은 대상)
</aside>

<aside>
➡️

- 번역과 같은 흐름에서 언어 코드만 ko-easy로: 짧은 문장, 어려운 한자어 대신 쉬운 말
- 템플릿 단위로 만들고 담당자 확인 후 재사용
</aside>

## 알림톡 실패 시 문자 대체

`제안 · 확장` · 담당: 미정

<aside>
📁

- backend/src/acadesk/integrations/sms/
- backend/src/acadesk/api/v1/webhooks.py
</aside>

<aside>
💡 기획 요구: 발송 결과 웹훅, 채널별 템플릿
</aside>

<aside>
➡️

- 알림톡 실패 웹훅을 받으면 같은 내용을 문자로 1회 재발송 (멱등키는 원래 발송 건 기준)
- 대체 발송 여부를 이력에 표시
</aside>
