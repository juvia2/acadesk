from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ACADESK_", env_file=".env", extra="ignore")

    env: str = "local"
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:3000"]
    # infra/docker/docker-compose.yml 기준. 로컬 Postgres(5432)와 겹치지 않게 5433.
    database_url: str = "postgresql+psycopg://acadesk:acadesk@localhost:5433/acadesk"
    redis_url: str = "redis://localhost:6380/0"
    frontend_url: str = "http://localhost:3000"
    # QR 출석 토큰 서명 키. 운영에서는 반드시 긴 임의 값으로 바꾼다 (ACADESK_QR_SECRET)
    qr_secret: str = "dev-only-qr-secret-change-me"
    qr_rotate_seconds: int = 30
    # 로컬 개발용: 토큰 없이 원장 권한 가상 사용자로 요청을 받음. 운영에서는 반드시 False.
    auth_dev_bypass: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
