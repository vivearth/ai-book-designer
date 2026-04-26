def test_no_source_behavior_by_domain(client):
    fiction = client.post('/api/books', json={'title': 'Fiction', 'book_type_id': 'fiction_novel'}).json()
    fp = client.post(f"/api/books/{fiction['id']}/pages", json={'page_number': 1, 'user_prompt': 'bridge chase'}).json()
    fg = client.post(f"/api/pages/{fp['id']}/generate", json={'instruction': 'scene', 'content_mode': 'fiction_novel'}).json()
    assert not any('No source material' in w for w in fg['warnings'])

    marketing = client.post('/api/books', json={'title': 'Marketing', 'book_type_id': 'marketing_story'}).json()
    mp = client.post(f"/api/books/{marketing['id']}/pages", json={'page_number': 1, 'user_prompt': 'messaging'}).json()
    mg = client.post(f"/api/pages/{mp['id']}/generate", json={'instruction': 'page', 'content_mode': 'marketing_story'}).json()
    assert any('No source material' in w for w in mg['warnings'])
