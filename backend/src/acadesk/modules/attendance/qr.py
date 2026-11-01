"""QR 출석 토큰과 체크인 판정.

교사 화면의 QR은 `qr_rotate_seconds`(기본 30초)마다 바뀐다. 토큰은 (회차 ID, 시간 구간)을
HMAC으로 서명한 값이라 DB에 저장하지 않는다. 사진을 찍어 친구에게 보내도 구간이 지나면 무효가 된다.
스캔이 구간 경계에 걸리는 경우를 위해 바로 앞 구간 하나까지 받아 준다 (최대 약 60초 유효).

토큰 형식 (base64url): 버전 1바이트 | 회차 UUID 16바이트 | 구간 번호 4바이트 | 서명 앞 16바이트
"""

import base64
import hashlib
import hmac
import struct
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum

VERSION = 1
SIG_LEN = 16
_LAYOUT = struct.Struct(">B16sI")


class QrError(StrEnum):
    MALFORMED = "malformed"
    BAD_SIGNATURE = "bad_signature"
    EXPIRED = "expired"


class InvalidQrToken(Exception):
    def __init__(self, reason: QrError):
        super().__init__(reason.value)
        self.reason = reason


@dataclass(frozen=True)
class IssuedToken:
    token: str
    expires_at: datetime


def _window(now: datetime, period: int) -> int:
    return int(now.timestamp()) // period


def _sign(secret: str, body: bytes) -> bytes:
    return hmac.new(secret.encode(), b"acadesk-qr|" + body, hashlib.sha256).digest()[:SIG_LEN]


def issue_token(
    session_id: uuid.UUID, secret: str, period: int = 30, now: datetime | None = None
) -> IssuedToken:
    now = now or datetime.now(UTC)
    window = _window(now, period)
    body = _LAYOUT.pack(VERSION, session_id.bytes, window)
    token = base64.urlsafe_b64encode(body + _sign(secret, body)).rstrip(b"=").decode()
    expires_at = datetime.fromtimestamp((window + 1) * period, UTC)
    return IssuedToken(token=token, expires_at=expires_at)


def verify_token(
    token: str, secret: str, period: int = 30, now: datetime | None = None
) -> uuid.UUID:
    """유효하면 회차 ID를 돌려준다. 아니면 InvalidQrToken."""
    now = now or datetime.now(UTC)
    try:
        raw = base64.urlsafe_b64decode(token + "=" * (-len(token) % 4))
    except (ValueError, TypeError) as e:
        raise InvalidQrToken(QrError.MALFORMED) from e
    if len(raw) != _LAYOUT.size + SIG_LEN:
        raise InvalidQrToken(QrError.MALFORMED)
    body, sig = raw[: _LAYOUT.size], raw[_LAYOUT.size :]
    version, session_bytes, window = _LAYOUT.unpack(body)
    if version != VERSION:
        raise InvalidQrToken(QrError.MALFORMED)
    if not hmac.compare_digest(sig, _sign(secret, body)):
        raise InvalidQrToken(QrError.BAD_SIGNATURE)
    current = _window(now, period)
    if window not in (current, current - 1):
        raise InvalidQrToken(QrError.EXPIRED)
    return uuid.UUID(bytes=session_bytes)


class CheckInOutcome(StrEnum):
    PRESENT = "present"
    LATE = "late"
    TOO_EARLY = "too_early"
    CLOSED = "closed"


def classify_check_in(
    starts_at: datetime,
    ends_at: datetime,
    checked_at: datetime,
    late_after_minutes: int = 10,
    open_before_minutes: int = 15,
) -> CheckInOutcome:
    """체크인 시각으로 출석/지각을 정한다. 출석 가능 시간: 시작 15분 전 ~ 종료."""
    if checked_at < starts_at - timedelta(minutes=open_before_minutes):
        return CheckInOutcome.TOO_EARLY
    if checked_at > ends_at:
        return CheckInOutcome.CLOSED
    if checked_at > starts_at + timedelta(minutes=late_after_minutes):
        return CheckInOutcome.LATE
    return CheckInOutcome.PRESENT
