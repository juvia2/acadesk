# acadesk API 명세서

버전 0.1.0 · 엔드포인트 132개 (MVP 95 · 확장 23 · 제안 13)

> 이 문서는 `scripts/export_api_spec.py`가 백엔드 코드에서 자동으로 만든다. 직접 고치지 말고 라우터를 고친 뒤 다시 생성한다. 기계용 명세는 `docs/api/openapi.json`, 서버를 켜면 `http://localhost:8000/docs`에서도 볼 수 있다.

## 공통 규칙

| 항목 | 내용 |
|---|---|
| 기본 경로 | `/api/v1` |
| 인증 | `Authorization: Bearer <access_token>`. 로컬에서는 `ACADESK_AUTH_DEV_BYPASS=true`로 개발용 원장 계정 사용 |
| 학원 격리 | 토큰의 `academy_id`로 모든 조회·변경 범위를 제한한다. 요청 본문으로 academy_id를 받지 않는다 |
| 역할 | 원장(owner) · 실장(manager) · 교사(teacher) |
| 단계 | **MVP** 첫 출시 · **확장** 이후 단계 · **제안** 회의에서 채택 여부 결정 |
| 목록 | `?page=1&size=20` (size 최대 100). 응답은 `{items, total, page, size}` |
| 금액 | 정수(원) |
| 시각 | ISO 8601, 날짜는 `YYYY-MM-DD` |
| AI 작업 | 202로 `AiRun`을 돌려주고 결과는 확인 후보로만 저장. AI가 사실·발송을 확정하지 않음 |

| 상태 코드 | 의미 |
|---|---|
| 200 / 201 / 202 / 204 | 성공 / 생성됨 / 접수됨(비동기) / 본문 없음 |
| 401 | 로그인 필요, 토큰 오류 |
| 403 | 역할 권한 없음 |
| 404 | 없음 (다른 학원 데이터도 404) |
| 409 | 상태 충돌 (예: 이미 발송된 건 취소) |
| 422 | 입력 형식 오류 |
| 501 | 계약만 있고 아직 구현 안 됨 |

## 엔드포인트 목록

