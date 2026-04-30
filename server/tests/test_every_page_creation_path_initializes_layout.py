def _assert_layout(page: dict):
    layout = page.get('layout_json') or {}
    assert layout
    assert layout.get('layout_schema') == 'page-layout-1'
    assert isinstance(layout.get('elements'), list) and layout['elements']
    assert (layout.get('validation') or {}).get('valid') is True


def test_every_page_creation_path_initializes_layout(client):
    book = client.post('/api/books', json={'title': 'Invariant Test', 'book_type_id': 'marketing_story'}).json()

    p1 = client.post(f"/api/books/{book['id']}/pages", json={'page_number': 1, 'user_text': 'hello'}).json()
    _assert_layout(p1)

    p2 = client.post(f"/api/books/{book['id']}/pages/next", json={}).json()
    _assert_layout(p2)

    generated = client.post(
        f"/api/pages/{p2['id']}/generate",
        json={
            'instruction': 'Write a detailed marketing page with enough copy to overflow the current page.',
            'content_mode': 'marketing_story',
            'target_words': 280,
            'page_capacity_hint': {
                'visible_text_area_width_px': 460,
                'visible_text_area_height_px': 320,
                'font_family': 'Georgia',
                'font_size_px': 16,
                'line_height_px': 28,
                'estimated_chars_per_line': 42,
                'estimated_lines': 11,
                'estimated_words': 70,
                'composition': 'text_with_image',
            },
        },
    ).json()
    _assert_layout(generated['page'])
    if generated.get('overflow_created_page'):
      _assert_layout(generated['overflow_created_page'])

    draft = client.post(f"/api/books/{book['id']}/draft/generate", json={
        'target_page_count': 2,
        'book_type_id': 'marketing_story',
        'creation_mode': 'expert',
    }).json()
    for page in draft['created_pages']:
        _assert_layout(page)
