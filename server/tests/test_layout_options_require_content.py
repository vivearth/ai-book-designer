def test_layout_options_require_content(client):
    book = client.post('/api/books', json={'title': 'Need Content', 'book_type_id': 'custom'}).json()
    page = client.post(f"/api/books/{book['id']}/pages", json={'page_number': 1}).json()

    response = client.post(
        f"/api/pages/{page['id']}/layout-options",
        json={'preserve_text': True, 'option_count': 2},
    )

    assert response.status_code == 400
    assert 'Add page text or image before generating layout options.' in response.text
