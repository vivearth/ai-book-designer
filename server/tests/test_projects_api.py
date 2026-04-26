def test_project_crud_and_defaults(client):
    created = client.post('/api/projects', json={
        'name': 'Partner Growth Project',
        'content_direction': 'Marketing',
        'audience': 'CMOs',
        'objective': 'Convert campaign content into a book',
    }).json()
    assert created['id'].startswith('proj_')
    assert created['brand_profiles']
    assert created['format_profiles']

    listing = client.get('/api/projects').json()
    assert any(p['id'] == created['id'] for p in listing)

    fetched = client.get(f"/api/projects/{created['id']}").json()
    assert fetched['name'] == 'Partner Growth Project'

    updated = client.patch(f"/api/projects/{created['id']}", json={'status': 'active'}).json()
    assert updated['status'] == 'active'

    book = client.post(f"/api/projects/{created['id']}/books", json={'title': 'Growth Systems'}).json()
    assert book['project_id'] == created['id']

    project_books = client.get(f"/api/projects/{created['id']}/books").json()
    assert project_books and project_books[0]['id'] == book['id']
