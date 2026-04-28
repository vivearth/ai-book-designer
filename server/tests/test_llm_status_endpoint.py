def test_llm_status_endpoint(client):
    data = client.get('/api/llm/status').json()
    assert 'provider' in data
    assert 'available' in data


def test_llm_warmup_endpoint(client):
    data = client.post('/api/llm/warmup').json()
    assert 'warmed' in data
