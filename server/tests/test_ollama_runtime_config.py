import asyncio

import httpx

from app.core.config import get_settings
from app.engines.llm_engine import LLMEngine
from app.skills.base import SkillContext
from app.skills.writing_flow import maybe_run_two_pass_page_generation


def test_ollama_timeout_config(monkeypatch):
    monkeypatch.setenv('MODEL_PROVIDER', 'ollama')
    monkeypatch.setenv('OLLAMA_TIMEOUT_SECONDS', '321')
    get_settings.cache_clear()

    engine = LLMEngine()

    async def timed_out(*args, **kwargs):
        raise httpx.TimeoutException('slow')

    monkeypatch.setattr(engine, '_ollama_generate', timed_out)
    _, notes = asyncio.run(engine.generate_text('Target words: 120', purpose='general'))

    assert engine.settings.ollama_timeout_seconds == 321
    assert any('Ollama timeout after 321' in note for note in notes)


def test_ollama_payload_options(monkeypatch):
    monkeypatch.setenv('MODEL_PROVIDER', 'ollama')
    monkeypatch.setenv('OLLAMA_TIMEOUT_SECONDS', '400')
    monkeypatch.setenv('OLLAMA_NUM_CTX', '2048')
    monkeypatch.setenv('OLLAMA_NUM_PREDICT', '280')
    monkeypatch.setenv('OLLAMA_KEEP_ALIVE', '10m')
    monkeypatch.setenv('OLLAMA_STREAM', 'false')
    get_settings.cache_clear()

    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {'response': 'ok'}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, url, json):
            captured['url'] = url
            captured['payload'] = json
            return FakeResponse()

    monkeypatch.setattr(httpx, 'AsyncClient', FakeClient)

    engine = LLMEngine()
    text = asyncio.run(engine._ollama_generate('Target words: 150', temperature=0.4, model='mini', purpose='general'))
    assert text == 'ok'
    payload = captured['payload']
    assert payload['model'] == 'mini'
    assert payload['keep_alive'] == '10m'
    assert payload['options']['num_ctx'] == 2048
    assert payload['options']['num_predict'] <= 280
    assert payload['options']['temperature'] == 0.4


def test_fast_mode_skips_plan_pass(monkeypatch):
    class FakeEngine:
        def __init__(self):
            self.calls = 0
            self.settings = type('S', (), {'model_provider': 'ollama', 'llm_fast_mode': True, 'llm_two_pass_enabled': True})()

        async def generate_text(self, prompt, **kwargs):
            self.calls += 1
            return 'fast prose', []

    fake = FakeEngine()
    ctx = SkillContext(db=None, llm_engine=fake)
    prose, _, plan, _ = asyncio.run(
        maybe_run_two_pass_page_generation(
            context=ctx,
            skill_kind='general',
            title='T',
            topic='Topic',
            book_type='general',
            previous_summary='summary',
            direction='direction',
            rough_notes='rough',
            source_excerpts='source',
            target_words=120,
            composition='text_only',
        )
    )
    assert prose
    assert plan == 'fast_mode_no_plan'
    assert fake.calls == 1


def test_prompt_truncation():
    ctx = SkillContext(db=None, llm_engine=None)
    prose, _, _, meta = asyncio.run(
        maybe_run_two_pass_page_generation(
            context=ctx,
            skill_kind='general',
            title='T',
            topic='X' * 500,
            book_type='general',
            previous_summary='P' * 4000,
            direction='d',
            rough_notes='R' * 5000,
            source_excerpts='S' * 6000,
            target_words=120,
            composition='text_only',
        )
    )
    assert prose
    assert meta['prompt_truncated'] is True
    assert meta['prompt_length_chars'] < 5000
