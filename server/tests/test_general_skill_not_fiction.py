def test_general_skill_not_fiction(client):
    book = client.post('/api/books', json={'title': 'Guide', 'book_type_id': 'educational_how_to', 'topic': 'Time blocking'}).json()
    page = client.post(f"/api/books/{book['id']}/pages", json={'page_number': 1, 'user_prompt': 'Explain time blocking'}).json()
    gen = client.post(f"/api/pages/{page['id']}/generate", json={'instruction': 'Teach it clearly'}).json()
    text = gen['page']['generated_text'].lower()

    assert gen['page']['generation_metadata']['skill_id'] == 'general_book_page'
    assert any(term in text for term in ['explain', 'practical', 'example', 'takeaway', 'concept'])
    assert not any(term in text for term in ['gunfire', 'bridge', 'chase'])
    assert not any(term in text for term in ['campaign', 'buyers', 'positioning'])
