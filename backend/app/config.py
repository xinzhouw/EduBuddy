from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    openai_api_key: str = ""
    secret_key: str = "dev-secret-key-change-in-production"
    database_url: str = "sqlite:///./data/edubuddy.db"
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 20
    cors_origins: str = "http://localhost:5173,http://localhost:80"

    algorithm: str = "HS256"
    access_token_expire_days: int = 7

    class Config:
        env_file = ".env"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


@lru_cache()
def get_settings() -> Settings:
    return Settings()
