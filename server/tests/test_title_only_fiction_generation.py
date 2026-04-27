def test_title_only_fiction_generation(client):
    book = client.post('/api/books', json={'title': 'Shantaram', 'book_type_id': 'fiction_novel'}).json()
    page = client.post(f"/api/books/{book['id']}/pages", json={'page_number': 1, 'user_prompt': '', 'user_text': ''}).json()

    gen = client.post(f"/api/pages/{page['id']}/generate", json={'instruction': 'Keep voice immersive'}).json()
    text = gen['page']['generated_text'].lower()

    assert gen['page']['generation_metadata']['skill_id'] == 'fiction_book_page'
    assert len(text.split()) > 40
    assert any(token in text for token in ['street', 'scene', 'breath', 'night', 'river', 'road', 'alley', 'city', 'story'])
    assert 'system:' not in text
    assert 'task:' not in text
