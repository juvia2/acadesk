import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from acadesk.api.deps import MVP, STAGE3, CurrentUserDep, access
from acadesk.core.errors import not_implemented
from acadesk.core.schemas import Page, PageParams, page_params
from acadesk.core.security import STAFF, STAFF_ADMIN

from .schemas import (
    CancelBody,
    CandidateOut,
    CandidateStatus,
    CorrectionBody,
    EmergencyMessageDetail,
    EmergencyMessageOut,
    EmergencyPreview,
    EmergencyPreviewBody,
    EmergencySendBody,
    MessageOut,
    MessageStatus,
    NoticeKind,
    PreviewBody,
    PreviewOut,
    ReplyIntent,
    ReplyOut,
    ReplyStatus,
    ReplyUpdate,
    TemplateCreate,
    TemplateOut,
    TemplateUpdate,
    TemplateVersionCreate,
    TemplateVersionOut,
    TranslationOut,
    TranslationRequest,
    TranslationUpdate,
)

templates_router = APIRouter(prefix="/templates", tags=["템플릿"])
candidates_router = APIRouter(prefix="/candidates", tags=["안내 후보"])
messages_router = APIRouter(
    prefix="/messages", tags=["발송 이력"]
)  # 문자 1건 단위 (긴급·안내 공통)
replies_router = APIRouter(prefix="/replies", tags=["회신"])
emergency_router = APIRouter(prefix="/emergency-messages", tags=["긴급 문자"])

Paging = Annotated[PageParams, Depends(page_params)]


# ── 템플릿 ───────────────────────────────────────────


@templates_router.get("", summary="템플릿 목록", **access(STAGE3, *STAFF))
def list_templates(
    user: CurrentUserDep, kind: NoticeKind | None = None, archived: bool = False
) -> list[TemplateOut]:
    raise not_implemented()


@templates_router.post(
    "",
    summary="템플릿 만들기 (버전 1 초안)",
    status_code=status.HTTP_201_CREATED,
    **access(STAGE3, *STAFF_ADMIN),
)
def create_template(user: CurrentUserDep, body: TemplateCreate) -> TemplateOut:
    raise not_implemented()


@templates_router.get("/{template_id}", summary="템플릿 상세", **access(STAGE3, *STAFF))
def get_template(user: CurrentUserDep, template_id: uuid.UUID) -> TemplateOut:
    raise not_implemented()


@templates_router.patch(
    "/{template_id}", summary="템플릿 이름 수정·보관", **access(STAGE3, *STAFF_ADMIN)
)
def update_template(
    user: CurrentUserDep, template_id: uuid.UUID, body: TemplateUpdate
) -> TemplateOut:
    raise not_implemented()


@templates_router.get(
    "/{template_id}/versions", summary="템플릿 버전 목록", **access(STAGE3, *STAFF)
)
def list_versions(user: CurrentUserDep, template_id: uuid.UUID) -> list[TemplateVersionOut]:
    raise not_implemented()


@templates_router.post(
    "/{template_id}/versions",
    summary="새 버전 초안",
    description="문구를 고치면 새 버전이 생긴다. 이미 보낸 건은 당시 버전을 기록하고 있다.",
    status_code=status.HTTP_201_CREATED,
    **access(STAGE3, *STAFF_ADMIN),
)
def create_version(
    user: CurrentUserDep, template_id: uuid.UUID, body: TemplateVersionCreate
) -> TemplateVersionOut:
    raise not_implemented()


@templates_router.post(
    "/{template_id}/versions/{version}/approve",
    summary="버전 승인",
    description="승인된 버전만 발송에 쓴다.",
    **access(STAGE3, *STAFF_ADMIN),
)
def approve_version(
    user: CurrentUserDep, template_id: uuid.UUID, version: int
) -> TemplateVersionOut:
    raise not_implemented()


@templates_router.post(
    "/{template_id}/preview", summary="자리 표시 채워 미리 보기", **access(STAGE3, *STAFF)
)
def preview(user: CurrentUserDep, template_id: uuid.UUID, body: PreviewBody) -> PreviewOut:
    raise not_implemented()


@templates_router.get(
    "/{template_id}/versions/{version}/translations",
    summary="번역 목록",
    **access(STAGE3, *STAFF),
)
def list_translations(
    user: CurrentUserDep, template_id: uuid.UUID, version: int
) -> list[TranslationOut]:
    raise not_implemented()


@templates_router.post(
    "/{template_id}/versions/{version}/translations",
    summary="번역 생성 요청 (AI)",
    description="템플릿 버전 × 언어 단위로 한 번 번역한다. 자리 표시는 번역하지 않고 그대로 둔다.",
    status_code=status.HTTP_202_ACCEPTED,
    **access(STAGE3, *STAFF_ADMIN),
)
def request_translation(
    user: CurrentUserDep, template_id: uuid.UUID, version: int, body: TranslationRequest
) -> TranslationOut:
    raise not_implemented()


@templates_router.patch(
    "/{template_id}/versions/{version}/translations/{language}",
    summary="번역 수정·승인",
    description="검증 오류가 남아 있으면 승인할 수 없다.",
    **access(STAGE3, *STAFF_ADMIN),
)
def update_translation(
    user: CurrentUserDep,
    template_id: uuid.UUID,
    version: int,
    language: str,
    body: TranslationUpdate,
) -> TranslationOut:
    raise not_implemented()


# ── 안내 후보 ───────────────────────────────────────


