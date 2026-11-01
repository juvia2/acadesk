# acadesk 기능 정리 (v2)

## 회원가입 / 초대 코드 / 역할별 화면

`MVP` · 담당: 미정

<aside>
📁

- backend/src/acadesk/api/v1/auth.py
- backend/src/acadesk/modules/academies/ (invitations)
- backend/src/acadesk/core/security.py
- backend/src/acadesk/api/deps.py
</aside>

<aside>
💡 기획 요구: 학원 관리자·교사·학생·학부모 4역할, 로그인하면 역할별 다른 화면, 아무나 학부모로 가입 못 하게
</aside>

<aside>
➡️

- 학원 관리자는 학원 등록과 함께 가입, 나머지는 일회용 초대 코드로 가입 (코드는 해시만 저장)
- 명부 업로드 뒤 학생·학부모 코드 일괄 발급 → 안내문 인쇄
- 만 14세 미만 학생은 학부모가 승인할 때까지 pending_guardian_consent
- /auth/me의 home으로 첫 화면 결정 (/admin, /teacher, /student, /parent)
- 엔드포인트마다 access(단계, *역할)로 권한을 한 곳에 적음
</aside>

## 강의 / 강의 회차

`MVP` · 담당: 미정

<aside>
📁

- backend/src/acadesk/modules/lectures/
- backend/src/acadesk/workers/ (주간 회차 생성)
</aside>

<aside>
💡 기획 요구: 출결은 강의별, 시간표·휴강·보강
</aside>

<aside>
➡️

- 강의(시간표) → 강의 회차(날짜·시작·종료)를 워커가 매주 자동 생성
- 휴강은 회차 status=cancelled + 학생·학부모 앱 알림
- 보강은 회차 kind=makeup, 대상 학생만 session_students에
</aside>

## QR 강의별 출결

`MVP` · 담당: 미정

<aside>
📁

- backend/src/acadesk/modules/attendance/qr.py (구현 완료)
- backend/src/acadesk/modules/attendance/router.py
- frontend/src/app/teacher/sessions/[id]/qr/
- frontend/src/app/student/scan/
</aside>

<aside>
💡 기획 요구: 교사가 매일 다른 QR, 학생이 찍어 출석, 대리 출석 방지
</aside>

<aside>
➡️

- QR 토큰 = (회차 ID, 30초 구간) HMAC 서명. DB 저장 없음, 사진 공유해도 약 60초 뒤 무효
- 체크인: 서명·시간 → 수강생 여부 → 출석 가능 시간(시작 15분 전~종료) → (회차, 학생) 유니크로 1회
- 시작 10분 뒤부터 지각, 마감 때 미출석은 auto_absent + 학부모 푸시 + 결석 알림
- 같은 device_id로 여러 학생이 찍으면 확인 필요함에 표시
- 휴대전화 없는 학생은 교사가 수동 처리 (method=manual)
</aside>

## 학생 / 보호자 / 형제 연동

`MVP` · 담당: 미정

<aside>
📁

- backend/src/acadesk/modules/students/
</aside>

<aside>
💡 기획 요구: 학부모 계정 하나에 자녀 여럿, 리포트 자녀 전환
</aside>

<aside>
➡️

- 가구(household)로 형제 묶음, 연결은 담당자 확인 후 확정
- 학부모 계정 = 보호자 기록(guardian_id), 자녀는 student_guardians로
- 둘째 자녀는 학부모 초대 코드를 추가 입력 (POST /children)
- 연락처는 암호화 + 해시, 화면에는 마스킹
</aside>

## 명부 업로드

`MVP` · 담당: 미정

<aside>
📁

- backend/src/acadesk/modules/imports/
</aside>

<aside>
💡 기획 요구: 학원 도입 시 학생·학부모 명단 일괄 등록
</aside>

<aside>
➡️

- CSV·엑셀 → 열 매핑 → 행별 검사 → 반영 (오류 행만 확인 필요함으로)
- 반영 뒤 형제 연결 후보 생성, 초대 코드 일괄 발급으로 이어짐
</aside>

## 공지사항

`MVP` · 담당: 미정

<aside>
📁

- backend/src/acadesk/modules/notices/
</aside>

<aside>
💡 기획 요구: 학생·학부모 화면의 공지
</aside>

<aside>
➡️

- 학원 전체 / 강의별, 대상 학생 / 학부모 / 둘 다
- 고정, 첨부(files), 읽음 기록 → 관리자는 안 읽은 사람 확인
- 새 공지는 앱 푸시, 문자는 쓰지 않음
</aside>

## 질의응답 (상담)

`MVP` · 담당: 미정

<aside>
📁

- backend/src/acadesk/modules/questions/
</aside>

<aside>
💡 기획 요구: 학생이 선생님과 상담, 학부모 상담
</aside>

<aside>
➡️

- 질문 1개 = 스레드. 강의를 고르면 그 교사에게, 아니면 관리자에게 배정
- 학생–교사 스레드는 학부모에게 비공개
- 교사가 답하면 answered, 질문자가 다시 쓰면 open. 안 읽은 수는 question_reads로
</aside>

## 학부모 리포트 / 학생 화면

