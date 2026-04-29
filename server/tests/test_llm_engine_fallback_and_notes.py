import asyncio

import pytest

from app.core.config import get_settings
from app.engines.llm_engine import LLMEngine
from app.llm.providers.errors import ProviderError


def test_hf_failure_no_fallback_raises(monkeypatch):
    monkeypatch.setenv('LLM_PROVIDER', 'hf')
    monkeypatch.setenv('HF_API_TOKEN', 'x')
    monkeypatch.setenv('LLM_FALLBACK_TO_MOCK_ON_PROVIDER_ERROR', 'false')
    get_settings.cache_clear()
    engine = LLMEngine()

    async def fail(*args, **kwargs):
        raise ProviderError('boom')

    monkeypatch.setattr(engine.provider, 'generate_text', fail)
    with pytest.raises(ProviderError):
        asyncio.run(engine.generate_text('Book title: T\nGenre or content direction: fiction'))


def test_hf_failure_with_fallback_returns_mock(monkeypatch):
    monkeypatch.setenv('LLM_PROVIDER', 'hf')
    monkeypatch.setenv('HF_API_TOKEN', 'x')
    monkeypatch.setenv('LLM_FALLBACK_TO_MOCK_ON_PROVIDER_ERROR', 'true')
    get_settings.cache_clear()
    engine = LLMEngine()

    async def fail(*args, **kwargs):
        raise ProviderError('boom')

    monkeypatch.setattr(engine.provider, 'generate_text', fail)
    text, notes = asyncio.run(engine.generate_text('Book title: T\nGenre or content direction: fiction\nPage direction: Chase'))
    assert 'Mock content fallback output.' not in text
    assert any('fallback_used=true' in n for n in notes)
    assert any('fallback_reason=' in n for n in notes)


def test_mock_provider_meaningful_output_and_notes(monkeypatch):
    monkeypatch.setenv('LLM_PROVIDER', 'mock')
    get_settings.cache_clear()
    engine = LLMEngine()
    text, notes = asyncio.run(engine.generate_text('Book title: T\nGenre or content direction: marketing\nBook topic: GTM\nPage direction: Start'))
    assert 'Mock content fallback output.' not in text
    assert any(n.startswith('provider=') for n in notes)
    assert any(n.startswith('model=') for n in notes)
    assert any(n.startswith('model_source=') for n in notes)
    assert any(n.startswith('llm_elapsed_ms=') for n in notes)
