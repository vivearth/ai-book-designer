def test_page_budget_prompting_or_metadata(client):
    book = client.post('/api/books', json={'title': 'Budget', 'book_type_id': 'fiction_novel'}).json()
    page = client.post(f"/api/books/{book['id']}/pages", json={'page_number': 1, 'user_prompt': 'Scene start'}).json()

    gen = client.post(
        f"/api/pages/{page['id']}/generate",
        json={
            'instruction': 'Write page',
            'page_capacity_hint': {
                'visible_text_area_width_px': 320,
                'visible_text_area_height_px': 420,
                'font_family': 'Georgia',
                'font_size_px': 14,
                'line_height_px': 20,
                'estimated_chars_per_line': 32,
                'estimated_lines': 12,
                'estimated_words': 90,
                'composition': 'text_only',
            },
        },
    ).json()

    target_words = gen['page']['generation_metadata']['target_words']
    assert target_words <= 90
    wc = len(gen['page']['generated_text'].split())
    assert wc <= max(120, int(target_words * 2.2))
