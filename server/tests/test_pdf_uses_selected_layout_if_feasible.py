def test_pdf_uses_selected_layout_if_feasible(client):
    book = client.post('/api/books', json={'title': 'PDF Layout Selection'}).json()
    page = client.post(
        f"/api/books/{book['id']}/pages",
        json={'page_number': 1, 'user_text': 'PDF export should reflect selected layout option.'},
    ).json()

    generated = client.post(f"/api/pages/{page['id']}/layout-options", json={'option_count': 2}).json()
    option_b = generated['options'][1]
    client.post(f"/api/pages/{page['id']}/layout-options/{option_b['id']}/select")

    exported = client.post(f"/api/books/{book['id']}/export/pdf", json={'approved_only': False})
    assert exported.status_code == 200
    payload = exported.json()
    assert payload['filename'].endswith('.pdf')
