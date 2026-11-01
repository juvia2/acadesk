from typing import Annotated

from fastapi import APIRouter, Depends, status

from acadesk.api.deps import MVP, CurrentUserDep, access
from acadesk.core.errors import not_implemented
from acadesk.core.schemas import Page, PageParams, page_params
from acadesk.core.security import MEMBERS

from .schemas import (
    NotificationOut,
    NotificationPreferences,
    PushSubscriptionBody,
    ReadBody,
    UnsubscribeBody,
)

router = APIRouter(prefix="/notifications", tags=["알림"])


@router.get("", summary="알림함", **access(MVP, *MEMBERS))
def list_notifications(
    user: CurrentUserDep,
    paging: Annotated[PageParams, Depends(page_params)],
    unread: bool = False,
) -> Page[NotificationOut]:
    raise not_implemented()


@router.post(
    "/read",
    summary="알림 읽음",
    status_code=status.HTTP_204_NO_CONTENT,
    **access(MVP, *MEMBERS),
)
def mark_read(user: CurrentUserDep, body: ReadBody) -> None:
    raise not_implemented()


@router.post(
    "/push-subscriptions",
    summary="앱 푸시 구독 등록",
    description="기기마다 한 번. 같은 endpoint면 갱신한다.",
    status_code=status.HTTP_204_NO_CONTENT,
    **access(MVP, *MEMBERS),
)
def subscribe(user: CurrentUserDep, body: PushSubscriptionBody) -> None:
    raise not_implemented()


@router.post(
    "/push-subscriptions/delete",
    summary="앱 푸시 구독 해제",
    status_code=status.HTTP_204_NO_CONTENT,
    **access(MVP, *MEMBERS),
)
def unsubscribe(user: CurrentUserDep, body: UnsubscribeBody) -> None:
    raise not_implemented()


@router.get("/preferences", summary="알림 설정 조회", **access(MVP, *MEMBERS))
def get_preferences(user: CurrentUserDep) -> NotificationPreferences:
    raise not_implemented()


@router.put("/preferences", summary="알림 설정 저장", **access(MVP, *MEMBERS))
def put_preferences(user: CurrentUserDep, body: NotificationPreferences) -> NotificationPreferences:
    raise not_implemented()


routers = [router]