`MVP` · 담당: 미정

<aside>
📁

- backend/src/acadesk/modules/reports/
- frontend/src/app/parent/
- frontend/src/app/student/
</aside>

<aside>
💡 기획 요구: 자녀의 강의별 출결, 등원 확인, 시간표, 공지 (과제·수납은 2단계)
</aside>

<aside>
➡️

- 읽기 전용 모음 API. 출결 기록·회차·공지·긴급 문자를 기간(주·월)으로 합침
- QR 찍은 시각을 "실제 도착 시각"으로 보여줌
- 과제·수납 항목은 해당 기능을 켠 학원만 채움
</aside>

## 앱 알림

`MVP` · 담당: 미정

<aside>
📁

- backend/src/acadesk/modules/notifications/
- frontend/public/sw.js (Web Push)
</aside>

<aside>
💡 기획 요구: 일반 알림은 앱 푸시, 문자는 긴급할 때만
</aside>

<aside>
➡️

- PWA Web Push 구독을 기기별로 저장, 알림함(notifications)에 같이 기록
- 종류별 끄기와 방해 금지 시간. 긴급은 끌 수 없음
</aside>

## 긴급 문자

`MVP` · 담당: 미정

<aside>
📁

- backend/src/acadesk/modules/messaging/ (emergency_messages)
- backend/src/acadesk/integrations/sms/
</aside>

<aside>
💡 기획 요구: 정말 긴급할 때만 학부모에게 SMS
</aside>

<aside>
➡️

- 미리 보기(인원·번역·한도) → preview_token → 발송. 미리 보기 없이 못 보냄
- 교사는 자기 강의 학부모만, 학원 전체는 관리자만, 하루 한도
- 학부모별 문자는 messages에 남기고 대행사 멱등키로 중복 방지
</aside>

## 감사 로그

`MVP` · 담당: 미정

<aside>
📁

- backend/src/acadesk/modules/audit/
</aside>

<aside>
💡 기획 요구: 출결 정정, 긴급 문자, 계정 승인, 커뮤니티 제재 기록
</aside>

<aside>
➡️

- 추가만 가능. UPDATE·DELETE는 DB 트리거가 막음
</aside>

## 학부모 익명 커뮤니티

`2단계` · 담당: 미정

<aside>
📁

- backend/src/acadesk/modules/community/
- frontend/src/app/parent/community/
</aside>

<aside>
💡 기획 요구: 같은 학원 학부모끼리 블라인드·당근처럼 익명(공개/비공개) 커뮤니티
</aside>

<aside>
➡️

- 인증 학부모만. 글마다 익명/닉네임, 학원 전체/학년/강의 범위
- 응답에 작성자 ID를 넣지 않음 (is_mine만). 익명 댓글은 글마다 익명1, 익명2
- 소속 표시("중2 학부모")는 그룹 5명 이상일 때만
- 학원 직원은 글을 못 봄. 건의 게시판 글과 숫자 통계만
- 전화번호·실명 자동 가림, 신고 3건 임시 블라인드 → 운영자(operator) 검토, 제재는 실제 계정에
</aside>

## 과제

`2단계` · 담당: 미정

<aside>
📁

- backend/src/acadesk/modules/homework/
</aside>

<aside>
💡 기획 요구: 리포트의 과제 제출률·미제출 목록
</aside>

<aside>
➡️

- 강의별 과제와 학생별 제출 기록
</aside>

## 수납 기록

`2단계` · 담당: 미정

<aside>
📁

- backend/src/acadesk/modules/billing/ (invoices, payments)
</aside>

<aside>
💡 기획 요구: 리포트에서 이번 달 청구·납부·남은 금액, 형제 합산
</aside>

<aside>
➡️

- 금액은 정수(원), 납부는 여러 청구(형제)에 나눠 반영
- 자동 독촉은 3단계
</aside>

## 미납 자동 안내 (보류)

`3단계` · 담당: lshee9008 (제안)

<aside>
📁

- backend/src/acadesk/modules/rules/
- backend/src/acadesk/modules/approvals/
- backend/src/acadesk/modules/messaging/ (templates, candidates, replies)
- backend/src/acadesk/modules/documents/
</aside>

<aside>
💡 기획 요구: v1 기획의 단계별 미납 안내, 승인함 (2026-11-01 3단계로 미룸)
</aside>

<aside>
➡️

- API·DB는 v1 설계 그대로 남겨 둠 (3단계 표시)
- 입금자명 매칭·납부 약속·형제 할인도 3단계
</aside>

## AI 보조

`3단계` · 담당: lshee9008 (에이전트), Olivia (LLM·프롬프트)

<aside>
📁

- backend/src/acadesk/ai/
- backend/src/acadesk/api/v1/ai.py
</aside>

<aside>
💡 기획 요구: 월간 리포트 요약, 커뮤니티 위험 글 검토 보조, 다국어 번역
</aside>

<aside>
➡️

- 결과는 모두 확인 후보. 요약은 교사 확인 뒤 공개, 커뮤니티 삭제는 운영자가 결정
- 번역은 템플릿·공지 단위로 한 번, 숫자·날짜 칸은 코드가 채움
</aside>
