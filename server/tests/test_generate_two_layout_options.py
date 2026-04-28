def test_generate_two_layout_options(client):
    book = client.post('/api/books', json={'title': 'Layout Test', 'book_type_id': 'custom'}).json()
    page = client.post(
        f"/api/books/{book['id']}/pages",
        json={'page_number': 1, 'user_text': 'This is stable provided text that should be preserved during layout option generation.'},
    ).json()

    baseline = client.get(f"/api/books/{book['id']}/pages").json()[0]
    response = client.post(
        f"/api/pages/{page['id']}/layout-options",
        json={'preserve_text': True, 'option_count': 2},
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload['options']) == 2
    assert payload['options'][0]['layout_json']['variant'] != payload['options'][1]['layout_json']['variant']
    assert payload['options'][0]['layout_json']['composition'] != payload['options'][1]['layout_json']['composition'] or payload['options'][0]['layout_json']['variant'] != payload['options'][1]['layout_json']['variant']

    page_after = client.get(f"/api/books/{book['id']}/pages").json()[0]
    assert page_after['user_text'] == baseline['user_text']
    assert page_after.get('generated_text') == baseline.get('generated_text')
