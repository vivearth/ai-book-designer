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
    llm_provider: str = Field(default="mock", alias="LLM_PROVIDER")
    ollama_base_url: str = Field(default="http://ollama:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="qwen2.5:3b-instruct", alias="OLLAMA_MODEL")
    ollama_timeout_seconds: float = Field(default=300, alias="OLLAMA_TIMEOUT_SECONDS")
    ollama_num_ctx: int = Field(default=2048, alias="OLLAMA_NUM_CTX")
    ollama_num_predict: int = Field(default=320, alias="OLLAMA_NUM_PREDICT")
    ollama_keep_alive: str = Field(default="5m", alias="OLLAMA_KEEP_ALIVE")
    ollama_stream: bool = Field(default=False, alias="OLLAMA_STREAM")
    llm_two_pass_enabled: bool = Field(default=True, alias="LLM_TWO_PASS_ENABLED")
    llm_fallback_to_mock_on_provider_error: bool = Field(default=False, alias="LLM_FALLBACK_TO_MOCK_ON_PROVIDER_ERROR")
    llm_fast_mode: bool = Field(default=False, alias="LLM_FAST_MODE")
    default_llm_model: str | None = Field(default=None, alias="DEFAULT_LLM_MODEL")
    fiction_llm_model: str | None = Field(default=None, alias="FICTION_LLM_MODEL")
    marketing_llm_model: str | None = Field(default=None, alias="MARKETING_LLM_MODEL")
    finance_llm_model: str | None = Field(default=None, alias="FINANCE_LLM_MODEL")
    general_llm_model: str | None = Field(default=None, alias="GENERAL_LLM_MODEL")
    quality_llm_model: str | None = Field(default=None, alias="QUALITY_LLM_MODEL")
    hf_api_token: str | None = Field(default=None, alias="HF_API_TOKEN")
    hf_base_url: str = Field(default="https://router.huggingface.co/v1", alias="HF_BASE_URL")
    hf_model: str = Field(default="Qwen/Qwen2.5-7B-Instruct", alias="HF_MODEL")
    hf_timeout_seconds: float = Field(default=90, alias="HF_TIMEOUT_SECONDS")
    hf_max_new_tokens: int = Field(default=320, alias="HF_MAX_NEW_TOKENS")
    hf_retry_attempts: int = Field(default=3, alias="HF_RETRY_ATTEMPTS")
    hf_retry_backoff_seconds: float = Field(default=1.0, alias="HF_RETRY_BACKOFF_SECONDS")
    hf_chat_template: str = Field(default="plain", alias="HF_CHAT_TEMPLATE")
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

    @property
    def active_llm_provider(self) -> str:
        return self.llm_provider.lower().strip() or "mock"


@lru_cache
def get_settings() -> Settings:
    return Settings()
