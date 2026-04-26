from io import BytesIO


def test_sources_upload_process_and_query(client):
    project = client.post('/api/projects', json={'name': 'Sources Project'}).json()
    project_id = project['id']

    text_source = client.post(f'/api/projects/{project_id}/sources/text', json={'title': 'Campaign notes', 'text': 'Messaging clarity reduces acquisition waste for buying committees.'}).json()
    assert text_source['source_type'] == 'note'

    file_source = client.post(
        f'/api/projects/{project_id}/sources',
        files={'file': ('insight.md', b'# Insight\nForecast reliability matters for CFO planning.', 'text/markdown')},
        data={'source_type': 'markdown', 'tags': 'finance,cfo'},
    ).json()
    assert file_source['id']

    processed = client.post(f"/api/sources/{file_source['id']}/process").json()
    assert processed['status'] == 'processed'

    sources = client.get(f'/api/projects/{project_id}/sources').json()
    assert len(sources) >= 2

    chunks = client.get(f'/api/projects/{project_id}/source-chunks', params={'query': 'forecast'}).json()
    assert chunks

    img = client.post(
        f'/api/projects/{project_id}/sources',
        files={'file': ('diagram.png', BytesIO(b'fakepng'), 'image/png')},
        data={'source_type': 'image'},
    ).json()
    assert img['source_type'] == 'image'

    assert client.delete(f"/api/sources/{text_source['id']}").json()['deleted'] is True
