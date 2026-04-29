from app.core.config import get_settings
from app.llm.factory import create_provider


def test_factory_ollama(monkeypatch):
    monkeypatch.setenv('LLM_PROVIDER', 'ollama')
    get_settings.cache_clear()
    assert create_provider(get_settings()).name == 'ollama'


def test_factory_hf(monkeypatch):
    monkeypatch.setenv('LLM_PROVIDER', 'hf')
    get_settings.cache_clear()
    assert create_provider(get_settings()).name == 'hf'


def test_factory_model_provider_fallback(monkeypatch):
    monkeypatch.delenv('LLM_PROVIDER', raising=False)
    monkeypatch.setenv('MODEL_PROVIDER', 'mock')
    get_settings.cache_clear()
    assert create_provider(get_settings()).name == 'mock'
