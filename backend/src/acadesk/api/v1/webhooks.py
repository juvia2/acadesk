"""발송 대행사 웹훅. 로그인 대신 서명으로 검증한다. 본문 형식은 대행사마다 달라 원문을 받는다."""

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, status

from acadesk.api.deps import MVP, access, verify_webhook_signature
from acadesk.core.errors import not_implemented

router = APIRouter(
    prefix="/webhooks/sms/{provider}",
    tags=["웹훅"],
    dependencies=[Depends(verify_webhook_signature)],
)


@router.post(
    "/delivery",
    summary="발송 결과 수신",
    description="발송 이력 상태를 갱신한다. 알림톡 실패면 문자 대체 발송을 예약한다. "
    "같은 이벤트가 여러 번 와도 한 번만 반영한다.",
    status_code=status.HTTP_204_NO_CONTENT,
    **access(MVP),
)
def delivery(provider: str, payload: Annotated[dict[str, Any], Body()]) -> None:
    raise not_implemented()


@router.post(
    "/inbound",
    summary="학부모 회신 수신",
    description="회신을 저장하고 원래 발송 건과 연결한다. 외국어면 번역을, AI가 켜져 있으면 분류를 요청한다.",
    status_code=status.HTTP_204_NO_CONTENT,
    **access(MVP),
)
def inbound(provider: str, payload: Annotated[dict[str, Any], Body()]) -> None:
    raise not_implemented()
