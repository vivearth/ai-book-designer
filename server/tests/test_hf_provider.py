import asyncio

import httpx
import pytest

from app.core.config import get_settings
from app.llm.providers.errors import ProviderConfigurationError, ProviderTimeoutError
from app.llm.providers.huggingface import HuggingFaceProvider


def _settings(monkeypatch):
    monkeypatch.setenv('LLM_PROVIDER', 'hf')
    monkeypatch.setenv('HF_API_TOKEN', 'x')
    get_settings.cache_clear()
    return get_settings()


def test_hf_parses_list_response(monkeypatch):
    s = _settings(monkeypatch)
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
    assert asyncio.run(HuggingFaceProvider(s).generate_text('p', temperature=0.2, model='m')) == 'hello'


def test_hf_parses_dict_response(monkeypatch):
    s = _settings(monkeypatch)
    class R:
        status_code = 200
        def raise_for_status(self): return None
        def json(self): return {'generated_text': 'world'}
    class C:
        def __init__(self,*a,**k): pass
        async def __aenter__(self): return self
        async def __aexit__(self,*a): return None
        async def post(self,*a,**k): return R()
    monkeypatch.setattr(httpx, 'AsyncClient', C)
    assert asyncio.run(HuggingFaceProvider(s).generate_text('p', temperature=0.2, model='m')) == 'world'


def test_hf_503_retry_succeeds(monkeypatch):
    s = _settings(monkeypatch)
    calls = {'n': 0}
    class R:
        def __init__(self, code): self.status_code = code
        def raise_for_status(self):
            if self.status_code >= 400:
                req = httpx.Request('POST', 'http://x')
                raise httpx.HTTPStatusError('e', request=req, response=httpx.Response(self.status_code, request=req, json={'estimated_time': 0.01}))
        def json(self): return {'generated_text': 'ok', 'estimated_time': 0.01}
    class C:
        def __init__(self,*a,**k): pass
        async def __aenter__(self): return self
        async def __aexit__(self,*a): return None
        async def post(self,*a,**k):
            calls['n'] += 1
            return R(503 if calls['n'] == 1 else 200)
    monkeypatch.setattr(httpx, 'AsyncClient', C)
    async def no_sleep(*_args, **_kwargs):
        return None
    monkeypatch.setattr(asyncio, 'sleep', no_sleep)
    assert asyncio.run(HuggingFaceProvider(s).generate_text('p', temperature=0.2, model='m')) == 'ok'
    assert calls['n'] == 2


def test_hf_missing_token_raises(monkeypatch):
    monkeypatch.setenv('LLM_PROVIDER', 'hf')
    monkeypatch.delenv('HF_API_TOKEN', raising=False)
    get_settings.cache_clear()
    with pytest.raises(ProviderConfigurationError, match='HF_API_TOKEN is required'):
        asyncio.run(HuggingFaceProvider(get_settings()).generate_text('p', temperature=0.2, model='m'))


def test_hf_timeout_maps(monkeypatch):
    s = _settings(monkeypatch)
    class C:
        def __init__(self,*a,**k): pass
        async def __aenter__(self): return self
        async def __aexit__(self,*a): return None
        async def post(self,*a,**k): raise httpx.TimeoutException('timeout')
    monkeypatch.setattr(httpx, 'AsyncClient', C)
    with pytest.raises(ProviderTimeoutError):
        asyncio.run(HuggingFaceProvider(s).generate_text('p', temperature=0.2, model='m'))