### 인증

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| MVP | POST | [`/auth/login`](#op-post-auth-login) | 로그인 | 공개 |
| MVP | POST | [`/auth/refresh`](#op-post-auth-refresh) | 토큰 갱신 | 공개 |
| MVP | POST | [`/auth/logout`](#op-post-auth-logout) | 로그아웃 (리프레시 토큰 폐기) | 원장, 실장, 교사 |
| MVP | GET | [`/auth/me`](#op-get-auth-me) | 내 정보·역할 | 원장, 실장, 교사 |

### 오늘의 소통함

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| MVP | GET | [`/dashboard/today`](#op-get-dashboard-today) | 오늘의 소통함 요약 | 원장, 실장, 교사 |
| 제안 | GET | [`/dashboard/briefing`](#op-get-dashboard-briefing) | 담당자 아침 브리핑 | 원장, 실장, 교사 |
| MVP | GET | [`/review-items`](#op-get-review-items) | 확인 필요함 | 원장, 실장, 교사 |

### 학원

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| MVP | GET | [`/academy`](#op-get-academy) | 내 학원 정보 | 원장, 실장, 교사 |
| MVP | PATCH | [`/academy`](#op-patch-academy) | 학원 정보 수정 | 원장 |
| MVP | GET | [`/academy/branches`](#op-get-academy-branches) | 지점 목록 | 원장, 실장, 교사 |
| MVP | POST | [`/academy/branches`](#op-post-academy-branches) | 지점 추가 | 원장 |
| MVP | PATCH | [`/academy/branches/{branch_id}`](#op-patch-academy-branches-branch_id) | 지점 수정 | 원장 |
| 제안 | GET | [`/academy/calendar`](#op-get-academy-calendar) | 휴원·방학·공휴일 목록 | 원장, 실장, 교사 |
| 제안 | POST | [`/academy/calendar`](#op-post-academy-calendar) | 휴원·방학·공휴일 등록 | 원장, 실장 |
| 제안 | DELETE | [`/academy/calendar/{event_id}`](#op-delete-academy-calendar-event_id) | 휴원·방학·공휴일 삭제 | 원장, 실장 |

### 사용자

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| MVP | GET | [`/users`](#op-get-users) | 직원 목록 | 원장, 실장 |
| MVP | POST | [`/users/invitations`](#op-post-users-invitations) | 직원 초대 | 원장 |
| MVP | PATCH | [`/users/{user_id}`](#op-patch-users-user_id) | 직원 역할·정보 수정 | 원장 |
| MVP | DELETE | [`/users/{user_id}`](#op-delete-users-user_id) | 직원 비활성화 | 원장 |

### 반

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| MVP | GET | [`/classes`](#op-get-classes) | 반 목록 | 원장, 실장, 교사 |
| MVP | POST | [`/classes`](#op-post-classes) | 반 만들기 | 원장, 실장 |
| MVP | GET | [`/classes/{class_id}`](#op-get-classes-class_id) | 반 상세 | 원장, 실장, 교사 |
| MVP | PATCH | [`/classes/{class_id}`](#op-patch-classes-class_id) | 반 수정 | 원장, 실장 |
| MVP | POST | [`/classes/{class_id}/students`](#op-post-classes-class_id-students) | 반에 학생 등록 | 원장, 실장 |
| MVP | DELETE | [`/classes/{class_id}/students/{student_id}`](#op-delete-classes-class_id-students-student_id) | 반에서 학생 빼기 | 원장, 실장 |

### 학생

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| MVP | GET | [`/students`](#op-get-students) | 학생 목록·검색 | 원장, 실장, 교사 |
| MVP | POST | [`/students`](#op-post-students) | 학생 등록 | 원장, 실장 |
| MVP | GET | [`/students/{student_id}`](#op-get-students-student_id) | 학생 상세 | 원장, 실장, 교사 |
| MVP | PATCH | [`/students/{student_id}`](#op-patch-students-student_id) | 학생 정보·상태 수정 | 원장, 실장 |
| MVP | GET | [`/students/{student_id}/timeline`](#op-get-students-student_id-timeline) | 학생별 기록 | 원장, 실장, 교사 |
| 확장 | POST | [`/students/{student_id}/notes`](#op-post-students-student_id-notes) | 상담·통화 메모 추가 | 원장, 실장, 교사 |
| MVP | POST | [`/students/{student_id}/guardians`](#op-post-students-student_id-guardians) | 보호자 연결 | 원장, 실장 |
| MVP | PATCH | [`/students/{student_id}/guardians/{guardian_id}`](#op-patch-students-student_id-guardians-guardian_id) | 보호자 관계·기본 수신자 수정 | 원장, 실장 |
| MVP | DELETE | [`/students/{student_id}/guardians/{guardian_id}`](#op-delete-students-student_id-guardians-guardian_id) | 보호자 연결 해제 | 원장, 실장 |

### 보호자

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| MVP | GET | [`/guardians`](#op-get-guardians) | 보호자 검색 | 원장, 실장 |
| MVP | POST | [`/guardians`](#op-post-guardians) | 보호자 등록 | 원장, 실장 |
| MVP | GET | [`/guardians/{guardian_id}`](#op-get-guardians-guardian_id) | 보호자 상세 | 원장, 실장, 교사 |
| MVP | PATCH | [`/guardians/{guardian_id}`](#op-patch-guardians-guardian_id) | 보호자 연락처·수신 언어·동의 수정 | 원장, 실장 |

### 형제 연동

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| MVP | GET | [`/households/suggestions`](#op-get-households-suggestions) | 형제 연결 후보 목록 | 원장, 실장 |
| MVP | POST | [`/households/suggestions/{suggestion_id}/accept`](#op-post-households-suggestions-suggestion_id-accept) | 형제 연결 후보 수락 | 원장, 실장 |
| MVP | POST | [`/households/suggestions/{suggestion_id}/reject`](#op-post-households-suggestions-suggestion_id-reject) | 형제 연결 후보 거절 | 원장, 실장 |
| MVP | GET | [`/households`](#op-get-households) | 가구 목록 | 원장, 실장 |
| MVP | POST | [`/households`](#op-post-households) | 가구 직접 만들기 | 원장, 실장 |
| MVP | GET | [`/households/{household_id}`](#op-get-households-household_id) | 가구 상세 | 원장, 실장, 교사 |
| MVP | PATCH | [`/households/{household_id}`](#op-patch-households-household_id) | 가구 이름 수정 | 원장, 실장 |
| MVP | POST | [`/households/{household_id}/members`](#op-post-households-household_id-members) | 가구에 형제 추가 | 원장, 실장 |
| MVP | DELETE | [`/households/{household_id}/members/{student_id}`](#op-delete-households-household_id-members-student_id) | 가구에서 학생 빼기 | 원장, 실장 |

### 업로드

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| MVP | GET | [`/imports/kinds/{kind}/fields`](#op-get-imports-kinds-kind-fields) | 업로드 종류별 필드 목록 | 원장, 실장 |
| MVP | GET | [`/imports`](#op-get-imports) | 업로드 기록 | 원장, 실장 |
| MVP | POST | [`/imports`](#op-post-imports) | CSV·엑셀 업로드 | 원장, 실장 |
| 확장 | POST | [`/imports/sheets`](#op-post-imports-sheets) | 구글 시트에서 가져오기 | 원장, 실장 |
| MVP | GET | [`/imports/{import_id}`](#op-get-imports-import_id) | 업로드 상태 | 원장, 실장 |
| MVP | DELETE | [`/imports/{import_id}`](#op-delete-imports-import_id) | 반영 전 업로드 버리기 | 원장, 실장 |
| MVP | GET | [`/imports/{import_id}/rows`](#op-get-imports-import_id-rows) | 행별 검사 결과 | 원장, 실장 |
| MVP | PUT | [`/imports/{import_id}/mapping`](#op-put-imports-import_id-mapping) | 열 매핑 저장 후 다시 검사 | 원장, 실장 |
| MVP | POST | [`/imports/{import_id}/commit`](#op-post-imports-import_id-commit) | 검사 통과한 행 반영 | 원장, 실장 |

### 수납

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| MVP | GET | [`/invoices`](#op-get-invoices) | 청구 목록 | 원장, 실장 |
| MVP | POST | [`/invoices`](#op-post-invoices) | 청구 직접 등록 | 원장, 실장 |
| MVP | GET | [`/invoices/{invoice_id}`](#op-get-invoices-invoice_id) | 청구 상세 | 원장, 실장 |
| MVP | PATCH | [`/invoices/{invoice_id}`](#op-patch-invoices-invoice_id) | 청구 수정·취소 | 원장, 실장 |
| MVP | POST | [`/invoices/{invoice_id}/holds`](#op-post-invoices-invoice_id-holds) | 자동 안내 보류 걸기 | 원장, 실장 |
| MVP | DELETE | [`/invoices/{invoice_id}/holds/{reason}`](#op-delete-invoices-invoice_id-holds-reason) | 보류 해제 | 원장, 실장 |
| 제안 | GET | [`/invoices/{invoice_id}/promises`](#op-get-invoices-invoice_id-promises) | 납부 약속 목록 | 원장, 실장 |
| 제안 | POST | [`/invoices/{invoice_id}/promises`](#op-post-invoices-invoice_id-promises) | 납부 약속 등록 | 원장, 실장 |
| 제안 | DELETE | [`/invoices/{invoice_id}/promises/{promise_id}`](#op-delete-invoices-invoice_id-promises-promise_id) | 납부 약속 취소 | 원장, 실장 |
| MVP | GET | [`/payments`](#op-get-payments) | 납부 기록 | 원장, 실장 |
| MVP | POST | [`/payments`](#op-post-payments) | 납부 등록 | 원장, 실장 |
| MVP | POST | [`/payments/{payment_id}/void`](#op-post-payments-payment_id-void) | 납부 취소 | 원장, 실장 |
| 제안 | GET | [`/deposit-matches`](#op-get-deposit-matches) | 입금자명 매칭 후보 | 원장, 실장 |
| 제안 | POST | [`/deposit-matches/{match_id}/confirm`](#op-post-deposit-matches-match_id-confirm) | 매칭 확정 → 납부 등록 | 원장, 실장 |
| 제안 | POST | [`/deposit-matches/{match_id}/reject`](#op-post-deposit-matches-match_id-reject) | 매칭 거절 | 원장, 실장 |
| 확장 | GET | [`/billing/sibling-discount`](#op-get-billing-sibling-discount) | 형제 할인 규칙 조회 | 원장, 실장, 교사 |
| 확장 | PUT | [`/billing/sibling-discount`](#op-put-billing-sibling-discount) | 형제 할인 규칙 저장 | 원장 |

### 출결

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| MVP | GET | [`/attendance`](#op-get-attendance) | 출결 조회 | 원장, 실장, 교사 |
| MVP | POST | [`/attendance/batch`](#op-post-attendance-batch) | 출결 일괄 입력 | 원장, 실장, 교사 |
| MVP | GET | [`/attendance/alerts`](#op-get-attendance-alerts) | 긴급 결석 알림 | 원장, 실장, 교사 |
| MVP | POST | [`/attendance/alerts/{alert_id}/ack`](#op-post-attendance-alerts-alert_id-ack) | 긴급 알림 확인 | 원장, 실장, 교사 |
| MVP | PATCH | [`/attendance/{attendance_id}`](#op-patch-attendance-attendance_id) | 출결 정정 | 원장, 실장, 교사 |

### 과제

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| 확장 | GET | [`/homework`](#op-get-homework) | 과제 목록 | 원장, 실장, 교사 |
| 확장 | POST | [`/homework`](#op-post-homework) | 과제 등록 | 원장, 실장, 교사 |
| 확장 | PATCH | [`/homework/{homework_id}`](#op-patch-homework-homework_id) | 과제 수정 | 원장, 실장, 교사 |
| 확장 | GET | [`/homework/{homework_id}/submissions`](#op-get-homework-homework_id-submissions) | 제출 현황 | 원장, 실장, 교사 |
| 확장 | PUT | [`/homework/{homework_id}/submissions`](#op-put-homework-homework_id-submissions) | 제출 기록 일괄 입력 | 원장, 실장, 교사 |

### 규칙 엔진

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| MVP | GET | [`/rules/settings`](#op-get-rules-settings) | 안내 규칙 설정 조회 | 원장, 실장 |
| MVP | PUT | [`/rules/settings`](#op-put-rules-settings) | 안내 규칙 설정 저장 | 원장 |
| MVP | GET | [`/rules/runs`](#op-get-rules-runs) | 실행 기록 | 원장, 실장 |
| MVP | POST | [`/rules/runs`](#op-post-rules-runs) | 규칙 엔진 수동 실행 | 원장, 실장 |
| MVP | GET | [`/rules/runs/{run_id}`](#op-get-rules-runs-run_id) | 실행 결과 | 원장, 실장 |

### 승인함

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| MVP | GET | [`/approvals`](#op-get-approvals) | 승인함 목록 | 원장, 실장, 교사 |
| MVP | POST | [`/approvals/bulk-approve`](#op-post-approvals-bulk-approve) | 여러 건 한 번에 승인 | 원장, 실장, 교사 |
| MVP | GET | [`/approvals/{approval_id}`](#op-get-approvals-approval_id) | 승인 상세 | 원장, 실장, 교사 |
| MVP | POST | [`/approvals/{approval_id}/approve`](#op-post-approvals-approval_id-approve) | 승인 (수정 후 승인 포함) | 원장, 실장, 교사 |
| MVP | POST | [`/approvals/{approval_id}/hold`](#op-post-approvals-approval_id-hold) | 보류 | 원장, 실장, 교사 |
| MVP | POST | [`/approvals/{approval_id}/reject`](#op-post-approvals-approval_id-reject) | 반려 | 원장, 실장, 교사 |

### 템플릿

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| MVP | GET | [`/templates`](#op-get-templates) | 템플릿 목록 | 원장, 실장, 교사 |
| MVP | POST | [`/templates`](#op-post-templates) | 템플릿 만들기 (버전 1 초안) | 원장, 실장 |
| MVP | GET | [`/templates/{template_id}`](#op-get-templates-template_id) | 템플릿 상세 | 원장, 실장, 교사 |
| MVP | PATCH | [`/templates/{template_id}`](#op-patch-templates-template_id) | 템플릿 이름 수정·보관 | 원장, 실장 |
| MVP | GET | [`/templates/{template_id}/versions`](#op-get-templates-template_id-versions) | 템플릿 버전 목록 | 원장, 실장, 교사 |
| MVP | POST | [`/templates/{template_id}/versions`](#op-post-templates-template_id-versions) | 새 버전 초안 | 원장, 실장 |
| MVP | POST | [`/templates/{template_id}/versions/{version}/approve`](#op-post-templates-template_id-versions-version-approve) | 버전 승인 | 원장, 실장 |
| MVP | POST | [`/templates/{template_id}/preview`](#op-post-templates-template_id-preview) | 자리 표시 채워 미리 보기 | 원장, 실장, 교사 |
| 확장 | GET | [`/templates/{template_id}/versions/{version}/translations`](#op-get-templates-template_id-versions-version-translations) | 번역 목록 | 원장, 실장, 교사 |
| 확장 | POST | [`/templates/{template_id}/versions/{version}/translations`](#op-post-templates-template_id-versions-version-translations) | 번역 생성 요청 (AI) | 원장, 실장 |
| 확장 | PATCH | [`/templates/{template_id}/versions/{version}/translations/{language}`](#op-patch-templates-template_id-versions-version-translations-language) | 번역 수정·승인 | 원장, 실장 |

### 안내 후보

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| MVP | GET | [`/candidates`](#op-get-candidates) | 안내 후보 목록 | 원장, 실장, 교사 |
| MVP | GET | [`/candidates/{candidate_id}`](#op-get-candidates-candidate_id) | 안내 후보 상세 | 원장, 실장, 교사 |
| MVP | POST | [`/candidates/{candidate_id}/cancel`](#op-post-candidates-candidate_id-cancel) | 안내 후보 취소 | 원장, 실장 |

### 발송 이력

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| MVP | GET | [`/messages`](#op-get-messages) | 발송 이력 | 원장, 실장, 교사 |
| MVP | GET | [`/messages/{message_id}`](#op-get-messages-message_id) | 발송 건 상세 | 원장, 실장, 교사 |
| MVP | POST | [`/messages/{message_id}/cancel`](#op-post-messages-message_id-cancel) | 예약 발송 취소 | 원장, 실장 |
| 제안 | POST | [`/messages/{message_id}/corrections`](#op-post-messages-message_id-corrections) | 오발송 정정 안내 만들기 | 원장, 실장 |

### 회신

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| MVP | GET | [`/replies`](#op-get-replies) | 학부모 회신 목록 | 원장, 실장, 교사 |
| MVP | GET | [`/replies/{reply_id}`](#op-get-replies-reply_id) | 회신 상세 | 원장, 실장, 교사 |
| MVP | PATCH | [`/replies/{reply_id}`](#op-patch-replies-reply_id) | 회신 분류 확정·처리 완료 | 원장, 실장, 교사 |

### 수납 안내 PDF

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| 확장 | POST | [`/documents/billing-notices`](#op-post-documents-billing-notices) | 수납 안내 PDF 생성 | 원장, 실장 |
| 확장 | GET | [`/documents/{document_id}`](#op-get-documents-document_id) | PDF 상태 | 원장, 실장 |
| 확장 | POST | [`/documents/{document_id}/links`](#op-post-documents-document_id-links) | 만료되는 열람 링크 발급 | 원장, 실장 |

### 감사 로그

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| MVP | GET | [`/audit-logs`](#op-get-audit-logs) | 감사 로그 조회 | 원장, 실장 |

### AI 보조

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| 확장 | POST | [`/ai/replies/{reply_id}/classify`](#op-post-ai-replies-reply_id-classify) | 회신 분류·후속 업무 제안 | 원장, 실장, 교사 |
| 확장 | POST | [`/ai/candidates/{candidate_id}/draft`](#op-post-ai-candidates-candidate_id-draft) | 안내문 초안 | 원장, 실장 |
| 확장 | POST | [`/ai/students/{student_id}/summary`](#op-post-ai-students-student_id-summary) | 상담 전 연락 이력 요약 | 원장, 실장, 교사 |
| 확장 | POST | [`/ai/mismatch-scans`](#op-post-ai-mismatch-scans) | 수납·출결 불일치 후보 찾기 | 원장, 실장 |
| 확장 | GET | [`/ai/runs`](#op-get-ai-runs) | AI 실행 기록 | 원장, 실장 |
| 확장 | GET | [`/ai/runs/{run_id}`](#op-get-ai-runs-run_id) | AI 실행 결과 | 원장, 실장, 교사 |
| 확장 | GET | [`/ai/runs/{run_id}/steps`](#op-get-ai-runs-run_id-steps) | AI 실행 단계별 기록 | 원장, 실장 |
| 확장 | POST | [`/ai/runs/{run_id}/feedback`](#op-post-ai-runs-run_id-feedback) | AI 결과 채택·수정 기록 | 원장, 실장, 교사 |

### 웹훅

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| MVP | POST | [`/webhooks/sms/{provider}/delivery`](#op-post-webhooks-sms-provider-delivery) | 발송 결과 수신 | 공개 (서명 검증) |
| MVP | POST | [`/webhooks/sms/{provider}/inbound`](#op-post-webhooks-sms-provider-inbound) | 학부모 회신 수신 | 공개 (서명 검증) |

### 공개 링크

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| 제안 | GET | [`/public/replies/{token}`](#op-get-public-replies-token) | 원클릭 응답 화면 정보 | 공개 (일회용 토큰) |
| 제안 | POST | [`/public/replies/{token}`](#op-post-public-replies-token) | 원클릭 응답 제출 | 공개 (일회용 토큰) |

### 상태

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
|  | GET | [`/health`](#op-get--health) | 서버 상태 확인 | 공개 |

## 엔드포인트 상세

### 인증

<a id="op-post-auth-login"></a>

#### POST `/api/v1/auth/login`

**로그인** · 단계 `MVP` · 권한 공개

요청 본문: [LoginBody](#schema-loginbody)

응답 `200`: [TokenPair](#schema-tokenpair)

<a id="op-post-auth-refresh"></a>

#### POST `/api/v1/auth/refresh`

**토큰 갱신** · 단계 `MVP` · 권한 공개

요청 본문: [RefreshBody](#schema-refreshbody)

응답 `200`: [TokenPair](#schema-tokenpair)

<a id="op-post-auth-logout"></a>

#### POST `/api/v1/auth/logout`

**로그아웃 (리프레시 토큰 폐기)** · 단계 `MVP` · 권한 원장, 실장, 교사

요청 본문: [RefreshBody](#schema-refreshbody)

응답 `204`: (본문 없음)

<a id="op-get-auth-me"></a>

#### GET `/api/v1/auth/me`

**내 정보·역할** · 단계 `MVP` · 권한 원장, 실장, 교사

응답 `200`: [MeOut](#schema-meout)

### 오늘의 소통함

<a id="op-get-dashboard-today"></a>

#### GET `/api/v1/dashboard/today`

**오늘의 소통함 요약** · 단계 `MVP` · 권한 원장, 실장, 교사

응답 `200`: [TodaySummary](#schema-todaysummary)

<a id="op-get-dashboard-briefing"></a>

#### GET `/api/v1/dashboard/briefing`

**담당자 아침 브리핑** · 단계 `제안` · 권한 원장, 실장, 교사

응답 `200`: [Briefing](#schema-briefing)

<a id="op-get-review-items"></a>

#### GET `/api/v1/review-items`

**확인 필요함** · 단계 `MVP` · 권한 원장, 실장, 교사

업로드 오류, 매칭 후보, 형제 연결 후보, 미분류 회신 등 사람이 봐야 할 것을 한 목록으로.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `kind` | 쿼리 | [ReviewKind](#schema-reviewkind) \| null |  |  |  |
| `page` | 쿼리 | integer |  | `1` | ≥ 1 |
| `size` | 쿼리 | integer |  | `20` | ≥ 1, ≤ 100 |

응답 `200`: [Page_ReviewItem_](#schema-page-reviewitem-)

### 학원

<a id="op-get-academy"></a>

#### GET `/api/v1/academy`

**내 학원 정보** · 단계 `MVP` · 권한 원장, 실장, 교사

응답 `200`: [AcademyOut](#schema-academyout)

<a id="op-patch-academy"></a>

#### PATCH `/api/v1/academy`

**학원 정보 수정** · 단계 `MVP` · 권한 원장

요청 본문: [AcademyUpdate](#schema-academyupdate)

응답 `200`: [AcademyOut](#schema-academyout)

<a id="op-get-academy-branches"></a>

#### GET `/api/v1/academy/branches`

**지점 목록** · 단계 `MVP` · 권한 원장, 실장, 교사

응답 `200`: [BranchOut](#schema-branchout)[]

<a id="op-post-academy-branches"></a>

#### POST `/api/v1/academy/branches`

**지점 추가** · 단계 `MVP` · 권한 원장

요청 본문: [BranchCreate](#schema-branchcreate)

응답 `201`: [BranchOut](#schema-branchout)

<a id="op-patch-academy-branches-branch_id"></a>

#### PATCH `/api/v1/academy/branches/{branch_id}`

**지점 수정** · 단계 `MVP` · 권한 원장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `branch_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [BranchUpdate](#schema-branchupdate)

응답 `200`: [BranchOut](#schema-branchout)

<a id="op-get-academy-calendar"></a>

#### GET `/api/v1/academy/calendar`

**휴원·방학·공휴일 목록** · 단계 `제안` · 권한 원장, 실장, 교사

규칙 엔진이 쉬는 날에는 결석 후보를 만들지 않고, 수납 단계를 영업일로 셀 때 쓴다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `from` | 쿼리 | string (date) | 예 |  |  |
| `to` | 쿼리 | string (date) | 예 |  |  |

응답 `200`: [CalendarEventOut](#schema-calendareventout)[]

<a id="op-post-academy-calendar"></a>

#### POST `/api/v1/academy/calendar`

**휴원·방학·공휴일 등록** · 단계 `제안` · 권한 원장, 실장

요청 본문: [CalendarEventCreate](#schema-calendareventcreate)

응답 `201`: [CalendarEventOut](#schema-calendareventout)

<a id="op-delete-academy-calendar-event_id"></a>

#### DELETE `/api/v1/academy/calendar/{event_id}`

**휴원·방학·공휴일 삭제** · 단계 `제안` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `event_id` | 경로 | string (uuid) | 예 |  |  |

응답 `204`: (본문 없음)

### 사용자

<a id="op-get-users"></a>

#### GET `/api/v1/users`

**직원 목록** · 단계 `MVP` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `role` | 쿼리 | [Role](#schema-role) \| null |  |  |  |
| `page` | 쿼리 | integer |  | `1` | ≥ 1 |
| `size` | 쿼리 | integer |  | `20` | ≥ 1, ≤ 100 |

응답 `200`: [Page_UserOut_](#schema-page-userout-)

<a id="op-post-users-invitations"></a>

#### POST `/api/v1/users/invitations`

**직원 초대** · 단계 `MVP` · 권한 원장

초대 메일을 보내고, 수락하면 계정이 활성화된다.

요청 본문: [UserInvite](#schema-userinvite)

응답 `201`: [UserOut](#schema-userout)

<a id="op-patch-users-user_id"></a>

#### PATCH `/api/v1/users/{user_id}`

**직원 역할·정보 수정** · 단계 `MVP` · 권한 원장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `user_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [UserUpdate](#schema-userupdate)

응답 `200`: [UserOut](#schema-userout)

<a id="op-delete-users-user_id"></a>

#### DELETE `/api/v1/users/{user_id}`

**직원 비활성화** · 단계 `MVP` · 권한 원장

삭제하지 않고 비활성화한다. 승인·발송 기록의 작성자는 그대로 남는다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `user_id` | 경로 | string (uuid) | 예 |  |  |

응답 `204`: (본문 없음)

### 반

<a id="op-get-classes"></a>

#### GET `/api/v1/classes`

**반 목록** · 단계 `MVP` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `teacher_id` | 쿼리 | string (uuid) \| null |  |  |  |
| `branch_id` | 쿼리 | string (uuid) \| null |  |  |  |

응답 `200`: [ClassOut](#schema-classout)[]

<a id="op-post-classes"></a>

#### POST `/api/v1/classes`

**반 만들기** · 단계 `MVP` · 권한 원장, 실장

요청 본문: [ClassCreate](#schema-classcreate)

응답 `201`: [ClassOut](#schema-classout)

<a id="op-get-classes-class_id"></a>

#### GET `/api/v1/classes/{class_id}`

**반 상세** · 단계 `MVP` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `class_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [ClassOut](#schema-classout)

<a id="op-patch-classes-class_id"></a>

#### PATCH `/api/v1/classes/{class_id}`

**반 수정** · 단계 `MVP` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `class_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [ClassUpdate](#schema-classupdate)

응답 `200`: [ClassOut](#schema-classout)

<a id="op-post-classes-class_id-students"></a>

#### POST `/api/v1/classes/{class_id}/students`

**반에 학생 등록** · 단계 `MVP` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `class_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [EnrollBody](#schema-enrollbody)

응답 `200`: [ClassOut](#schema-classout)

<a id="op-delete-classes-class_id-students-student_id"></a>

#### DELETE `/api/v1/classes/{class_id}/students/{student_id}`

**반에서 학생 빼기** · 단계 `MVP` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `class_id` | 경로 | string (uuid) | 예 |  |  |
| `student_id` | 경로 | string (uuid) | 예 |  |  |

응답 `204`: (본문 없음)

### 학생

<a id="op-get-students"></a>

#### GET `/api/v1/students`

**학생 목록·검색** · 단계 `MVP` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `q` | 쿼리 | string \| null |  |  |  |
| `status` | 쿼리 | [StudentStatus](#schema-studentstatus) \| null |  |  |  |
| `class_id` | 쿼리 | string (uuid) \| null |  |  |  |
| `household_id` | 쿼리 | string (uuid) \| null |  |  |  |
| `page` | 쿼리 | integer |  | `1` | ≥ 1 |
| `size` | 쿼리 | integer |  | `20` | ≥ 1, ≤ 100 |

응답 `200`: [Page_StudentSummary_](#schema-page-studentsummary-)

<a id="op-post-students"></a>

#### POST `/api/v1/students`

**학생 등록** · 단계 `MVP` · 권한 원장, 실장

요청 본문: [StudentCreate](#schema-studentcreate)

응답 `201`: [StudentOut](#schema-studentout)

<a id="op-get-students-student_id"></a>

#### GET `/api/v1/students/{student_id}`

**학생 상세** · 단계 `MVP` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `student_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [StudentOut](#schema-studentout)

<a id="op-patch-students-student_id"></a>

#### PATCH `/api/v1/students/{student_id}`

**학생 정보·상태 수정** · 단계 `MVP` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `student_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [StudentUpdate](#schema-studentupdate)

응답 `200`: [StudentOut](#schema-studentout)

<a id="op-get-students-student_id-timeline"></a>

#### GET `/api/v1/students/{student_id}/timeline`

**학생별 기록** · 단계 `MVP` · 권한 원장, 실장, 교사

수납·출결·과제·발송·회신·승인·메모를 시간순으로 합쳐 보여준다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `student_id` | 경로 | string (uuid) | 예 |  |  |
| `kinds` | 쿼리 | [TimelineKind](#schema-timelinekind)[] \| null |  |  |  |
| `page` | 쿼리 | integer |  | `1` | ≥ 1 |
| `size` | 쿼리 | integer |  | `20` | ≥ 1, ≤ 100 |

응답 `200`: [Page_TimelineItem_](#schema-page-timelineitem-)

<a id="op-post-students-student_id-notes"></a>

#### POST `/api/v1/students/{student_id}/notes`

**상담·통화 메모 추가** · 단계 `확장` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `student_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [NoteCreate](#schema-notecreate)

응답 `201`: [TimelineItem](#schema-timelineitem)

<a id="op-post-students-student_id-guardians"></a>

#### POST `/api/v1/students/{student_id}/guardians`

**보호자 연결** · 단계 `MVP` · 권한 원장, 실장

기존 보호자를 연결하거나 새 보호자를 만들어 연결한다. 같은 연락처가 다른 학생에도 있으면 형제 연결 후보가 생긴다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `student_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [GuardianLinkCreate](#schema-guardianlinkcreate)

응답 `201`: [StudentOut](#schema-studentout)

<a id="op-patch-students-student_id-guardians-guardian_id"></a>

#### PATCH `/api/v1/students/{student_id}/guardians/{guardian_id}`

**보호자 관계·기본 수신자 수정** · 단계 `MVP` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `student_id` | 경로 | string (uuid) | 예 |  |  |
| `guardian_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [GuardianLinkUpdate](#schema-guardianlinkupdate)

응답 `200`: [StudentOut](#schema-studentout)

<a id="op-delete-students-student_id-guardians-guardian_id"></a>

#### DELETE `/api/v1/students/{student_id}/guardians/{guardian_id}`

**보호자 연결 해제** · 단계 `MVP` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `student_id` | 경로 | string (uuid) | 예 |  |  |
| `guardian_id` | 경로 | string (uuid) | 예 |  |  |

응답 `204`: (본문 없음)

### 보호자

<a id="op-get-guardians"></a>

#### GET `/api/v1/guardians`

**보호자 검색** · 단계 `MVP` · 권한 원장, 실장

이름이나 연락처 뒷자리로 찾는다. 응답의 연락처는 항상 마스킹한다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `q` | 쿼리 | string \| null |  |  |  |
| `page` | 쿼리 | integer |  | `1` | ≥ 1 |
| `size` | 쿼리 | integer |  | `20` | ≥ 1, ≤ 100 |

응답 `200`: [Page_GuardianOut_](#schema-page-guardianout-)

<a id="op-post-guardians"></a>

#### POST `/api/v1/guardians`

**보호자 등록** · 단계 `MVP` · 권한 원장, 실장

요청 본문: [GuardianCreate](#schema-guardiancreate)

응답 `201`: [GuardianOut](#schema-guardianout)

<a id="op-get-guardians-guardian_id"></a>

#### GET `/api/v1/guardians/{guardian_id}`

**보호자 상세** · 단계 `MVP` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `guardian_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [GuardianOut](#schema-guardianout)

<a id="op-patch-guardians-guardian_id"></a>

#### PATCH `/api/v1/guardians/{guardian_id}`

**보호자 연락처·수신 언어·동의 수정** · 단계 `MVP` · 권한 원장, 실장

연결된 모든 학생(형제)에 한 번에 반영된다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `guardian_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [GuardianUpdate](#schema-guardianupdate)

응답 `200`: [GuardianOut](#schema-guardianout)

### 형제 연동

<a id="op-get-households-suggestions"></a>

#### GET `/api/v1/households/suggestions`

**형제 연결 후보 목록** · 단계 `MVP` · 권한 원장, 실장

업로드나 보호자 연결 때 같은 연락처·입금자명이 발견되면 생긴다. 자동 확정하지 않는다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `status` | 쿼리 | [SuggestionStatus](#schema-suggestionstatus) |  | `"pending"` |  |
| `page` | 쿼리 | integer |  | `1` | ≥ 1 |
| `size` | 쿼리 | integer |  | `20` | ≥ 1, ≤ 100 |

응답 `200`: [Page_HouseholdSuggestion_](#schema-page-householdsuggestion-)

<a id="op-post-households-suggestions-suggestion_id-accept"></a>

#### POST `/api/v1/households/suggestions/{suggestion_id}/accept`

**형제 연결 후보 수락** · 단계 `MVP` · 권한 원장, 실장

가구를 만들거나 기존 가구에 합친다. 감사 로그에 기록된다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `suggestion_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [HouseholdOut](#schema-householdout)

<a id="op-post-households-suggestions-suggestion_id-reject"></a>

#### POST `/api/v1/households/suggestions/{suggestion_id}/reject`

**형제 연결 후보 거절** · 단계 `MVP` · 권한 원장, 실장

같은 학생 조합으로는 다시 제안하지 않는다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `suggestion_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [SuggestionReject](#schema-suggestionreject)

응답 `204`: (본문 없음)

<a id="op-get-households"></a>

#### GET `/api/v1/households`

**가구 목록** · 단계 `MVP` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `page` | 쿼리 | integer |  | `1` | ≥ 1 |
| `size` | 쿼리 | integer |  | `20` | ≥ 1, ≤ 100 |

응답 `200`: [Page_HouseholdOut_](#schema-page-householdout-)

<a id="op-post-households"></a>

#### POST `/api/v1/households`

**가구 직접 만들기** · 단계 `MVP` · 권한 원장, 실장

요청 본문: [HouseholdCreate](#schema-householdcreate)

응답 `201`: [HouseholdOut](#schema-householdout)

<a id="op-get-households-household_id"></a>

#### GET `/api/v1/households/{household_id}`

**가구 상세** · 단계 `MVP` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `household_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [HouseholdOut](#schema-householdout)

<a id="op-patch-households-household_id"></a>

#### PATCH `/api/v1/households/{household_id}`

**가구 이름 수정** · 단계 `MVP` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `household_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [HouseholdUpdate](#schema-householdupdate)

응답 `200`: [HouseholdOut](#schema-householdout)

<a id="op-post-households-household_id-members"></a>

#### POST `/api/v1/households/{household_id}/members`

**가구에 형제 추가** · 단계 `MVP` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `household_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [HouseholdMembersAdd](#schema-householdmembersadd)

응답 `200`: [HouseholdOut](#schema-householdout)

<a id="op-delete-households-household_id-members-student_id"></a>

#### DELETE `/api/v1/households/{household_id}/members/{student_id}`

**가구에서 학생 빼기** · 단계 `MVP` · 권한 원장, 실장

형제 할인을 쓰는 학원이면 할인 재계산 후보가 생긴다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `household_id` | 경로 | string (uuid) | 예 |  |  |
| `student_id` | 경로 | string (uuid) | 예 |  |  |

응답 `204`: (본문 없음)

### 업로드

<a id="op-get-imports-kinds-kind-fields"></a>

#### GET `/api/v1/imports/kinds/{kind}/fields`

**업로드 종류별 필드 목록** · 단계 `MVP` · 권한 원장, 실장

열 매핑 화면과 CSV 양식 안내에 쓴다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `kind` | 경로 | [ImportKind](#schema-importkind) | 예 |  |  |

응답 `200`: [FieldSpec](#schema-fieldspec)[]

<a id="op-get-imports"></a>

#### GET `/api/v1/imports`

**업로드 기록** · 단계 `MVP` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `kind` | 쿼리 | [ImportKind](#schema-importkind) \| null |  |  |  |
| `status` | 쿼리 | [ImportStatus](#schema-importstatus) \| null |  |  |  |
| `page` | 쿼리 | integer |  | `1` | ≥ 1 |
| `size` | 쿼리 | integer |  | `20` | ≥ 1, ≤ 100 |

응답 `200`: [Page_ImportBatchOut_](#schema-page-importbatchout-)

<a id="op-post-imports"></a>

#### POST `/api/v1/imports`

**CSV·엑셀 업로드** · 단계 `MVP` · 권한 원장, 실장

원본 파일은 비공개 저장소에 두고 검사를 시작한다. 업로드 1회 = 배치 1건. 열 이름을 자동으로 맞추지 못하면 mapping_required 상태가 된다.

요청 본문: [Body_upload_api_v1_imports_post](#schema-body-upload-api-v1-imports-post) (`multipart/form-data`)

응답 `202`: [ImportBatchOut](#schema-importbatchout)

<a id="op-post-imports-sheets"></a>

#### POST `/api/v1/imports/sheets`

**구글 시트에서 가져오기** · 단계 `확장` · 권한 원장, 실장

요청 본문: [SheetImportBody](#schema-sheetimportbody)

응답 `202`: [ImportBatchOut](#schema-importbatchout)

<a id="op-get-imports-import_id"></a>

#### GET `/api/v1/imports/{import_id}`

**업로드 상태** · 단계 `MVP` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `import_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [ImportBatchOut](#schema-importbatchout)

<a id="op-delete-imports-import_id"></a>

#### DELETE `/api/v1/imports/{import_id}`

**반영 전 업로드 버리기** · 단계 `MVP` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `import_id` | 경로 | string (uuid) | 예 |  |  |

응답 `204`: (본문 없음)

<a id="op-get-imports-import_id-rows"></a>

#### GET `/api/v1/imports/{import_id}/rows`

**행별 검사 결과** · 단계 `MVP` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `import_id` | 경로 | string (uuid) | 예 |  |  |
| `status` | 쿼리 | [RowStatus](#schema-rowstatus) \| null |  |  |  |
| `page` | 쿼리 | integer |  | `1` | ≥ 1 |
| `size` | 쿼리 | integer |  | `20` | ≥ 1, ≤ 100 |

응답 `200`: [Page_ImportRowOut_](#schema-page-importrowout-)

<a id="op-put-imports-import_id-mapping"></a>

#### PUT `/api/v1/imports/{import_id}/mapping`

**열 매핑 저장 후 다시 검사** · 단계 `MVP` · 권한 원장, 실장

같은 학원이 같은 열 이름으로 다시 올리면 저장한 매핑을 자동으로 쓴다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `import_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [ColumnMappingBody](#schema-columnmappingbody)

응답 `202`: [ImportBatchOut](#schema-importbatchout)

<a id="op-post-imports-import_id-commit"></a>

#### POST `/api/v1/imports/{import_id}/commit`

**검사 통과한 행 반영** · 단계 `MVP` · 권한 원장, 실장

ok·warning·duplicate 행만 외부 키로 upsert한다. error 행은 확인 필요함에 남는다. 반영 뒤 형제 연결 후보와 입금자명 매칭 후보를 만든다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `import_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [ImportBatchOut](#schema-importbatchout)

### 수납

<a id="op-get-invoices"></a>

#### GET `/api/v1/invoices`

**청구 목록** · 단계 `MVP` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `status` | 쿼리 | [InvoiceStatus](#schema-invoicestatus) \| null |  |  |  |
| `student_id` | 쿼리 | string (uuid) \| null |  |  |  |
| `household_id` | 쿼리 | string (uuid) \| null |  |  |  |
| `billing_month` | 쿼리 | string \| null |  |  | `형식 ^\d{4}-\d{2}$` |
| `overdue` | 쿼리 | boolean \| null |  |  |  |
| `on_hold` | 쿼리 | boolean \| null |  |  |  |
| `page` | 쿼리 | integer |  | `1` | ≥ 1 |
| `size` | 쿼리 | integer |  | `20` | ≥ 1, ≤ 100 |

응답 `200`: [Page_InvoiceOut_](#schema-page-invoiceout-)

<a id="op-post-invoices"></a>

#### POST `/api/v1/invoices`

**청구 직접 등록** · 단계 `MVP` · 권한 원장, 실장

요청 본문: [InvoiceCreate](#schema-invoicecreate)

응답 `201`: [InvoiceOut](#schema-invoiceout)

<a id="op-get-invoices-invoice_id"></a>

#### GET `/api/v1/invoices/{invoice_id}`

**청구 상세** · 단계 `MVP` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `invoice_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [InvoiceOut](#schema-invoiceout)

<a id="op-patch-invoices-invoice_id"></a>

#### PATCH `/api/v1/invoices/{invoice_id}`

**청구 수정·취소** · 단계 `MVP` · 권한 원장, 실장

금액이 바뀌거나 취소되면 예약된 수납 안내를 다시 검사한다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `invoice_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [InvoiceUpdate](#schema-invoiceupdate)

응답 `200`: [InvoiceOut](#schema-invoiceout)

<a id="op-post-invoices-invoice_id-holds"></a>

#### POST `/api/v1/invoices/{invoice_id}/holds`

**자동 안내 보류 걸기** · 단계 `MVP` · 권한 원장, 실장

보류가 하나라도 있으면 이 청구의 자동 안내는 만들어지지 않고 예약 건도 취소된다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `invoice_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [HoldCreate](#schema-holdcreate)

응답 `200`: [InvoiceOut](#schema-invoiceout)

<a id="op-delete-invoices-invoice_id-holds-reason"></a>

#### DELETE `/api/v1/invoices/{invoice_id}/holds/{reason}`

**보류 해제** · 단계 `MVP` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `invoice_id` | 경로 | string (uuid) | 예 |  |  |
| `reason` | 경로 | [HoldReason](#schema-holdreason) | 예 |  |  |

응답 `200`: [InvoiceOut](#schema-invoiceout)

<a id="op-get-invoices-invoice_id-promises"></a>

#### GET `/api/v1/invoices/{invoice_id}/promises`

**납부 약속 목록** · 단계 `제안` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `invoice_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [PromiseOut](#schema-promiseout)[]

<a id="op-post-invoices-invoice_id-promises"></a>

#### POST `/api/v1/invoices/{invoice_id}/promises`

**납부 약속 등록** · 단계 `제안` · 권한 원장, 실장

약속일까지 수납 안내를 보류하고, 약속일 다음 날 납부 확인 후보를 만든다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `invoice_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [PromiseCreate](#schema-promisecreate)

응답 `201`: [PromiseOut](#schema-promiseout)

<a id="op-delete-invoices-invoice_id-promises-promise_id"></a>

#### DELETE `/api/v1/invoices/{invoice_id}/promises/{promise_id}`

**납부 약속 취소** · 단계 `제안` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `invoice_id` | 경로 | string (uuid) | 예 |  |  |
| `promise_id` | 경로 | string (uuid) | 예 |  |  |

응답 `204`: (본문 없음)

<a id="op-get-payments"></a>

#### GET `/api/v1/payments`

**납부 기록** · 단계 `MVP` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `student_id` | 쿼리 | string (uuid) \| null |  |  |  |
| `household_id` | 쿼리 | string (uuid) \| null |  |  |  |
| `page` | 쿼리 | integer |  | `1` | ≥ 1 |
| `size` | 쿼리 | integer |  | `20` | ≥ 1, ≤ 100 |

응답 `200`: [Page_PaymentOut_](#schema-page-paymentout-)

<a id="op-post-payments"></a>

#### POST `/api/v1/payments`

**납부 등록** · 단계 `MVP` · 권한 원장, 실장

여러 청구(형제 포함)에 나눠 반영할 수 있다. 완납된 청구의 예약 안내는 취소된다.

요청 본문: [PaymentCreate](#schema-paymentcreate)

응답 `201`: [PaymentOut](#schema-paymentout)

<a id="op-post-payments-payment_id-void"></a>

#### POST `/api/v1/payments/{payment_id}/void`

**납부 취소** · 단계 `MVP` · 권한 원장, 실장

삭제하지 않고 취소 표시만 한다. 잔액이 다시 생기면 규칙 엔진이 다음 실행에서 판단한다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `payment_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [VoidBody](#schema-voidbody)

응답 `200`: [PaymentOut](#schema-paymentout)

<a id="op-get-deposit-matches"></a>

#### GET `/api/v1/deposit-matches`

**입금자명 매칭 후보** · 단계 `제안` · 권한 원장, 실장

통장 입금 내역 업로드 후 생긴다. 가구 단위로 찾아 형 이름으로 낸 동생 학원비도 잡는다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `status` | 쿼리 | [DepositMatchStatus](#schema-depositmatchstatus) |  | `"pending"` |  |
| `page` | 쿼리 | integer |  | `1` | ≥ 1 |
| `size` | 쿼리 | integer |  | `20` | ≥ 1, ≤ 100 |

응답 `200`: [Page_DepositMatchOut_](#schema-page-depositmatchout-)

<a id="op-post-deposit-matches-match_id-confirm"></a>

#### POST `/api/v1/deposit-matches/{match_id}/confirm`

**매칭 확정 → 납부 등록** · 단계 `제안` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `match_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [DepositMatchConfirm](#schema-depositmatchconfirm)

응답 `200`: [PaymentOut](#schema-paymentout)

<a id="op-post-deposit-matches-match_id-reject"></a>

#### POST `/api/v1/deposit-matches/{match_id}/reject`

**매칭 거절** · 단계 `제안` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `match_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [DepositMatchReject](#schema-depositmatchreject)

응답 `204`: (본문 없음)

<a id="op-get-billing-sibling-discount"></a>

#### GET `/api/v1/billing/sibling-discount`

**형제 할인 규칙 조회** · 단계 `확장` · 권한 원장, 실장, 교사

응답 `200`: [SiblingDiscountSettings](#schema-siblingdiscountsettings)

<a id="op-put-billing-sibling-discount"></a>

#### PUT `/api/v1/billing/sibling-discount`

**형제 할인 규칙 저장** · 단계 `확장` · 권한 원장

청구 생성 때 할인 줄로 기록한다. 바꾼 뒤 이미 만든 청구는 바뀌지 않는다.

요청 본문: [SiblingDiscountSettings](#schema-siblingdiscountsettings)

응답 `200`: [SiblingDiscountSettings](#schema-siblingdiscountsettings)

### 출결

<a id="op-get-attendance"></a>

#### GET `/api/v1/attendance`

**출결 조회** · 단계 `MVP` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `date` | 쿼리 | string (date) \| null |  |  |  |
| `class_id` | 쿼리 | string (uuid) \| null |  |  |  |
| `student_id` | 쿼리 | string (uuid) \| null |  |  |  |
| `status` | 쿼리 | [AttendanceStatus](#schema-attendancestatus) \| null |  |  |  |
| `page` | 쿼리 | integer |  | `1` | ≥ 1 |
| `size` | 쿼리 | integer |  | `20` | ≥ 1, ≤ 100 |

응답 `200`: [Page_AttendanceOut_](#schema-page-attendanceout-)

<a id="op-post-attendance-batch"></a>

#### POST `/api/v1/attendance/batch`

**출결 일괄 입력** · 단계 `MVP` · 권한 원장, 실장, 교사

(학생, 반, 날짜)로 upsert한다. 당일 무단결석은 예약 안내 대신 담당자 긴급 알림을 만든다.

요청 본문: [AttendanceBatch](#schema-attendancebatch)

응답 `200`: [AttendanceOut](#schema-attendanceout)[]

<a id="op-get-attendance-alerts"></a>

#### GET `/api/v1/attendance/alerts`

**긴급 결석 알림** · 단계 `MVP` · 권한 원장, 실장, 교사

형제가 같은 날 함께 결석하면 한 건으로 묶는다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `status` | 쿼리 | [AlertStatus](#schema-alertstatus) |  | `"open"` |  |
| `page` | 쿼리 | integer |  | `1` | ≥ 1 |
| `size` | 쿼리 | integer |  | `20` | ≥ 1, ≤ 100 |

응답 `200`: [Page_AttendanceAlertOut_](#schema-page-attendancealertout-)

<a id="op-post-attendance-alerts-alert_id-ack"></a>

#### POST `/api/v1/attendance/alerts/{alert_id}/ack`

**긴급 알림 확인** · 단계 `MVP` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `alert_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [AlertAck](#schema-alertack)

응답 `200`: [AttendanceAlertOut](#schema-attendancealertout)

<a id="op-patch-attendance-attendance_id"></a>

#### PATCH `/api/v1/attendance/{attendance_id}`

**출결 정정** · 단계 `MVP` · 권한 원장, 실장, 교사

예약된 결석 안내는 취소되고, 이미 나간 안내가 있으면 정정 안내 후보가 승인함에 생긴다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `attendance_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [AttendanceCorrection](#schema-attendancecorrection)

응답 `200`: [AttendanceOut](#schema-attendanceout)

### 과제

<a id="op-get-homework"></a>

#### GET `/api/v1/homework`

**과제 목록** · 단계 `확장` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `class_id` | 쿼리 | string (uuid) \| null |  |  |  |
| `due_from` | 쿼리 | string (date) \| null |  |  |  |
| `due_to` | 쿼리 | string (date) \| null |  |  |  |
| `page` | 쿼리 | integer |  | `1` | ≥ 1 |
| `size` | 쿼리 | integer |  | `20` | ≥ 1, ≤ 100 |

응답 `200`: [Page_HomeworkOut_](#schema-page-homeworkout-)

<a id="op-post-homework"></a>

#### POST `/api/v1/homework`

**과제 등록** · 단계 `확장` · 권한 원장, 실장, 교사

요청 본문: [HomeworkCreate](#schema-homeworkcreate)

응답 `201`: [HomeworkOut](#schema-homeworkout)

<a id="op-patch-homework-homework_id"></a>

#### PATCH `/api/v1/homework/{homework_id}`

**과제 수정** · 단계 `확장` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `homework_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [HomeworkUpdate](#schema-homeworkupdate)

응답 `200`: [HomeworkOut](#schema-homeworkout)

<a id="op-get-homework-homework_id-submissions"></a>

#### GET `/api/v1/homework/{homework_id}/submissions`

**제출 현황** · 단계 `확장` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `homework_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [SubmissionOut](#schema-submissionout)[]

<a id="op-put-homework-homework_id-submissions"></a>

#### PUT `/api/v1/homework/{homework_id}/submissions`

**제출 기록 일괄 입력** · 단계 `확장` · 권한 원장, 실장, 교사

과제 모듈은 사실만 기록한다. 반복 미완료 판단은 규칙 엔진이 한다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `homework_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [SubmissionBatch](#schema-submissionbatch)

응답 `200`: [SubmissionOut](#schema-submissionout)[]

### 규칙 엔진

<a id="op-get-rules-settings"></a>

#### GET `/api/v1/rules/settings`

**안내 규칙 설정 조회** · 단계 `MVP` · 권한 원장, 실장

응답 `200`: [RuleSettings](#schema-rulesettings)

<a id="op-put-rules-settings"></a>

#### PUT `/api/v1/rules/settings`

**안내 규칙 설정 저장** · 단계 `MVP` · 권한 원장

기준값은 코드 상수가 아니라 학원별 설정이다. 변경 내역은 감사 로그에 남는다.

요청 본문: [RuleSettings](#schema-rulesettings)

응답 `200`: [RuleSettings](#schema-rulesettings)

<a id="op-get-rules-runs"></a>

#### GET `/api/v1/rules/runs`

**실행 기록** · 단계 `MVP` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `page` | 쿼리 | integer |  | `1` | ≥ 1 |
| `size` | 쿼리 | integer |  | `20` | ≥ 1, ≤ 100 |

응답 `200`: [Page_RuleRunOut_](#schema-page-rulerunout-)

<a id="op-post-rules-runs"></a>

#### POST `/api/v1/rules/runs`

**규칙 엔진 수동 실행** · 단계 `MVP` · 권한 원장, 실장

평소에는 Celery beat가 매일 정해진 시각에 실행한다. dry_run으로 결과를 미리 볼 수 있다.

요청 본문: [RuleRunCreate](#schema-ruleruncreate)

응답 `202`: [RuleRunOut](#schema-rulerunout)

<a id="op-get-rules-runs-run_id"></a>

#### GET `/api/v1/rules/runs/{run_id}`

**실행 결과** · 단계 `MVP` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `run_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [RuleRunOut](#schema-rulerunout)

### 승인함

<a id="op-get-approvals"></a>

#### GET `/api/v1/approvals`

**승인함 목록** · 단계 `MVP` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `status` | 쿼리 | [ApprovalStatus](#schema-approvalstatus) |  | `"pending"` |  |
| `kind` | 쿼리 | [NoticeKind](#schema-noticekind) \| null |  |  |  |
| `mine` | 쿼리 | boolean |  | `false` | 내가 승인할 수 있는 건만 |
| `page` | 쿼리 | integer |  | `1` | ≥ 1 |
| `size` | 쿼리 | integer |  | `20` | ≥ 1, ≤ 100 |

응답 `200`: [Page_ApprovalSummary_](#schema-page-approvalsummary-)

<a id="op-post-approvals-bulk-approve"></a>

#### POST `/api/v1/approvals/bulk-approve`

**여러 건 한 번에 승인** · 단계 `MVP` · 권한 원장, 실장, 교사

문구 수정 없이 승인한다. 건별로 성공·실패를 돌려준다.

요청 본문: [IdsBody](#schema-idsbody)

응답 `200`: [BulkResult](#schema-bulkresult)

<a id="op-get-approvals-approval_id"></a>

#### GET `/api/v1/approvals/{approval_id}`

**승인 상세** · 단계 `MVP` · 권한 원장, 실장, 교사

수신자, 사실, 근거, 문구를 나란히 보여준다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `approval_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [ApprovalDetail](#schema-approvaldetail)

<a id="op-post-approvals-approval_id-approve"></a>

#### POST `/api/v1/approvals/{approval_id}/approve`

**승인 (수정 후 승인 포함)** · 단계 `MVP` · 권한 원장, 실장, 교사

승인 시점의 사실을 스냅샷으로 저장한다. 발송 직전에 DB를 다시 확인해 스냅샷과 다르면(예: 그 사이 납부) 발송을 취소한다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `approval_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [ApproveBody](#schema-approvebody)

응답 `200`: [ApprovalDetail](#schema-approvaldetail)

<a id="op-post-approvals-approval_id-hold"></a>

#### POST `/api/v1/approvals/{approval_id}/hold`

**보류** · 단계 `MVP` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `approval_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [HoldBody](#schema-holdbody)

응답 `200`: [ApprovalDetail](#schema-approvaldetail)

<a id="op-post-approvals-approval_id-reject"></a>

#### POST `/api/v1/approvals/{approval_id}/reject`

**반려** · 단계 `MVP` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `approval_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [RejectBody](#schema-rejectbody)

응답 `200`: [ApprovalDetail](#schema-approvaldetail)

### 템플릿

<a id="op-get-templates"></a>

#### GET `/api/v1/templates`

**템플릿 목록** · 단계 `MVP` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `kind` | 쿼리 | [NoticeKind](#schema-noticekind) \| null |  |  |  |
| `archived` | 쿼리 | boolean |  | `false` |  |

응답 `200`: [TemplateOut](#schema-templateout)[]

<a id="op-post-templates"></a>

#### POST `/api/v1/templates`

**템플릿 만들기 (버전 1 초안)** · 단계 `MVP` · 권한 원장, 실장

요청 본문: [TemplateCreate](#schema-templatecreate)

응답 `201`: [TemplateOut](#schema-templateout)

<a id="op-get-templates-template_id"></a>

#### GET `/api/v1/templates/{template_id}`

**템플릿 상세** · 단계 `MVP` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `template_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [TemplateOut](#schema-templateout)

<a id="op-patch-templates-template_id"></a>

#### PATCH `/api/v1/templates/{template_id}`

**템플릿 이름 수정·보관** · 단계 `MVP` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `template_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [TemplateUpdate](#schema-templateupdate)

응답 `200`: [TemplateOut](#schema-templateout)

<a id="op-get-templates-template_id-versions"></a>

#### GET `/api/v1/templates/{template_id}/versions`

**템플릿 버전 목록** · 단계 `MVP` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `template_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [TemplateVersionOut](#schema-templateversionout)[]

<a id="op-post-templates-template_id-versions"></a>

#### POST `/api/v1/templates/{template_id}/versions`

**새 버전 초안** · 단계 `MVP` · 권한 원장, 실장

문구를 고치면 새 버전이 생긴다. 이미 보낸 건은 당시 버전을 기록하고 있다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `template_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [TemplateVersionCreate](#schema-templateversioncreate)

응답 `201`: [TemplateVersionOut](#schema-templateversionout)

<a id="op-post-templates-template_id-versions-version-approve"></a>

#### POST `/api/v1/templates/{template_id}/versions/{version}/approve`

**버전 승인** · 단계 `MVP` · 권한 원장, 실장

승인된 버전만 발송에 쓴다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `template_id` | 경로 | string (uuid) | 예 |  |  |
| `version` | 경로 | integer | 예 |  |  |

응답 `200`: [TemplateVersionOut](#schema-templateversionout)

<a id="op-post-templates-template_id-preview"></a>

#### POST `/api/v1/templates/{template_id}/preview`

**자리 표시 채워 미리 보기** · 단계 `MVP` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `template_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [PreviewBody](#schema-previewbody)

응답 `200`: [PreviewOut](#schema-previewout)

<a id="op-get-templates-template_id-versions-version-translations"></a>

#### GET `/api/v1/templates/{template_id}/versions/{version}/translations`

**번역 목록** · 단계 `확장` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `template_id` | 경로 | string (uuid) | 예 |  |  |
| `version` | 경로 | integer | 예 |  |  |

응답 `200`: [TranslationOut](#schema-translationout)[]

<a id="op-post-templates-template_id-versions-version-translations"></a>

#### POST `/api/v1/templates/{template_id}/versions/{version}/translations`

**번역 생성 요청 (AI)** · 단계 `확장` · 권한 원장, 실장

템플릿 버전 × 언어 단위로 한 번 번역한다. 자리 표시는 번역하지 않고 그대로 둔다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `template_id` | 경로 | string (uuid) | 예 |  |  |
| `version` | 경로 | integer | 예 |  |  |

요청 본문: [TranslationRequest](#schema-translationrequest)

응답 `202`: [TranslationOut](#schema-translationout)

<a id="op-patch-templates-template_id-versions-version-translations-language"></a>

#### PATCH `/api/v1/templates/{template_id}/versions/{version}/translations/{language}`

**번역 수정·승인** · 단계 `확장` · 권한 원장, 실장

검증 오류가 남아 있으면 승인할 수 없다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `template_id` | 경로 | string (uuid) | 예 |  |  |
| `version` | 경로 | integer | 예 |  |  |
| `language` | 경로 | string | 예 |  |  |

요청 본문: [TranslationUpdate](#schema-translationupdate)

응답 `200`: [TranslationOut](#schema-translationout)

### 안내 후보

<a id="op-get-candidates"></a>

#### GET `/api/v1/candidates`

**안내 후보 목록** · 단계 `MVP` · 권한 원장, 실장, 교사

규칙 엔진이 만든 모든 후보. 승인이 필요한 건은 승인함(/approvals)에서 처리한다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `status` | 쿼리 | [CandidateStatus](#schema-candidatestatus) \| null |  |  |  |
| `kind` | 쿼리 | [NoticeKind](#schema-noticekind) \| null |  |  |  |
| `student_id` | 쿼리 | string (uuid) \| null |  |  |  |
| `rule_run_id` | 쿼리 | string (uuid) \| null |  |  |  |
| `page` | 쿼리 | integer |  | `1` | ≥ 1 |
| `size` | 쿼리 | integer |  | `20` | ≥ 1, ≤ 100 |

응답 `200`: [Page_CandidateOut_](#schema-page-candidateout-)

<a id="op-get-candidates-candidate_id"></a>

#### GET `/api/v1/candidates/{candidate_id}`

**안내 후보 상세** · 단계 `MVP` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `candidate_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [CandidateOut](#schema-candidateout)

<a id="op-post-candidates-candidate_id-cancel"></a>

#### POST `/api/v1/candidates/{candidate_id}/cancel`

**안내 후보 취소** · 단계 `MVP` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `candidate_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [CancelBody](#schema-cancelbody)

응답 `200`: [CandidateOut](#schema-candidateout)

### 발송 이력

<a id="op-get-messages"></a>

#### GET `/api/v1/messages`

**발송 이력** · 단계 `MVP` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `status` | 쿼리 | [MessageStatus](#schema-messagestatus) \| null |  |  |  |
| `student_id` | 쿼리 | string (uuid) \| null |  |  |  |
| `guardian_id` | 쿼리 | string (uuid) \| null |  |  |  |
| `from` | 쿼리 | string (date-time) \| null |  |  |  |
| `to` | 쿼리 | string (date-time) \| null |  |  |  |
| `page` | 쿼리 | integer |  | `1` | ≥ 1 |
| `size` | 쿼리 | integer |  | `20` | ≥ 1, ≤ 100 |

응답 `200`: [Page_MessageOut_](#schema-page-messageout-)

<a id="op-get-messages-message_id"></a>

#### GET `/api/v1/messages/{message_id}`

**발송 건 상세** · 단계 `MVP` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `message_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [MessageOut](#schema-messageout)

<a id="op-post-messages-message_id-cancel"></a>

#### POST `/api/v1/messages/{message_id}/cancel`

**예약 발송 취소** · 단계 `MVP` · 권한 원장, 실장

scheduled 상태에서만 가능하다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `message_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [CancelBody](#schema-cancelbody)

응답 `200`: [MessageOut](#schema-messageout)

<a id="op-post-messages-message_id-corrections"></a>

#### POST `/api/v1/messages/{message_id}/corrections`

**오발송 정정 안내 만들기** · 단계 `제안` · 권한 원장, 실장

정정 안내 초안을 승인함에 올리고, 같은 사유 후속 안내를 멈추고, 원인을 기록한다. 응답은 생성된 정정 안내 후보.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `message_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [CorrectionBody](#schema-correctionbody)

응답 `201`: [CandidateOut](#schema-candidateout)

### 회신

<a id="op-get-replies"></a>

#### GET `/api/v1/replies`

**학부모 회신 목록** · 단계 `MVP` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `status` | 쿼리 | [ReplyStatus](#schema-replystatus) \| null |  | `"open"` |  |
| `intent` | 쿼리 | [ReplyIntent](#schema-replyintent) \| null |  |  |  |
| `student_id` | 쿼리 | string (uuid) \| null |  |  |  |
| `page` | 쿼리 | integer |  | `1` | ≥ 1 |
| `size` | 쿼리 | integer |  | `20` | ≥ 1, ≤ 100 |

응답 `200`: [Page_ReplyOut_](#schema-page-replyout-)

<a id="op-get-replies-reply_id"></a>

#### GET `/api/v1/replies/{reply_id}`

**회신 상세** · 단계 `MVP` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `reply_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [ReplyOut](#schema-replyout)

<a id="op-patch-replies-reply_id"></a>

#### PATCH `/api/v1/replies/{reply_id}`

**회신 분류 확정·처리 완료** · 단계 `MVP` · 권한 원장, 실장, 교사

paid·correction·consult_request로 확정하면 같은 사유 후속 안내를 멈춘다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `reply_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [ReplyUpdate](#schema-replyupdate)

응답 `200`: [ReplyOut](#schema-replyout)

### 수납 안내 PDF

<a id="op-post-documents-billing-notices"></a>

#### POST `/api/v1/documents/billing-notices`

**수납 안내 PDF 생성** · 단계 `확장` · 권한 원장, 실장

수납 3단계 승인이 끝난 건만 가능하다. 생성 시점 DB 값이 아니라 승인 스냅샷 값으로 만든다.

요청 본문: [BillingNoticeCreate](#schema-billingnoticecreate)

응답 `202`: [DocumentOut](#schema-documentout)

<a id="op-get-documents-document_id"></a>

#### GET `/api/v1/documents/{document_id}`

**PDF 상태** · 단계 `확장` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `document_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [DocumentOut](#schema-documentout)

<a id="op-post-documents-document_id-links"></a>

#### POST `/api/v1/documents/{document_id}/links`

**만료되는 열람 링크 발급** · 단계 `확장` · 권한 원장, 실장

비공개 저장소의 서명 URL. 발급 기록이 감사 로그에 남는다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `document_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [DocumentLink](#schema-documentlink)

### 감사 로그

<a id="op-get-audit-logs"></a>

#### GET `/api/v1/audit-logs`

**감사 로그 조회** · 단계 `MVP` · 권한 원장, 실장

추가만 가능한 기록이라 수정·삭제 엔드포인트는 없다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `entity_type` | 쿼리 | string \| null |  |  |  |
| `entity_id` | 쿼리 | string (uuid) \| null |  |  |  |
| `actor_id` | 쿼리 | string (uuid) \| null |  |  |  |
| `from` | 쿼리 | string (date-time) \| null |  |  |  |
| `to` | 쿼리 | string (date-time) \| null |  |  |  |
| `page` | 쿼리 | integer |  | `1` | ≥ 1 |
| `size` | 쿼리 | integer |  | `20` | ≥ 1, ≤ 100 |

응답 `200`: [Page_AuditLogOut_](#schema-page-auditlogout-)

### AI 보조

<a id="op-post-ai-replies-reply_id-classify"></a>

#### POST `/api/v1/ai/replies/{reply_id}/classify`

**회신 분류·후속 업무 제안** · 단계 `확장` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `reply_id` | 경로 | string (uuid) | 예 |  |  |

응답 `202`: [AiRunOut](#schema-airunout)

<a id="op-post-ai-candidates-candidate_id-draft"></a>

#### POST `/api/v1/ai/candidates/{candidate_id}/draft`

**안내문 초안** · 단계 `확장` · 권한 원장, 실장

자리 표시가 남은 문구를 만든다. 숫자·날짜는 코드가 채운다. 결과는 승인함으로 간다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `candidate_id` | 경로 | string (uuid) | 예 |  |  |

응답 `202`: [AiRunOut](#schema-airunout)

<a id="op-post-ai-students-student_id-summary"></a>

#### POST `/api/v1/ai/students/{student_id}/summary`

**상담 전 연락 이력 요약** · 단계 `확장` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `student_id` | 경로 | string (uuid) | 예 |  |  |

응답 `202`: [AiRunOut](#schema-airunout)

<a id="op-post-ai-mismatch-scans"></a>

#### POST `/api/v1/ai/mismatch-scans`

**수납·출결 불일치 후보 찾기** · 단계 `확장` · 권한 원장, 실장

찾은 후보는 확인 필요함(ai_mismatch)에 올라간다.

요청 본문: [MismatchScanBody](#schema-mismatchscanbody)

응답 `202`: [AiRunOut](#schema-airunout)

<a id="op-get-ai-runs"></a>

#### GET `/api/v1/ai/runs`

**AI 실행 기록** · 단계 `확장` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `task` | 쿼리 | [AiTask](#schema-aitask) \| null |  |  |  |
| `page` | 쿼리 | integer |  | `1` | ≥ 1 |
| `size` | 쿼리 | integer |  | `20` | ≥ 1, ≤ 100 |

응답 `200`: [Page_AiRunOut_](#schema-page-airunout-)

<a id="op-get-ai-runs-run_id"></a>

#### GET `/api/v1/ai/runs/{run_id}`

**AI 실행 결과** · 단계 `확장` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `run_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [AiRunOut](#schema-airunout)

<a id="op-get-ai-runs-run_id-steps"></a>

#### GET `/api/v1/ai/runs/{run_id}/steps`

**AI 실행 단계별 기록** · 단계 `확장` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `run_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [AiStepOut](#schema-aistepout)[]

<a id="op-post-ai-runs-run_id-feedback"></a>

#### POST `/api/v1/ai/runs/{run_id}/feedback`

**AI 결과 채택·수정 기록** · 단계 `확장` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `run_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [FeedbackBody](#schema-feedbackbody)

응답 `204`: (본문 없음)

### 웹훅

<a id="op-post-webhooks-sms-provider-delivery"></a>

#### POST `/api/v1/webhooks/sms/{provider}/delivery`

**발송 결과 수신** · 단계 `MVP` · 권한 공개 (서명 검증)

발송 이력 상태를 갱신한다. 알림톡 실패면 문자 대체 발송을 예약한다. 같은 이벤트가 여러 번 와도 한 번만 반영한다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `provider` | 경로 | string | 예 |  |  |

요청 본문: object

응답 `204`: (본문 없음)

<a id="op-post-webhooks-sms-provider-inbound"></a>

#### POST `/api/v1/webhooks/sms/{provider}/inbound`

**학부모 회신 수신** · 단계 `MVP` · 권한 공개 (서명 검증)

회신을 저장하고 원래 발송 건과 연결한다. 외국어면 번역을, AI가 켜져 있으면 분류를 요청한다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `provider` | 경로 | string | 예 |  |  |

요청 본문: object

응답 `204`: (본문 없음)

### 공개 링크

<a id="op-get-public-replies-token"></a>

#### GET `/api/v1/public/replies/{token}`

**원클릭 응답 화면 정보** · 단계 `제안` · 권한 공개 (일회용 토큰)

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `token` | 경로 | string | 예 |  | 길이 ≥ 16, 길이 ≤ 128 |

응답 `200`: [PublicReplyPage](#schema-publicreplypage)

<a id="op-post-public-replies-token"></a>

#### POST `/api/v1/public/replies/{token}`

**원클릭 응답 제출** · 단계 `제안` · 권한 공개 (일회용 토큰)

AI 분류 없이 의도가 기록되고, 같은 사유 후속 안내가 바로 멈추며 담당자 확인 작업이 생긴다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `token` | 경로 | string | 예 |  | 길이 ≥ 16, 길이 ≤ 128 |

요청 본문: [PublicReplyBody](#schema-publicreplybody)

응답 `200`: [PublicReplyResult](#schema-publicreplyresult)

### 상태

<a id="op-get--health"></a>

#### GET `/health`

**서버 상태 확인** · 단계 `-` · 권한 공개

응답 `200`: map<string, string>

## 스키마

요청·응답 본문의 필드. *는 필수.

<a id="schema-academyout"></a>

#### AcademyOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `name`* | string |  |  |
| `timezone` | string | `"Asia/Seoul"` |  |
| `phone` | string \| null |  |  |
| `created_at`* | string (date-time) |  |  |

<a id="schema-academyupdate"></a>

#### AcademyUpdate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `name` | string \| null |  |  |
| `timezone` | string \| null |  |  |
| `phone` | string \| null |  |  |

<a id="schema-airunout"></a>

#### AiRunOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `task`* | [AiTask](#schema-aitask) |  |  |
| `status`* | [AiRunStatus](#schema-airunstatus) |  |  |
| `target_type`* | string |  |  |
| `target_id` | string (uuid) \| null |  |  |
| `output` | object \| null |  |  |
| `evidence_ids` | string (uuid)[] | `[]` | 근거로 쓴 기록·문서 조각 |
| `validation_errors` | string[] | `[]` |  |
| `prompt_id`* | string |  |  |
| `prompt_version`* | string |  |  |
| `model`* | string |  |  |
| `created_by`* | string (uuid) |  |  |
| `created_at`* | string (date-time) |  |  |
| `finished_at` | string (date-time) \| null |  |  |

<a id="schema-airunstatus"></a>

#### AiRunStatus

값: `queued`, `running`, `succeeded`, `needs_review`, `failed`

<a id="schema-aistepout"></a>

#### AiStepOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `seq`* | integer |  |  |
| `node`* | string |  | fetch_facts, retrieve, draft, validate 등 |
| `tool` | string \| null |  |  |
| `input_summary` | string \| null |  |  |
| `output_summary` | string \| null |  |  |
| `duration_ms`* | integer |  |  |
| `error` | string \| null |  |  |

<a id="schema-aitask"></a>

#### AiTask

값: `reply_classification`, `draft`, `consult_summary`, `mismatch_detection`, `translation`

<a id="schema-alertack"></a>

#### AlertAck

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `note` | string \| null |  | 예: 보호자와 통화, 병원 진료 |

<a id="schema-alertkind"></a>

#### AlertKind

값: `unexcused_absence`, `sibling_absence`

<a id="schema-alertstatus"></a>

#### AlertStatus

값: `open`, `acknowledged`

<a id="schema-allocation"></a>

#### Allocation

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `invoice_id`* | string (uuid) |  |  |
| `amount`* | integer |  | > 0 |

<a id="schema-approvaldetail"></a>

#### ApprovalDetail

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `candidate_id`* | string (uuid) |  |  |
| `kind`* | [NoticeKind](#schema-noticekind) |  |  |
| `stage` | integer \| null |  |  |
| `student_names`* | string[] |  |  |
| `guardian_name`* | string |  |  |
| `status`* | [ApprovalStatus](#schema-approvalstatus) |  |  |
| `reason`* | string |  |  |
| `can_approve`* | boolean |  | 요청한 사용자의 역할로 승인할 수 있는지 |
| `created_at`* | string (date-time) |  |  |
| `facts`* | object |  | 승인 화면에 보여줄 사실. 금액·날짜 등. 승인 시 스냅샷으로 저장 |
| `evidence` | [EvidenceRef](#schema-evidenceref)[] | `[]` |  |
| `body_template`* | string |  | 자리 표시가 남아 있는 문구 ({amount} 등) |
| `rendered_body`* | string |  | 사실 값으로 채운 미리 보기 |
| `language` | string | `"ko"` |  |
| `translated_body` | string \| null |  |  |
| `ai_run_id` | string (uuid) \| null |  | AI가 초안을 쓴 경우 |
| `history` | [ApprovalEvent](#schema-approvalevent)[] | `[]` |  |

<a id="schema-approvalevent"></a>

#### ApprovalEvent

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `at`* | string (date-time) |  |  |
| `actor_id` | string (uuid) \| null |  |  |
| `action`* | string |  |  |
| `note` | string \| null |  |  |

<a id="schema-approvalstatus"></a>

#### ApprovalStatus

값: `pending`, `approved`, `edited_approved`, `held`, `rejected`, `expired`

<a id="schema-approvalsummary"></a>

#### ApprovalSummary

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `candidate_id`* | string (uuid) |  |  |
| `kind`* | [NoticeKind](#schema-noticekind) |  |  |
| `stage` | integer \| null |  |  |
| `student_names`* | string[] |  |  |
| `guardian_name`* | string |  |  |
| `status`* | [ApprovalStatus](#schema-approvalstatus) |  |  |
| `reason`* | string |  |  |
| `can_approve`* | boolean |  | 요청한 사용자의 역할로 승인할 수 있는지 |
| `created_at`* | string (date-time) |  |  |

<a id="schema-approvebody"></a>

#### ApproveBody

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `edited_body` | string \| null |  | 문구를 고친 경우. 자리 표시 밖에 숫자를 직접 쓰면 거절된다 |
| `scheduled_at` | string (date-time) \| null |  | 비우면 다음 발송 가능 시간대 |

<a id="schema-attendancealertout"></a>

#### AttendanceAlertOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `kind`* | [AlertKind](#schema-alertkind) |  |  |
| `student_ids`* | string (uuid)[] |  |  |
| `student_names`* | string[] |  |  |
| `class_id`* | string (uuid) |  |  |
| `date`* | string (date) |  |  |
| `status`* | [AlertStatus](#schema-alertstatus) |  |  |
| `created_at`* | string (date-time) |  |  |
| `escalated_at` | string (date-time) \| null |  | 담당 교사 미확인으로 실장·원장에게 다시 알린 시각 |
| `acknowledged_by` | string (uuid) \| null |  |  |
| `acknowledged_at` | string (date-time) \| null |  |  |
| `note` | string \| null |  |  |

<a id="schema-attendancebatch"></a>

#### AttendanceBatch

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `items`* | [AttendanceItem](#schema-attendanceitem)[] |  | 개수 ≥ 1, 개수 ≤ 500 |

<a id="schema-attendancecorrection"></a>

#### AttendanceCorrection

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `status`* | [AttendanceStatus](#schema-attendancestatus) |  |  |
| `note` | string \| null |  |  |
| `reason`* | string |  | 정정 사유. 이미 나간 안내가 있으면 정정 안내 후보가 생긴다 |

<a id="schema-attendanceitem"></a>

#### AttendanceItem

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `student_id`* | string (uuid) |  |  |
| `class_id`* | string (uuid) |  |  |
| `date`* | string (date) |  |  |
| `status`* | [AttendanceStatus](#schema-attendancestatus) |  |  |
| `note` | string \| null |  |  |

<a id="schema-attendanceout"></a>

#### AttendanceOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `student_id`* | string (uuid) |  |  |
| `student_name`* | string |  |  |
| `class_id`* | string (uuid) |  |  |
| `date`* | string (date) |  |  |
| `status`* | [AttendanceStatus](#schema-attendancestatus) |  |  |
| `note` | string \| null |  |  |
| `recorded_at`* | string (date-time) |  |  |
| `recorded_by` | string (uuid) \| null |  |  |
| `is_late_entry`* | boolean |  | 수업 시작 후 기준 시간이 지나 입력됨 → 안내 전 확인 |

<a id="schema-attendancestatus"></a>

#### AttendanceStatus

값: `present`, `late`, `absent`, `excused`, `early_leave`, `makeup`

<a id="schema-auditlogout"></a>

#### AuditLogOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `at`* | string (date-time) |  |  |
| `actor_id` | string (uuid) \| null |  |  |
| `actor_name` | string \| null |  |  |
| `action`* | string |  |  |
| `entity_type`* | string |  |  |
| `entity_id`* | string (uuid) |  |  |
| `before` | object \| null |  |  |
| `after` | object \| null |  |  |
| `reason` | string \| null |  |  |

<a id="schema-billingnoticecreate"></a>

#### BillingNoticeCreate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `approval_id`* | string (uuid) |  |  |

<a id="schema-billingstage"></a>

#### BillingStage

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `stage`* | integer |  | ≥ 1 |
| `days_after_due`* | integer |  | ≥ 0 |
| `requires_approval`* | boolean |  |  |

<a id="schema-body-upload-api-v1-imports-post"></a>

#### Body_upload_api_v1_imports_post

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `kind`* | [ImportKind](#schema-importkind) |  |  |
| `file`* | string |  | .csv, .xlsx |

<a id="schema-branchcreate"></a>

#### BranchCreate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `name`* | string |  |  |
| `address` | string \| null |  |  |

<a id="schema-branchout"></a>

#### BranchOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `name`* | string |  |  |
| `address` | string \| null |  |  |

<a id="schema-branchupdate"></a>

#### BranchUpdate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `name` | string \| null |  |  |
| `address` | string \| null |  |  |

<a id="schema-briefing"></a>

#### Briefing

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `date`* | string (date) |  |  |
| `summary`* | [TodaySummary](#schema-todaysummary) |  |  |
| `held_reasons`* | map<string, integer> |  | 보류 사유별 건수 |
| `overnight_replies`* | integer |  |  |
| `reply_digest` | string \| null |  | AI 요약 (선택) |

<a id="schema-bulkresult"></a>

#### BulkResult

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `succeeded`* | string (uuid)[] |  |  |
| `failed` | map<string, string> |  | ID → 실패 사유 |

<a id="schema-calendareventcreate"></a>

#### CalendarEventCreate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `kind`* | [CalendarKind](#schema-calendarkind) |  |  |
| `start_date`* | string (date) |  |  |
| `end_date`* | string (date) |  |  |
| `student_id` | string (uuid) \| null |  | kind=student_leave일 때 필수 |
| `note` | string \| null |  |  |

<a id="schema-calendareventout"></a>

#### CalendarEventOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `kind`* | [CalendarKind](#schema-calendarkind) |  |  |
| `start_date`* | string (date) |  |  |
| `end_date`* | string (date) |  |  |
| `student_id` | string (uuid) \| null |  |  |
| `note` | string \| null |  |  |

<a id="schema-calendarkind"></a>

#### CalendarKind

값: `closure`, `vacation`, `holiday`, `student_leave`

<a id="schema-cancelbody"></a>

#### CancelBody

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `reason`* | string |  |  |

<a id="schema-candidateout"></a>

#### CandidateOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `kind`* | [NoticeKind](#schema-noticekind) |  |  |
| `stage` | integer \| null |  |  |
| `student_ids`* | string (uuid)[] |  |  |
| `guardian_id`* | string (uuid) |  |  |
| `status`* | [CandidateStatus](#schema-candidatestatus) |  |  |
| `dedupe_key`* | string |  | 예: invoice:{id}:stage:2. 같은 키는 한 번만 생성 |
| `reason`* | string |  | 규칙이 만든 이유. 예: 납부 기한 +3일, 잔액 150,000원 |
| `hold_reason` | string \| null |  |  |
| `rule_run_id`* | string (uuid) |  |  |
| `created_at`* | string (date-time) |  |  |

<a id="schema-candidatestatus"></a>

#### CandidateStatus

값: `awaiting_approval`, `scheduled`, `held`, `cancelled`, `sent`

<a id="schema-channel"></a>

#### Channel

값: `alimtalk`, `sms`

<a id="schema-classcreate"></a>

#### ClassCreate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `name`* | string |  |  |
| `branch_id` | string (uuid) \| null |  |  |
| `teacher_id` | string (uuid) \| null |  |  |
| `schedule` | [ClassSlot](#schema-classslot)[] | `[]` |  |

<a id="schema-classout"></a>

#### ClassOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `name`* | string |  |  |
| `branch_id` | string (uuid) \| null |  |  |
| `teacher_id` | string (uuid) \| null |  |  |
| `schedule` | [ClassSlot](#schema-classslot)[] | `[]` |  |
| `student_count` | integer | `0` |  |

<a id="schema-classslot"></a>

#### ClassSlot

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `weekday`* | integer |  | 0=월요일 ≥ 0, ≤ 6 |
| `start`* | string (time) |  |  |
| `end`* | string (time) |  |  |

<a id="schema-classupdate"></a>

#### ClassUpdate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `name` | string \| null |  |  |
| `teacher_id` | string (uuid) \| null |  |  |
| `schedule` | [ClassSlot](#schema-classslot)[] \| null |  |  |

<a id="schema-columnmappingbody"></a>

#### ColumnMappingBody

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `mapping`* | map<string, string> |  | 파일 열 이름 → 필드 이름 |

<a id="schema-correctionbody"></a>

#### CorrectionBody

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `reason`* | string |  | 오발송 원인 |

<a id="schema-deposit"></a>

#### Deposit

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `payer_name`* | string |  |  |
| `amount`* | integer |  |  |
| `deposited_at`* | string (date-time) |  |  |
| `import_batch_id`* | string (uuid) |  |  |

<a id="schema-depositmatchconfirm"></a>

#### DepositMatchConfirm

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `allocations`* | [Allocation](#schema-allocation)[] |  | 개수 ≥ 1 |
| `remember_payer_name` | boolean | `true` | 다음 달부터 이 입금자명을 자동 매칭 |

<a id="schema-depositmatchout"></a>

#### DepositMatchOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `deposit`* | [Deposit](#schema-deposit) |  |  |
| `candidates`* | [MatchCandidate](#schema-matchcandidate)[] |  |  |
| `status`* | [DepositMatchStatus](#schema-depositmatchstatus) |  |  |

<a id="schema-depositmatchreject"></a>

#### DepositMatchReject

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `note` | string \| null |  |  |

<a id="schema-depositmatchstatus"></a>

#### DepositMatchStatus

값: `pending`, `confirmed`, `rejected`

<a id="schema-documentlink"></a>

#### DocumentLink

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `url`* | string |  |  |
| `expires_at`* | string (date-time) |  |  |

<a id="schema-documentout"></a>

#### DocumentOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `kind` | string | `"billing_notice"` |  |
| `approval_id`* | string (uuid) |  |  |
| `status`* | [DocumentStatus](#schema-documentstatus) |  |  |
| `created_at`* | string (date-time) |  |  |

<a id="schema-documentstatus"></a>

#### DocumentStatus

값: `generating`, `ready`, `failed`

<a id="schema-enrollbody"></a>

#### EnrollBody

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `student_ids`* | string (uuid)[] |  | 개수 ≥ 1 |

<a id="schema-errorbody"></a>

#### ErrorBody

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `detail`* | string |  |  |

<a id="schema-evidenceref"></a>

#### EvidenceRef

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `kind`* | string |  | invoice, payment, attendance, reply, rag_chunk 등 |
| `ref_id`* | string (uuid) |  |  |
| `label`* | string |  |  |

<a id="schema-feedbackbody"></a>

#### FeedbackBody

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `accepted`* | boolean |  |  |
| `edited_output` | object \| null |  | 담당자가 고친 결과 (수정률 측정) |
| `note` | string \| null |  |  |

<a id="schema-fieldspec"></a>

#### FieldSpec

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `field`* | string |  |  |
| `label`* | string |  |  |
| `required`* | boolean |  |  |
| `example` | string \| null |  |  |

<a id="schema-guardiancreate"></a>

#### GuardianCreate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `name`* | string |  |  |
| `phone`* | string |  |  |
| `preferred_language` | string | `"ko"` |  |
| `consent_notices` | boolean | `true` |  |

<a id="schema-guardianlink"></a>

#### GuardianLink

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `guardian`* | [GuardianOut](#schema-guardianout) |  |  |
| `relation`* | string |  | 모, 부, 조모 등 |
| `is_primary`* | boolean |  | 기본 수신자 |
| `receives_notices`* | boolean |  |  |

<a id="schema-guardianlinkcreate"></a>

#### GuardianLinkCreate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `guardian_id` | string (uuid) \| null |  | 기존 보호자 연결. 없으면 new_guardian |
| `new_guardian` | [GuardianCreate](#schema-guardiancreate) \| null |  |  |
| `relation`* | string |  |  |
| `is_primary` | boolean | `false` |  |
| `receives_notices` | boolean | `true` |  |

<a id="schema-guardianlinkupdate"></a>

#### GuardianLinkUpdate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `relation` | string \| null |  |  |
| `is_primary` | boolean \| null |  |  |
| `receives_notices` | boolean \| null |  |  |

<a id="schema-guardianout"></a>

#### GuardianOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `name`* | string |  |  |
| `phone_masked`* | string |  | 010-****-1234. 원문은 발송 시점에만 복호화 |
| `preferred_language` | string | `"ko"` | 수신 언어: ko, en, ko-easy 등 |
| `consent_notices`* | boolean |  | 안내 수신 동의 |

<a id="schema-guardianupdate"></a>

#### GuardianUpdate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `name` | string \| null |  |  |
| `phone` | string \| null |  |  |
| `preferred_language` | string \| null |  |  |
| `consent_notices` | boolean \| null |  |  |

<a id="schema-holdbody"></a>

#### HoldBody

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `reason`* | string |  |  |
| `until` | string (date) \| null |  |  |

<a id="schema-holdcreate"></a>

#### HoldCreate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `reason`* | [HoldReason](#schema-holdreason) |  |  |
| `note` | string \| null |  |  |

<a id="schema-holdout"></a>

#### HoldOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `reason`* | [HoldReason](#schema-holdreason) |  |  |
| `note` | string \| null |  |  |
| `created_by` | string (uuid) \| null |  | 규칙 엔진이 건 보류면 null |
| `created_at`* | string (date-time) |  |  |

<a id="schema-holdreason"></a>

#### HoldReason

값: `depositor_mismatch`, `partial_payment`, `installment_promise`, `refund`, `leave_or_withdrawal`, `dispute`, `manual`

<a id="schema-homeworkcreate"></a>

#### HomeworkCreate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `class_id`* | string (uuid) |  |  |
| `title`* | string |  |  |
| `due_date`* | string (date) |  |  |

<a id="schema-homeworkout"></a>

#### HomeworkOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `class_id`* | string (uuid) |  |  |
| `title`* | string |  |  |
| `due_date`* | string (date) |  |  |
| `created_by`* | string (uuid) |  |  |
| `created_at`* | string (date-time) |  |  |
| `missing_count` | integer | `0` |  |

<a id="schema-homeworkupdate"></a>

#### HomeworkUpdate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `title` | string \| null |  |  |
| `due_date` | string (date) \| null |  |  |

<a id="schema-householdcreate"></a>

#### HouseholdCreate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `student_ids`* | string (uuid)[] |  | 개수 ≥ 2 |
| `name` | string \| null |  |  |

<a id="schema-householdmembersadd"></a>

#### HouseholdMembersAdd

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `student_ids`* | string (uuid)[] |  | 개수 ≥ 1 |

<a id="schema-householdout"></a>

#### HouseholdOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `name` | string \| null |  | 예: 김민준·김서연 가구 |
| `students`* | [StudentSummary](#schema-studentsummary)[] |  |  |
| `guardians`* | [GuardianOut](#schema-guardianout)[] |  |  |
| `open_balance` | integer | `0` | 가구 전체 미납 잔액(원) |

<a id="schema-householdsuggestion"></a>

#### HouseholdSuggestion

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `students`* | [StudentSummary](#schema-studentsummary)[] |  |  |
| `reason`* | [SuggestionReason](#schema-suggestionreason) |  |  |
| `evidence`* | string |  | 예: 보호자 연락처 010-****-1234 공유 |
| `status`* | [SuggestionStatus](#schema-suggestionstatus) |  |  |
| `created_at`* | string (date-time) |  |  |

<a id="schema-householdupdate"></a>

#### HouseholdUpdate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `name` | string \| null |  |  |

<a id="schema-idsbody"></a>

#### IdsBody

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `ids`* | string (uuid)[] |  | 개수 ≥ 1, 개수 ≤ 200 |

<a id="schema-importbatchout"></a>

#### ImportBatchOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `kind`* | [ImportKind](#schema-importkind) |  |  |
| `source`* | string |  | file 또는 google_sheets |
| `filename` | string \| null |  |  |
| `status`* | [ImportStatus](#schema-importstatus) |  |  |
| `row_count` | integer | `0` |  |
| `ok_count` | integer | `0` |  |
| `error_count` | integer | `0` |  |
| `warning_count` | integer | `0` |  |
| `duplicate_count` | integer | `0` |  |
| `column_mapping` | map<string, string> \| null |  | 파일 열 이름 → 필드 |
| `created_by`* | string (uuid) |  |  |
| `created_at`* | string (date-time) |  |  |
| `committed_at` | string (date-time) \| null |  |  |

<a id="schema-importkind"></a>

#### ImportKind

값: `students`, `invoices`, `payments`, `attendance`, `homework`, `bank_deposits`

<a id="schema-importrowout"></a>

#### ImportRowOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `row_number`* | integer |  |  |
| `status`* | [RowStatus](#schema-rowstatus) |  |  |
| `data`* | map<string, string \| null> |  |  |
| `messages` | string[] | `[]` |  |

<a id="schema-importstatus"></a>

#### ImportStatus

값: `uploaded`, `mapping_required`, `validating`, `validated`, `committed`, `discarded`, `failed`

<a id="schema-intentsource"></a>

#### IntentSource

값: `button`, `ai`, `staff`

<a id="schema-invoicecreate"></a>

#### InvoiceCreate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `student_id`* | string (uuid) |  |  |
| `billing_month`* | string |  | `형식 ^\d{4}-\d{2}$` |
| `due_date`* | string (date) |  |  |
| `amount`* | integer |  | ≥ 0 |
| `discount` | integer | `0` | ≥ 0 |
| `memo` | string \| null |  |  |

<a id="schema-invoiceout"></a>

#### InvoiceOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `student_id`* | string (uuid) |  |  |
| `student_name`* | string |  |  |
| `household_id` | string (uuid) \| null |  |  |
| `billing_month`* | string |  | `형식 ^\d{4}-\d{2}$` |
| `due_date`* | string (date) |  |  |
| `amount`* | integer |  | ≥ 0 |
| `discount` | integer | `0` | ≥ 0 |
| `paid` | integer | `0` | ≥ 0 |
| `balance`* | integer |  | amount - discount - paid |
| `status`* | [InvoiceStatus](#schema-invoicestatus) |  |  |
| `overdue_days` | integer | `0` |  |
| `holds` | [HoldOut](#schema-holdout)[] | `[]` |  |

<a id="schema-invoicestatus"></a>

#### InvoiceStatus

값: `open`, `partially_paid`, `paid`, `cancelled`

<a id="schema-invoiceupdate"></a>

#### InvoiceUpdate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `due_date` | string (date) \| null |  |  |
| `amount` | integer \| null |  | ≥ 0 |
| `discount` | integer \| null |  | ≥ 0 |
| `status` | [InvoiceStatus](#schema-invoicestatus) \| null |  | cancelled로만 직접 변경 가능 |
| `reason`* | string |  | 변경 사유 (감사 로그) |

<a id="schema-loginbody"></a>

#### LoginBody

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `email`* | string |  |  |
| `password`* | string |  |  |

<a id="schema-matchcandidate"></a>

#### MatchCandidate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `student_id`* | string (uuid) |  |  |
| `student_name`* | string |  |  |
| `household_id` | string (uuid) \| null |  |  |
| `invoice_ids`* | string (uuid)[] |  |  |
| `score`* | number |  | ≥ 0, ≤ 1 |
| `reasons`* | string[] |  | 예: 보호자 이름 일치, 금액이 형제 청구 합계와 같음 |

<a id="schema-meout"></a>

#### MeOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `academy_id`* | string (uuid) |  |  |
| `role`* | [Role](#schema-role) |  |  |
| `name`* | string |  |  |
| `academy_name`* | string |  |  |
| `preferred_language` | string | `"ko"` |  |

<a id="schema-messageout"></a>

#### MessageOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `candidate_ids`* | string (uuid)[] |  | 형제 묶음 안내면 여러 건 |
| `guardian_id`* | string (uuid) |  |  |
| `guardian_name`* | string |  |  |
| `student_ids`* | string (uuid)[] |  |  |
| `channel`* | [Channel](#schema-channel) |  |  |
| `language` | string | `"ko"` |  |
| `body`* | string |  |  |
| `template_version` | integer \| null |  |  |
| `status`* | [MessageStatus](#schema-messagestatus) |  |  |
| `scheduled_at` | string (date-time) \| null |  |  |
| `sent_at` | string (date-time) \| null |  |  |
| `delivered_at` | string (date-time) \| null |  |  |
| `failure_reason` | string \| null |  |  |
| `fallback_of` | string (uuid) \| null |  | 알림톡 실패로 대신 보낸 문자면 원래 건 |
| `approved_by` | string (uuid) \| null |  |  |

<a id="schema-messagestatus"></a>

#### MessageStatus

값: `scheduled`, `sending`, `sent`, `delivered`, `failed`, `cancelled`

<a id="schema-mismatchscanbody"></a>

#### MismatchScanBody

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `scopes` | string[] | `["billing", "attendance"]` | 검사할 기록 종류 |

<a id="schema-notecreate"></a>

#### NoteCreate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `body`* | string |  | 상담·통화 메모 길이 ≥ 1, 길이 ≤ 2000 |

<a id="schema-noticekind"></a>

#### NoticeKind

값: `billing_reminder`, `absence`, `repeated_absence`, `homework`, `payment_check`, `correction`, `general`

<a id="schema-page-airunout-"></a>

#### Page_AiRunOut_

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `items`* | [AiRunOut](#schema-airunout)[] |  |  |
| `total`* | integer |  |  |
| `page`* | integer |  |  |
| `size`* | integer |  |  |

<a id="schema-page-approvalsummary-"></a>

#### Page_ApprovalSummary_

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `items`* | [ApprovalSummary](#schema-approvalsummary)[] |  |  |
| `total`* | integer |  |  |
| `page`* | integer |  |  |
| `size`* | integer |  |  |

<a id="schema-page-attendancealertout-"></a>

#### Page_AttendanceAlertOut_

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `items`* | [AttendanceAlertOut](#schema-attendancealertout)[] |  |  |
| `total`* | integer |  |  |
| `page`* | integer |  |  |
| `size`* | integer |  |  |

<a id="schema-page-attendanceout-"></a>

#### Page_AttendanceOut_

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `items`* | [AttendanceOut](#schema-attendanceout)[] |  |  |
| `total`* | integer |  |  |
| `page`* | integer |  |  |
| `size`* | integer |  |  |

<a id="schema-page-auditlogout-"></a>

#### Page_AuditLogOut_

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `items`* | [AuditLogOut](#schema-auditlogout)[] |  |  |
| `total`* | integer |  |  |
| `page`* | integer |  |  |
| `size`* | integer |  |  |

<a id="schema-page-candidateout-"></a>

#### Page_CandidateOut_

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `items`* | [CandidateOut](#schema-candidateout)[] |  |  |
| `total`* | integer |  |  |
| `page`* | integer |  |  |
| `size`* | integer |  |  |

<a id="schema-page-depositmatchout-"></a>

#### Page_DepositMatchOut_

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `items`* | [DepositMatchOut](#schema-depositmatchout)[] |  |  |
| `total`* | integer |  |  |
| `page`* | integer |  |  |
| `size`* | integer |  |  |

<a id="schema-page-guardianout-"></a>

#### Page_GuardianOut_

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `items`* | [GuardianOut](#schema-guardianout)[] |  |  |
| `total`* | integer |  |  |
| `page`* | integer |  |  |
| `size`* | integer |  |  |

<a id="schema-page-homeworkout-"></a>

#### Page_HomeworkOut_

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `items`* | [HomeworkOut](#schema-homeworkout)[] |  |  |
| `total`* | integer |  |  |
| `page`* | integer |  |  |
| `size`* | integer |  |  |

<a id="schema-page-householdout-"></a>

#### Page_HouseholdOut_

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `items`* | [HouseholdOut](#schema-householdout)[] |  |  |
| `total`* | integer |  |  |
| `page`* | integer |  |  |
| `size`* | integer |  |  |

<a id="schema-page-householdsuggestion-"></a>

#### Page_HouseholdSuggestion_

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `items`* | [HouseholdSuggestion](#schema-householdsuggestion)[] |  |  |
| `total`* | integer |  |  |
| `page`* | integer |  |  |
| `size`* | integer |  |  |

<a id="schema-page-importbatchout-"></a>

#### Page_ImportBatchOut_

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `items`* | [ImportBatchOut](#schema-importbatchout)[] |  |  |
| `total`* | integer |  |  |
| `page`* | integer |  |  |
| `size`* | integer |  |  |

<a id="schema-page-importrowout-"></a>

#### Page_ImportRowOut_

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `items`* | [ImportRowOut](#schema-importrowout)[] |  |  |
| `total`* | integer |  |  |
| `page`* | integer |  |  |
| `size`* | integer |  |  |

<a id="schema-page-invoiceout-"></a>

#### Page_InvoiceOut_

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `items`* | [InvoiceOut](#schema-invoiceout)[] |  |  |
| `total`* | integer |  |  |
| `page`* | integer |  |  |
| `size`* | integer |  |  |

<a id="schema-page-messageout-"></a>

#### Page_MessageOut_

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `items`* | [MessageOut](#schema-messageout)[] |  |  |
| `total`* | integer |  |  |
| `page`* | integer |  |  |
| `size`* | integer |  |  |

<a id="schema-page-paymentout-"></a>

#### Page_PaymentOut_

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `items`* | [PaymentOut](#schema-paymentout)[] |  |  |
| `total`* | integer |  |  |
| `page`* | integer |  |  |
| `size`* | integer |  |  |

<a id="schema-page-replyout-"></a>

#### Page_ReplyOut_

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `items`* | [ReplyOut](#schema-replyout)[] |  |  |
| `total`* | integer |  |  |
| `page`* | integer |  |  |
| `size`* | integer |  |  |

<a id="schema-page-reviewitem-"></a>

#### Page_ReviewItem_

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `items`* | [ReviewItem](#schema-reviewitem)[] |  |  |
| `total`* | integer |  |  |
| `page`* | integer |  |  |
| `size`* | integer |  |  |

<a id="schema-page-rulerunout-"></a>

#### Page_RuleRunOut_

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `items`* | [RuleRunOut](#schema-rulerunout)[] |  |  |
| `total`* | integer |  |  |
| `page`* | integer |  |  |
| `size`* | integer |  |  |

<a id="schema-page-studentsummary-"></a>

#### Page_StudentSummary_

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `items`* | [StudentSummary](#schema-studentsummary)[] |  |  |
| `total`* | integer |  |  |
| `page`* | integer |  |  |
| `size`* | integer |  |  |

<a id="schema-page-timelineitem-"></a>

#### Page_TimelineItem_

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `items`* | [TimelineItem](#schema-timelineitem)[] |  |  |
| `total`* | integer |  |  |
| `page`* | integer |  |  |
| `size`* | integer |  |  |

<a id="schema-page-userout-"></a>

#### Page_UserOut_

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `items`* | [UserOut](#schema-userout)[] |  |  |
| `total`* | integer |  |  |
| `page`* | integer |  |  |
| `size`* | integer |  |  |

<a id="schema-paymentcreate"></a>

#### PaymentCreate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `amount`* | integer |  | > 0 |
| `paid_at`* | string (date-time) |  |  |
| `method`* | [PaymentMethod](#schema-paymentmethod) |  |  |
| `payer_name` | string \| null |  |  |
| `allocations`* | [Allocation](#schema-allocation)[] |  | 형제 청구서 여러 건에 나눠 반영 가능. 합계 = amount 개수 ≥ 1 |

<a id="schema-paymentmethod"></a>

#### PaymentMethod

값: `bank_transfer`, `card`, `cash`, `other`

<a id="schema-paymentout"></a>

#### PaymentOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `amount`* | integer |  |  |
| `paid_at`* | string (date-time) |  |  |
| `method`* | [PaymentMethod](#schema-paymentmethod) |  |  |
| `payer_name` | string \| null |  |  |
| `allocations`* | [Allocation](#schema-allocation)[] |  |  |
| `voided` | boolean | `false` |  |
| `created_by`* | string (uuid) |  |  |

<a id="schema-previewbody"></a>

#### PreviewBody

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `version` | integer \| null |  | 비우면 최신 버전 |
| `student_id` | string (uuid) \| null |  | 실제 학생 값으로 채워 보기 |
| `language` | string | `"ko"` |  |

<a id="schema-previewout"></a>

#### PreviewOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `rendered`* | string |  |  |
| `missing_variables` | string[] | `[]` |  |

<a id="schema-promisecreate"></a>

#### PromiseCreate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `promised_date`* | string (date) |  |  |
| `amount` | integer \| null |  | 일부만 약속한 경우 > 0 |
| `note` | string \| null |  |  |
| `source_reply_id` | string (uuid) \| null |  |  |

<a id="schema-promiseout"></a>

#### PromiseOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `invoice_id`* | string (uuid) |  |  |
| `promised_date`* | string (date) |  |  |
| `amount` | integer \| null |  |  |
| `note` | string \| null |  |  |
| `status`* | [PromiseStatus](#schema-promisestatus) |  |  |
| `source_reply_id` | string (uuid) \| null |  |  |

<a id="schema-promisestatus"></a>

#### PromiseStatus

값: `active`, `kept`, `broken`, `cancelled`

<a id="schema-publicreplybody"></a>

#### PublicReplyBody

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `intent`* | [ReplyIntent](#schema-replyintent) |  |  |
| `message` | string \| null |  | 길이 ≤ 500 |

<a id="schema-publicreplypage"></a>

#### PublicReplyPage

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `academy_name`* | string |  |  |
| `notice_label`* | string |  | 예: 11월 수강료 안내 |
| `language`* | string |  |  |
| `options`* | [ReplyOption](#schema-replyoption)[] |  |  |
| `answered`* | boolean |  |  |
| `expires_at`* | string |  |  |

<a id="schema-publicreplyresult"></a>

#### PublicReplyResult

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `ok` | boolean | `true` |  |
| `thank_you`* | string |  |  |

<a id="schema-refreshbody"></a>

#### RefreshBody

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `refresh_token`* | string |  |  |

<a id="schema-rejectbody"></a>

#### RejectBody

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `reason`* | string |  |  |

<a id="schema-replyintent"></a>

#### ReplyIntent

값: `paid`, `already_notified`, `consult_request`, `correction`, `promise`, `other`, `unknown`

<a id="schema-replyoption"></a>

#### ReplyOption

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `intent`* | [ReplyIntent](#schema-replyintent) |  |  |
| `label`* | string |  | 수신 언어로 번역된 버튼 문구 |

<a id="schema-replyout"></a>

#### ReplyOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `message_id` | string (uuid) \| null |  |  |
| `guardian_id`* | string (uuid) |  |  |
| `guardian_name`* | string |  |  |
| `student_ids`* | string (uuid)[] |  |  |
| `received_at`* | string (date-time) |  |  |
| `body`* | string |  |  |
| `language` | string | `"ko"` |  |
| `translated_body` | string \| null |  | 외국어 회신의 한국어 번역 |
| `intent`* | [ReplyIntent](#schema-replyintent) |  |  |
| `intent_source` | [IntentSource](#schema-intentsource) \| null |  |  |
| `intent_confirmed` | boolean | `false` |  |
| `follow_up_stopped`* | boolean |  | 같은 사유의 후속 안내를 멈췄는지 |
| `status`* | [ReplyStatus](#schema-replystatus) |  |  |
| `handled_by` | string (uuid) \| null |  |  |

<a id="schema-replystatus"></a>

#### ReplyStatus

값: `open`, `handled`

<a id="schema-replyupdate"></a>

#### ReplyUpdate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `intent` | [ReplyIntent](#schema-replyintent) \| null |  | 보내면 분류를 담당자가 확정한 것으로 기록 |
| `status` | [ReplyStatus](#schema-replystatus) \| null |  |  |
| `note` | string \| null |  |  |

<a id="schema-reviewitem"></a>

#### ReviewItem

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `kind`* | [ReviewKind](#schema-reviewkind) |  |  |
| `title`* | string |  |  |
| `detail` | string \| null |  |  |
| `ref_id`* | string (uuid) |  | 처리할 대상 ID (업로드, 매칭 후보 등) |
| `created_at`* | string (date-time) |  |  |

<a id="schema-reviewkind"></a>

#### ReviewKind

값: `import_error`, `deposit_match`, `household_suggestion`, `unclassified_reply`, `late_attendance_entry`, `discount_recalc`, `ai_mismatch`

<a id="schema-reviewstatus"></a>

#### ReviewStatus

값: `none`, `pending`, `approved`, `rejected`

<a id="schema-role"></a>

#### Role

값: `owner`, `manager`, `teacher`

<a id="schema-rowstatus"></a>

#### RowStatus

값: `ok`, `warning`, `error`, `duplicate`

<a id="schema-ruleruncreate"></a>

#### RuleRunCreate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `dry_run` | boolean | `true` | true면 후보를 저장하지 않고 결과만 보여줌 |
| `kinds` | [NoticeKind](#schema-noticekind)[] \| null |  |  |

<a id="schema-rulerunout"></a>

#### RuleRunOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `status`* | [RuleRunStatus](#schema-rulerunstatus) |  |  |
| `dry_run`* | boolean |  |  |
| `trigger`* | string |  | schedule 또는 manual |
| `started_at` | string (date-time) \| null |  |  |
| `finished_at` | string (date-time) \| null |  |  |
| `created_count` | integer | `0` |  |
| `held_count` | integer | `0` |  |
| `skipped_duplicate_count` | integer | `0` |  |
| `error` | string \| null |  |  |

<a id="schema-rulerunstatus"></a>

#### RuleRunStatus

값: `queued`, `running`, `succeeded`, `failed`

<a id="schema-rulesettings"></a>

#### RuleSettings

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `billing_stages` | [BillingStage](#schema-billingstage)[] | (설정 참고) |  |
| `repeated_absence` | [WindowRule](#schema-windowrule) | `{"window_days": 14, "count": 3}` |  |
| `homework_missing` | [WindowRule](#schema-windowrule) | `{"window_days": 14, "count": 2}` |  |
| `send_window_start` | string (time) | `"09:00:00"` |  |
| `send_window_end` | string (time) | `"21:00:00"` |  |
| `daily_cap_per_guardian` | integer | `2` | ≥ 1 |
| `use_business_days` | boolean | `false` | 수납 단계 일수를 영업일로 셈 (캘린더 사용) |
| `bundle_siblings` | boolean | `true` | 같은 보호자에게 같은 날 가는 안내를 한 통으로 |
| `auto_send_enabled` | boolean | `false` | 꺼 두면 모든 안내가 승인함을 거친다 |
| `approval_roles` | map<string, [Role](#schema-role)[]> | (설정 참고) |  |
| `late_entry_minutes` | integer | `30` | 수업 시작 후 이 시간이 지나 입력된 출결은 확인 필요 ≥ 0 |
| `alert_escalation_minutes` | integer | `20` | 긴급 결석 알림 미확인 시 상위자에게 ≥ 1 |

<a id="schema-sheetimportbody"></a>

#### SheetImportBody

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `kind`* | [ImportKind](#schema-importkind) |  |  |
| `sheet_url`* | string |  |  |
| `worksheet` | string \| null |  |  |

<a id="schema-siblingdiscountrule"></a>

#### SiblingDiscountRule

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `nth_child`* | integer |  | 몇째부터 ≥ 2 |
| `percent` | integer \| null |  | ≥ 0, ≤ 100 |
| `fixed_amount` | integer \| null |  | ≥ 0 |

<a id="schema-siblingdiscountsettings"></a>

#### SiblingDiscountSettings

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `enabled` | boolean | `false` |  |
| `rules` | [SiblingDiscountRule](#schema-siblingdiscountrule)[] | `[]` |  |

<a id="schema-studentcreate"></a>

#### StudentCreate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `external_id` | string \| null |  |  |
| `name`* | string |  |  |
| `grade` | string \| null |  |  |
| `school` | string \| null |  |  |
| `class_ids` | string (uuid)[] | `[]` |  |
| `guardians` | [GuardianLinkCreate](#schema-guardianlinkcreate)[] | `[]` |  |

<a id="schema-studentout"></a>

#### StudentOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `external_id` | string \| null |  | 학원이 쓰는 학생 번호 (업로드 upsert 키) |
| `name`* | string |  |  |
| `grade` | string \| null |  |  |
| `status`* | [StudentStatus](#schema-studentstatus) |  |  |
| `household_id` | string (uuid) \| null |  |  |
| `class_ids` | string (uuid)[] | `[]` |  |
| `school` | string \| null |  |  |
| `guardians` | [GuardianLink](#schema-guardianlink)[] | `[]` |  |
| `sibling_ids` | string (uuid)[] | `[]` | 같은 가구의 다른 학생 |
| `created_at`* | string (date-time) |  |  |

<a id="schema-studentstatus"></a>

#### StudentStatus

값: `active`, `on_leave`, `withdrawn`

<a id="schema-studentsummary"></a>

#### StudentSummary

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `external_id` | string \| null |  | 학원이 쓰는 학생 번호 (업로드 upsert 키) |
| `name`* | string |  |  |
| `grade` | string \| null |  |  |
| `status`* | [StudentStatus](#schema-studentstatus) |  |  |
| `household_id` | string (uuid) \| null |  |  |
| `class_ids` | string (uuid)[] | `[]` |  |

<a id="schema-studentupdate"></a>

#### StudentUpdate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `external_id` | string \| null |  |  |
| `name` | string \| null |  |  |
| `grade` | string \| null |  |  |
| `school` | string \| null |  |  |
| `status` | [StudentStatus](#schema-studentstatus) \| null |  | 휴원·퇴원으로 바꾸면 예약 안내가 보류된다 |

<a id="schema-submissionbatch"></a>

#### SubmissionBatch

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `items`* | [SubmissionItem](#schema-submissionitem)[] |  | 개수 ≥ 1 |

<a id="schema-submissionitem"></a>

#### SubmissionItem

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `student_id`* | string (uuid) |  |  |
| `status`* | [SubmissionStatus](#schema-submissionstatus) |  |  |
| `note` | string \| null |  |  |

<a id="schema-submissionout"></a>

#### SubmissionOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `student_id`* | string (uuid) |  |  |
| `student_name`* | string |  |  |
| `status`* | [SubmissionStatus](#schema-submissionstatus) |  |  |
| `note` | string \| null |  |  |
| `recorded_at`* | string (date-time) |  |  |

<a id="schema-submissionstatus"></a>

#### SubmissionStatus

값: `done`, `partial`, `missing`

<a id="schema-suggestionreason"></a>

#### SuggestionReason

값: `shared_guardian_phone`, `shared_payer_name`

<a id="schema-suggestionreject"></a>

#### SuggestionReject

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `note` | string \| null |  |  |

<a id="schema-suggestionstatus"></a>

#### SuggestionStatus

값: `pending`, `accepted`, `rejected`

<a id="schema-templatecreate"></a>

#### TemplateCreate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `kind`* | [NoticeKind](#schema-noticekind) |  |  |
| `stage` | integer \| null |  |  |
| `name`* | string |  |  |
| `channel`* | [Channel](#schema-channel) |  |  |
| `body`* | string |  | {student_name}, {amount}, {due_date} 같은 자리 표시를 쓴다 |

<a id="schema-templateout"></a>

#### TemplateOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `kind`* | [NoticeKind](#schema-noticekind) |  |  |
| `stage` | integer \| null |  | 수납 단계 1·2·3 |
| `name`* | string |  |  |
| `channel`* | [Channel](#schema-channel) |  |  |
| `current_version` | integer \| null |  | 승인된 최신 버전 |
| `archived` | boolean | `false` |  |

<a id="schema-templateupdate"></a>

#### TemplateUpdate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `name` | string \| null |  |  |
| `archived` | boolean \| null |  |  |

<a id="schema-templateversioncreate"></a>

#### TemplateVersionCreate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `body`* | string |  |  |

<a id="schema-templateversionout"></a>

#### TemplateVersionOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `template_id`* | string (uuid) |  |  |
| `version`* | integer |  |  |
| `body`* | string |  |  |
| `variables`* | string[] |  |  |
| `approved_by` | string (uuid) \| null |  |  |
| `approved_at` | string (date-time) \| null |  |  |
| `alimtalk_review` | [ReviewStatus](#schema-reviewstatus) | `"none"` |  |
| `created_at`* | string (date-time) |  |  |

<a id="schema-timelineitem"></a>

#### TimelineItem

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `at`* | string (date-time) |  |  |
| `kind`* | [TimelineKind](#schema-timelinekind) |  |  |
| `title`* | string |  |  |
| `detail` | string \| null |  |  |
| `ref_id`* | string (uuid) |  |  |
| `actor_name` | string \| null |  |  |

<a id="schema-timelinekind"></a>

#### TimelineKind

값: `invoice`, `payment`, `attendance`, `homework`, `message`, `reply`, `approval`, `note`

<a id="schema-todaysummary"></a>

#### TodaySummary

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `date`* | string (date) |  |  |
| `pending_approvals`* | integer |  |  |
| `my_pending_approvals`* | integer |  | 내가 승인할 수 있는 건 |
| `scheduled_today`* | integer |  |  |
| `sent_today`* | integer |  |  |
| `failed_today`* | integer |  |  |
| `cancelled_by_recheck_today`* | integer |  | 발송 직전 재검증으로 막은 건 |
| `open_alerts`* | integer |  |  |
| `open_replies`* | integer |  |  |
| `review_items`* | integer |  |  |

<a id="schema-tokenpair"></a>

#### TokenPair

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `access_token`* | string |  |  |
| `refresh_token`* | string |  |  |
| `token_type` | string | `"bearer"` |  |
| `expires_in`* | integer |  |  |

<a id="schema-translationout"></a>

#### TranslationOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `template_id`* | string (uuid) |  |  |
| `version`* | integer |  |  |
| `language`* | string |  |  |
| `body` | string \| null |  |  |
| `status`* | [TranslationStatus](#schema-translationstatus) |  |  |
| `validation_errors` | string[] | `[]` | 자리 표시 누락·변경, 원문에 없는 숫자 등 |
| `ai_run_id` | string (uuid) \| null |  |  |
| `approved_by` | string (uuid) \| null |  |  |

<a id="schema-translationrequest"></a>

#### TranslationRequest

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `language`* | string |  |  |

<a id="schema-translationstatus"></a>

#### TranslationStatus

값: `generating`, `draft`, `approved`

<a id="schema-translationupdate"></a>

#### TranslationUpdate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `body` | string \| null |  | 담당자가 고친 번역 |
| `approve` | boolean | `false` |  |

<a id="schema-userinvite"></a>

#### UserInvite

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `email`* | string |  |  |
| `name`* | string |  |  |
| `role`* | [Role](#schema-role) |  |  |
| `branch_ids` | string (uuid)[] | `[]` |  |

<a id="schema-userout"></a>

#### UserOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `name`* | string |  |  |
| `email`* | string |  |  |
| `role`* | [Role](#schema-role) |  |  |
| `branch_ids` | string (uuid)[] | `[]` |  |
| `is_active`* | boolean |  |  |
| `preferred_language` | string | `"ko"` | 화면 언어. 외국인 강사는 en 등 |

<a id="schema-userupdate"></a>

#### UserUpdate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `name` | string \| null |  |  |
| `role` | [Role](#schema-role) \| null |  |  |
| `branch_ids` | string (uuid)[] \| null |  |  |
| `preferred_language` | string \| null |  |  |

<a id="schema-voidbody"></a>

#### VoidBody

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `reason`* | string |  |  |

<a id="schema-windowrule"></a>

#### WindowRule

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `window_days`* | integer |  | ≥ 1 |
| `count`* | integer |  | ≥ 1 |

