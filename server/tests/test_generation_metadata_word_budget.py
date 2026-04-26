def test_generation_metadata_contains_word_budget_fields(client):
    book = client.post('/api/books', json={'title': 'Budget Meta', 'book_type_id': 'fiction_novel'}).json()
    page = client.post(f"/api/books/{book['id']}/pages", json={'page_number': 1, 'user_prompt': 'Opening'}).json()

    generated = client.post(
        f"/api/pages/{page['id']}/generate",
        json={
            'instruction': 'Write a page.',
            'page_capacity_hint': {
                'visible_text_area_width_px': 470,
                'visible_text_area_height_px': 600,
                'font_family': 'Georgia',
                'font_size_px': 16,
                'line_height_px': 28,
                'estimated_chars_per_line': 44,
                'estimated_lines': 20,
                'estimated_words': 200,
                'composition': 'text_only',
            },
        },
    ).json()

    metadata = generated['page']['generation_metadata']
    assert metadata['target_words'] <= 200
    assert metadata['word_budget_reason']
    assert metadata['page_capacity_hint']['estimated_words'] == 200
