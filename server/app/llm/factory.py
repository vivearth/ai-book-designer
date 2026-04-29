from app.core.config import Settings
from app.llm.providers.base import BaseProvider
from app.llm.providers.huggingface import HuggingFaceProvider
from app.llm.providers.mock import MockProvider
from app.llm.providers.ollama import OllamaProvider


def create_provider(settings: Settings, *, mock_generator=None) -> BaseProvider:
    provider = settings.active_llm_provider
    if provider == "ollama":
        return OllamaProvider(settings)
    if provider in {"hf", "huggingface"}:
        return HuggingFaceProvider(settings)
    p = MockProvider()
    if mock_generator is not None:
        async def _gen(prompt: str, *, temperature: float, model: str, purpose: str | None = None) -> str:
            _ = (temperature, model, purpose)
            return mock_generator(prompt)
        p.generate_text = _gen  # type: ignore[method-assign]
    return p
