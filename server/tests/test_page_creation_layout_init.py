
def test_create_page_initializes_layout(client):
    book = client.post('/api/books', json={'title':'t','book_type_id':'custom'}).json()
    page = client.post(f"/api/books/{book['id']}/pages", json={'page_number':1}).json()
    layout = page['layout_json']
    assert layout.get('layout_schema') == 'page-layout-1'
    assert isinstance(layout.get('elements'), list) and layout['elements']
    assert (layout.get('validation') or {}).get('valid') is True


def test_create_next_page_initializes_layout(client):
    book = client.post('/api/books', json={'title':'t','book_type_id':'custom'}).json()
    p1 = client.post(f"/api/books/{book['id']}/pages/next", json={}).json()
    p2 = client.post(f"/api/books/{book['id']}/pages/next", json={}).json()
    assert p1['layout_json'].get('layout_schema') == 'page-layout-1'
    assert p2['layout_json'].get('layout_schema') == 'page-layout-1'


def test_generate_layout_options_are_page_layout_schema(client):
    book = client.post('/api/books', json={'title':'t','book_type_id':'custom'}).json()
    page = client.post(f"/api/books/{book['id']}/pages", json={'page_number':1, 'user_text':'hello world '*40}).json()
    resp = client.post(f"/api/pages/{page['id']}/layout-options", json={'preserve_text': True, 'option_count': 2}).json()
    assert len(resp['options']) == 2
    assert all(o['layout_json'].get('layout_schema') == 'page-layout-1' for o in resp['options'])
    assert all((o['layout_json'].get('validation') or {}).get('valid') is True for o in resp['options'])
