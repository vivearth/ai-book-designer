import pytest

from app.core.config import get_settings
from app.llm.factory import create_provider
from app.llm.providers.errors import ProviderConfigurationError


def test_factory_ollama(monkeypatch):
    monkeypatch.setenv('LLM_PROVIDER', 'ollama')
    get_settings.cache_clear()
    assert create_provider(get_settings()).name == 'ollama'


def test_factory_hf(monkeypatch):
    monkeypatch.setenv('LLM_PROVIDER', 'hf')
    get_settings.cache_clear()
    assert create_provider(get_settings()).name == 'hf'


def test_factory_mock_default(monkeypatch):
    monkeypatch.delenv('LLM_PROVIDER', raising=False)
    get_settings.cache_clear()
    assert create_provider(get_settings()).name == 'mock'


def test_factory_invalid_provider_raises(monkeypatch):
    monkeypatch.setenv('LLM_PROVIDER', 'bad-provider')
    get_settings.cache_clear()
    with pytest.raises(ProviderConfigurationError, match='Unsupported LLM_PROVIDER=bad-provider. Expected one of: mock, ollama, hf.'):
        create_provider(get_settings())
