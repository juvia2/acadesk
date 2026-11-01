from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ACADESK_", env_file=".env", extra="ignore")

    env: str = "local"
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:3000"]
    # 로컬 개발용: 토큰 없이 원장 권한 가상 사용자로 요청을 받음. 운영에서는 반드시 False.
    auth_dev_bypass: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
