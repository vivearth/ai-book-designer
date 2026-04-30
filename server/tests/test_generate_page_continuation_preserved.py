def test_generate_page_preserves_existing_continuation(client):
    book = client.post('/api/books', json={'title': 'Continuation Preserve'}).json()
    p1 = client.post(f"/api/books/{book['id']}/pages", json={'page_number': 1, 'generated_text': 'page1'}).json()
    p2 = client.post(f"/api/books/{book['id']}/pages", json={'page_number': 2, 'generated_text': 'overflow from page1'}).json()
    p2 = client.patch(
        f"/api/pages/{p2['id']}",
        json={'generation_metadata': {'continued_from_page_id': p1['id']}, 'generated_text': 'overflow from page1'},
    ).json()

    result = client.post(f"/api/pages/{p2['id']}/generate", json={'instruction': 'Write next part.'}).json()
    assert result['page']['generated_text'].startswith('overflow from page1')
    assert any('Existing continuation text was preserved' in w for w in result.get('warnings') or [])
