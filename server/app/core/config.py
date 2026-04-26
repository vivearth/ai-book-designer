from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "AI Book Designer POC"
    database_url: str = Field(
        default="sqlite:///./data/book_designer.db",
        alias="DATABASE_URL",
    )
    model_provider: str = Field(default="mock", alias="MODEL_PROVIDER")
    ollama_base_url: str = Field(default="http://ollama:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="qwen3:8b", alias="OLLAMA_MODEL")
    default_llm_model: str | None = Field(default=None, alias="DEFAULT_LLM_MODEL")
    fiction_llm_model: str | None = Field(default=None, alias="FICTION_LLM_MODEL")
    marketing_llm_model: str | None = Field(default=None, alias="MARKETING_LLM_MODEL")
    finance_llm_model: str | None = Field(default=None, alias="FINANCE_LLM_MODEL")
    general_llm_model: str | None = Field(default=None, alias="GENERAL_LLM_MODEL")
    quality_llm_model: str | None = Field(default=None, alias="QUALITY_LLM_MODEL")
    server_cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:3000,http://localhost:8080",
        alias="SERVER_CORS_ORIGINS",
    )
    data_dir: Path = Field(default=Path("./data"), alias="DATA_DIR")

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
