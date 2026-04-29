import asyncio

from app.core.config import get_settings
from app.engines.llm_engine import LLMEngine


def test_ollama_timeout_config(monkeypatch):
    monkeypatch.setenv('MODEL_PROVIDER', 'ollama')
    monkeypatch.setenv('OLLAMA_TIMEOUT_SECONDS', '321')
    get_settings.cache_clear()
    engine = LLMEngine()
    assert engine.settings.ollama_timeout_seconds == 321


def test_fast_mode_skips_plan_pass(monkeypatch):
    from app.skills.base import SkillContext
    from app.skills.writing_flow import maybe_run_two_pass_page_generation

    class FakeEngine:
        def __init__(self):
            self.calls = 0
            self.settings = type('S', (), {'model_provider': 'ollama', 'llm_fast_mode': True, 'llm_two_pass_enabled': True})()

        async def generate_text(self, prompt, **kwargs):
            self.calls += 1
            return 'fast prose', []

    fake = FakeEngine()
    ctx = SkillContext(db=None, llm_engine=fake)
    prose, _, plan, _ = asyncio.run(maybe_run_two_pass_page_generation(context=ctx, skill_kind='general', title='T', topic='Topic', book_type='general', previous_summary='summary', direction='direction', rough_notes='rough', source_excerpts='source', target_words=120, composition='text_only'))
    assert prose
    assert plan == 'fast_mode_no_plan'
    assert fake.calls == 1
