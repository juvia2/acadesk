from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


class AppError(Exception):
    """서비스가 던지는 예상된 오류. code는 프론트가 분기할 때 쓴다 (예: expired_qr)."""

    def __init__(self, status_code: int, code: str, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def not_found(what: str = "대상") -> AppError:
    # 다른 학원 데이터도 404로 돌려 존재 여부를 드러내지 않는다
    return AppError(status.HTTP_404_NOT_FOUND, "not_found", f"{what}을(를) 찾을 수 없습니다")


def forbidden(code: str, message: str) -> AppError:
    return AppError(status.HTTP_403_FORBIDDEN, code, message)


def conflict(code: str, message: str) -> AppError:
    return AppError(status.HTTP_409_CONFLICT, code, message)


def bad_request(code: str, message: str) -> AppError:
    return AppError(status.HTTP_400_BAD_REQUEST, code, message)


async def app_error_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, AppError)
    return JSONResponse(
        status_code=exc.status_code, content={"detail": exc.message, "code": exc.code}
    )


def not_implemented() -> HTTPException:
    """엔드포인트 계약만 있고 서비스가 아직 없을 때 쓴다."""
    return HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "아직 구현되지 않았습니다")
