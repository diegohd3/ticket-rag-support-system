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
    cors_allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    cors_allowed_methods: str = "GET,POST,PATCH,OPTIONS"
    cors_allowed_headers: str = "Authorization,Content-Type,X-API-Key,X-Request-ID"
    cors_allow_credentials: bool = True
    trust_x_forwarded_for: bool = False

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
    embedding_reindex_batch_size: int = 50
    vector_search_probes: int = 10

    search_candidate_limit: int = 50
    semantic_candidate_limit: int = 25
    default_query_limit: int = 10
    max_query_limit: int = 100
    hybrid_text_weight: float = 0.55
    hybrid_semantic_weight: float = 0.45
    semantic_search_enabled: bool = True
    rerank_enabled: bool = True
    rerank_window: int = 10
    openai_timeout_seconds: float = 30.0

    chat_max_context_tickets: int = 5
    ticket_embedding_source_fields: str = (
        "titulo,descripcion_problema,descripcion_solucion,categoria,tags,sistema_afectado,causa_raiz,pasos_diagnostico,logs"
    )

    auth_token_secret: str = "dev-insecure-change-me"
    auth_token_ttl_minutes: int = 60
    auth_bootstrap_admin_username: str = "admin"
    auth_bootstrap_admin_password: str = ""
    auth_bootstrap_admin_display_name: str = "Platform Admin"

    api_key_required: bool = False
    internal_api_key: str = ""
    user_guard_enabled: bool = True
    user_violation_threshold: int = 3

    rate_limit_enabled: bool = True
    rate_limit_requests: int = 120
    rate_limit_window_seconds: int = 60
    rate_limit_login_requests: int = 8
    rate_limit_login_window_seconds: int = 60
    rate_limit_chat_requests: int = 40
    rate_limit_search_requests: int = 60
    rate_limit_reindex_requests: int = 3
    rate_limit_ops_requests: int = 20

    security_headers_enabled: bool = True
    security_csp: str = (
        "default-src 'self'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'none'; "
        "img-src 'self' data:; "
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'self' 'unsafe-inline'"
    )
    security_referrer_policy: str = "strict-origin-when-cross-origin"
    security_permissions_policy: str = "geolocation=(), microphone=(), camera=()"
    security_hsts_enabled: bool = True
    security_hsts_max_age_seconds: int = 31536000
    security_hsts_include_subdomains: bool = True
    security_hsts_preload: bool = False

    demo_endpoint_enabled: bool = True

    observability_enabled: bool = True
    llm_input_cost_per_1m_tokens: float = 0.0
    llm_output_cost_per_1m_tokens: float = 0.0
    embedding_input_cost_per_1m_tokens: float = 0.0

    def parse_csv(self, value: str) -> list[str]:
        normalized = value.strip()
        if not normalized:
            return []
        if normalized == "*":
            return ["*"]
        return [item.strip() for item in normalized.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
