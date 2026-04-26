def test_expert_draft_generation(client):
    project = client.post('/api/projects', json={'name': 'Marketing Proj', 'content_direction': 'Marketing'}).json()
    book = client.post(f"/api/projects/{project['id']}/books", json={'title': 'Draft', 'book_type_id': 'marketing_story', 'creation_mode': 'expert'}).json()

    s1 = client.post(f"/api/projects/{project['id']}/sources/text", json={'title': 'Source1', 'text': 'Messaging clarity for buying committees and campaign proof points.'}).json()
    s2 = client.post(f"/api/projects/{project['id']}/sources/text", json={'title': 'Source2', 'text': 'Audience alignment and positioning reduce acquisition waste.'}).json()
    client.post(f"/api/sources/{s1['id']}/process")
    client.post(f"/api/sources/{s2['id']}/process")

    res = client.post(f"/api/books/{book['id']}/draft/generate", json={
        'target_page_count': 5,
        'source_asset_ids': [s1['id'], s2['id']],
        'book_type_id': 'marketing_story',
        'creation_mode': 'expert',
    }).json()

    pages = res['created_pages']
    assert len(pages) == 5
    assert [p['page_number'] for p in pages] == [1, 2, 3, 4, 5]
    assert all(p['generated_text'] for p in pages)
    assert all('SYSTEM:' not in p['generated_text'] for p in pages)
    assert res['source_summary']['selected_source_count'] == 2
