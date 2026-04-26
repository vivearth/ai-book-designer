def test_expert_book_created_under_project(client):
    project = client.post('/api/projects', json={
        'name': 'Expert Project',
        'content_direction': 'Marketing',
        'objective': 'Turn source material into a draft book',
    }).json()

    book = client.post(f"/api/projects/{project['id']}/books", json={
        'title': 'Expert Book',
        'book_type_id': 'marketing_story',
        'creation_mode': 'expert',
    }).json()

    assert book['project_id'] == project['id']
    assert book['creation_mode'] == 'expert'
