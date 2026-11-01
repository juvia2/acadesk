from fastapi import HTTPException, status


def not_implemented() -> HTTPException:
    """엔드포인트 계약만 있고 서비스가 아직 없을 때 쓴다."""
    return HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "아직 구현되지 않았습니다")
