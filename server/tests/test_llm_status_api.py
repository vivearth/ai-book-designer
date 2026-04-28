import asyncio

import httpx

from app.core.config import get_settings
from app.engines.llm_engine import LLMEngine


def test_llm_status_mock(monkeypatch):
    monkeypatch.setenv('MODEL_PROVIDER', 'mock')
    get_settings.cache_clear()
    status = asyncio.run(LLMEngine().get_provider_status())
    assert status['provider'] == 'mock'
    assert status['available'] is True
    assert status['configured_model_present'] is True


def test_llm_status_ollama_mocked(monkeypatch):
    monkeypatch.setenv('MODEL_PROVIDER', 'ollama')
    monkeypatch.setenv('OLLAMA_MODEL', 'qwen2.5:3b-instruct')
    get_settings.cache_clear()

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {'models': [{'name': 'qwen2.5:3b-instruct'}]}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def get(self, url):
            return FakeResponse()

    monkeypatch.setattr(httpx, 'AsyncClient', FakeClient)

    result = asyncio.run(LLMEngine().get_provider_status())
    assert result['provider'] == 'ollama'
    assert result['available'] is True
    assert 'qwen2.5:3b-instruct' in result['models']
    assert result['configured_model_present'] is True
