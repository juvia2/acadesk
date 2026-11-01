import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class NotificationKind(StrEnum):
    CHECK_IN = "check_in"  # 자녀 출석
    ABSENCE = "absence"  # 자녀 결석
    ATTENDANCE_CORRECTED = "attendance_corrected"
    SESSION_CANCELLED = "session_cancelled"  # 휴강
    NOTICE = "notice"
    QUESTION = "question"  # 새 질문·답변
    EMERGENCY = "emergency"
    COMMUNITY = "community"  # 내 글 댓글 (2단계)


class NotificationOut(BaseModel):
    id: uuid.UUID
    kind: NotificationKind
    title: str
    body: str
    link: str = Field(description="앱 안 이동 경로. 예: /parent/children/{id}/attendance")
    created_at: datetime
    read_at: datetime | None = None


class ReadBody(BaseModel):
    ids: list[uuid.UUID] | None = Field(None, description="비우면 전부 읽음")


class PushKeys(BaseModel):
    p256dh: str
    auth: str


class PushSubscriptionBody(BaseModel):
    """브라우저 Web Push 구독 (PWA). 앱 출시 후에는 FCM/APNs 토큰도 같은 자리에."""

    endpoint: str
    keys: PushKeys
    user_agent: str | None = None


class UnsubscribeBody(BaseModel):
    endpoint: str


class NotificationPreferences(BaseModel):
    """종류별 앱 푸시 켜기/끄기. 긴급은 끌 수 없다."""

    check_in: bool = True
    absence: bool = True
    notice: bool = True
    question: bool = True
    community: bool = True
    quiet_start: str | None = Field(None, pattern=r"^\d{2}:\d{2}$", examples=["22:00"])
    quiet_end: str | None = Field(None, pattern=r"^\d{2}:\d{2}$", examples=["07:00"])
