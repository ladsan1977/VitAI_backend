from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "VitAI"
    version: str = "0.1.0"
    app_env: str = "dev"
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:5173"]
    database_url: str = "postgresql://postgres:postgres@localhost:5432/vitai"
    port: int = 8000

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", case_sensitive=False, env_file_encoding="utf-8")

settings = Settings()