@candidates_router.get(
    "",
    summary="안내 후보 목록",
    description="규칙 엔진이 만든 모든 후보. 승인이 필요한 건은 승인함(/approvals)에서 처리한다.",
    **access(STAGE3, *STAFF),
)
def list_candidates(
    user: CurrentUserDep,
    paging: Paging,
    status_: Annotated[CandidateStatus | None, Query(alias="status")] = None,
    kind: NoticeKind | None = None,
    student_id: uuid.UUID | None = None,
    rule_run_id: uuid.UUID | None = None,
) -> Page[CandidateOut]:
    raise not_implemented()


@candidates_router.get("/{candidate_id}", summary="안내 후보 상세", **access(STAGE3, *STAFF))
def get_candidate(user: CurrentUserDep, candidate_id: uuid.UUID) -> CandidateOut:
    raise not_implemented()


@candidates_router.post(
    "/{candidate_id}/cancel", summary="안내 후보 취소", **access(STAGE3, *STAFF_ADMIN)
)
def cancel_candidate(
    user: CurrentUserDep, candidate_id: uuid.UUID, body: CancelBody
) -> CandidateOut:
    raise not_implemented()


# ── 발송 이력 ───────────────────────────────────────


@messages_router.get("", summary="발송 이력", **access(MVP, *STAFF))
def list_messages(
    user: CurrentUserDep,
    paging: Paging,
    status_: Annotated[MessageStatus | None, Query(alias="status")] = None,
    student_id: uuid.UUID | None = None,
    guardian_id: uuid.UUID | None = None,
    from_: Annotated[datetime | None, Query(alias="from")] = None,
    to: datetime | None = None,
) -> Page[MessageOut]:
    raise not_implemented()


@messages_router.get("/{message_id}", summary="발송 건 상세", **access(MVP, *STAFF))
def get_message(user: CurrentUserDep, message_id: uuid.UUID) -> MessageOut:
    raise not_implemented()


@messages_router.post(
    "/{message_id}/cancel",
    summary="예약 발송 취소",
    description="scheduled 상태에서만 가능하다.",
    **access(MVP, *STAFF_ADMIN),
)
def cancel_message(user: CurrentUserDep, message_id: uuid.UUID, body: CancelBody) -> MessageOut:
    raise not_implemented()


@messages_router.post(
    "/{message_id}/corrections",
    summary="오발송 정정 안내 만들기",
    description="정정 안내 초안을 승인함에 올리고, 같은 사유 후속 안내를 멈추고, 원인을 기록한다. "
    "응답은 생성된 정정 안내 후보.",
    status_code=status.HTTP_201_CREATED,
    **access(STAGE3, *STAFF_ADMIN),
)
def create_correction(
    user: CurrentUserDep, message_id: uuid.UUID, body: CorrectionBody
) -> CandidateOut:
    raise not_implemented()


# ── 회신 ─────────────────────────────────────────────


@replies_router.get("", summary="학부모 회신 목록", **access(STAGE3, *STAFF))
def list_replies(
    user: CurrentUserDep,
    paging: Paging,
    status_: Annotated[ReplyStatus | None, Query(alias="status")] = ReplyStatus.OPEN,
    intent: ReplyIntent | None = None,
    student_id: uuid.UUID | None = None,
) -> Page[ReplyOut]:
    raise not_implemented()


@replies_router.get("/{reply_id}", summary="회신 상세", **access(STAGE3, *STAFF))
def get_reply(user: CurrentUserDep, reply_id: uuid.UUID) -> ReplyOut:
    raise not_implemented()


@replies_router.patch(
    "/{reply_id}",
    summary="회신 분류 확정·처리 완료",
    description="paid·correction·consult_request로 확정하면 같은 사유 후속 안내를 멈춘다.",
    **access(STAGE3, *STAFF),
)
def update_reply(user: CurrentUserDep, reply_id: uuid.UUID, body: ReplyUpdate) -> ReplyOut:
    raise not_implemented()


# ── 긴급 문자 ───────────────────────────────────────


@emergency_router.post(
    "/preview",
    summary="긴급 문자 미리 보기",
    description="받을 인원, 번역 필요 인원, 오늘 남은 발송 한도를 보여주고 preview_token을 준다. "
    "교사는 자기 강의 학생의 학부모만, 학원 전체(academy)는 관리자만.",
    **access(MVP, *STAFF),
)
def preview_emergency(user: CurrentUserDep, body: EmergencyPreviewBody) -> EmergencyPreview:
    raise not_implemented()


@emergency_router.post(
    "",
    summary="긴급 문자 발송",
    description="미리 보기에서 받은 preview_token이 있어야 보낸다. 문자와 앱 푸시를 같이 보내고, "
    "외국어 수신자에게는 번역문을 덧붙인다. 발송 기록은 감사 로그에 남는다.",
    status_code=status.HTTP_202_ACCEPTED,
    **access(MVP, *STAFF),
)
def send_emergency(user: CurrentUserDep, body: EmergencySendBody) -> EmergencyMessageOut:
    raise not_implemented()


@emergency_router.get("", summary="긴급 문자 이력", **access(MVP, *STAFF))
def list_emergency(user: CurrentUserDep, paging: Paging) -> Page[EmergencyMessageOut]:
    raise not_implemented()


@emergency_router.get("/{emergency_id}", summary="긴급 문자 상세·수신 결과", **access(MVP, *STAFF))
def get_emergency(user: CurrentUserDep, emergency_id: uuid.UUID) -> EmergencyMessageDetail:
    raise not_implemented()


routers = [templates_router, candidates_router, messages_router, replies_router, emergency_router]
