from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from acadesk.api.v1.router import api_router
from acadesk.core.config import get_settings
from acadesk.core.schemas import ErrorBody


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="acadesk API",
        version="0.1.0",
        description="학원 학부모 소통 자동화 API. 모든 데이터는 로그인한 사용자의 학원으로 범위가 제한된다.",
        responses={
            401: {"model": ErrorBody, "description": "로그인 필요"},
            403: {"model": ErrorBody, "description": "권한 없음"},
        },
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix=settings.api_prefix)

    @app.get("/health", tags=["상태"], summary="서버 상태 확인")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
