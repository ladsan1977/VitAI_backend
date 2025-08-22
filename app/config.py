from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    app_env: str = "dev"
    log_level: str = "INFO"
    cors_origins: List[str] = ["http://localhost:5173"]
    port: int = 8000

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", case_sensitive=False)

settings = Settings()
