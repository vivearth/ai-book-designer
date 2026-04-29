import asyncio

import httpx
import pytest

from app.core.config import get_settings
from app.llm.providers.errors import ProviderConfigurationError, ProviderError, ProviderHTTPError, ProviderTimeoutError
from app.llm.providers.huggingface import HuggingFaceProvider


def _settings(monkeypatch):
    monkeypatch.setenv('LLM_PROVIDER', 'hf')
    monkeypatch.setenv('HF_API_TOKEN', 'x')
    monkeypatch.setenv('HF_BASE_URL', 'https://router.huggingface.co/v1')
    get_settings.cache_clear()
    return get_settings()


def test_hf_posts_to_router_chat_completions(monkeypatch):
    s = _settings(monkeypatch)
    captured = {}

    class R:
        status_code = 200
        text = 'ok'
        def json(self): return {'choices': [{'message': {'content': 'hello'}}]}

    class C:
        def __init__(self, *a, **k): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return None
        async def post(self, *a, **k):
            captured['url'] = a[0]
            captured['headers'] = k['headers']
            captured['json'] = k['json']
            return R()

    monkeypatch.setattr(httpx, 'AsyncClient', C)
    out = asyncio.run(HuggingFaceProvider(s).generate_text('prompt', temperature=0.2, model='Qwen/Qwen2.5-7B-Instruct:fastest'))
    assert out == 'hello'
    assert captured['url'] == 'https://router.huggingface.co/v1/chat/completions'
    assert captured['headers'].get('Authorization', '').startswith('Bearer ')
    assert captured['json']['model'] == 'Qwen/Qwen2.5-7B-Instruct:fastest'
    assert captured['json']['messages'][0]['role'] == 'user'
    assert captured['json']['messages'][0]['content'] == 'prompt'
    assert captured['json']['max_tokens'] == s.hf_max_new_tokens
    assert captured['json']['temperature'] == 0.2
    assert captured['json']['stream'] is False


def test_hf_parses_openai_content(monkeypatch):
    s = _settings(monkeypatch)
    class R:
        status_code = 200
        text = 'ok'
        def json(self): return {'choices': [{'message': {'content': 'hello'}}]}
    class C:
        def __init__(self,*a,**k): pass
        async def __aenter__(self): return self
        async def __aexit__(self,*a): return None
        async def post(self,*a,**k): return R()
    monkeypatch.setattr(httpx, 'AsyncClient', C)
    assert asyncio.run(HuggingFaceProvider(s).generate_text('p', temperature=0.2, model='m')) == 'hello'


def test_hf_parses_choices_text_fallback(monkeypatch):
    s = _settings(monkeypatch)
    class R:
        status_code = 200
        text = 'ok'
        def json(self): return {'choices': [{'text': 'hello'}]}
    class C:
        def __init__(self,*a,**k): pass
        async def __aenter__(self): return self
        async def __aexit__(self,*a): return None
        async def post(self,*a,**k): return R()
    monkeypatch.setattr(httpx, 'AsyncClient', C)
    assert asyncio.run(HuggingFaceProvider(s).generate_text('p', temperature=0.2, model='m')) == 'hello'


def test_hf_unknown_shape_raises_with_preview(monkeypatch):
    s = _settings(monkeypatch)
    class R:
        status_code = 200
        text = 'ok'
        def json(self): return {'unexpected': True}
    class C:
        def __init__(self,*a,**k): pass
        async def __aenter__(self): return self
        async def __aexit__(self,*a): return None
        async def post(self,*a,**k): return R()
    monkeypatch.setattr(httpx, 'AsyncClient', C)
    with pytest.raises(ProviderError, match='body_preview'):
        asyncio.run(HuggingFaceProvider(s).generate_text('p', temperature=0.2, model='m'))


def test_hf_404_error_contains_status_and_body(monkeypatch):
    s = _settings(monkeypatch)
    class R:
        status_code = 404
        text = 'Cannot POST /models/Qwen/Qwen2.5-7B-Instruct'
        def json(self): return {'error':'bad'}
    class C:
        def __init__(self,*a,**k): pass
        async def __aenter__(self): return self
        async def __aexit__(self,*a): return None
        async def post(self,*a,**k): return R()
    monkeypatch.setattr(httpx, 'AsyncClient', C)
    with pytest.raises(ProviderHTTPError) as ei:
        asyncio.run(HuggingFaceProvider(s).generate_text('p', temperature=0.2, model='m'))
    assert ei.value.status == 404
    assert 'Cannot POST /models' in str(ei.value)


def test_hf_503_non_json_retry_succeeds(monkeypatch):
    s = _settings(monkeypatch)
    calls = {'n': 0}
    class R:
        def __init__(self, code): self.status_code = code; self.text='svc unavailable'
        def json(self):
            if self.status_code == 503:
                raise ValueError('not json')
            return {'choices': [{'message': {'content': 'ok'}}]}
    class C:
        def __init__(self,*a,**k): pass
        async def __aenter__(self): return self
        async def __aexit__(self,*a): return None
        async def post(self,*a,**k):
            calls['n'] += 1
            return R(503 if calls['n'] == 1 else 200)
    monkeypatch.setattr(httpx, 'AsyncClient', C)
    async def no_sleep(*_args, **_kwargs): return None
    monkeypatch.setattr(asyncio, 'sleep', no_sleep)
    assert asyncio.run(HuggingFaceProvider(s).generate_text('p', temperature=0.2, model='m')) == 'ok'


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
