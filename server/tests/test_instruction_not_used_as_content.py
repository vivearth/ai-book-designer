def test_instruction_not_used_as_content(client):
    book = client.post('/api/books', json={'title': 'Untitled Fiction', 'book_type_id': 'fiction_novel'}).json()
    page = client.post(f"/api/books/{book['id']}/pages", json={'page_number': 1, 'user_prompt': '', 'user_text': ''}).json()

    gen = client.post(
        f"/api/pages/{page['id']}/generate",
        json={'instruction': 'Shape this into a polished page while preserving continuity.'},
    ).json()
    text = gen['page']['generated_text'].lower()

    assert 'shape this' not in text
    assert 'preserving continuity' not in text
    assert 'polished page' not in text
    assert gen['page']['generation_metadata'].get('seed_reason')
