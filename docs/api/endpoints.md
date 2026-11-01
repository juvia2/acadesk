# acadesk API 명세서

버전 0.1.0 · 엔드포인트 211개 (MVP 110 · 2단계 45 · 3단계 55)

> 이 문서는 `scripts/export_api_spec.py`가 백엔드 코드에서 자동으로 만든다. 직접 고치지 말고 라우터를 고친 뒤 다시 생성한다. 기계용 명세는 `docs/api/openapi.json`, 서버를 켜면 `http://localhost:8000/docs`에서도 볼 수 있다.

## 공통 규칙

| 항목 | 내용 |
|---|---|
| 기본 경로 | `/api/v1` |
| 인증 | `Authorization: Bearer <access_token>`. 로컬에서는 `ACADESK_AUTH_DEV_BYPASS=true`로 개발용 원장 계정 사용 |
| 학원 격리 | 토큰의 `academy_id`로 모든 조회·변경 범위를 제한한다. 요청 본문으로 academy_id를 받지 않는다 |
| 역할 | 학원 관리자: 원장(owner)·실장(manager) · 교사(teacher) · 학생(student) · 학부모(parent) · 플랫폼 운영자(operator, 커뮤니티 신고 처리만) |
| 단계 | 기획안 v2 11장 출시 순서: **MVP** · **2단계**(커뮤니티·과제·수납 기록) · **3단계**(미납 자동 안내·AI·번역) |
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
| MVP | POST | [`/auth/academies`](#op-post-auth-academies) | 학원 등록 + 관리자 가입 | 공개 |
| MVP | GET | [`/auth/invitations/{code}`](#op-get-auth-invitations-code) | 초대 코드 확인 | 공개 |
| MVP | POST | [`/auth/signup`](#op-post-auth-signup) | 초대 코드로 가입 (교사·학생·학부모) | 공개 |
| MVP | POST | [`/auth/login`](#op-post-auth-login) | 로그인 | 공개 |
| MVP | POST | [`/auth/refresh`](#op-post-auth-refresh) | 토큰 갱신 | 공개 |
| MVP | POST | [`/auth/logout`](#op-post-auth-logout) | 로그아웃 (리프레시 토큰 폐기) | 원장, 실장, 교사, 학생, 학부모 |
| MVP | GET | [`/auth/me`](#op-get-auth-me) | 내 정보·역할·첫 화면 | 원장, 실장, 교사, 학생, 학부모 |

### 대시보드

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| MVP | GET | [`/dashboard/today`](#op-get-dashboard-today) | 관리자·교사 대시보드 요약 | 원장, 실장, 교사 |
| 3단계 | GET | [`/dashboard/briefing`](#op-get-dashboard-briefing) | 담당자 아침 브리핑 | 원장, 실장, 교사 |
| MVP | GET | [`/review-items`](#op-get-review-items) | 확인 필요함 | 원장, 실장, 교사 |

### 학원

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| MVP | GET | [`/academy`](#op-get-academy) | 내 학원 정보 | 원장, 실장, 교사 |
| MVP | PATCH | [`/academy`](#op-patch-academy) | 학원 정보 수정 | 원장 |
| MVP | GET | [`/academy/branches`](#op-get-academy-branches) | 지점 목록 | 원장, 실장, 교사 |
| MVP | POST | [`/academy/branches`](#op-post-academy-branches) | 지점 추가 | 원장 |
| MVP | PATCH | [`/academy/branches/{branch_id}`](#op-patch-academy-branches-branch_id) | 지점 수정 | 원장 |
| 2단계 | GET | [`/academy/calendar`](#op-get-academy-calendar) | 휴원·방학·공휴일 목록 | 원장, 실장, 교사 |
| 2단계 | POST | [`/academy/calendar`](#op-post-academy-calendar) | 휴원·방학·공휴일 등록 | 원장, 실장 |
| 2단계 | DELETE | [`/academy/calendar/{event_id}`](#op-delete-academy-calendar-event_id) | 휴원·방학·공휴일 삭제 | 원장, 실장 |

### 사용자

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| MVP | GET | [`/users`](#op-get-users) | 계정 목록 | 원장, 실장 |
| MVP | PATCH | [`/users/{user_id}`](#op-patch-users-user_id) | 직원 역할·정보 수정 | 원장 |
| MVP | DELETE | [`/users/{user_id}`](#op-delete-users-user_id) | 직원 비활성화 | 원장 |

### 초대 코드

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| MVP | GET | [`/invitations`](#op-get-invitations) | 초대 코드 목록 | 원장, 실장 |
| MVP | POST | [`/invitations`](#op-post-invitations) | 초대 코드 발급 | 원장, 실장 |
| MVP | POST | [`/invitations/bulk`](#op-post-invitations-bulk) | 학생·학부모 초대 코드 일괄 발급 | 원장, 실장 |
| MVP | DELETE | [`/invitations/{invitation_id}`](#op-delete-invitations-invitation_id) | 초대 코드 폐기 | 원장, 실장 |

### 강의

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| MVP | GET | [`/lectures`](#op-get-lectures) | 강의 목록 | 원장, 실장, 교사 |
| MVP | POST | [`/lectures`](#op-post-lectures) | 강의 개설 | 원장, 실장 |
| MVP | GET | [`/lectures/{lecture_id}`](#op-get-lectures-lecture_id) | 강의 상세 | 원장, 실장, 교사 |
| MVP | PATCH | [`/lectures/{lecture_id}`](#op-patch-lectures-lecture_id) | 강의 수정·종강 | 원장, 실장 |
| MVP | GET | [`/lectures/{lecture_id}/students`](#op-get-lectures-lecture_id-students) | 수강생 목록 | 원장, 실장, 교사 |
| MVP | POST | [`/lectures/{lecture_id}/students`](#op-post-lectures-lecture_id-students) | 수강생 등록 | 원장, 실장 |
| MVP | DELETE | [`/lectures/{lecture_id}/students/{student_id}`](#op-delete-lectures-lecture_id-students-student_id) | 수강 종료 | 원장, 실장 |
| MVP | POST | [`/lectures/{lecture_id}/sessions/generate`](#op-post-lectures-lecture_id-sessions-generate) | 시간표로 회차 만들기 | 원장, 실장 |

### 강의 회차

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| MVP | GET | [`/lecture-sessions`](#op-get-lecture-sessions) | 회차 목록 (오늘의 강의) | 원장, 실장, 교사 |
| MVP | POST | [`/lecture-sessions`](#op-post-lecture-sessions) | 보강 회차 추가 | 원장, 실장, 교사 |
| MVP | GET | [`/lecture-sessions/{session_id}`](#op-get-lecture-sessions-session_id) | 회차 상세 | 원장, 실장, 교사 |
| MVP | PATCH | [`/lecture-sessions/{session_id}`](#op-patch-lecture-sessions-session_id) | 회차 시간 변경·휴강 | 원장, 실장, 교사 |

### 출결

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| MVP | POST | [`/lecture-sessions/{session_id}/attendance/open`](#op-post-lecture-sessions-session_id-attendance-open) | 출석 시작 | 원장, 실장, 교사 |
| MVP | GET | [`/lecture-sessions/{session_id}/attendance/qr`](#op-get-lecture-sessions-session_id-attendance-qr) | 현재 QR 토큰 | 원장, 실장, 교사 |
| MVP | GET | [`/lecture-sessions/{session_id}/attendance`](#op-get-lecture-sessions-session_id-attendance) | 실시간 출석 명단 | 원장, 실장, 교사 |
| MVP | PUT | [`/lecture-sessions/{session_id}/attendance/{student_id}`](#op-put-lecture-sessions-session_id-attendance-student_id) | 수동 출결 처리 | 원장, 실장, 교사 |
| MVP | POST | [`/lecture-sessions/{session_id}/attendance/close`](#op-post-lecture-sessions-session_id-attendance-close) | 출석 마감 | 원장, 실장, 교사 |
| MVP | POST | [`/attendance/check-in`](#op-post-attendance-check-in) | QR 출석 (학생) | 학생 |
| MVP | GET | [`/attendance`](#op-get-attendance) | 출결 조회 | 원장, 실장, 교사 |
| MVP | GET | [`/attendance/alerts`](#op-get-attendance-alerts) | 결석 알림 | 원장, 실장, 교사 |
| MVP | POST | [`/attendance/alerts/{alert_id}/ack`](#op-post-attendance-alerts-alert_id-ack) | 결석 알림 확인 | 원장, 실장, 교사 |
| MVP | PATCH | [`/attendance/{attendance_id}`](#op-patch-attendance-attendance_id) | 출결 정정 | 원장, 실장, 교사 |

### 학생

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| MVP | GET | [`/students`](#op-get-students) | 학생 목록·검색 | 원장, 실장, 교사 |
| MVP | POST | [`/students`](#op-post-students) | 학생 등록 | 원장, 실장 |
| MVP | GET | [`/students/{student_id}`](#op-get-students-student_id) | 학생 상세 | 원장, 실장, 교사 |
| MVP | PATCH | [`/students/{student_id}`](#op-patch-students-student_id) | 학생 정보·상태 수정 | 원장, 실장 |
| MVP | GET | [`/students/{student_id}/timeline`](#op-get-students-student_id-timeline) | 학생별 기록 | 원장, 실장, 교사 |
| 2단계 | POST | [`/students/{student_id}/notes`](#op-post-students-student_id-notes) | 상담·통화 메모 추가 | 원장, 실장, 교사 |
| MVP | POST | [`/students/{student_id}/guardians`](#op-post-students-student_id-guardians) | 보호자 연결 | 원장, 실장 |
| MVP | PATCH | [`/students/{student_id}/guardians/{guardian_id}`](#op-patch-students-student_id-guardians-guardian_id) | 보호자 관계·기본 수신자 수정 | 원장, 실장 |
| MVP | DELETE | [`/students/{student_id}/guardians/{guardian_id}`](#op-delete-students-student_id-guardians-guardian_id) | 보호자 연결 해제 | 원장, 실장 |
| MVP | GET | [`/students/{student_id}/report`](#op-get-students-student_id-report) | 학생 리포트 (직원용) | 원장, 실장, 교사 |

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

### 학생 화면

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| MVP | GET | [`/me/schedule`](#op-get-me-schedule) | 내 시간표 | 학생 |
| MVP | GET | [`/me/attendance`](#op-get-me-attendance) | 내 출결 | 학생 |
| MVP | GET | [`/me/attendance/summary`](#op-get-me-attendance-summary) | 내 강의별 출석률 | 학생 |

### 학부모 화면

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| MVP | GET | [`/children`](#op-get-children) | 내 자녀 목록 | 학부모 |
| MVP | POST | [`/children`](#op-post-children) | 자녀 추가 (형제) | 학부모 |
| MVP | POST | [`/children/{student_id}/approve-account`](#op-post-children-student_id-approve-account) | 자녀 학생 계정 승인 | 학부모 |
| MVP | GET | [`/children/{student_id}/report`](#op-get-children-student_id-report) | 자녀 리포트 | 학부모 |
| MVP | GET | [`/children/{student_id}/attendance`](#op-get-children-student_id-attendance) | 자녀 출결 달력 | 학부모 |

### 공지사항

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| MVP | GET | [`/notices`](#op-get-notices) | 공지 목록 | 원장, 실장, 교사, 학생, 학부모 |
| MVP | POST | [`/notices`](#op-post-notices) | 공지 작성 | 원장, 실장, 교사 |
| MVP | POST | [`/notices/attachments`](#op-post-notices-attachments) | 첨부 파일 올리기 | 원장, 실장, 교사 |
| MVP | GET | [`/notices/{notice_id}`](#op-get-notices-notice_id) | 공지 상세 | 원장, 실장, 교사, 학생, 학부모 |
| MVP | PATCH | [`/notices/{notice_id}`](#op-patch-notices-notice_id) | 공지 수정 | 원장, 실장, 교사 |
| MVP | DELETE | [`/notices/{notice_id}`](#op-delete-notices-notice_id) | 공지 삭제 | 원장, 실장, 교사 |
| MVP | POST | [`/notices/{notice_id}/read`](#op-post-notices-notice_id-read) | 읽음 표시 | 원장, 실장, 교사, 학생, 학부모 |
| MVP | GET | [`/notices/{notice_id}/reads`](#op-get-notices-notice_id-reads) | 읽음 현황 | 원장, 실장, 교사 |

### 질의응답

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| MVP | GET | [`/questions`](#op-get-questions) | 질문 목록 | 원장, 실장, 교사, 학생, 학부모 |
| MVP | POST | [`/questions`](#op-post-questions) | 질문하기 (학생·학부모) | 학생, 학부모 |
| 2단계 | GET | [`/questions/public`](#op-get-questions-public) | 같은 강의 공개 질문 (익명) | 학생 |
| MVP | GET | [`/questions/{question_id}`](#op-get-questions-question_id) | 질문 상세·대화 | 원장, 실장, 교사, 학생, 학부모 |
| MVP | PATCH | [`/questions/{question_id}`](#op-patch-questions-question_id) | 종료·담당 변경·공개 전환 | 원장, 실장, 교사, 학생, 학부모 |
| MVP | POST | [`/questions/{question_id}/messages`](#op-post-questions-question_id-messages) | 답변·추가 질문 | 원장, 실장, 교사, 학생, 학부모 |
| MVP | POST | [`/questions/{question_id}/read`](#op-post-questions-question_id-read) | 읽음 표시 | 원장, 실장, 교사, 학생, 학부모 |

### 알림

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| MVP | GET | [`/notifications`](#op-get-notifications) | 알림함 | 원장, 실장, 교사, 학생, 학부모 |
| MVP | POST | [`/notifications/read`](#op-post-notifications-read) | 알림 읽음 | 원장, 실장, 교사, 학생, 학부모 |
| MVP | POST | [`/notifications/push-subscriptions`](#op-post-notifications-push-subscriptions) | 앱 푸시 구독 등록 | 원장, 실장, 교사, 학생, 학부모 |
| MVP | POST | [`/notifications/push-subscriptions/delete`](#op-post-notifications-push-subscriptions-delete) | 앱 푸시 구독 해제 | 원장, 실장, 교사, 학생, 학부모 |
| MVP | GET | [`/notifications/preferences`](#op-get-notifications-preferences) | 알림 설정 조회 | 원장, 실장, 교사, 학생, 학부모 |
| MVP | PUT | [`/notifications/preferences`](#op-put-notifications-preferences) | 알림 설정 저장 | 원장, 실장, 교사, 학생, 학부모 |

### 템플릿

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| 3단계 | GET | [`/templates`](#op-get-templates) | 템플릿 목록 | 원장, 실장, 교사 |
| 3단계 | POST | [`/templates`](#op-post-templates) | 템플릿 만들기 (버전 1 초안) | 원장, 실장 |
| 3단계 | GET | [`/templates/{template_id}`](#op-get-templates-template_id) | 템플릿 상세 | 원장, 실장, 교사 |
| 3단계 | PATCH | [`/templates/{template_id}`](#op-patch-templates-template_id) | 템플릿 이름 수정·보관 | 원장, 실장 |
| 3단계 | GET | [`/templates/{template_id}/versions`](#op-get-templates-template_id-versions) | 템플릿 버전 목록 | 원장, 실장, 교사 |
| 3단계 | POST | [`/templates/{template_id}/versions`](#op-post-templates-template_id-versions) | 새 버전 초안 | 원장, 실장 |
| 3단계 | POST | [`/templates/{template_id}/versions/{version}/approve`](#op-post-templates-template_id-versions-version-approve) | 버전 승인 | 원장, 실장 |
| 3단계 | POST | [`/templates/{template_id}/preview`](#op-post-templates-template_id-preview) | 자리 표시 채워 미리 보기 | 원장, 실장, 교사 |
| 3단계 | GET | [`/templates/{template_id}/versions/{version}/translations`](#op-get-templates-template_id-versions-version-translations) | 번역 목록 | 원장, 실장, 교사 |
| 3단계 | POST | [`/templates/{template_id}/versions/{version}/translations`](#op-post-templates-template_id-versions-version-translations) | 번역 생성 요청 (AI) | 원장, 실장 |
| 3단계 | PATCH | [`/templates/{template_id}/versions/{version}/translations/{language}`](#op-patch-templates-template_id-versions-version-translations-language) | 번역 수정·승인 | 원장, 실장 |

### 안내 후보

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| 3단계 | GET | [`/candidates`](#op-get-candidates) | 안내 후보 목록 | 원장, 실장, 교사 |
| 3단계 | GET | [`/candidates/{candidate_id}`](#op-get-candidates-candidate_id) | 안내 후보 상세 | 원장, 실장, 교사 |
| 3단계 | POST | [`/candidates/{candidate_id}/cancel`](#op-post-candidates-candidate_id-cancel) | 안내 후보 취소 | 원장, 실장 |

### 발송 이력

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| MVP | GET | [`/messages`](#op-get-messages) | 발송 이력 | 원장, 실장, 교사 |
| MVP | GET | [`/messages/{message_id}`](#op-get-messages-message_id) | 발송 건 상세 | 원장, 실장, 교사 |
| MVP | POST | [`/messages/{message_id}/cancel`](#op-post-messages-message_id-cancel) | 예약 발송 취소 | 원장, 실장 |
| 3단계 | POST | [`/messages/{message_id}/corrections`](#op-post-messages-message_id-corrections) | 오발송 정정 안내 만들기 | 원장, 실장 |

### 회신

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| 3단계 | GET | [`/replies`](#op-get-replies) | 학부모 회신 목록 | 원장, 실장, 교사 |
| 3단계 | GET | [`/replies/{reply_id}`](#op-get-replies-reply_id) | 회신 상세 | 원장, 실장, 교사 |
| 3단계 | PATCH | [`/replies/{reply_id}`](#op-patch-replies-reply_id) | 회신 분류 확정·처리 완료 | 원장, 실장, 교사 |

### 긴급 문자

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| MVP | POST | [`/emergency-messages/preview`](#op-post-emergency-messages-preview) | 긴급 문자 미리 보기 | 원장, 실장, 교사 |
| MVP | GET | [`/emergency-messages`](#op-get-emergency-messages) | 긴급 문자 이력 | 원장, 실장, 교사 |
| MVP | POST | [`/emergency-messages`](#op-post-emergency-messages) | 긴급 문자 발송 | 원장, 실장, 교사 |
| MVP | GET | [`/emergency-messages/{emergency_id}`](#op-get-emergency-messages-emergency_id) | 긴급 문자 상세·수신 결과 | 원장, 실장, 교사 |

### 업로드

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| MVP | GET | [`/imports/kinds/{kind}/fields`](#op-get-imports-kinds-kind-fields) | 업로드 종류별 필드 목록 | 원장, 실장 |
| MVP | GET | [`/imports`](#op-get-imports) | 업로드 기록 | 원장, 실장 |
| MVP | POST | [`/imports`](#op-post-imports) | CSV·엑셀 업로드 | 원장, 실장 |
| 3단계 | POST | [`/imports/sheets`](#op-post-imports-sheets) | 구글 시트에서 가져오기 | 원장, 실장 |
| MVP | GET | [`/imports/{import_id}`](#op-get-imports-import_id) | 업로드 상태 | 원장, 실장 |
| MVP | DELETE | [`/imports/{import_id}`](#op-delete-imports-import_id) | 반영 전 업로드 버리기 | 원장, 실장 |
| MVP | GET | [`/imports/{import_id}/rows`](#op-get-imports-import_id-rows) | 행별 검사 결과 | 원장, 실장 |
| MVP | PUT | [`/imports/{import_id}/mapping`](#op-put-imports-import_id-mapping) | 열 매핑 저장 후 다시 검사 | 원장, 실장 |
| MVP | POST | [`/imports/{import_id}/commit`](#op-post-imports-import_id-commit) | 검사 통과한 행 반영 | 원장, 실장 |

### 감사 로그

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| MVP | GET | [`/audit-logs`](#op-get-audit-logs) | 감사 로그 조회 | 원장, 실장 |

### 학부모 커뮤니티

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| 2단계 | GET | [`/community/profile`](#op-get-community-profile) | 내 커뮤니티 프로필 | 학부모 |
| 2단계 | PUT | [`/community/profile`](#op-put-community-profile) | 닉네임 설정 | 학부모 |
| 2단계 | POST | [`/community/profile/agree-rules`](#op-post-community-profile-agree-rules) | 커뮤니티 이용 규칙 동의 | 학부모 |
| 2단계 | GET | [`/community/boards`](#op-get-community-boards) | 게시판 목록 | 학부모 |
| 2단계 | GET | [`/community/posts`](#op-get-community-posts) | 글 목록 | 학부모 |
| 2단계 | POST | [`/community/posts`](#op-post-community-posts) | 글쓰기 | 학부모 |
| 2단계 | POST | [`/community/posts/images`](#op-post-community-posts-images) | 글 이미지 올리기 | 학부모 |
| 2단계 | GET | [`/community/posts/{post_id}`](#op-get-community-posts-post_id) | 글 보기 | 학부모 |
| 2단계 | PATCH | [`/community/posts/{post_id}`](#op-patch-community-posts-post_id) | 글 수정 (작성자) | 학부모 |
| 2단계 | DELETE | [`/community/posts/{post_id}`](#op-delete-community-posts-post_id) | 글 삭제 (작성자) | 학부모 |
| 2단계 | PUT | [`/community/posts/{post_id}/like`](#op-put-community-posts-post_id-like) | 공감 | 학부모 |
| 2단계 | DELETE | [`/community/posts/{post_id}/like`](#op-delete-community-posts-post_id-like) | 공감 취소 | 학부모 |
| 2단계 | PUT | [`/community/posts/{post_id}/bookmark`](#op-put-community-posts-post_id-bookmark) | 북마크 | 학부모 |
| 2단계 | DELETE | [`/community/posts/{post_id}/bookmark`](#op-delete-community-posts-post_id-bookmark) | 북마크 취소 | 학부모 |
| 2단계 | GET | [`/community/posts/{post_id}/comments`](#op-get-community-posts-post_id-comments) | 댓글 목록 | 학부모 |
| 2단계 | POST | [`/community/posts/{post_id}/comments`](#op-post-community-posts-post_id-comments) | 댓글 쓰기 | 학부모 |
| 2단계 | DELETE | [`/community/comments/{comment_id}`](#op-delete-community-comments-comment_id) | 댓글 삭제 (작성자) | 학부모 |
| 2단계 | POST | [`/community/posts/{post_id}/reports`](#op-post-community-posts-post_id-reports) | 글 신고 | 학부모 |
| 2단계 | POST | [`/community/comments/{comment_id}/reports`](#op-post-community-comments-comment_id-reports) | 댓글 신고 | 학부모 |
| 2단계 | GET | [`/community/blocks`](#op-get-community-blocks) | 차단 목록 | 학부모 |
| 2단계 | POST | [`/community/blocks`](#op-post-community-blocks) | 작성자 차단 | 학부모 |
| 2단계 | DELETE | [`/community/blocks/{block_id}`](#op-delete-community-blocks-block_id) | 차단 해제 | 학부모 |

### 학부모 커뮤니티 (학원)

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| 2단계 | GET | [`/community/academy/suggestions`](#op-get-community-academy-suggestions) | 학원에 건의 글 | 원장, 실장 |
| 2단계 | GET | [`/community/academy/stats`](#op-get-community-academy-stats) | 커뮤니티 통계 (숫자만) | 원장, 실장 |
| 2단계 | GET | [`/community/academy/settings`](#op-get-community-academy-settings) | 커뮤니티 설정 조회 | 원장, 실장 |
| 2단계 | PUT | [`/community/academy/settings`](#op-put-community-academy-settings) | 커뮤니티 켜기·끄기, 소속 표시 최소 인원 | 원장 |

### 커뮤니티 신고 처리 (운영자)

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| 2단계 | GET | [`/ops/community/queue`](#op-get-ops-community-queue) | 신고 검토 대기열 | 플랫폼 운영자 |
| 2단계 | POST | [`/ops/community/{target_type}/{target_id}/decision`](#op-post-ops-community-target_type-target_id-decision) | 신고 처리 (복구·삭제·제재) | 플랫폼 운영자 |

### 과제

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| 2단계 | GET | [`/homework`](#op-get-homework) | 과제 목록 | 원장, 실장, 교사 |
| 2단계 | POST | [`/homework`](#op-post-homework) | 과제 등록 | 원장, 실장, 교사 |
| 2단계 | PATCH | [`/homework/{homework_id}`](#op-patch-homework-homework_id) | 과제 수정 | 원장, 실장, 교사 |
| 2단계 | GET | [`/homework/{homework_id}/submissions`](#op-get-homework-homework_id-submissions) | 제출 현황 | 원장, 실장, 교사 |
| 2단계 | PUT | [`/homework/{homework_id}/submissions`](#op-put-homework-homework_id-submissions) | 제출 기록 일괄 입력 | 원장, 실장, 교사 |

### 수납

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| 2단계 | GET | [`/invoices`](#op-get-invoices) | 청구 목록 | 원장, 실장 |
| 2단계 | POST | [`/invoices`](#op-post-invoices) | 청구 직접 등록 | 원장, 실장 |
| 2단계 | GET | [`/invoices/{invoice_id}`](#op-get-invoices-invoice_id) | 청구 상세 | 원장, 실장 |
| 2단계 | PATCH | [`/invoices/{invoice_id}`](#op-patch-invoices-invoice_id) | 청구 수정·취소 | 원장, 실장 |
| 3단계 | POST | [`/invoices/{invoice_id}/holds`](#op-post-invoices-invoice_id-holds) | 자동 안내 보류 걸기 | 원장, 실장 |
| 3단계 | DELETE | [`/invoices/{invoice_id}/holds/{reason}`](#op-delete-invoices-invoice_id-holds-reason) | 보류 해제 | 원장, 실장 |
| 3단계 | GET | [`/invoices/{invoice_id}/promises`](#op-get-invoices-invoice_id-promises) | 납부 약속 목록 | 원장, 실장 |
| 3단계 | POST | [`/invoices/{invoice_id}/promises`](#op-post-invoices-invoice_id-promises) | 납부 약속 등록 | 원장, 실장 |
| 3단계 | DELETE | [`/invoices/{invoice_id}/promises/{promise_id}`](#op-delete-invoices-invoice_id-promises-promise_id) | 납부 약속 취소 | 원장, 실장 |
| 2단계 | GET | [`/payments`](#op-get-payments) | 납부 기록 | 원장, 실장 |
| 2단계 | POST | [`/payments`](#op-post-payments) | 납부 등록 | 원장, 실장 |
| 2단계 | POST | [`/payments/{payment_id}/void`](#op-post-payments-payment_id-void) | 납부 취소 | 원장, 실장 |
| 3단계 | GET | [`/deposit-matches`](#op-get-deposit-matches) | 입금자명 매칭 후보 | 원장, 실장 |
| 3단계 | POST | [`/deposit-matches/{match_id}/confirm`](#op-post-deposit-matches-match_id-confirm) | 매칭 확정 → 납부 등록 | 원장, 실장 |
| 3단계 | POST | [`/deposit-matches/{match_id}/reject`](#op-post-deposit-matches-match_id-reject) | 매칭 거절 | 원장, 실장 |
| 3단계 | GET | [`/billing/sibling-discount`](#op-get-billing-sibling-discount) | 형제 할인 규칙 조회 | 원장, 실장, 교사 |
| 3단계 | PUT | [`/billing/sibling-discount`](#op-put-billing-sibling-discount) | 형제 할인 규칙 저장 | 원장 |

### 규칙 엔진

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| 3단계 | GET | [`/rules/settings`](#op-get-rules-settings) | 안내 규칙 설정 조회 | 원장, 실장 |
| 3단계 | PUT | [`/rules/settings`](#op-put-rules-settings) | 안내 규칙 설정 저장 | 원장 |
| 3단계 | GET | [`/rules/runs`](#op-get-rules-runs) | 실행 기록 | 원장, 실장 |
| 3단계 | POST | [`/rules/runs`](#op-post-rules-runs) | 규칙 엔진 수동 실행 | 원장, 실장 |
| 3단계 | GET | [`/rules/runs/{run_id}`](#op-get-rules-runs-run_id) | 실행 결과 | 원장, 실장 |

### 승인함

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| 3단계 | GET | [`/approvals`](#op-get-approvals) | 승인함 목록 | 원장, 실장, 교사 |
| 3단계 | POST | [`/approvals/bulk-approve`](#op-post-approvals-bulk-approve) | 여러 건 한 번에 승인 | 원장, 실장, 교사 |
| 3단계 | GET | [`/approvals/{approval_id}`](#op-get-approvals-approval_id) | 승인 상세 | 원장, 실장, 교사 |
| 3단계 | POST | [`/approvals/{approval_id}/approve`](#op-post-approvals-approval_id-approve) | 승인 (수정 후 승인 포함) | 원장, 실장, 교사 |
| 3단계 | POST | [`/approvals/{approval_id}/hold`](#op-post-approvals-approval_id-hold) | 보류 | 원장, 실장, 교사 |
| 3단계 | POST | [`/approvals/{approval_id}/reject`](#op-post-approvals-approval_id-reject) | 반려 | 원장, 실장, 교사 |

### 수납 안내 PDF

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| 3단계 | POST | [`/documents/billing-notices`](#op-post-documents-billing-notices) | 수납 안내 PDF 생성 | 원장, 실장 |
| 3단계 | GET | [`/documents/{document_id}`](#op-get-documents-document_id) | PDF 상태 | 원장, 실장 |
| 3단계 | POST | [`/documents/{document_id}/links`](#op-post-documents-document_id-links) | 만료되는 열람 링크 발급 | 원장, 실장 |

### AI 보조

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| 3단계 | POST | [`/ai/replies/{reply_id}/classify`](#op-post-ai-replies-reply_id-classify) | 회신 분류·후속 업무 제안 | 원장, 실장, 교사 |
| 3단계 | POST | [`/ai/candidates/{candidate_id}/draft`](#op-post-ai-candidates-candidate_id-draft) | 안내문 초안 | 원장, 실장 |
| 3단계 | POST | [`/ai/students/{student_id}/summary`](#op-post-ai-students-student_id-summary) | 상담 전 연락 이력 요약 | 원장, 실장, 교사 |
| 3단계 | POST | [`/ai/mismatch-scans`](#op-post-ai-mismatch-scans) | 수납·출결 불일치 후보 찾기 | 원장, 실장 |
| 3단계 | GET | [`/ai/runs`](#op-get-ai-runs) | AI 실행 기록 | 원장, 실장 |
| 3단계 | GET | [`/ai/runs/{run_id}`](#op-get-ai-runs-run_id) | AI 실행 결과 | 원장, 실장, 교사 |
| 3단계 | GET | [`/ai/runs/{run_id}/steps`](#op-get-ai-runs-run_id-steps) | AI 실행 단계별 기록 | 원장, 실장 |
| 3단계 | POST | [`/ai/runs/{run_id}/feedback`](#op-post-ai-runs-run_id-feedback) | AI 결과 채택·수정 기록 | 원장, 실장, 교사 |

### 웹훅

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| MVP | POST | [`/webhooks/sms/{provider}/delivery`](#op-post-webhooks-sms-provider-delivery) | 발송 결과 수신 | 공개 (서명 검증) |
| 3단계 | POST | [`/webhooks/sms/{provider}/inbound`](#op-post-webhooks-sms-provider-inbound) | 학부모 회신 수신 | 공개 (서명 검증) |

### 공개 링크

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
| 3단계 | GET | [`/public/replies/{token}`](#op-get-public-replies-token) | 원클릭 응답 화면 정보 | 공개 (일회용 토큰) |
| 3단계 | POST | [`/public/replies/{token}`](#op-post-public-replies-token) | 원클릭 응답 제출 | 공개 (일회용 토큰) |

### 상태

| 단계 | 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|---|
|  | GET | [`/health`](#op-get--health) | 서버 상태 확인 | 공개 |

## 엔드포인트 상세

### 인증

<a id="op-post-auth-academies"></a>

#### POST `/api/v1/auth/academies`

**학원 등록 + 관리자 가입** · 단계 `MVP` · 권한 공개

학원의 첫 계정(원장)을 만든다.

요청 본문: [AcademyRegister](#schema-academyregister)

응답 `201`: [TokenPair](#schema-tokenpair)

<a id="op-get-auth-invitations-code"></a>

#### GET `/api/v1/auth/invitations/{code}`

**초대 코드 확인** · 단계 `MVP` · 권한 공개

가입 화면에서 어느 학원, 어떤 역할 코드인지 보여준다. 학생 이름은 가려서 보낸다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `code` | 경로 | string | 예 |  | 길이 ≥ 6, 길이 ≤ 32 |

응답 `200`: [InvitationPreview](#schema-invitationpreview)

<a id="op-post-auth-signup"></a>

#### POST `/api/v1/auth/signup`

**초대 코드로 가입 (교사·학생·학부모)** · 단계 `MVP` · 권한 공개

코드는 한 번 쓰면 만료된다. 학부모 코드는 보호자 기록과, 학생 코드는 학생 명부와 연결된다. 만 14세 미만 학생은 보호자가 승인할 때까지 pending_guardian_consent 상태.

요청 본문: [SignupBody](#schema-signupbody)

응답 `201`: [SignupResult](#schema-signupresult)

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

**로그아웃 (리프레시 토큰 폐기)** · 단계 `MVP` · 권한 원장, 실장, 교사, 학생, 학부모

요청 본문: [RefreshBody](#schema-refreshbody)

응답 `204`: (본문 없음)

<a id="op-get-auth-me"></a>

#### GET `/api/v1/auth/me`

**내 정보·역할·첫 화면** · 단계 `MVP` · 권한 원장, 실장, 교사, 학생, 학부모

응답 `200`: [MeOut](#schema-meout)

### 대시보드

<a id="op-get-dashboard-today"></a>

#### GET `/api/v1/dashboard/today`

**관리자·교사 대시보드 요약** · 단계 `MVP` · 권한 원장, 실장, 교사

응답 `200`: [TodaySummary](#schema-todaysummary)

<a id="op-get-dashboard-briefing"></a>

#### GET `/api/v1/dashboard/briefing`

**담당자 아침 브리핑** · 단계 `3단계` · 권한 원장, 실장, 교사

응답 `200`: [Briefing](#schema-briefing)

<a id="op-get-review-items"></a>

#### GET `/api/v1/review-items`

**확인 필요함** · 단계 `MVP` · 권한 원장, 실장, 교사

업로드 오류, 형제 연결 후보, 같은 기기 출석 등 사람이 봐야 할 것을 한 목록으로.

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

**휴원·방학·공휴일 목록** · 단계 `2단계` · 권한 원장, 실장, 교사

규칙 엔진이 쉬는 날에는 결석 후보를 만들지 않고, 수납 단계를 영업일로 셀 때 쓴다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `from` | 쿼리 | string (date) | 예 |  |  |
| `to` | 쿼리 | string (date) | 예 |  |  |

응답 `200`: [CalendarEventOut](#schema-calendareventout)[]

<a id="op-post-academy-calendar"></a>

#### POST `/api/v1/academy/calendar`

**휴원·방학·공휴일 등록** · 단계 `2단계` · 권한 원장, 실장

요청 본문: [CalendarEventCreate](#schema-calendareventcreate)

응답 `201`: [CalendarEventOut](#schema-calendareventout)

<a id="op-delete-academy-calendar-event_id"></a>

#### DELETE `/api/v1/academy/calendar/{event_id}`

**휴원·방학·공휴일 삭제** · 단계 `2단계` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `event_id` | 경로 | string (uuid) | 예 |  |  |

응답 `204`: (본문 없음)

### 사용자

<a id="op-get-users"></a>

#### GET `/api/v1/users`

**계정 목록** · 단계 `MVP` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `role` | 쿼리 | [Role](#schema-role) \| null |  |  |  |
| `page` | 쿼리 | integer |  | `1` | ≥ 1 |
| `size` | 쿼리 | integer |  | `20` | ≥ 1, ≤ 100 |

응답 `200`: [Page_UserOut_](#schema-page-userout-)

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

### 초대 코드

<a id="op-get-invitations"></a>

#### GET `/api/v1/invitations`

**초대 코드 목록** · 단계 `MVP` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `role` | 쿼리 | [Role](#schema-role) \| null |  |  |  |
| `status` | 쿼리 | [InvitationStatus](#schema-invitationstatus) \| null |  |  |  |
| `student_id` | 쿼리 | string (uuid) \| null |  |  |  |
| `page` | 쿼리 | integer |  | `1` | ≥ 1 |
| `size` | 쿼리 | integer |  | `20` | ≥ 1, ≤ 100 |

응답 `200`: [Page_InvitationOut_](#schema-page-invitationout-)

<a id="op-post-invitations"></a>

#### POST `/api/v1/invitations`

**초대 코드 발급** · 단계 `MVP` · 권한 원장, 실장

교사·학생·학부모 가입용 일회용 코드. 코드 원문은 이 응답에서만 보인다 (DB에는 해시).

요청 본문: [InvitationCreate](#schema-invitationcreate)

응답 `201`: [InvitationOut](#schema-invitationout)

<a id="op-post-invitations-bulk"></a>

#### POST `/api/v1/invitations/bulk`

**학생·학부모 초대 코드 일괄 발급** · 단계 `MVP` · 권한 원장, 실장

명부 업로드 뒤 학생별 코드와 기본 보호자 코드를 한 번에 만든다. 안내문 인쇄용.

요청 본문: [InvitationBulkCreate](#schema-invitationbulkcreate)

응답 `201`: [InvitationOut](#schema-invitationout)[]

<a id="op-delete-invitations-invitation_id"></a>

#### DELETE `/api/v1/invitations/{invitation_id}`

**초대 코드 폐기** · 단계 `MVP` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `invitation_id` | 경로 | string (uuid) | 예 |  |  |

응답 `204`: (본문 없음)

### 강의

<a id="op-get-lectures"></a>

#### GET `/api/v1/lectures`

**강의 목록** · 단계 `MVP` · 권한 원장, 실장, 교사

교사는 mine=true로 내 강의만 본다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `mine` | 쿼리 | boolean |  | `false` |  |
| `teacher_id` | 쿼리 | string (uuid) \| null |  |  |  |
| `archived` | 쿼리 | boolean |  | `false` |  |

응답 `200`: [LectureOut](#schema-lectureout)[]

<a id="op-post-lectures"></a>

#### POST `/api/v1/lectures`

**강의 개설** · 단계 `MVP` · 권한 원장, 실장

시간표(schedule)가 있으면 개강일부터 4주치 회차를 자동으로 만든다.

요청 본문: [LectureCreate](#schema-lecturecreate)

응답 `201`: [LectureOut](#schema-lectureout)

<a id="op-get-lectures-lecture_id"></a>

#### GET `/api/v1/lectures/{lecture_id}`

**강의 상세** · 단계 `MVP` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `lecture_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [LectureOut](#schema-lectureout)

<a id="op-patch-lectures-lecture_id"></a>

#### PATCH `/api/v1/lectures/{lecture_id}`

**강의 수정·종강** · 단계 `MVP` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `lecture_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [LectureUpdate](#schema-lectureupdate)

응답 `200`: [LectureOut](#schema-lectureout)

<a id="op-get-lectures-lecture_id-students"></a>

#### GET `/api/v1/lectures/{lecture_id}/students`

**수강생 목록** · 단계 `MVP` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `lecture_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [StudentSummary](#schema-studentsummary)[]

<a id="op-post-lectures-lecture_id-students"></a>

#### POST `/api/v1/lectures/{lecture_id}/students`

**수강생 등록** · 단계 `MVP` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `lecture_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [EnrollBody](#schema-enrollbody)

응답 `200`: [LectureOut](#schema-lectureout)

<a id="op-delete-lectures-lecture_id-students-student_id"></a>

#### DELETE `/api/v1/lectures/{lecture_id}/students/{student_id}`

**수강 종료** · 단계 `MVP` · 권한 원장, 실장

지난 출결 기록은 남고, 앞으로의 회차에서만 빠진다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `lecture_id` | 경로 | string (uuid) | 예 |  |  |
| `student_id` | 경로 | string (uuid) | 예 |  |  |

응답 `204`: (본문 없음)

<a id="op-post-lectures-lecture_id-sessions-generate"></a>

#### POST `/api/v1/lectures/{lecture_id}/sessions/generate`

**시간표로 회차 만들기** · 단계 `MVP` · 권한 원장, 실장

기간 안의 회차를 만든다. 이미 있는 회차는 건너뛴다. 평소에는 워커가 매주 자동 실행.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `lecture_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [GenerateSessionsBody](#schema-generatesessionsbody)

응답 `200`: [LectureSessionOut](#schema-lecturesessionout)[]

### 강의 회차

<a id="op-get-lecture-sessions"></a>

#### GET `/api/v1/lecture-sessions`

**회차 목록 (오늘의 강의)** · 단계 `MVP` · 권한 원장, 실장, 교사

date를 비우면 오늘. 교사는 mine=true로 내 강의 회차만.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `date` | 쿼리 | string (date) \| null |  |  |  |
| `from` | 쿼리 | string (date) \| null |  |  |  |
| `to` | 쿼리 | string (date) \| null |  |  |  |
| `lecture_id` | 쿼리 | string (uuid) \| null |  |  |  |
| `mine` | 쿼리 | boolean |  | `false` |  |
| `status` | 쿼리 | [SessionStatus](#schema-sessionstatus) \| null |  |  |  |
| `page` | 쿼리 | integer |  | `1` | ≥ 1 |
| `size` | 쿼리 | integer |  | `20` | ≥ 1, ≤ 100 |

응답 `200`: [Page_LectureSessionOut_](#schema-page-lecturesessionout-)

<a id="op-post-lecture-sessions"></a>

#### POST `/api/v1/lecture-sessions`

**보강 회차 추가** · 단계 `MVP` · 권한 원장, 실장, 교사

요청 본문: [SessionCreate](#schema-sessioncreate)

응답 `201`: [LectureSessionOut](#schema-lecturesessionout)

<a id="op-get-lecture-sessions-session_id"></a>

#### GET `/api/v1/lecture-sessions/{session_id}`

**회차 상세** · 단계 `MVP` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `session_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [LectureSessionOut](#schema-lecturesessionout)

<a id="op-patch-lecture-sessions-session_id"></a>

#### PATCH `/api/v1/lecture-sessions/{session_id}`

**회차 시간 변경·휴강** · 단계 `MVP` · 권한 원장, 실장, 교사

휴강하면 수강생과 학부모에게 앱 알림이 간다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `session_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [SessionUpdate](#schema-sessionupdate)

응답 `200`: [LectureSessionOut](#schema-lecturesessionout)

### 출결

<a id="op-post-lecture-sessions-session_id-attendance-open"></a>

#### POST `/api/v1/lecture-sessions/{session_id}/attendance/open`

**출석 시작** · 단계 `MVP` · 권한 원장, 실장, 교사

회차를 open으로 바꾸고 QR 발급을 시작한다. 출석 가능 시간(시작 15분 전 ~ 종료) 안에서만.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `session_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [LectureSessionOut](#schema-lecturesessionout)

<a id="op-get-lecture-sessions-session_id-attendance-qr"></a>

#### GET `/api/v1/lecture-sessions/{session_id}/attendance/qr`

**현재 QR 토큰** · 단계 `MVP` · 권한 원장, 실장, 교사

토큰은 30초마다 바뀐다. 교실 화면은 refresh_in_seconds마다 다시 요청한다. 토큰은 저장하지 않는 서명 값이라 사진으로 공유해도 곧 무효가 된다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `session_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [QrTokenOut](#schema-qrtokenout)

<a id="op-get-lecture-sessions-session_id-attendance"></a>

#### GET `/api/v1/lecture-sessions/{session_id}/attendance`

**실시간 출석 명단** · 단계 `MVP` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `session_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [SessionRoster](#schema-sessionroster)

<a id="op-put-lecture-sessions-session_id-attendance-student_id"></a>

#### PUT `/api/v1/lecture-sessions/{session_id}/attendance/{student_id}`

**수동 출결 처리** · 단계 `MVP` · 권한 원장, 실장, 교사

휴대전화가 없는 학생, 사전 연락된 결석 등. method=manual로 기록된다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `session_id` | 경로 | string (uuid) | 예 |  |  |
| `student_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [ManualMark](#schema-manualmark)

응답 `200`: [AttendanceOut](#schema-attendanceout)

<a id="op-post-lecture-sessions-session_id-attendance-close"></a>

#### POST `/api/v1/lecture-sessions/{session_id}/attendance/close`

**출석 마감** · 단계 `MVP` · 권한 원장, 실장, 교사

안 찍은 학생은 결석(auto_absent)으로 기록하고 학부모에게 앱 푸시, 관리자에게 결석 알림을 만든다. 교사가 마감하지 않으면 회차 종료 시각에 워커가 자동 마감한다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `session_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [SessionRoster](#schema-sessionroster)

<a id="op-post-attendance-check-in"></a>

#### POST `/api/v1/attendance/check-in`

**QR 출석 (학생)** · 단계 `MVP` · 권한 학생

토큰 서명·유효 시간, 수강생 여부, 출석 가능 시간을 확인한다. 같은 회차에 두 번 찍으면 첫 기록을 돌려준다. 실패 사유: 400 expired_qr · 403 not_enrolled · 409 attendance_closed / too_early

요청 본문: [CheckInBody](#schema-checkinbody)

응답 `200`: [CheckInResult](#schema-checkinresult)

<a id="op-get-attendance"></a>

#### GET `/api/v1/attendance`

**출결 조회** · 단계 `MVP` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `lecture_id` | 쿼리 | string (uuid) \| null |  |  |  |
| `session_id` | 쿼리 | string (uuid) \| null |  |  |  |
| `student_id` | 쿼리 | string (uuid) \| null |  |  |  |
| `from` | 쿼리 | string (date) \| null |  |  |  |
| `to` | 쿼리 | string (date) \| null |  |  |  |
| `status` | 쿼리 | [AttendanceStatus](#schema-attendancestatus) \| null |  |  |  |
| `page` | 쿼리 | integer |  | `1` | ≥ 1 |
| `size` | 쿼리 | integer |  | `20` | ≥ 1, ≤ 100 |

응답 `200`: [Page_AttendanceOut_](#schema-page-attendanceout-)

<a id="op-get-attendance-alerts"></a>

#### GET `/api/v1/attendance/alerts`

**결석 알림** · 단계 `MVP` · 권한 원장, 실장, 교사

마감 때 무단결석이면 생긴다. 형제가 같은 날 함께 결석하면 한 건으로 묶는다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `status` | 쿼리 | [AlertStatus](#schema-alertstatus) |  | `"open"` |  |
| `page` | 쿼리 | integer |  | `1` | ≥ 1 |
| `size` | 쿼리 | integer |  | `20` | ≥ 1, ≤ 100 |

응답 `200`: [Page_AttendanceAlertOut_](#schema-page-attendancealertout-)

<a id="op-post-attendance-alerts-alert_id-ack"></a>

#### POST `/api/v1/attendance/alerts/{alert_id}/ack`

**결석 알림 확인** · 단계 `MVP` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `alert_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [AlertAck](#schema-alertack)

응답 `200`: [AttendanceAlertOut](#schema-attendancealertout)

<a id="op-patch-attendance-attendance_id"></a>

#### PATCH `/api/v1/attendance/{attendance_id}`

**출결 정정** · 단계 `MVP` · 권한 원장, 실장, 교사

결석 → 출석으로 정정하면 학부모에게 정정 알림(앱 푸시)이 간다. 이력은 감사 로그에 남는다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `attendance_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [AttendanceCorrection](#schema-attendancecorrection)

응답 `200`: [AttendanceOut](#schema-attendanceout)

### 학생

<a id="op-get-students"></a>

#### GET `/api/v1/students`

**학생 목록·검색** · 단계 `MVP` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `q` | 쿼리 | string \| null |  |  |  |
| `status` | 쿼리 | [StudentStatus](#schema-studentstatus) \| null |  |  |  |
| `lecture_id` | 쿼리 | string (uuid) \| null |  |  |  |
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

**상담·통화 메모 추가** · 단계 `2단계` · 권한 원장, 실장, 교사

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

<a id="op-get-students-student_id-report"></a>

#### GET `/api/v1/students/{student_id}/report`

**학생 리포트 (직원용)** · 단계 `MVP` · 권한 원장, 실장, 교사

학부모가 보는 것과 같은 리포트. 상담 준비용.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `student_id` | 경로 | string (uuid) | 예 |  |  |
| `period` | 쿼리 | [ReportPeriod](#schema-reportperiod) |  | `"month"` |  |
| `date` | 쿼리 | string (date) \| null |  |  |  |

응답 `200`: [ChildReport](#schema-childreport)

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

### 학생 화면

<a id="op-get-me-schedule"></a>

#### GET `/api/v1/me/schedule`

**내 시간표** · 단계 `MVP` · 권한 학생

응답 `200`: [MySchedule](#schema-myschedule)

<a id="op-get-me-attendance"></a>

#### GET `/api/v1/me/attendance`

**내 출결** · 단계 `MVP` · 권한 학생

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `from` | 쿼리 | string (date) \| null |  |  |  |
| `to` | 쿼리 | string (date) \| null |  |  |  |

응답 `200`: [AttendanceOut](#schema-attendanceout)[]

<a id="op-get-me-attendance-summary"></a>

#### GET `/api/v1/me/attendance/summary`

**내 강의별 출석률** · 단계 `MVP` · 권한 학생

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `from` | 쿼리 | string (date) \| null |  |  |  |
| `to` | 쿼리 | string (date) \| null |  |  |  |

응답 `200`: [AttendanceSummary](#schema-attendancesummary)[]

### 학부모 화면

<a id="op-get-children"></a>

#### GET `/api/v1/children`

**내 자녀 목록** · 단계 `MVP` · 권한 학부모

응답 `200`: [ChildOut](#schema-childout)[]

<a id="op-post-children"></a>

#### POST `/api/v1/children`

**자녀 추가 (형제)** · 단계 `MVP` · 권한 학부모

둘째 자녀의 학부모 초대 코드를 넣으면 같은 계정에 연결된다.

요청 본문: [AddChildBody](#schema-addchildbody)

응답 `201`: [ChildOut](#schema-childout)

<a id="op-post-children-student_id-approve-account"></a>

#### POST `/api/v1/children/{student_id}/approve-account`

**자녀 학생 계정 승인** · 단계 `MVP` · 권한 학부모

만 14세 미만 학생 가입에 필요한 법정대리인 동의. 승인 기록은 감사 로그에 남는다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `student_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [ChildOut](#schema-childout)

<a id="op-get-children-student_id-report"></a>

#### GET `/api/v1/children/{student_id}/report`

**자녀 리포트** · 단계 `MVP` · 권한 학부모

period=week|month, date가 속한 주·월. 비우면 이번 주. 자녀와 교사의 질의응답은 포함하지 않는다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `student_id` | 경로 | string (uuid) | 예 |  |  |
| `period` | 쿼리 | [ReportPeriod](#schema-reportperiod) |  | `"week"` |  |
| `date` | 쿼리 | string (date) \| null |  |  |  |

응답 `200`: [ChildReport](#schema-childreport)

<a id="op-get-children-student_id-attendance"></a>

#### GET `/api/v1/children/{student_id}/attendance`

**자녀 출결 달력** · 단계 `MVP` · 권한 학부모

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `student_id` | 경로 | string (uuid) | 예 |  |  |
| `from` | 쿼리 | string (date) \| null |  |  |  |
| `to` | 쿼리 | string (date) \| null |  |  |  |

응답 `200`: [AttendanceOut](#schema-attendanceout)[]

### 공지사항

<a id="op-get-notices"></a>

#### GET `/api/v1/notices`

**공지 목록** · 단계 `MVP` · 권한 원장, 실장, 교사, 학생, 학부모

요청한 사람에게 보이는 공지만 준다. 학생은 학원 전체·내 강의의 학생 대상 공지, 학부모는 자녀 강의의 학부모 대상 공지. 고정 공지가 먼저.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `lecture_id` | 쿼리 | string (uuid) \| null |  |  |  |
| `audience` | 쿼리 | [NoticeAudience](#schema-noticeaudience) \| null |  |  |  |
| `unread` | 쿼리 | boolean |  | `false` |  |
| `student_id` | 쿼리 | string (uuid) \| null |  |  |  |
| `page` | 쿼리 | integer |  | `1` | ≥ 1 |
| `size` | 쿼리 | integer |  | `20` | ≥ 1, ≤ 100 |

응답 `200`: [Page_NoticeOut_](#schema-page-noticeout-)

<a id="op-post-notices"></a>

#### POST `/api/v1/notices`

**공지 작성** · 단계 `MVP` · 권한 원장, 실장, 교사

관리자는 학원 전체·모든 강의, 교사는 자기 강의만. notify=true면 앱 푸시 (문자는 보내지 않음).

요청 본문: [NoticeCreate](#schema-noticecreate)

응답 `201`: [NoticeOut](#schema-noticeout)

<a id="op-post-notices-attachments"></a>

#### POST `/api/v1/notices/attachments`

**첨부 파일 올리기** · 단계 `MVP` · 권한 원장, 실장, 교사

비공개 저장소에 저장. 공지 작성 때 attachment_ids로 연결한다. 10MB 이하.

요청 본문: [Body_upload_attachment_api_v1_notices_attachments_post](#schema-body-upload-attachment-api-v1-notices-attachments-post) (`multipart/form-data`)

응답 `201`: [AttachmentOut](#schema-attachmentout)

<a id="op-get-notices-notice_id"></a>

#### GET `/api/v1/notices/{notice_id}`

**공지 상세** · 단계 `MVP` · 권한 원장, 실장, 교사, 학생, 학부모

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `notice_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [NoticeOut](#schema-noticeout)

<a id="op-patch-notices-notice_id"></a>

#### PATCH `/api/v1/notices/{notice_id}`

**공지 수정** · 단계 `MVP` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `notice_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [NoticeUpdate](#schema-noticeupdate)

응답 `200`: [NoticeOut](#schema-noticeout)

<a id="op-delete-notices-notice_id"></a>

#### DELETE `/api/v1/notices/{notice_id}`

**공지 삭제** · 단계 `MVP` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `notice_id` | 경로 | string (uuid) | 예 |  |  |

응답 `204`: (본문 없음)

<a id="op-post-notices-notice_id-read"></a>

#### POST `/api/v1/notices/{notice_id}/read`

**읽음 표시** · 단계 `MVP` · 권한 원장, 실장, 교사, 학생, 학부모

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `notice_id` | 경로 | string (uuid) | 예 |  |  |

응답 `204`: (본문 없음)

<a id="op-get-notices-notice_id-reads"></a>

#### GET `/api/v1/notices/{notice_id}/reads`

**읽음 현황** · 단계 `MVP` · 권한 원장, 실장, 교사

누가 아직 안 읽었는지. 작성자와 관리자만.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `notice_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [NoticeReads](#schema-noticereads)

### 질의응답

<a id="op-get-questions"></a>

#### GET `/api/v1/questions`

**질문 목록** · 단계 `MVP` · 권한 원장, 실장, 교사, 학생, 학부모

학생·학부모는 자기가 쓴 질문, 교사는 배정된 질문과 자기 강의 질문, 관리자는 전체. 학부모는 자녀가 교사와 나눈 질문을 볼 수 없다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `status` | 쿼리 | [QuestionStatus](#schema-questionstatus) \| null |  |  |  |
| `category` | 쿼리 | [QuestionCategory](#schema-questioncategory) \| null |  |  |  |
| `lecture_id` | 쿼리 | string (uuid) \| null |  |  |  |
| `assigned_to_me` | 쿼리 | boolean |  | `false` |  |
| `page` | 쿼리 | integer |  | `1` | ≥ 1 |
| `size` | 쿼리 | integer |  | `20` | ≥ 1, ≤ 100 |

응답 `200`: [Page_QuestionOut_](#schema-page-questionout-)

<a id="op-post-questions"></a>

#### POST `/api/v1/questions`

**질문하기 (학생·학부모)** · 단계 `MVP` · 권한 학생, 학부모

lecture_id를 고르면 그 강의 교사에게, 아니면 학원 관리자에게 간다. 받는 사람에게 앱 푸시.

요청 본문: [QuestionCreate](#schema-questioncreate)

응답 `201`: [QuestionDetail](#schema-questiondetail)

<a id="op-get-questions-public"></a>

#### GET `/api/v1/questions/public`

**같은 강의 공개 질문 (익명)** · 단계 `2단계` · 권한 학생

학생이 공개로 바꾼 질문을 같은 강의 학생이 본다. 작성자 이름은 보이지 않는다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `lecture_id` | 쿼리 | string (uuid) | 예 |  |  |
| `page` | 쿼리 | integer |  | `1` | ≥ 1 |
| `size` | 쿼리 | integer |  | `20` | ≥ 1, ≤ 100 |

응답 `200`: [Page_QuestionOut_](#schema-page-questionout-)

<a id="op-get-questions-question_id"></a>

#### GET `/api/v1/questions/{question_id}`

**질문 상세·대화** · 단계 `MVP` · 권한 원장, 실장, 교사, 학생, 학부모

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `question_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [QuestionDetail](#schema-questiondetail)

<a id="op-patch-questions-question_id"></a>

#### PATCH `/api/v1/questions/{question_id}`

**종료·담당 변경·공개 전환** · 단계 `MVP` · 권한 원장, 실장, 교사, 학생, 학부모

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `question_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [QuestionUpdate](#schema-questionupdate)

응답 `200`: [QuestionOut](#schema-questionout)

<a id="op-post-questions-question_id-messages"></a>

#### POST `/api/v1/questions/{question_id}/messages`

**답변·추가 질문** · 단계 `MVP` · 권한 원장, 실장, 교사, 학생, 학부모

교사가 답하면 상태가 answered, 질문자가 다시 쓰면 open으로 바뀐다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `question_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [QuestionMessageCreate](#schema-questionmessagecreate)

응답 `201`: [QuestionMessageOut](#schema-questionmessageout)

<a id="op-post-questions-question_id-read"></a>

#### POST `/api/v1/questions/{question_id}/read`

**읽음 표시** · 단계 `MVP` · 권한 원장, 실장, 교사, 학생, 학부모

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `question_id` | 경로 | string (uuid) | 예 |  |  |

응답 `204`: (본문 없음)

### 알림

<a id="op-get-notifications"></a>

#### GET `/api/v1/notifications`

**알림함** · 단계 `MVP` · 권한 원장, 실장, 교사, 학생, 학부모

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `unread` | 쿼리 | boolean |  | `false` |  |
| `page` | 쿼리 | integer |  | `1` | ≥ 1 |
| `size` | 쿼리 | integer |  | `20` | ≥ 1, ≤ 100 |

응답 `200`: [Page_NotificationOut_](#schema-page-notificationout-)

<a id="op-post-notifications-read"></a>

#### POST `/api/v1/notifications/read`

**알림 읽음** · 단계 `MVP` · 권한 원장, 실장, 교사, 학생, 학부모

요청 본문: [ReadBody](#schema-readbody)

응답 `204`: (본문 없음)

<a id="op-post-notifications-push-subscriptions"></a>

#### POST `/api/v1/notifications/push-subscriptions`

**앱 푸시 구독 등록** · 단계 `MVP` · 권한 원장, 실장, 교사, 학생, 학부모

기기마다 한 번. 같은 endpoint면 갱신한다.

요청 본문: [PushSubscriptionBody](#schema-pushsubscriptionbody)

응답 `204`: (본문 없음)

<a id="op-post-notifications-push-subscriptions-delete"></a>

#### POST `/api/v1/notifications/push-subscriptions/delete`

**앱 푸시 구독 해제** · 단계 `MVP` · 권한 원장, 실장, 교사, 학생, 학부모

요청 본문: [UnsubscribeBody](#schema-unsubscribebody)

응답 `204`: (본문 없음)

<a id="op-get-notifications-preferences"></a>

#### GET `/api/v1/notifications/preferences`

**알림 설정 조회** · 단계 `MVP` · 권한 원장, 실장, 교사, 학생, 학부모

응답 `200`: [NotificationPreferences](#schema-notificationpreferences)

<a id="op-put-notifications-preferences"></a>

#### PUT `/api/v1/notifications/preferences`

**알림 설정 저장** · 단계 `MVP` · 권한 원장, 실장, 교사, 학생, 학부모

요청 본문: [NotificationPreferences](#schema-notificationpreferences)

응답 `200`: [NotificationPreferences](#schema-notificationpreferences)

### 템플릿

<a id="op-get-templates"></a>

#### GET `/api/v1/templates`

**템플릿 목록** · 단계 `3단계` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `kind` | 쿼리 | [NoticeKind](#schema-noticekind) \| null |  |  |  |
| `archived` | 쿼리 | boolean |  | `false` |  |

응답 `200`: [TemplateOut](#schema-templateout)[]

<a id="op-post-templates"></a>

#### POST `/api/v1/templates`

**템플릿 만들기 (버전 1 초안)** · 단계 `3단계` · 권한 원장, 실장

요청 본문: [TemplateCreate](#schema-templatecreate)

응답 `201`: [TemplateOut](#schema-templateout)

<a id="op-get-templates-template_id"></a>

#### GET `/api/v1/templates/{template_id}`

**템플릿 상세** · 단계 `3단계` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `template_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [TemplateOut](#schema-templateout)

<a id="op-patch-templates-template_id"></a>

#### PATCH `/api/v1/templates/{template_id}`

**템플릿 이름 수정·보관** · 단계 `3단계` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `template_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [TemplateUpdate](#schema-templateupdate)

응답 `200`: [TemplateOut](#schema-templateout)

<a id="op-get-templates-template_id-versions"></a>

#### GET `/api/v1/templates/{template_id}/versions`

**템플릿 버전 목록** · 단계 `3단계` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `template_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [TemplateVersionOut](#schema-templateversionout)[]

<a id="op-post-templates-template_id-versions"></a>

#### POST `/api/v1/templates/{template_id}/versions`

**새 버전 초안** · 단계 `3단계` · 권한 원장, 실장

문구를 고치면 새 버전이 생긴다. 이미 보낸 건은 당시 버전을 기록하고 있다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `template_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [TemplateVersionCreate](#schema-templateversioncreate)

응답 `201`: [TemplateVersionOut](#schema-templateversionout)

<a id="op-post-templates-template_id-versions-version-approve"></a>

#### POST `/api/v1/templates/{template_id}/versions/{version}/approve`

**버전 승인** · 단계 `3단계` · 권한 원장, 실장

승인된 버전만 발송에 쓴다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `template_id` | 경로 | string (uuid) | 예 |  |  |
| `version` | 경로 | integer | 예 |  |  |

응답 `200`: [TemplateVersionOut](#schema-templateversionout)

<a id="op-post-templates-template_id-preview"></a>

#### POST `/api/v1/templates/{template_id}/preview`

**자리 표시 채워 미리 보기** · 단계 `3단계` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `template_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [PreviewBody](#schema-previewbody)

응답 `200`: [PreviewOut](#schema-previewout)

<a id="op-get-templates-template_id-versions-version-translations"></a>

#### GET `/api/v1/templates/{template_id}/versions/{version}/translations`

**번역 목록** · 단계 `3단계` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `template_id` | 경로 | string (uuid) | 예 |  |  |
| `version` | 경로 | integer | 예 |  |  |

응답 `200`: [TranslationOut](#schema-translationout)[]

<a id="op-post-templates-template_id-versions-version-translations"></a>

#### POST `/api/v1/templates/{template_id}/versions/{version}/translations`

**번역 생성 요청 (AI)** · 단계 `3단계` · 권한 원장, 실장

템플릿 버전 × 언어 단위로 한 번 번역한다. 자리 표시는 번역하지 않고 그대로 둔다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `template_id` | 경로 | string (uuid) | 예 |  |  |
| `version` | 경로 | integer | 예 |  |  |

요청 본문: [TranslationRequest](#schema-translationrequest)

응답 `202`: [TranslationOut](#schema-translationout)

<a id="op-patch-templates-template_id-versions-version-translations-language"></a>

#### PATCH `/api/v1/templates/{template_id}/versions/{version}/translations/{language}`

**번역 수정·승인** · 단계 `3단계` · 권한 원장, 실장

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

**안내 후보 목록** · 단계 `3단계` · 권한 원장, 실장, 교사

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

**안내 후보 상세** · 단계 `3단계` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `candidate_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [CandidateOut](#schema-candidateout)

<a id="op-post-candidates-candidate_id-cancel"></a>

#### POST `/api/v1/candidates/{candidate_id}/cancel`

**안내 후보 취소** · 단계 `3단계` · 권한 원장, 실장

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

**오발송 정정 안내 만들기** · 단계 `3단계` · 권한 원장, 실장

정정 안내 초안을 승인함에 올리고, 같은 사유 후속 안내를 멈추고, 원인을 기록한다. 응답은 생성된 정정 안내 후보.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `message_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [CorrectionBody](#schema-correctionbody)

응답 `201`: [CandidateOut](#schema-candidateout)

### 회신

<a id="op-get-replies"></a>

#### GET `/api/v1/replies`

**학부모 회신 목록** · 단계 `3단계` · 권한 원장, 실장, 교사

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

**회신 상세** · 단계 `3단계` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `reply_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [ReplyOut](#schema-replyout)

<a id="op-patch-replies-reply_id"></a>

#### PATCH `/api/v1/replies/{reply_id}`

**회신 분류 확정·처리 완료** · 단계 `3단계` · 권한 원장, 실장, 교사

paid·correction·consult_request로 확정하면 같은 사유 후속 안내를 멈춘다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `reply_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [ReplyUpdate](#schema-replyupdate)

응답 `200`: [ReplyOut](#schema-replyout)

### 긴급 문자

<a id="op-post-emergency-messages-preview"></a>

#### POST `/api/v1/emergency-messages/preview`

**긴급 문자 미리 보기** · 단계 `MVP` · 권한 원장, 실장, 교사

받을 인원, 번역 필요 인원, 오늘 남은 발송 한도를 보여주고 preview_token을 준다. 교사는 자기 강의 학생의 학부모만, 학원 전체(academy)는 관리자만.

요청 본문: [EmergencyPreviewBody](#schema-emergencypreviewbody)

응답 `200`: [EmergencyPreview](#schema-emergencypreview)

<a id="op-get-emergency-messages"></a>

#### GET `/api/v1/emergency-messages`

**긴급 문자 이력** · 단계 `MVP` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `page` | 쿼리 | integer |  | `1` | ≥ 1 |
| `size` | 쿼리 | integer |  | `20` | ≥ 1, ≤ 100 |

응답 `200`: [Page_EmergencyMessageOut_](#schema-page-emergencymessageout-)

<a id="op-post-emergency-messages"></a>

#### POST `/api/v1/emergency-messages`

**긴급 문자 발송** · 단계 `MVP` · 권한 원장, 실장, 교사

미리 보기에서 받은 preview_token이 있어야 보낸다. 문자와 앱 푸시를 같이 보내고, 외국어 수신자에게는 번역문을 덧붙인다. 발송 기록은 감사 로그에 남는다.

요청 본문: [EmergencySendBody](#schema-emergencysendbody)

응답 `202`: [EmergencyMessageOut](#schema-emergencymessageout)

<a id="op-get-emergency-messages-emergency_id"></a>

#### GET `/api/v1/emergency-messages/{emergency_id}`

**긴급 문자 상세·수신 결과** · 단계 `MVP` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `emergency_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [EmergencyMessageDetail](#schema-emergencymessagedetail)

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

**구글 시트에서 가져오기** · 단계 `3단계` · 권한 원장, 실장

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

### 학부모 커뮤니티

<a id="op-get-community-profile"></a>

#### GET `/api/v1/community/profile`

**내 커뮤니티 프로필** · 단계 `2단계` · 권한 학부모

응답 `200`: [CommunityProfile](#schema-communityprofile)

<a id="op-put-community-profile"></a>

#### PUT `/api/v1/community/profile`

**닉네임 설정** · 단계 `2단계` · 권한 학부모

공개(닉네임) 글에만 쓰인다. 학원 안에서 중복 불가.

요청 본문: [ProfileUpdate](#schema-profileupdate)

응답 `200`: [CommunityProfile](#schema-communityprofile)

<a id="op-post-community-profile-agree-rules"></a>

#### POST `/api/v1/community/profile/agree-rules`

**커뮤니티 이용 규칙 동의** · 단계 `2단계` · 권한 학부모

동의해야 글·댓글을 쓸 수 있다.

응답 `200`: [CommunityProfile](#schema-communityprofile)

<a id="op-get-community-boards"></a>

#### GET `/api/v1/community/boards`

**게시판 목록** · 단계 `2단계` · 권한 학부모

응답 `200`: [BoardOut](#schema-boardout)[]

<a id="op-get-community-posts"></a>

#### GET `/api/v1/community/posts`

**글 목록** · 단계 `2단계` · 권한 학부모

내가 볼 수 있는 범위(학원 전체 + 내 자녀 학년·강의)의 글만. 차단한 사람의 글은 빠진다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `board_id` | 쿼리 | string (uuid) \| null |  |  |  |
| `scope` | 쿼리 | [PostScope](#schema-postscope) \| null |  |  |  |
| `q` | 쿼리 | string \| null |  |  | 길이 ≤ 50 |
| `sort` | 쿼리 | `recent` \| `popular` |  | `"recent"` |  |
| `mine` | 쿼리 | boolean |  | `false` |  |
| `bookmarked` | 쿼리 | boolean |  | `false` |  |
| `page` | 쿼리 | integer |  | `1` | ≥ 1 |
| `size` | 쿼리 | integer |  | `20` | ≥ 1, ≤ 100 |

응답 `200`: [Page_PostOut_](#schema-page-postout-)

<a id="op-post-community-posts"></a>

#### POST `/api/v1/community/posts`

**글쓰기** · 단계 `2단계` · 권한 학부모

저장 전에 전화번호·실명 패턴을 가리고 결과를 check로 알려준다. 금칙어·다른 학원 홍보는 거부(422). 건의 게시판 글은 학원 관리자에게 전달된다.

요청 본문: [PostCreate](#schema-postcreate)

응답 `201`: [PostCreateResult](#schema-postcreateresult)

<a id="op-post-community-posts-images"></a>

#### POST `/api/v1/community/posts/images`

**글 이미지 올리기** · 단계 `2단계` · 권한 학부모

사진 위치 정보(EXIF)는 지우고 저장한다.

요청 본문: [Body_upload_image_api_v1_community_posts_images_post](#schema-body-upload-image-api-v1-community-posts-images-post) (`multipart/form-data`)

응답 `201`: map<string, string>

<a id="op-get-community-posts-post_id"></a>

#### GET `/api/v1/community/posts/{post_id}`

**글 보기** · 단계 `2단계` · 권한 학부모

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `post_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [PostDetail](#schema-postdetail)

<a id="op-patch-community-posts-post_id"></a>

#### PATCH `/api/v1/community/posts/{post_id}`

**글 수정 (작성자)** · 단계 `2단계` · 권한 학부모

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `post_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [PostUpdate](#schema-postupdate)

응답 `200`: [PostDetail](#schema-postdetail)

<a id="op-delete-community-posts-post_id"></a>

#### DELETE `/api/v1/community/posts/{post_id}`

**글 삭제 (작성자)** · 단계 `2단계` · 권한 학부모

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `post_id` | 경로 | string (uuid) | 예 |  |  |

응답 `204`: (본문 없음)

<a id="op-put-community-posts-post_id-like"></a>

#### PUT `/api/v1/community/posts/{post_id}/like`

**공감** · 단계 `2단계` · 권한 학부모

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `post_id` | 경로 | string (uuid) | 예 |  |  |

응답 `204`: (본문 없음)

<a id="op-delete-community-posts-post_id-like"></a>

#### DELETE `/api/v1/community/posts/{post_id}/like`

**공감 취소** · 단계 `2단계` · 권한 학부모

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `post_id` | 경로 | string (uuid) | 예 |  |  |

응답 `204`: (본문 없음)

<a id="op-put-community-posts-post_id-bookmark"></a>

#### PUT `/api/v1/community/posts/{post_id}/bookmark`

**북마크** · 단계 `2단계` · 권한 학부모

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `post_id` | 경로 | string (uuid) | 예 |  |  |

응답 `204`: (본문 없음)

<a id="op-delete-community-posts-post_id-bookmark"></a>

#### DELETE `/api/v1/community/posts/{post_id}/bookmark`

**북마크 취소** · 단계 `2단계` · 권한 학부모

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `post_id` | 경로 | string (uuid) | 예 |  |  |

응답 `204`: (본문 없음)

<a id="op-get-community-posts-post_id-comments"></a>

#### GET `/api/v1/community/posts/{post_id}/comments`

**댓글 목록** · 단계 `2단계` · 권한 학부모

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `post_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [CommentOut](#schema-commentout)[]

<a id="op-post-community-posts-post_id-comments"></a>

#### POST `/api/v1/community/posts/{post_id}/comments`

**댓글 쓰기** · 단계 `2단계` · 권한 학부모

익명 댓글은 이 글 안에서만 쓰는 번호(익명1, 익명2)가 붙는다. 글쓴이는 '글쓴이'로 표시.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `post_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [CommentCreate](#schema-commentcreate)

응답 `201`: [CommentOut](#schema-commentout)

<a id="op-delete-community-comments-comment_id"></a>

#### DELETE `/api/v1/community/comments/{comment_id}`

**댓글 삭제 (작성자)** · 단계 `2단계` · 권한 학부모

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `comment_id` | 경로 | string (uuid) | 예 |  |  |

응답 `204`: (본문 없음)

<a id="op-post-community-posts-post_id-reports"></a>

#### POST `/api/v1/community/posts/{post_id}/reports`

**글 신고** · 단계 `2단계` · 권한 학부모

한 사람이 같은 글을 한 번만 신고할 수 있다. 서로 다른 3명이 신고하면 임시 블라인드되고 운영자 검토로 간다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `post_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [ReportBody](#schema-reportbody)

응답 `200`: [ReportResult](#schema-reportresult)

<a id="op-post-community-comments-comment_id-reports"></a>

#### POST `/api/v1/community/comments/{comment_id}/reports`

**댓글 신고** · 단계 `2단계` · 권한 학부모

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `comment_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [ReportBody](#schema-reportbody)

응답 `200`: [ReportResult](#schema-reportresult)

<a id="op-get-community-blocks"></a>

#### GET `/api/v1/community/blocks`

**차단 목록** · 단계 `2단계` · 권한 학부모

응답 `200`: [BlockOut](#schema-blockout)[]

<a id="op-post-community-blocks"></a>

#### POST `/api/v1/community/blocks`

**작성자 차단** · 단계 `2단계` · 권한 학부모

글이나 댓글 ID로 차단한다. 그 사람의 글·댓글이 내 화면에서 사라진다.

요청 본문: [BlockBody](#schema-blockbody)

응답 `201`: [BlockOut](#schema-blockout)

<a id="op-delete-community-blocks-block_id"></a>

#### DELETE `/api/v1/community/blocks/{block_id}`

**차단 해제** · 단계 `2단계` · 권한 학부모

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `block_id` | 경로 | string (uuid) | 예 |  |  |

응답 `204`: (본문 없음)

### 학부모 커뮤니티 (학원)

<a id="op-get-community-academy-suggestions"></a>

#### GET `/api/v1/community/academy/suggestions`

**학원에 건의 글** · 단계 `2단계` · 권한 원장, 실장

학원이 볼 수 있는 유일한 커뮤니티 글. 작성자는 익명 표시 그대로.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `page` | 쿼리 | integer |  | `1` | ≥ 1 |
| `size` | 쿼리 | integer |  | `20` | ≥ 1, ≤ 100 |

응답 `200`: [Page_PostDetail_](#schema-page-postdetail-)

<a id="op-get-community-academy-stats"></a>

#### GET `/api/v1/community/academy/stats`

**커뮤니티 통계 (숫자만)** · 단계 `2단계` · 권한 원장, 실장

응답 `200`: [CommunityStats](#schema-communitystats)

<a id="op-get-community-academy-settings"></a>

#### GET `/api/v1/community/academy/settings`

**커뮤니티 설정 조회** · 단계 `2단계` · 권한 원장, 실장

응답 `200`: [CommunitySettings](#schema-communitysettings)

<a id="op-put-community-academy-settings"></a>

#### PUT `/api/v1/community/academy/settings`

**커뮤니티 켜기·끄기, 소속 표시 최소 인원** · 단계 `2단계` · 권한 원장

요청 본문: [CommunitySettings](#schema-communitysettings)

응답 `200`: [CommunitySettings](#schema-communitysettings)

### 커뮤니티 신고 처리 (운영자)

<a id="op-get-ops-community-queue"></a>

#### GET `/api/v1/ops/community/queue`

**신고 검토 대기열** · 단계 `2단계` · 권한 플랫폼 운영자

임시 블라인드된 글·댓글과 신고 사유. 학원을 가리지 않고 본다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `academy_id` | 쿼리 | string (uuid) \| null |  |  |  |
| `page` | 쿼리 | integer |  | `1` | ≥ 1 |
| `size` | 쿼리 | integer |  | `20` | ≥ 1, ≤ 100 |

응답 `200`: [Page_ModerationItem_](#schema-page-moderationitem-)

<a id="op-post-ops-community-target_type-target_id-decision"></a>

#### POST `/api/v1/ops/community/{target_type}/{target_id}/decision`

**신고 처리 (복구·삭제·제재)** · 단계 `2단계` · 권한 플랫폼 운영자

제재는 익명 뒤의 실제 계정에 적용된다. 처리 기록은 감사 로그에 남는다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `target_type` | 경로 | [ModerationTarget](#schema-moderationtarget) | 예 |  |  |
| `target_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [ModerationDecision](#schema-moderationdecision)

응답 `200`: [ModerationItem](#schema-moderationitem)

### 과제

<a id="op-get-homework"></a>

#### GET `/api/v1/homework`

**과제 목록** · 단계 `2단계` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `lecture_id` | 쿼리 | string (uuid) \| null |  |  |  |
| `due_from` | 쿼리 | string (date) \| null |  |  |  |
| `due_to` | 쿼리 | string (date) \| null |  |  |  |
| `page` | 쿼리 | integer |  | `1` | ≥ 1 |
| `size` | 쿼리 | integer |  | `20` | ≥ 1, ≤ 100 |

응답 `200`: [Page_HomeworkOut_](#schema-page-homeworkout-)

<a id="op-post-homework"></a>

#### POST `/api/v1/homework`

**과제 등록** · 단계 `2단계` · 권한 원장, 실장, 교사

요청 본문: [HomeworkCreate](#schema-homeworkcreate)

응답 `201`: [HomeworkOut](#schema-homeworkout)

<a id="op-patch-homework-homework_id"></a>

#### PATCH `/api/v1/homework/{homework_id}`

**과제 수정** · 단계 `2단계` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `homework_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [HomeworkUpdate](#schema-homeworkupdate)

응답 `200`: [HomeworkOut](#schema-homeworkout)

<a id="op-get-homework-homework_id-submissions"></a>

#### GET `/api/v1/homework/{homework_id}/submissions`

**제출 현황** · 단계 `2단계` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `homework_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [SubmissionOut](#schema-submissionout)[]

<a id="op-put-homework-homework_id-submissions"></a>

#### PUT `/api/v1/homework/{homework_id}/submissions`

**제출 기록 일괄 입력** · 단계 `2단계` · 권한 원장, 실장, 교사

과제 모듈은 사실만 기록한다. 반복 미완료 판단은 규칙 엔진이 한다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `homework_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [SubmissionBatch](#schema-submissionbatch)

응답 `200`: [SubmissionOut](#schema-submissionout)[]

### 수납

<a id="op-get-invoices"></a>

#### GET `/api/v1/invoices`

**청구 목록** · 단계 `2단계` · 권한 원장, 실장

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

**청구 직접 등록** · 단계 `2단계` · 권한 원장, 실장

요청 본문: [InvoiceCreate](#schema-invoicecreate)

응답 `201`: [InvoiceOut](#schema-invoiceout)

<a id="op-get-invoices-invoice_id"></a>

#### GET `/api/v1/invoices/{invoice_id}`

**청구 상세** · 단계 `2단계` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `invoice_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [InvoiceOut](#schema-invoiceout)

<a id="op-patch-invoices-invoice_id"></a>

#### PATCH `/api/v1/invoices/{invoice_id}`

**청구 수정·취소** · 단계 `2단계` · 권한 원장, 실장

금액이 바뀌거나 취소되면 예약된 수납 안내를 다시 검사한다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `invoice_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [InvoiceUpdate](#schema-invoiceupdate)

응답 `200`: [InvoiceOut](#schema-invoiceout)

<a id="op-post-invoices-invoice_id-holds"></a>

#### POST `/api/v1/invoices/{invoice_id}/holds`

**자동 안내 보류 걸기** · 단계 `3단계` · 권한 원장, 실장

보류가 하나라도 있으면 이 청구의 자동 안내는 만들어지지 않고 예약 건도 취소된다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `invoice_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [HoldCreate](#schema-holdcreate)

응답 `200`: [InvoiceOut](#schema-invoiceout)

<a id="op-delete-invoices-invoice_id-holds-reason"></a>

#### DELETE `/api/v1/invoices/{invoice_id}/holds/{reason}`

**보류 해제** · 단계 `3단계` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `invoice_id` | 경로 | string (uuid) | 예 |  |  |
| `reason` | 경로 | [HoldReason](#schema-holdreason) | 예 |  |  |

응답 `200`: [InvoiceOut](#schema-invoiceout)

<a id="op-get-invoices-invoice_id-promises"></a>

#### GET `/api/v1/invoices/{invoice_id}/promises`

**납부 약속 목록** · 단계 `3단계` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `invoice_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [PromiseOut](#schema-promiseout)[]

<a id="op-post-invoices-invoice_id-promises"></a>

#### POST `/api/v1/invoices/{invoice_id}/promises`

**납부 약속 등록** · 단계 `3단계` · 권한 원장, 실장

약속일까지 수납 안내를 보류하고, 약속일 다음 날 납부 확인 후보를 만든다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `invoice_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [PromiseCreate](#schema-promisecreate)

응답 `201`: [PromiseOut](#schema-promiseout)

<a id="op-delete-invoices-invoice_id-promises-promise_id"></a>

#### DELETE `/api/v1/invoices/{invoice_id}/promises/{promise_id}`

**납부 약속 취소** · 단계 `3단계` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `invoice_id` | 경로 | string (uuid) | 예 |  |  |
| `promise_id` | 경로 | string (uuid) | 예 |  |  |

응답 `204`: (본문 없음)

<a id="op-get-payments"></a>

#### GET `/api/v1/payments`

**납부 기록** · 단계 `2단계` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `student_id` | 쿼리 | string (uuid) \| null |  |  |  |
| `household_id` | 쿼리 | string (uuid) \| null |  |  |  |
| `page` | 쿼리 | integer |  | `1` | ≥ 1 |
| `size` | 쿼리 | integer |  | `20` | ≥ 1, ≤ 100 |

응답 `200`: [Page_PaymentOut_](#schema-page-paymentout-)

<a id="op-post-payments"></a>

#### POST `/api/v1/payments`

**납부 등록** · 단계 `2단계` · 권한 원장, 실장

여러 청구(형제 포함)에 나눠 반영할 수 있다. 완납된 청구의 예약 안내는 취소된다.

요청 본문: [PaymentCreate](#schema-paymentcreate)

응답 `201`: [PaymentOut](#schema-paymentout)

<a id="op-post-payments-payment_id-void"></a>

#### POST `/api/v1/payments/{payment_id}/void`

**납부 취소** · 단계 `2단계` · 권한 원장, 실장

삭제하지 않고 취소 표시만 한다. 잔액이 다시 생기면 규칙 엔진이 다음 실행에서 판단한다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `payment_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [VoidBody](#schema-voidbody)

응답 `200`: [PaymentOut](#schema-paymentout)

<a id="op-get-deposit-matches"></a>

#### GET `/api/v1/deposit-matches`

**입금자명 매칭 후보** · 단계 `3단계` · 권한 원장, 실장

통장 입금 내역 업로드 후 생긴다. 가구 단위로 찾아 형 이름으로 낸 동생 학원비도 잡는다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `status` | 쿼리 | [DepositMatchStatus](#schema-depositmatchstatus) |  | `"pending"` |  |
| `page` | 쿼리 | integer |  | `1` | ≥ 1 |
| `size` | 쿼리 | integer |  | `20` | ≥ 1, ≤ 100 |

응답 `200`: [Page_DepositMatchOut_](#schema-page-depositmatchout-)

<a id="op-post-deposit-matches-match_id-confirm"></a>

#### POST `/api/v1/deposit-matches/{match_id}/confirm`

**매칭 확정 → 납부 등록** · 단계 `3단계` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `match_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [DepositMatchConfirm](#schema-depositmatchconfirm)

응답 `200`: [PaymentOut](#schema-paymentout)

<a id="op-post-deposit-matches-match_id-reject"></a>

#### POST `/api/v1/deposit-matches/{match_id}/reject`

**매칭 거절** · 단계 `3단계` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `match_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [DepositMatchReject](#schema-depositmatchreject)

응답 `204`: (본문 없음)

<a id="op-get-billing-sibling-discount"></a>

#### GET `/api/v1/billing/sibling-discount`

**형제 할인 규칙 조회** · 단계 `3단계` · 권한 원장, 실장, 교사

응답 `200`: [SiblingDiscountSettings](#schema-siblingdiscountsettings)

<a id="op-put-billing-sibling-discount"></a>

#### PUT `/api/v1/billing/sibling-discount`

**형제 할인 규칙 저장** · 단계 `3단계` · 권한 원장

청구 생성 때 할인 줄로 기록한다. 바꾼 뒤 이미 만든 청구는 바뀌지 않는다.

요청 본문: [SiblingDiscountSettings](#schema-siblingdiscountsettings)

응답 `200`: [SiblingDiscountSettings](#schema-siblingdiscountsettings)

### 규칙 엔진

<a id="op-get-rules-settings"></a>

#### GET `/api/v1/rules/settings`

**안내 규칙 설정 조회** · 단계 `3단계` · 권한 원장, 실장

응답 `200`: [RuleSettings](#schema-rulesettings)

<a id="op-put-rules-settings"></a>

#### PUT `/api/v1/rules/settings`

**안내 규칙 설정 저장** · 단계 `3단계` · 권한 원장

기준값은 코드 상수가 아니라 학원별 설정이다. 변경 내역은 감사 로그에 남는다.

요청 본문: [RuleSettings](#schema-rulesettings)

응답 `200`: [RuleSettings](#schema-rulesettings)

<a id="op-get-rules-runs"></a>

#### GET `/api/v1/rules/runs`

**실행 기록** · 단계 `3단계` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `page` | 쿼리 | integer |  | `1` | ≥ 1 |
| `size` | 쿼리 | integer |  | `20` | ≥ 1, ≤ 100 |

응답 `200`: [Page_RuleRunOut_](#schema-page-rulerunout-)

<a id="op-post-rules-runs"></a>

#### POST `/api/v1/rules/runs`

**규칙 엔진 수동 실행** · 단계 `3단계` · 권한 원장, 실장

평소에는 Celery beat가 매일 정해진 시각에 실행한다. dry_run으로 결과를 미리 볼 수 있다.

요청 본문: [RuleRunCreate](#schema-ruleruncreate)

응답 `202`: [RuleRunOut](#schema-rulerunout)

<a id="op-get-rules-runs-run_id"></a>

#### GET `/api/v1/rules/runs/{run_id}`

**실행 결과** · 단계 `3단계` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `run_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [RuleRunOut](#schema-rulerunout)

### 승인함

<a id="op-get-approvals"></a>

#### GET `/api/v1/approvals`

**승인함 목록** · 단계 `3단계` · 권한 원장, 실장, 교사

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

**여러 건 한 번에 승인** · 단계 `3단계` · 권한 원장, 실장, 교사

문구 수정 없이 승인한다. 건별로 성공·실패를 돌려준다.

요청 본문: [IdsBody](#schema-idsbody)

응답 `200`: [BulkResult](#schema-bulkresult)

<a id="op-get-approvals-approval_id"></a>

#### GET `/api/v1/approvals/{approval_id}`

**승인 상세** · 단계 `3단계` · 권한 원장, 실장, 교사

수신자, 사실, 근거, 문구를 나란히 보여준다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `approval_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [ApprovalDetail](#schema-approvaldetail)

<a id="op-post-approvals-approval_id-approve"></a>

#### POST `/api/v1/approvals/{approval_id}/approve`

**승인 (수정 후 승인 포함)** · 단계 `3단계` · 권한 원장, 실장, 교사

승인 시점의 사실을 스냅샷으로 저장한다. 발송 직전에 DB를 다시 확인해 스냅샷과 다르면(예: 그 사이 납부) 발송을 취소한다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `approval_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [ApproveBody](#schema-approvebody)

응답 `200`: [ApprovalDetail](#schema-approvaldetail)

<a id="op-post-approvals-approval_id-hold"></a>

#### POST `/api/v1/approvals/{approval_id}/hold`

**보류** · 단계 `3단계` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `approval_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [HoldBody](#schema-holdbody)

응답 `200`: [ApprovalDetail](#schema-approvaldetail)

<a id="op-post-approvals-approval_id-reject"></a>

#### POST `/api/v1/approvals/{approval_id}/reject`

**반려** · 단계 `3단계` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `approval_id` | 경로 | string (uuid) | 예 |  |  |

요청 본문: [RejectBody](#schema-rejectbody)

응답 `200`: [ApprovalDetail](#schema-approvaldetail)

### 수납 안내 PDF

<a id="op-post-documents-billing-notices"></a>

#### POST `/api/v1/documents/billing-notices`

**수납 안내 PDF 생성** · 단계 `3단계` · 권한 원장, 실장

수납 3단계 승인이 끝난 건만 가능하다. 생성 시점 DB 값이 아니라 승인 스냅샷 값으로 만든다.

요청 본문: [BillingNoticeCreate](#schema-billingnoticecreate)

응답 `202`: [DocumentOut](#schema-documentout)

<a id="op-get-documents-document_id"></a>

#### GET `/api/v1/documents/{document_id}`

**PDF 상태** · 단계 `3단계` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `document_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [DocumentOut](#schema-documentout)

<a id="op-post-documents-document_id-links"></a>

#### POST `/api/v1/documents/{document_id}/links`

**만료되는 열람 링크 발급** · 단계 `3단계` · 권한 원장, 실장

비공개 저장소의 서명 URL. 발급 기록이 감사 로그에 남는다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `document_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [DocumentLink](#schema-documentlink)

### AI 보조

<a id="op-post-ai-replies-reply_id-classify"></a>

#### POST `/api/v1/ai/replies/{reply_id}/classify`

**회신 분류·후속 업무 제안** · 단계 `3단계` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `reply_id` | 경로 | string (uuid) | 예 |  |  |

응답 `202`: [AiRunOut](#schema-airunout)

<a id="op-post-ai-candidates-candidate_id-draft"></a>

#### POST `/api/v1/ai/candidates/{candidate_id}/draft`

**안내문 초안** · 단계 `3단계` · 권한 원장, 실장

자리 표시가 남은 문구를 만든다. 숫자·날짜는 코드가 채운다. 결과는 승인함으로 간다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `candidate_id` | 경로 | string (uuid) | 예 |  |  |

응답 `202`: [AiRunOut](#schema-airunout)

<a id="op-post-ai-students-student_id-summary"></a>

#### POST `/api/v1/ai/students/{student_id}/summary`

**상담 전 연락 이력 요약** · 단계 `3단계` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `student_id` | 경로 | string (uuid) | 예 |  |  |

응답 `202`: [AiRunOut](#schema-airunout)

<a id="op-post-ai-mismatch-scans"></a>

#### POST `/api/v1/ai/mismatch-scans`

**수납·출결 불일치 후보 찾기** · 단계 `3단계` · 권한 원장, 실장

찾은 후보는 확인 필요함(ai_mismatch)에 올라간다.

요청 본문: [MismatchScanBody](#schema-mismatchscanbody)

응답 `202`: [AiRunOut](#schema-airunout)

<a id="op-get-ai-runs"></a>

#### GET `/api/v1/ai/runs`

**AI 실행 기록** · 단계 `3단계` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `task` | 쿼리 | [AiTask](#schema-aitask) \| null |  |  |  |
| `page` | 쿼리 | integer |  | `1` | ≥ 1 |
| `size` | 쿼리 | integer |  | `20` | ≥ 1, ≤ 100 |

응답 `200`: [Page_AiRunOut_](#schema-page-airunout-)

<a id="op-get-ai-runs-run_id"></a>

#### GET `/api/v1/ai/runs/{run_id}`

**AI 실행 결과** · 단계 `3단계` · 권한 원장, 실장, 교사

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `run_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [AiRunOut](#schema-airunout)

<a id="op-get-ai-runs-run_id-steps"></a>

#### GET `/api/v1/ai/runs/{run_id}/steps`

**AI 실행 단계별 기록** · 단계 `3단계` · 권한 원장, 실장

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `run_id` | 경로 | string (uuid) | 예 |  |  |

응답 `200`: [AiStepOut](#schema-aistepout)[]

<a id="op-post-ai-runs-run_id-feedback"></a>

#### POST `/api/v1/ai/runs/{run_id}/feedback`

**AI 결과 채택·수정 기록** · 단계 `3단계` · 권한 원장, 실장, 교사

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

**학부모 회신 수신** · 단계 `3단계` · 권한 공개 (서명 검증)

회신을 저장하고 원래 발송 건과 연결한다. 외국어면 번역을, AI가 켜져 있으면 분류를 요청한다.

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `provider` | 경로 | string | 예 |  |  |

요청 본문: object

응답 `204`: (본문 없음)

### 공개 링크

<a id="op-get-public-replies-token"></a>

#### GET `/api/v1/public/replies/{token}`

**원클릭 응답 화면 정보** · 단계 `3단계` · 권한 공개 (일회용 토큰)

| 파라미터 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| `token` | 경로 | string | 예 |  | 길이 ≥ 16, 길이 ≤ 128 |

응답 `200`: [PublicReplyPage](#schema-publicreplypage)

<a id="op-post-public-replies-token"></a>

#### POST `/api/v1/public/replies/{token}`

**원클릭 응답 제출** · 단계 `3단계` · 권한 공개 (일회용 토큰)

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

<a id="schema-academyregister"></a>

#### AcademyRegister

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `academy_name`* | string |  |  |
| `academy_phone` | string \| null |  |  |
| `owner_name`* | string |  |  |
| `email`* | string |  |  |
| `password`* | string |  | 길이 ≥ 8 |

<a id="schema-academyupdate"></a>

#### AcademyUpdate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `name` | string \| null |  |  |
| `timezone` | string \| null |  |  |
| `phone` | string \| null |  |  |

<a id="schema-accountstatus"></a>

#### AccountStatus

값: `active`, `pending_guardian_consent`

<a id="schema-addchildbody"></a>

#### AddChildBody

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `code`* | string |  | 둘째 자녀의 학부모 초대 코드 길이 ≥ 6, 길이 ≤ 32 |

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

<a id="schema-attachmentout"></a>

#### AttachmentOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `filename`* | string |  |  |
| `size`* | integer |  |  |
| `content_type`* | string |  |  |

<a id="schema-attendancealertout"></a>

#### AttendanceAlertOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `kind`* | [AlertKind](#schema-alertkind) |  |  |
| `session_id`* | string (uuid) |  |  |
| `lecture_name`* | string |  |  |
| `student_ids`* | string (uuid)[] |  |  |
| `student_names`* | string[] |  |  |
| `status`* | [AlertStatus](#schema-alertstatus) |  |  |
| `parent_notified_at` | string (date-time) \| null |  | 학부모에게 앱 푸시를 보낸 시각 |
| `created_at`* | string (date-time) |  |  |
| `acknowledged_by` | string (uuid) \| null |  |  |
| `acknowledged_at` | string (date-time) \| null |  |  |
| `note` | string \| null |  |  |

<a id="schema-attendancecorrection"></a>

#### AttendanceCorrection

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `status`* | [AttendanceStatus](#schema-attendancestatus) |  |  |
| `note` | string \| null |  |  |
| `reason`* | string |  | 정정 사유 (감사 로그) |

<a id="schema-attendanceout"></a>

#### AttendanceOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `session_id`* | string (uuid) |  |  |
| `lecture_id`* | string (uuid) |  |  |
| `lecture_name`* | string |  |  |
| `student_id`* | string (uuid) |  |  |
| `student_name`* | string |  |  |
| `date`* | string (date) |  |  |
| `status`* | [AttendanceStatus](#schema-attendancestatus) |  |  |
| `method`* | [CheckInMethod](#schema-checkinmethod) |  |  |
| `checked_in_at` | string (date-time) \| null |  | QR을 찍은 시각 = 실제 도착 시각 |
| `note` | string \| null |  |  |
| `recorded_by` | string (uuid) \| null |  |  |
| `corrected` | boolean | `false` | 정정된 적이 있는지 (이력은 감사 로그) |

<a id="schema-attendancestatus"></a>

#### AttendanceStatus

값: `present`, `late`, `absent`, `excused`, `early_leave`

<a id="schema-attendancesummary"></a>

#### AttendanceSummary

기간 출결 요약. 학부모 리포트·학생 화면에서 쓴다.

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `lecture_id`* | string (uuid) |  |  |
| `lecture_name`* | string |  |  |
| `total_sessions`* | integer |  |  |
| `present`* | integer |  |  |
| `late`* | integer |  |  |
| `absent`* | integer |  |  |
| `excused`* | integer |  |  |
| `early_leave`* | integer |  |  |
| `attendance_rate`* | number |  | (출석+지각) / (전체-인정결석) ≥ 0, ≤ 1 |

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

<a id="schema-authordisplay"></a>

#### AuthorDisplay

값: `anonymous`, `nickname`

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

<a id="schema-billingsummary"></a>

#### BillingSummary

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `billing_month`* | string |  |  |
| `billed`* | integer |  |  |
| `paid`* | integer |  |  |
| `balance`* | integer |  |  |
| `household_balance` | integer \| null |  | 형제 합산 잔액 |

<a id="schema-blockbody"></a>

#### BlockBody

글이나 댓글을 기준으로 작성자를 차단한다. 차단해도 상대가 누군지는 알려주지 않는다.

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `post_id` | string (uuid) \| null |  |  |
| `comment_id` | string (uuid) \| null |  |  |

<a id="schema-blockout"></a>

#### BlockOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `label`* | string |  | 차단할 때 본 표시. 예: '익명 (자유게시판 글)' |
| `created_at`* | string (date-time) |  |  |

<a id="schema-boardkind"></a>

#### BoardKind

값: `free`, `question`, `info`, `market`, `suggestion`

<a id="schema-boardout"></a>

#### BoardOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `kind`* | [BoardKind](#schema-boardkind) |  |  |
| `name`* | string |  |  |
| `description` | string \| null |  |  |
| `visible_to_academy`* | boolean |  | 학원 관리자가 볼 수 있는지 (건의 게시판만 true) |

<a id="schema-body-upload-api-v1-imports-post"></a>

#### Body_upload_api_v1_imports_post

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `kind`* | [ImportKind](#schema-importkind) |  |  |
| `file`* | string |  | .csv, .xlsx |

<a id="schema-body-upload-attachment-api-v1-notices-attachments-post"></a>

#### Body_upload_attachment_api_v1_notices_attachments_post

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `file`* | string |  |  |

<a id="schema-body-upload-image-api-v1-community-posts-images-post"></a>

#### Body_upload_image_api_v1_community_posts_images_post

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `file`* | string |  |  |

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

<a id="schema-checkinbody"></a>

#### CheckInBody

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `token`* | string |  | 길이 ≥ 10, 길이 ≤ 200 |
| `device_id` | string \| null |  | 앱이 만든 기기 식별값 (대리 출석 감지용) 길이 ≤ 64 |

<a id="schema-checkinmethod"></a>

#### CheckInMethod

값: `qr`, `manual`, `auto_absent`

<a id="schema-checkinresult"></a>

#### CheckInResult

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `status`* | [AttendanceStatus](#schema-attendancestatus) |  |  |
| `lecture_name`* | string |  |  |
| `checked_in_at`* | string (date-time) |  |  |
| `already_checked_in` | boolean | `false` | 이미 찍었으면 첫 기록을 그대로 돌려줌 |

<a id="schema-checkinrow"></a>

#### CheckInRow

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `date`* | string (date) |  |  |
| `lecture_name`* | string |  |  |
| `status`* | [AttendanceStatus](#schema-attendancestatus) |  |  |
| `checked_in_at` | string (date-time) \| null |  | QR 찍은 시각 = 교실 도착 시각 |

<a id="schema-childaccountstatus"></a>

#### ChildAccountStatus

값: `no_account`, `pending_consent`, `active`

<a id="schema-childbrief"></a>

#### ChildBrief

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `student_id`* | string (uuid) |  |  |
| `name`* | string |  |  |
| `grade` | string \| null |  |  |
| `lecture_names` | string[] | `[]` |  |

<a id="schema-childout"></a>

#### ChildOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `student_id`* | string (uuid) |  |  |
| `name`* | string |  |  |
| `grade` | string \| null |  |  |
| `lecture_names` | string[] | `[]` |  |
| `account_status`* | [ChildAccountStatus](#schema-childaccountstatus) |  |  |
| `relation`* | string |  |  |

<a id="schema-childreport"></a>

#### ChildReport

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `student`* | [ChildOut](#schema-childout) |  |  |
| `period`* | [ReportPeriod](#schema-reportperiod) |  |  |
| `from`* | string (date) |  |  |
| `to`* | string (date) |  |  |
| `attendance_rate`* | number |  | 전체 강의 합산 출석률 ≥ 0, ≤ 1 |
| `attendance_by_lecture`* | [AttendanceSummary](#schema-attendancesummary)[] |  |  |
| `recent_check_ins`* | [CheckInRow](#schema-checkinrow)[] |  | 기간 안 회차별 출결, 최신순 |
| `upcoming_sessions`* | [LectureSessionOut](#schema-lecturesessionout)[] |  | 다음 7일 시간표 (휴강·보강 포함) |
| `notices`* | [NoticeBrief](#schema-noticebrief)[] |  |  |
| `emergency_messages`* | [EmergencyBrief](#schema-emergencybrief)[] |  |  |
| `homework` | [HomeworkSummary](#schema-homeworksummary) \| null |  | 2단계: 과제 기능을 켠 학원만 |
| `billing` | [BillingSummary](#schema-billingsummary) \| null |  | 2단계: 수납 기록을 쓰는 학원만 |

<a id="schema-columnmappingbody"></a>

#### ColumnMappingBody

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `mapping`* | map<string, string> |  | 파일 열 이름 → 필드 이름 |

<a id="schema-commentcreate"></a>

#### CommentCreate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `body`* | string |  | 길이 ≥ 1, 길이 ≤ 1000 |
| `parent_id` | string (uuid) \| null |  | 대댓글 |
| `author_display` | [AuthorDisplay](#schema-authordisplay) | `"anonymous"` |  |

<a id="schema-commentout"></a>

#### CommentOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `post_id`* | string (uuid) |  |  |
| `parent_id` | string (uuid) \| null |  |  |
| `author_label`* | string |  | 글쓴이 / 익명1 / 닉네임 |
| `body`* | string |  |  |
| `status`* | [ContentStatus](#schema-contentstatus) |  |  |
| `is_mine` | boolean | `false` |  |
| `created_at`* | string (date-time) |  |  |

<a id="schema-communityprofile"></a>

#### CommunityProfile

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `nickname` | string \| null |  |  |
| `agreed_rules_at` | string (date-time) \| null |  | 이용 규칙 동의 전에는 글쓰기 불가 |
| `muted_until` | string (date-time) \| null |  | 제재 중이면 글쓰기 정지 종료 시각 |

<a id="schema-communitysettings"></a>

#### CommunitySettings

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `enabled` | boolean | `true` |  |
| `min_group_size` | integer | `5` | 소속 표시를 붙이는 최소 인원 ≥ 3, ≤ 20 |
| `market_enabled` | boolean | `true` |  |

<a id="schema-communitystats"></a>

#### CommunityStats

학원이 볼 수 있는 숫자. 글 내용과 작성자는 포함하지 않는다.

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `joined_parents`* | integer |  |  |
| `active_parents_7d`* | integer |  |  |
| `posts_7d`* | integer |  |  |
| `reports_7d`* | integer |  |  |
| `blinded_now`* | integer |  |  |

<a id="schema-contentstatus"></a>

#### ContentStatus

값: `active`, `blinded`, `removed`, `deleted`

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

<a id="schema-emergencybrief"></a>

#### EmergencyBrief

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `reason`* | [EmergencyReason](#schema-emergencyreason) |  |  |
| `body`* | string |  |  |
| `sent_at`* | string (date-time) |  |  |

<a id="schema-emergencymessagedetail"></a>

#### EmergencyMessageDetail

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `reason`* | [EmergencyReason](#schema-emergencyreason) |  |  |
| `body`* | string |  |  |
| `target`* | [EmergencyTarget](#schema-emergencytarget) |  |  |
| `target_label`* | string |  | 예: 중2 수학 A 학부모 18명 |
| `sent_by`* | string (uuid) |  |  |
| `sent_by_name`* | string |  |  |
| `recipient_count`* | integer |  |  |
| `delivered_count` | integer | `0` |  |
| `failed_count` | integer | `0` |  |
| `status`* | [EmergencyStatus](#schema-emergencystatus) |  |  |
| `created_at`* | string (date-time) |  |  |
| `recipients`* | [EmergencyRecipient](#schema-emergencyrecipient)[] |  |  |

<a id="schema-emergencymessageout"></a>

#### EmergencyMessageOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `reason`* | [EmergencyReason](#schema-emergencyreason) |  |  |
| `body`* | string |  |  |
| `target`* | [EmergencyTarget](#schema-emergencytarget) |  |  |
| `target_label`* | string |  | 예: 중2 수학 A 학부모 18명 |
| `sent_by`* | string (uuid) |  |  |
| `sent_by_name`* | string |  |  |
| `recipient_count`* | integer |  |  |
| `delivered_count` | integer | `0` |  |
| `failed_count` | integer | `0` |  |
| `status`* | [EmergencyStatus](#schema-emergencystatus) |  |  |
| `created_at`* | string (date-time) |  |  |

<a id="schema-emergencypreview"></a>

#### EmergencyPreview

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `recipient_count`* | integer |  | 받을 학부모 수 (형제는 한 번만) |
| `sms_count`* | integer |  | 문자로 나갈 수 (앱 푸시만 받는 사람 제외 안 함: 긴급은 둘 다) |
| `guardians_without_phone`* | integer |  |  |
| `languages`* | map<string, integer> |  | 수신 언어별 인원. ko 외에는 번역문을 같이 보냄 |
| `segments`* | integer |  | 문자 길이로 나뉘는 건수 (LMS 여부 판단) |
| `sent_today`* | integer |  |  |
| `daily_limit`* | integer |  |  |
| `preview_token`* | string |  | 발송 요청에 그대로 넣는다. 미리 보기 없이 발송하지 못하게 |

<a id="schema-emergencypreviewbody"></a>

#### EmergencyPreviewBody

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `reason`* | [EmergencyReason](#schema-emergencyreason) |  |  |
| `body`* | string |  | 길이 ≤ 1000 |
| `target`* | [EmergencyTarget](#schema-emergencytarget) |  |  |

<a id="schema-emergencyreason"></a>

#### EmergencyReason

값: `safety`, `health`, `closure`, `other`

<a id="schema-emergencyrecipient"></a>

#### EmergencyRecipient

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `guardian_name`* | string |  |  |
| `student_names`* | string[] |  |  |
| `phone_masked`* | string |  |  |
| `language`* | string |  |  |
| `sms_status` | [MessageStatus](#schema-messagestatus) \| null |  |  |
| `push_sent`* | boolean |  |  |

<a id="schema-emergencysendbody"></a>

#### EmergencySendBody

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `reason`* | [EmergencyReason](#schema-emergencyreason) |  |  |
| `body`* | string |  | 길이 ≤ 1000 |
| `target`* | [EmergencyTarget](#schema-emergencytarget) |  |  |
| `preview_token`* | string |  |  |

<a id="schema-emergencystatus"></a>

#### EmergencyStatus

값: `sending`, `sent`, `partially_failed`

<a id="schema-emergencytarget"></a>

#### EmergencyTarget

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `type`* | [EmergencyTargetType](#schema-emergencytargettype) |  |  |
| `student_ids` | string (uuid)[] | `[]` |  |
| `lecture_id` | string (uuid) \| null |  |  |

<a id="schema-emergencytargettype"></a>

#### EmergencyTargetType

값: `students`, `lecture`, `academy`

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
| `code` | string \| null |  | 프론트 분기용 오류 코드. 예: expired_qr, not_enrolled |

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

<a id="schema-generatesessionsbody"></a>

#### GenerateSessionsBody

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `from`* | string (date) |  |  |
| `to`* | string (date) |  |  |

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
| `lecture_id`* | string (uuid) |  |  |
| `title`* | string |  |  |
| `due_date`* | string (date) |  |  |

<a id="schema-homeworkout"></a>

#### HomeworkOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `lecture_id`* | string (uuid) |  |  |
| `title`* | string |  |  |
| `due_date`* | string (date) |  |  |
| `created_by`* | string (uuid) |  |  |
| `created_at`* | string (date-time) |  |  |
| `missing_count` | integer | `0` |  |

<a id="schema-homeworksummary"></a>

#### HomeworkSummary

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `total`* | integer |  |  |
| `submitted`* | integer |  |  |
| `missing`* | [MissingHomework](#schema-missinghomework)[] |  |  |

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

<a id="schema-invitationbulkcreate"></a>

#### InvitationBulkCreate

학생 명부 업로드 뒤 한 번에 발급. 학생 코드와 기본 보호자 코드를 같이 만든다.

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `student_ids`* | string (uuid)[] |  | 개수 ≥ 1, 개수 ≤ 500 |
| `include_parents` | boolean | `true` |  |
| `expires_in_days` | integer | `14` | ≥ 1, ≤ 90 |

<a id="schema-invitationcreate"></a>

#### InvitationCreate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `role`* | [Role](#schema-role) |  | teacher, manager, student, parent |
| `student_id` | string (uuid) \| null |  | role=student, parent일 때 대상 학생 |
| `guardian_id` | string (uuid) \| null |  | role=parent: 학생의 어느 보호자인지 |
| `email` | string \| null |  | role=teacher·manager: 초대 메일 받을 주소 |
| `expires_in_days` | integer | `14` | ≥ 1, ≤ 90 |

<a id="schema-invitationout"></a>

#### InvitationOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `role`* | [Role](#schema-role) |  |  |
| `code` | string \| null |  | 발급 직후 응답에만 원문이 있다. 이후에는 null |
| `code_hint`* | string |  | 끝 2자리. 목록에서 구분용 |
| `student_id` | string (uuid) \| null |  |  |
| `student_name` | string \| null |  |  |
| `guardian_id` | string (uuid) \| null |  |  |
| `status`* | [InvitationStatus](#schema-invitationstatus) |  |  |
| `expires_at`* | string (date-time) |  |  |
| `used_by` | string (uuid) \| null |  |  |
| `used_at` | string (date-time) \| null |  |  |
| `created_at`* | string (date-time) |  |  |

<a id="schema-invitationpreview"></a>

#### InvitationPreview

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `academy_name`* | string |  |  |
| `role`* | [Role](#schema-role) |  |  |
| `student_name_masked` | string \| null |  | 김*준. 학부모·학생 코드일 때 |
| `expires_at`* | string |  |  |

<a id="schema-invitationstatus"></a>

#### InvitationStatus

값: `active`, `used`, `revoked`, `expired`

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

<a id="schema-lecturecreate"></a>

#### LectureCreate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `name`* | string |  |  |
| `subject` | string \| null |  |  |
| `grade` | string \| null |  |  |
| `room` | string \| null |  |  |
| `branch_id` | string (uuid) \| null |  |  |
| `teacher_id` | string (uuid) \| null |  |  |
| `schedule` | [LectureSlot](#schema-lectureslot)[] | `[]` |  |
| `starts_on` | string (date) \| null |  |  |
| `ends_on` | string (date) \| null |  |  |

<a id="schema-lectureout"></a>

#### LectureOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `name`* | string |  |  |
| `subject` | string \| null |  |  |
| `grade` | string \| null |  |  |
| `room` | string \| null |  |  |
| `branch_id` | string (uuid) \| null |  |  |
| `teacher_id` | string (uuid) \| null |  |  |
| `teacher_name` | string \| null |  |  |
| `schedule` | [LectureSlot](#schema-lectureslot)[] | `[]` |  |
| `starts_on` | string (date) \| null |  |  |
| `ends_on` | string (date) \| null |  |  |
| `student_count` | integer | `0` |  |
| `archived` | boolean | `false` |  |

<a id="schema-lecturesessionout"></a>

#### LectureSessionOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `lecture_id`* | string (uuid) |  |  |
| `lecture_name`* | string |  |  |
| `teacher_id` | string (uuid) \| null |  |  |
| `date`* | string (date) |  |  |
| `starts_at`* | string (date-time) |  |  |
| `ends_at`* | string (date-time) |  |  |
| `kind`* | [SessionKind](#schema-sessionkind) |  |  |
| `status`* | [SessionStatus](#schema-sessionstatus) |  |  |
| `attendance_opened_at` | string (date-time) \| null |  |  |
| `attendance_closed_at` | string (date-time) \| null |  |  |
| `present_count` | integer | `0` |  |
| `late_count` | integer | `0` |  |
| `absent_count` | integer | `0` |  |
| `enrolled_count` | integer | `0` |  |
| `cancel_reason` | string \| null |  |  |

<a id="schema-lectureslot"></a>

#### LectureSlot

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `weekday`* | integer |  | 0=월요일 ≥ 0, ≤ 6 |
| `start`* | string (time) |  |  |
| `end`* | string (time) |  |  |

<a id="schema-lectureupdate"></a>

#### LectureUpdate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `name` | string \| null |  |  |
| `subject` | string \| null |  |  |
| `grade` | string \| null |  |  |
| `room` | string \| null |  |  |
| `teacher_id` | string (uuid) \| null |  |  |
| `schedule` | [LectureSlot](#schema-lectureslot)[] \| null |  | 바꾸면 앞으로의 예정 회차만 다시 만든다. 지난 회차는 그대로 |
| `ends_on` | string (date) \| null |  |  |
| `archived` | boolean \| null |  |  |

<a id="schema-loginbody"></a>

#### LoginBody

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `email`* | string |  |  |
| `password`* | string |  |  |

<a id="schema-manualmark"></a>

#### ManualMark

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `status`* | [AttendanceStatus](#schema-attendancestatus) |  |  |
| `note` | string \| null |  | 예: 휴대전화 없음, 병원 진료 사전 연락 |

<a id="schema-marketinfo"></a>

#### MarketInfo

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `type`* | [MarketType](#schema-markettype) |  |  |
| `price` | integer \| null |  | 원. 나눔이면 null ≥ 0 |
| `status` | [MarketStatus](#schema-marketstatus) | `"available"` |  |

<a id="schema-marketstatus"></a>

#### MarketStatus

값: `available`, `reserved`, `done`

<a id="schema-markettype"></a>

#### MarketType

값: `share`, `sell`

<a id="schema-maskresult"></a>

#### MaskResult

글 저장 전 검사 결과. 전화번호·실명 패턴은 가려서 저장하고 작성자에게 알려준다.

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `masked`* | boolean |  |  |
| `warnings` | string[] | `[]` | 예: 전화번호가 가려졌습니다, 교사 이름이 포함돼 있습니다 |

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
| `status` | [AccountStatus](#schema-accountstatus) | `"active"` |  |
| `student_id` | string (uuid) \| null |  |  |
| `guardian_id` | string (uuid) \| null |  |  |
| `academy_name`* | string |  |  |
| `preferred_language` | string | `"ko"` |  |
| `children` | [ChildBrief](#schema-childbrief)[] | `[]` | role=parent: 연결된 자녀 (형제 포함) |
| `home`* | string |  | 역할별 첫 화면 경로. 예: /admin, /teacher, /student, /parent |

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

<a id="schema-missinghomework"></a>

#### MissingHomework

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `title`* | string |  |  |
| `lecture_name`* | string |  |  |
| `due_date`* | string (date) |  |  |

<a id="schema-moderationdecision"></a>

#### ModerationDecision

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `action`* | string |  | restore=블라인드 해제, remove=삭제 `형식 ^(restore\|remove)$` |
| `sanction` | [Sanction](#schema-sanction) | `"none"` |  |
| `note`* | string |  | 처리 사유 (기록용) |

<a id="schema-moderationitem"></a>

#### ModerationItem

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `target_type`* | [ModerationTarget](#schema-moderationtarget) |  |  |
| `target_id`* | string (uuid) |  |  |
| `academy_id`* | string (uuid) |  |  |
| `academy_name`* | string |  |  |
| `content`* | string |  |  |
| `status`* | [ContentStatus](#schema-contentstatus) |  |  |
| `report_count`* | integer |  |  |
| `reasons`* | map<string, integer> |  |  |
| `author_prior_sanctions`* | integer |  | 익명 뒤 실제 계정의 이전 제재 횟수 |
| `first_reported_at`* | string (date-time) |  |  |

<a id="schema-moderationtarget"></a>

#### ModerationTarget

값: `post`, `comment`

<a id="schema-myschedule"></a>

#### MySchedule

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `lectures`* | [LectureOut](#schema-lectureout)[] |  |  |
| `upcoming_sessions`* | [LectureSessionOut](#schema-lecturesessionout)[] |  | 오늘부터 7일. 휴강·보강 포함 |

<a id="schema-notecreate"></a>

#### NoteCreate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `body`* | string |  | 상담·통화 메모 길이 ≥ 1, 길이 ≤ 2000 |

<a id="schema-noticeaudience"></a>

#### NoticeAudience

값: `students`, `parents`, `all`

<a id="schema-noticebrief"></a>

#### NoticeBrief

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `title`* | string |  |  |
| `lecture_name` | string \| null |  |  |
| `published_at`* | string (date-time) |  |  |
| `read`* | boolean |  |  |

<a id="schema-noticecreate"></a>

#### NoticeCreate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `title`* | string |  | 길이 ≤ 200 |
| `body`* | string |  | 길이 ≤ 10000 |
| `lecture_id` | string (uuid) \| null |  | 교사는 자기 강의만 가능 |
| `audience` | [NoticeAudience](#schema-noticeaudience) | `"all"` |  |
| `pinned` | boolean | `false` |  |
| `attachment_ids` | string (uuid)[] | `[]` |  |
| `notify` | boolean | `true` | 앱 푸시 보내기 |

<a id="schema-noticekind"></a>

#### NoticeKind

값: `billing_reminder`, `absence`, `repeated_absence`, `homework`, `payment_check`, `correction`, `general`

<a id="schema-noticeout"></a>

#### NoticeOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `title`* | string |  |  |
| `body`* | string |  |  |
| `lecture_id` | string (uuid) \| null |  | null = 학원 전체 공지 |
| `lecture_name` | string \| null |  |  |
| `audience`* | [NoticeAudience](#schema-noticeaudience) |  |  |
| `pinned` | boolean | `false` |  |
| `attachments` | [AttachmentOut](#schema-attachmentout)[] | `[]` |  |
| `author_id`* | string (uuid) |  |  |
| `author_name`* | string |  |  |
| `published_at`* | string (date-time) |  |  |
| `updated_at` | string (date-time) \| null |  |  |
| `read` | boolean | `false` | 요청한 사용자가 읽었는지 |
| `read_count` | integer \| null |  | 직원에게만: 읽은 사람 수 |
| `target_count` | integer \| null |  | 직원에게만: 받을 사람 수 |

<a id="schema-noticereads"></a>

#### NoticeReads

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `read`* | [ReaderOut](#schema-readerout)[] |  |  |
| `unread`* | [ReaderOut](#schema-readerout)[] |  |  |

<a id="schema-noticeupdate"></a>

#### NoticeUpdate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `title` | string \| null |  | 길이 ≤ 200 |
| `body` | string \| null |  | 길이 ≤ 10000 |
| `pinned` | boolean \| null |  |  |
| `attachment_ids` | string (uuid)[] \| null |  |  |

<a id="schema-notificationkind"></a>

#### NotificationKind

값: `check_in`, `absence`, `attendance_corrected`, `session_cancelled`, `notice`, `question`, `emergency`, `community`

<a id="schema-notificationout"></a>

#### NotificationOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `kind`* | [NotificationKind](#schema-notificationkind) |  |  |
| `title`* | string |  |  |
| `body`* | string |  |  |
| `link`* | string |  | 앱 안 이동 경로. 예: /parent/children/{id}/attendance |
| `created_at`* | string (date-time) |  |  |
| `read_at` | string (date-time) \| null |  |  |

<a id="schema-notificationpreferences"></a>

#### NotificationPreferences

종류별 앱 푸시 켜기/끄기. 긴급은 끌 수 없다.

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `check_in` | boolean | `true` |  |
| `absence` | boolean | `true` |  |
| `notice` | boolean | `true` |  |
| `question` | boolean | `true` |  |
| `community` | boolean | `true` |  |
| `quiet_start` | string \| null |  | `형식 ^\d{2}:\d{2}$` |
| `quiet_end` | string \| null |  | `형식 ^\d{2}:\d{2}$` |

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

<a id="schema-page-emergencymessageout-"></a>

#### Page_EmergencyMessageOut_

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `items`* | [EmergencyMessageOut](#schema-emergencymessageout)[] |  |  |
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

<a id="schema-page-invitationout-"></a>

#### Page_InvitationOut_

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `items`* | [InvitationOut](#schema-invitationout)[] |  |  |
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

<a id="schema-page-lecturesessionout-"></a>

#### Page_LectureSessionOut_

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `items`* | [LectureSessionOut](#schema-lecturesessionout)[] |  |  |
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

<a id="schema-page-moderationitem-"></a>

#### Page_ModerationItem_

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `items`* | [ModerationItem](#schema-moderationitem)[] |  |  |
| `total`* | integer |  |  |
| `page`* | integer |  |  |
| `size`* | integer |  |  |

<a id="schema-page-noticeout-"></a>

#### Page_NoticeOut_

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `items`* | [NoticeOut](#schema-noticeout)[] |  |  |
| `total`* | integer |  |  |
| `page`* | integer |  |  |
| `size`* | integer |  |  |

<a id="schema-page-notificationout-"></a>

#### Page_NotificationOut_

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `items`* | [NotificationOut](#schema-notificationout)[] |  |  |
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

<a id="schema-page-postdetail-"></a>

#### Page_PostDetail_

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `items`* | [PostDetail](#schema-postdetail)[] |  |  |
| `total`* | integer |  |  |
| `page`* | integer |  |  |
| `size`* | integer |  |  |

<a id="schema-page-postout-"></a>

#### Page_PostOut_

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `items`* | [PostOut](#schema-postout)[] |  |  |
| `total`* | integer |  |  |
| `page`* | integer |  |  |
| `size`* | integer |  |  |

<a id="schema-page-questionout-"></a>

#### Page_QuestionOut_

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `items`* | [QuestionOut](#schema-questionout)[] |  |  |
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

<a id="schema-postcreate"></a>

#### PostCreate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `board_id`* | string (uuid) |  |  |
| `title`* | string |  | 길이 ≥ 2, 길이 ≤ 100 |
| `body`* | string |  | 길이 ≥ 2, 길이 ≤ 5000 |
| `author_display` | [AuthorDisplay](#schema-authordisplay) | `"anonymous"` |  |
| `show_group_label` | boolean | `true` | 익명일 때 '중2 학부모' 표시를 붙일지 |
| `scope` | [PostScope](#schema-postscope) | `"academy"` |  |
| `scope_grade` | string \| null |  | scope=grade: 내 자녀 학년 중 하나 |
| `scope_lecture_id` | string (uuid) \| null |  | scope=lecture: 내 자녀 강의 중 하나 |
| `market` | [MarketInfo](#schema-marketinfo) \| null |  | 나눔·거래 게시판만 |
| `image_ids` | string (uuid)[] | `[]` | 개수 ≤ 5 |

<a id="schema-postcreateresult"></a>

#### PostCreateResult

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `post`* | [PostDetail](#schema-postdetail) |  |  |
| `check`* | [MaskResult](#schema-maskresult) |  |  |

<a id="schema-postdetail"></a>

#### PostDetail

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `board_id`* | string (uuid) |  |  |
| `board_kind`* | [BoardKind](#schema-boardkind) |  |  |
| `title`* | string |  |  |
| `preview`* | string |  | 본문 앞부분 |
| `author_label`* | string |  | 익명 / 중2 학부모 / 닉네임 |
| `scope`* | [PostScope](#schema-postscope) |  |  |
| `scope_label`* | string |  | 학원 전체 / 중2 / 중2 수학 A |
| `status`* | [ContentStatus](#schema-contentstatus) |  |  |
| `market` | [MarketInfo](#schema-marketinfo) \| null |  |  |
| `like_count` | integer | `0` |  |
| `comment_count` | integer | `0` |  |
| `liked` | boolean | `false` |  |
| `bookmarked` | boolean | `false` |  |
| `is_mine` | boolean | `false` |  |
| `forwarded_to_academy` | boolean | `false` |  |
| `image_urls` | string[] | `[]` |  |
| `created_at`* | string (date-time) |  |  |
| `edited_at` | string (date-time) \| null |  |  |
| `body`* | string |  |  |

<a id="schema-postout"></a>

#### PostOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `board_id`* | string (uuid) |  |  |
| `board_kind`* | [BoardKind](#schema-boardkind) |  |  |
| `title`* | string |  |  |
| `preview`* | string |  | 본문 앞부분 |
| `author_label`* | string |  | 익명 / 중2 학부모 / 닉네임 |
| `scope`* | [PostScope](#schema-postscope) |  |  |
| `scope_label`* | string |  | 학원 전체 / 중2 / 중2 수학 A |
| `status`* | [ContentStatus](#schema-contentstatus) |  |  |
| `market` | [MarketInfo](#schema-marketinfo) \| null |  |  |
| `like_count` | integer | `0` |  |
| `comment_count` | integer | `0` |  |
| `liked` | boolean | `false` |  |
| `bookmarked` | boolean | `false` |  |
| `is_mine` | boolean | `false` |  |
| `forwarded_to_academy` | boolean | `false` |  |
| `image_urls` | string[] | `[]` |  |
| `created_at`* | string (date-time) |  |  |
| `edited_at` | string (date-time) \| null |  |  |

<a id="schema-postscope"></a>

#### PostScope

값: `academy`, `grade`, `lecture`

<a id="schema-postupdate"></a>

#### PostUpdate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `title` | string \| null |  | 길이 ≥ 2, 길이 ≤ 100 |
| `body` | string \| null |  | 길이 ≥ 2, 길이 ≤ 5000 |
| `market_status` | [MarketStatus](#schema-marketstatus) \| null |  |  |

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

<a id="schema-profileupdate"></a>

#### ProfileUpdate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `nickname`* | string |  | 길이 ≥ 2, 길이 ≤ 12 |

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

<a id="schema-pushkeys"></a>

#### PushKeys

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `p256dh`* | string |  |  |
| `auth`* | string |  |  |

<a id="schema-pushsubscriptionbody"></a>

#### PushSubscriptionBody

브라우저 Web Push 구독 (PWA). 앱 출시 후에는 FCM/APNs 토큰도 같은 자리에.

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `endpoint`* | string |  |  |
| `keys`* | [PushKeys](#schema-pushkeys) |  |  |
| `user_agent` | string \| null |  |  |

<a id="schema-qrtokenout"></a>

#### QrTokenOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `token`* | string |  |  |
| `scan_url`* | string |  | QR에 담는 주소. 휴대전화 기본 카메라로 찍어도 앱 출석 화면이 열림 |
| `expires_at`* | string (date-time) |  |  |
| `refresh_in_seconds`* | integer |  | 교사 화면은 이 시간 뒤에 새 토큰을 받는다 |

<a id="schema-questioncategory"></a>

#### QuestionCategory

값: `study`, `counsel`, `schedule`, `other`

<a id="schema-questioncreate"></a>

#### QuestionCreate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `title`* | string |  | 길이 ≤ 200 |
| `body`* | string |  | 길이 ≤ 5000 |
| `category` | [QuestionCategory](#schema-questioncategory) | `"study"` |  |
| `lecture_id` | string (uuid) \| null |  | 고르면 그 강의 교사에게 배정 |
| `student_id` | string (uuid) \| null |  | 학부모: 어느 자녀에 관한 질문인지 (필수) |
| `attachment_ids` | string (uuid)[] | `[]` |  |

<a id="schema-questiondetail"></a>

#### QuestionDetail

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `title`* | string |  |  |
| `category`* | [QuestionCategory](#schema-questioncategory) |  |  |
| `status`* | [QuestionStatus](#schema-questionstatus) |  |  |
| `visibility`* | [QuestionVisibility](#schema-questionvisibility) |  |  |
| `author_role`* | [Role](#schema-role) |  |  |
| `author_name` | string \| null |  | 공개 질문을 다른 학생이 볼 때는 null |
| `student_id`* | string (uuid) |  | 어느 학생에 관한 질문인지 (학부모는 자녀) |
| `student_name` | string \| null |  |  |
| `lecture_id` | string (uuid) \| null |  |  |
| `lecture_name` | string \| null |  |  |
| `assignee_id` | string (uuid) \| null |  | 답변할 교사. 비면 학원 관리자 |
| `assignee_name` | string \| null |  |  |
| `unread_count` | integer | `0` |  |
| `last_message_at`* | string (date-time) |  |  |
| `created_at`* | string (date-time) |  |  |
| `messages`* | [QuestionMessageOut](#schema-questionmessageout)[] |  |  |

<a id="schema-questionmessagecreate"></a>

#### QuestionMessageCreate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `body`* | string |  | 길이 ≤ 5000 |
| `attachment_ids` | string (uuid)[] | `[]` |  |

<a id="schema-questionmessageout"></a>

#### QuestionMessageOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `author_name`* | string |  |  |
| `author_role`* | [Role](#schema-role) |  |  |
| `body`* | string |  |  |
| `attachments` | [AttachmentOut](#schema-attachmentout)[] | `[]` |  |
| `is_mine`* | boolean |  |  |
| `created_at`* | string (date-time) |  |  |

<a id="schema-questionout"></a>

#### QuestionOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `title`* | string |  |  |
| `category`* | [QuestionCategory](#schema-questioncategory) |  |  |
| `status`* | [QuestionStatus](#schema-questionstatus) |  |  |
| `visibility`* | [QuestionVisibility](#schema-questionvisibility) |  |  |
| `author_role`* | [Role](#schema-role) |  |  |
| `author_name` | string \| null |  | 공개 질문을 다른 학생이 볼 때는 null |
| `student_id`* | string (uuid) |  | 어느 학생에 관한 질문인지 (학부모는 자녀) |
| `student_name` | string \| null |  |  |
| `lecture_id` | string (uuid) \| null |  |  |
| `lecture_name` | string \| null |  |  |
| `assignee_id` | string (uuid) \| null |  | 답변할 교사. 비면 학원 관리자 |
| `assignee_name` | string \| null |  |  |
| `unread_count` | integer | `0` |  |
| `last_message_at`* | string (date-time) |  |  |
| `created_at`* | string (date-time) |  |  |

<a id="schema-questionstatus"></a>

#### QuestionStatus

값: `open`, `answered`, `closed`

<a id="schema-questionupdate"></a>

#### QuestionUpdate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `status` | [QuestionStatus](#schema-questionstatus) \| null |  |  |
| `assignee_id` | string (uuid) \| null |  | 관리자만 변경 |
| `visibility` | [QuestionVisibility](#schema-questionvisibility) \| null |  | 작성 학생만 공개로 바꿀 수 있음 |

<a id="schema-questionvisibility"></a>

#### QuestionVisibility

값: `private`, `lecture_public`

<a id="schema-readbody"></a>

#### ReadBody

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `ids` | string (uuid)[] \| null |  | 비우면 전부 읽음 |

<a id="schema-readerout"></a>

#### ReaderOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `user_id`* | string (uuid) |  |  |
| `name`* | string |  |  |
| `role`* | string |  |  |
| `student_name` | string \| null |  | 학부모면 자녀 이름 |
| `read_at` | string (date-time) \| null |  |  |

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

<a id="schema-reportbody"></a>

#### ReportBody

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `reason`* | [ReportReason](#schema-reportreason) |  |  |
| `detail` | string \| null |  | 길이 ≤ 500 |

<a id="schema-reportperiod"></a>

#### ReportPeriod

값: `week`, `month`

<a id="schema-reportreason"></a>

#### ReportReason

값: `abuse`, `personal_info`, `defamation`, `ad`, `spam`, `illegal`, `other`

<a id="schema-reportresult"></a>

#### ReportResult

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `accepted` | boolean | `true` |  |
| `blinded`* | boolean |  | 이번 신고로 임시 블라인드됐는지 (신고 3건) |

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

값: `import_error`, `household_suggestion`, `shared_device_check_in`, `pending_child_consent`, `deposit_match`, `discount_recalc`, `ai_mismatch`

<a id="schema-reviewstatus"></a>

#### ReviewStatus

값: `none`, `pending`, `approved`, `rejected`

<a id="schema-role"></a>

#### Role

값: `owner`, `manager`, `teacher`, `student`, `parent`, `operator`

<a id="schema-rosteritem"></a>

#### RosterItem

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `student_id`* | string (uuid) |  |  |
| `student_name`* | string |  |  |
| `status` | [AttendanceStatus](#schema-attendancestatus) \| null |  | null = 아직 안 찍음 |
| `method` | [CheckInMethod](#schema-checkinmethod) \| null |  |  |
| `checked_in_at` | string (date-time) \| null |  |  |
| `shared_device` | boolean | `false` | 같은 기기로 다른 학생도 찍음 → 교사 확인 필요 |

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

<a id="schema-sanction"></a>

#### Sanction

값: `none`, `warn`, `mute_7d`, `mute_30d`, `ban`

<a id="schema-sessioncreate"></a>

#### SessionCreate

보강 등 시간표 밖 회차.

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `lecture_id`* | string (uuid) |  |  |
| `starts_at`* | string (date-time) |  |  |
| `ends_at`* | string (date-time) |  |  |
| `kind` | [SessionKind](#schema-sessionkind) | `"makeup"` |  |
| `student_ids` | string (uuid)[] \| null |  | 보강 대상만. 비우면 수강생 전체 |

<a id="schema-sessionkind"></a>

#### SessionKind

값: `regular`, `makeup`

<a id="schema-sessionroster"></a>

#### SessionRoster

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `session_id`* | string (uuid) |  |  |
| `lecture_name`* | string |  |  |
| `starts_at`* | string (date-time) |  |  |
| `ends_at`* | string (date-time) |  |  |
| `is_open`* | boolean |  |  |
| `present_count`* | integer |  |  |
| `late_count`* | integer |  |  |
| `absent_count`* | integer |  |  |
| `pending_count`* | integer |  | 아직 안 찍은 학생 수 |
| `items`* | [RosterItem](#schema-rosteritem)[] |  |  |

<a id="schema-sessionstatus"></a>

#### SessionStatus

값: `scheduled`, `open`, `closed`, `cancelled`

<a id="schema-sessionupdate"></a>

#### SessionUpdate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `starts_at` | string (date-time) \| null |  |  |
| `ends_at` | string (date-time) \| null |  |  |
| `status` | [SessionStatus](#schema-sessionstatus) \| null |  | cancelled로 휴강 처리 |
| `cancel_reason` | string \| null |  | 휴강 사유. 학생·학부모에게 앱 알림 |

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

<a id="schema-signupbody"></a>

#### SignupBody

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `code`* | string |  | 길이 ≥ 6, 길이 ≤ 32 |
| `name`* | string |  |  |
| `email`* | string |  |  |
| `password`* | string |  | 길이 ≥ 8 |
| `phone` | string \| null |  | 학부모: 긴급 문자 받을 번호 |
| `agree_terms`* | boolean |  |  |
| `agree_community_rules` | boolean | `false` | 학부모: 커뮤니티 이용 규칙 (2단계) |

<a id="schema-signupresult"></a>

#### SignupResult

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `access_token`* | string |  |  |
| `refresh_token`* | string |  |  |
| `token_type` | string | `"bearer"` |  |
| `expires_in`* | integer |  |  |
| `status`* | [AccountStatus](#schema-accountstatus) |  |  |

<a id="schema-studentcreate"></a>

#### StudentCreate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `external_id` | string \| null |  |  |
| `name`* | string |  |  |
| `grade` | string \| null |  |  |
| `school` | string \| null |  |  |
| `birth_date` | string (date) \| null |  |  |
| `lecture_ids` | string (uuid)[] | `[]` |  |
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
| `lecture_ids` | string (uuid)[] | `[]` |  |
| `school` | string \| null |  |  |
| `birth_date` | string (date) \| null |  | 만 14세 미만이면 학생 가입에 보호자 동의 필요 |
| `has_account` | boolean | `false` | 학생이 초대 코드로 가입했는지 |
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
| `lecture_ids` | string (uuid)[] | `[]` |  |

<a id="schema-studentupdate"></a>

#### StudentUpdate

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `external_id` | string \| null |  |  |
| `name` | string \| null |  |  |
| `grade` | string \| null |  |  |
| `school` | string \| null |  |  |
| `birth_date` | string (date) \| null |  |  |
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
| `sessions_today`* | integer |  | 오늘 강의 회차 수 (휴강 제외) |
| `sessions_open`* | integer |  | 지금 출석 받는 중 |
| `attendance_rate_today` | number \| null |  | 마감된 회차 기준 ≥ 0, ≤ 1 |
| `absent_today`* | integer |  |  |
| `open_alerts`* | integer |  | 확인 안 한 결석 알림 |
| `unanswered_questions`* | integer |  |  |
| `emergency_sent_today`* | integer |  |  |
| `review_items`* | integer |  |  |
| `community_reports_7d` | integer \| null |  | 2단계: 커뮤니티를 켠 학원만 |

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

<a id="schema-unsubscribebody"></a>

#### UnsubscribeBody

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `endpoint`* | string |  |  |

<a id="schema-userout"></a>

#### UserOut

| 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id`* | string (uuid) |  |  |
| `name`* | string |  |  |
| `email`* | string |  |  |
| `role`* | [Role](#schema-role) |  |  |
| `branch_ids` | string (uuid)[] | `[]` |  |
| `status`* | string |  | invited, active, pending_guardian_consent, disabled |
| `student_id` | string (uuid) \| null |  | role=student |
| `guardian_id` | string (uuid) \| null |  | role=parent |
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

