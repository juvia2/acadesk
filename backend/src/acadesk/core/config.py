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
    # 아래 비밀 값은 개발용 기본값이다. 운영에서는 반드시 환경 변수로 바꾼다.
    jwt_secret: str = "dev-only-jwt-secret-change-me-0000000000"
    access_token_minutes: int = 30
    refresh_token_days: int = 14
    # 연락처 암호화 키 (Fernet, url-safe base64 32바이트). 생성: Fernet.generate_key()
    phone_encryption_key: str = "ZGV2LW9ubHktcGhvbmUta2V5LWNoYW5nZS1tZS0wMDA="
    # 연락처 검색 해시·초대 코드 해시용 HMAC 키
    hash_secret: str = "dev-only-hash-secret-change-me"
    late_after_minutes: int = 10
    open_before_minutes: int = 15
    # 로컬 개발용: 토큰 없이 원장 권한 가상 사용자로 요청을 받음. 운영에서는 반드시 False.
    auth_dev_bypass: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
