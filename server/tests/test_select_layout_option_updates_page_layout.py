def test_select_layout_option_updates_page_layout(client):
    book = client.post('/api/books', json={'title': 'Selection Test'}).json()
    page = client.post(
        f"/api/books/{book['id']}/pages",
        json={'page_number': 1, 'user_text': 'Page content for layout options selection.'},
    ).json()
    client.patch(
        f"/api/pages/{page['id']}",
        json={
            'generated_text': 'Generated paragraph should remain untouched.',
            'final_text': 'Final paragraph should remain untouched.',
        },
    )

    generated = client.post(f"/api/pages/{page['id']}/layout-options", json={'option_count': 2}).json()
    option_b = next(option for option in generated['options'] if option['option_index'] == 2)

    selected_page = client.post(f"/api/pages/{page['id']}/layout-options/{option_b['id']}/select").json()

    assert selected_page['layout_json']['variant'] == option_b['layout_json']['variant']
    assert selected_page['selected_layout_option_id'] == option_b['id']
    assert selected_page['generation_metadata']['selected_layout_option_id'] == option_b['id']
    assert selected_page['user_text'] == 'Page content for layout options selection.'
    assert selected_page['generated_text'] == 'Generated paragraph should remain untouched.'
    assert selected_page['final_text'] == 'Final paragraph should remain untouched.'
