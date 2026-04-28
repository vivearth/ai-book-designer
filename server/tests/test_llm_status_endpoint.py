def test_llm_status_endpoint(client):
    data = client.get('/api/llm/status').json()
    assert 'provider' in data
    assert 'available' in data
