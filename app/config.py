from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "VitAI"
    version: str = "0.1.0"
    app_env: str = "dev"
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:8080", "http://127.0.0.1:8080"]
    database_url: str = "postgresql://postgres:postgres@localhost:5432/vitai"
    port: int = 8000

    # Production security settings
    https_only: bool = Field(default=False, description="Enforce HTTPS in production")
    allowed_hosts: list[str] = Field(
        default=["*.onrender.com", "localhost"], description="Allowed hostnames for TrustedHostMiddleware"
    )

    # OpenAI Configuration
    openai_api_key: str = Field(default="", alias="OPEN_AI_KEY")
    openai_model: str = "gpt-5.1-chat-latest"
    openai_max_output_tokens: int = 4000
    openai_temperature: float = 0.1

    # File Upload Configuration
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_image_types: list[str] = ["image/jpeg", "image/png", "image/webp"]

    # Security Configuration
    api_key: str = Field(default="", alias="API_KEY")
    api_key_header: str = "X-API-Key"

    # Rate Limiting Configuration
    rate_limit_enabled: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")
    rate_limit_per_minute: int = Field(default=20, alias="RATE_LIMIT_PER_MINUTE")
    rate_limit_per_hour: int = Field(default=160, alias="RATE_LIMIT_PER_HOUR")

    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379", alias="REDIS_URL")
    redis_enabled: bool = Field(default=True, alias="REDIS_ENABLED")
    redis_cache_ttl: int = Field(default=86400, alias="REDIS_CACHE_TTL")  # 24 hours
    redis_max_connections: int = Field(default=10, alias="REDIS_MAX_CONNECTIONS")
    redis_socket_timeout: float = Field(default=5.0, alias="REDIS_SOCKET_TIMEOUT")

    # Circuit Breaker Configuration
    redis_circuit_breaker_threshold: int = Field(default=5, alias="REDIS_CIRCUIT_BREAKER_THRESHOLD")
    redis_circuit_breaker_timeout: int = Field(default=60, alias="REDIS_CIRCUIT_BREAKER_TIMEOUT")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            import json

            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=False,
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore extra environment variables
    )


settings = Settings()
