import asyncio

from app.core.config import get_settings
from app.engines.llm_engine import LLMEngine
from app.llm.providers.errors import ProviderTimeoutError


def test_ollama_timeout_config(monkeypatch):
    monkeypatch.setenv('LLM_PROVIDER', 'ollama')
    monkeypatch.setenv('LLM_FALLBACK_TO_MOCK_ON_PROVIDER_ERROR', 'true')
    monkeypatch.setenv('OLLAMA_TIMEOUT_SECONDS', '321')
    get_settings.cache_clear()
    engine = LLMEngine()
    assert engine.settings.ollama_timeout_seconds == 321


def test_ollama_model_fallback(monkeypatch):
    monkeypatch.setenv('LLM_PROVIDER', 'ollama')
    monkeypatch.setenv('OLLAMA_MODEL', 'legacy-model')
    monkeypatch.delenv('DEFAULT_LLM_MODEL', raising=False)
    get_settings.cache_clear()
    engine = LLMEngine()
    model, source = engine.resolve_model(model=None, purpose='general')
    assert model == 'legacy-model'
    assert source == 'ollama_model'


def test_ollama_base_url_used_in_status(monkeypatch):
    monkeypatch.setenv('LLM_PROVIDER', 'ollama')
    monkeypatch.setenv('OLLAMA_BASE_URL', 'http://ollama-custom:11434')
    get_settings.cache_clear()
    engine = LLMEngine()
    status = asyncio.run(engine.get_provider_status())
    assert status['provider'] == 'ollama'
    assert status['base_url'] == 'http://ollama-custom:11434'


def test_engine_timeout_falls_back_to_mock(monkeypatch):
    monkeypatch.setenv('LLM_PROVIDER', 'ollama')
    monkeypatch.setenv('LLM_FALLBACK_TO_MOCK_ON_PROVIDER_ERROR', 'true')
    get_settings.cache_clear()
    engine = LLMEngine()

    async def _timeout(*args, **kwargs):
        raise ProviderTimeoutError('slow')

    monkeypatch.setattr(engine.provider, 'generate_text', _timeout)
    text, notes = asyncio.run(engine.generate_text('Target words: 120'))
    assert isinstance(text, str)
    assert isinstance(notes, list)
    assert any('fallback_used=true' in n for n in notes)


def test_fast_mode_skips_plan_pass(monkeypatch):
    from app.skills.base import SkillContext
    from app.skills.writing_flow import maybe_run_two_pass_page_generation

    class FakeEngine:
        def __init__(self):
            self.calls = 0
            self.settings = type('S', (), {'active_llm_provider': 'ollama', 'llm_fast_mode': True, 'llm_two_pass_enabled': True})()

        async def generate_text(self, prompt, **kwargs):
            self.calls += 1
            return 'fast prose', []

    fake = FakeEngine()
    ctx = SkillContext(db=None, llm_engine=fake)
    prose, _, plan, _ = asyncio.run(maybe_run_two_pass_page_generation(context=ctx, skill_kind='general', title='T', topic='Topic', book_type='general', previous_summary='summary', direction='direction', rough_notes='rough', source_excerpts='source', target_words=120, composition='text_only'))
    assert prose
    assert plan == 'fast_mode_no_plan'
    assert fake.calls == 1
