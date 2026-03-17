from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI Support Ticket Chatbot"
    app_version: str = "0.1.0"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"

    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/support_tickets"
    )
    db_echo: bool = False
    db_pool_size: int = 10
    db_max_overflow: int = 20

    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536

    search_candidate_limit: int = 50
    default_query_limit: int = 10
    max_query_limit: int = 100


@lru_cache
def get_settings() -> Settings:
    return Settings()
