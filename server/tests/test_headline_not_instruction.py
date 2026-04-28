def test_headline_not_instruction(client):
    book = client.post('/api/books', json={'title': 'Headline Check', 'book_type_id': 'educational_how_to'}).json()
    page = client.post(f"/api/books/{book['id']}/pages", json={'page_number': 1, 'user_prompt': '', 'user_text': ''}).json()
    instruction = 'Shape this into a polished page while preserving continuity.'

    gen = client.post(f"/api/pages/{page['id']}/generate", json={'instruction': instruction}).json()
    headline = (gen['page']['generation_metadata'].get('headline') or '').lower()

    assert 'shape this' not in headline
    assert 'polished page' not in headline
    assert 'preserving continuity' not in headline
