import uuid
from datetime import UTC, datetime, timedelta

import pytest

from acadesk.modules.attendance.qr import (
    CheckInOutcome,
    InvalidQrToken,
    QrError,
    classify_check_in,
    issue_token,
    verify_token,
)

SECRET = "test-secret"
SESSION = uuid.uuid4()
T0 = datetime(2026, 11, 3, 7, 0, 5, tzinfo=UTC)  # 구간 시작 직후


def test_round_trip():
    issued = issue_token(SESSION, SECRET, now=T0)
    assert verify_token(issued.token, SECRET, now=T0) == SESSION
    assert issued.expires_at > T0
    assert issued.expires_at - T0 <= timedelta(seconds=30)


def test_token_changes_every_period():
    a = issue_token(SESSION, SECRET, now=T0).token
    b = issue_token(SESSION, SECRET, now=T0 + timedelta(seconds=30)).token
    assert a != b


def test_previous_window_accepted_for_scan_delay():
    token = issue_token(SESSION, SECRET, now=T0).token
    assert verify_token(token, SECRET, now=T0 + timedelta(seconds=30)) == SESSION


def test_old_photo_rejected():
    token = issue_token(SESSION, SECRET, now=T0).token
    with pytest.raises(InvalidQrToken) as e:
        verify_token(token, SECRET, now=T0 + timedelta(seconds=61))
    assert e.value.reason == QrError.EXPIRED


def test_future_token_rejected():
    token = issue_token(SESSION, SECRET, now=T0 + timedelta(minutes=5)).token
    with pytest.raises(InvalidQrToken):
        verify_token(token, SECRET, now=T0)


def test_wrong_secret_rejected():
    token = issue_token(SESSION, SECRET, now=T0).token
    with pytest.raises(InvalidQrToken) as e:
        verify_token(token, "other", now=T0)
    assert e.value.reason == QrError.BAD_SIGNATURE


def test_tampered_session_rejected():
    import base64

    token = issue_token(SESSION, SECRET, now=T0).token
    raw = bytearray(base64.urlsafe_b64decode(token + "=" * (-len(token) % 4)))
    raw[5] ^= 0xFF  # 회차 ID 한 바이트 변경
    forged = base64.urlsafe_b64encode(bytes(raw)).rstrip(b"=").decode()
    with pytest.raises(InvalidQrToken) as e:
        verify_token(forged, SECRET, now=T0)
    assert e.value.reason == QrError.BAD_SIGNATURE


@pytest.mark.parametrize("bad", ["", "abc", "!!!!", "A" * 80])
def test_garbage_rejected(bad):
    with pytest.raises(InvalidQrToken) as e:
        verify_token(bad, SECRET, now=T0)
    assert e.value.reason == QrError.MALFORMED


START = datetime(2026, 11, 3, 16, 0, tzinfo=UTC)
END = START + timedelta(minutes=90)


@pytest.mark.parametrize(
    ("offset_min", "expected"),
    [
        (-16, CheckInOutcome.TOO_EARLY),
        (-15, CheckInOutcome.PRESENT),
        (0, CheckInOutcome.PRESENT),
        (10, CheckInOutcome.PRESENT),
        (11, CheckInOutcome.LATE),
        (90, CheckInOutcome.LATE),
        (91, CheckInOutcome.CLOSED),
    ],
)
def test_classify_check_in(offset_min, expected):
    at = START + timedelta(minutes=offset_min)
    assert classify_check_in(START, END, at) == expected
