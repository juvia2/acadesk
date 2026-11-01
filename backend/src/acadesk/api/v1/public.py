"""학부모 원클릭 응답 링크. 로그인 없이 발송 건별 일회용 토큰으로 접근한다. 개인정보는 보여주지 않는다."""

from typing import Annotated

from fastapi import APIRouter, Path
from pydantic import BaseModel, Field

from acadesk.api.deps import STAGE3, access
from acadesk.core.errors import not_implemented
from acadesk.modules.messaging.schemas import ReplyIntent

router = APIRouter(prefix="/public", tags=["공개 링크"])

Token = Annotated[str, Path(min_length=16, max_length=128)]


class ReplyOption(BaseModel):
    intent: ReplyIntent
    label: str = Field(description="수신 언어로 번역된 버튼 문구")


class PublicReplyPage(BaseModel):
    academy_name: str
    notice_label: str = Field(description="예: 11월 수강료 안내")
    language: str
    options: list[ReplyOption]
    answered: bool
    expires_at: str


class PublicReplyBody(BaseModel):
    intent: ReplyIntent
    message: str | None = Field(None, max_length=500)


class PublicReplyResult(BaseModel):
    ok: bool = True
    thank_you: str


@router.get("/replies/{token}", summary="원클릭 응답 화면 정보", **access(STAGE3))
def get_reply_page(token: Token) -> PublicReplyPage:
    raise not_implemented()


@router.post(
    "/replies/{token}",
    summary="원클릭 응답 제출",
    description="AI 분류 없이 의도가 기록되고, 같은 사유 후속 안내가 바로 멈추며 담당자 확인 작업이 생긴다.",
    **access(STAGE3),
)
def submit_reply(token: Token, body: PublicReplyBody) -> PublicReplyResult:
    raise not_implemented()
