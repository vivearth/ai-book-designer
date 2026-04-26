from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "AI Book Designer POC"
    database_url: str = "postgresql+psycopg2://book_user:book_password@db:5432/book_designer"
    model_provider: str = "mock"
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "qwen3:8b"
    server_cors_origins: str = "http://localhost:5173,http://localhost:3000,http://localhost:8080"
    data_dir: Path = Path("/app/data")

    @property
    def upload_dir(self) -> Path:
        path = self.data_dir / "uploads"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def export_dir(self) -> Path:
        path = self.data_dir / "exports"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def cors_origins(self) -> list[str]:
        return [item.strip() for item in self.server_cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
