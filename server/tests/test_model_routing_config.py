import asyncio

from app.core.config import get_settings
from app.engines.llm_engine import LLMEngine


def test_model_routing_config(monkeypatch):
    monkeypatch.setenv('MODEL_PROVIDER', 'ollama')
    monkeypatch.setenv('OLLAMA_MODEL', 'legacy-model')
    monkeypatch.setenv('DEFAULT_LLM_MODEL', 'default-model')
    monkeypatch.setenv('FICTION_LLM_MODEL', 'fiction-model')
    monkeypatch.delenv('MARKETING_LLM_MODEL', raising=False)
    get_settings.cache_clear()

    engine = LLMEngine()
    seen = {}

    async def fake_generate(prompt: str, *, temperature: float, model: str):
        seen['model'] = model
        return 'ok output'

    monkeypatch.setattr(engine, '_ollama_generate', fake_generate)

    asyncio.run(engine.generate_text('x', purpose='fiction'))
    assert seen['model'] == 'fiction-model'

    asyncio.run(engine.generate_text('x', purpose='marketing'))
    assert seen['model'] == 'default-model'

    asyncio.run(engine.generate_text('x', model='override-model', purpose='marketing'))
    assert seen['model'] == 'override-model'
