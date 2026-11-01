"""현재 시각. 테스트에서 시간을 고정할 수 있게 한 곳에서만 부른다."""

from datetime import UTC, datetime


def now() -> datetime:
    return datetime.now(UTC)
