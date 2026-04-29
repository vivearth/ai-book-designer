import asyncio

import httpx

from app.core.config import get_settings
from app.llm.providers.huggingface import HuggingFaceProvider


def test_hf_parses_list_response(monkeypatch):
    monkeypatch.setenv('HF_API_TOKEN', 'x')
    get_settings.cache_clear()

    class R:
        status_code = 200
        def raise_for_status(self): return None
        def json(self): return [{'generated_text': 'hello'}]

    class C:
        def __init__(self,*a,**k): pass
        async def __aenter__(self): return self
        async def __aexit__(self,*a): return None
        async def post(self,*a,**k): return R()

    monkeypatch.setattr(httpx, 'AsyncClient', C)
    text = asyncio.run(HuggingFaceProvider(get_settings()).generate_text('p', temperature=0.2, model='m'))
    assert text == 'hello'
