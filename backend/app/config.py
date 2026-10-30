from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://insightops:insightops@localhost:5432/insightops"
    analytics_database_url: str = (
        "postgresql+psycopg://analytics_readonly:analytics_readonly@localhost:5432/insightops"
    )

    client_url: str = "http://localhost:3000"

    jwt_secret_key: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    max_result_rows: int = 500
    query_timeout_seconds: int = 10


@lru_cache
def get_settings() -> Settings:
    return Settings()


def is_ai_configured() -> bool:
    return bool(get_settings().openai_api_key)
