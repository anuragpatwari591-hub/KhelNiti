"""Application configuration, read from environment variables (see
`.env.example`). Never hard-code a secret here — `app_secret_key` and
`jwt_secret_key` must come from the environment.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    app_secret_key: str = "dev-only-insecure-key-change-me"
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg2://khelniti:khelniti@localhost:5432/khelniti"

    jwt_secret_key: str = "dev-only-insecure-key-change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    api_rate_limit_per_minute: int = 120
    cors_allowed_origins: str = "http://localhost:3000"

    data_provider_mode: str = "mock"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
