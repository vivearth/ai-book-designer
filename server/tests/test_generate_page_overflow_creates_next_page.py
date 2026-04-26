def test_generate_page_overflow_creates_next_page(client):
    book = client.post('/api/books', json={'title': 'Overflow Test', 'book_type_id': 'fiction_novel'}).json()
    page1 = client.post(f"/api/books/{book['id']}/pages", json={'page_number': 1, 'user_prompt': 'Open with a long chase'}).json()

    generated = client.post(
        f"/api/pages/{page1['id']}/generate",
        json={
            'instruction': 'Write a tense chase scene with strong pacing.',
            'content_mode': 'fiction_novel',
            'target_words': 320,
            'page_capacity_hint': {
                'visible_text_area_width_px': 470,
                'visible_text_area_height_px': 360,
                'font_family': 'Georgia',
                'font_size_px': 16,
                'line_height_px': 28,
                'estimated_chars_per_line': 44,
                'estimated_lines': 13,
                'estimated_words': 80,
                'composition': 'text_with_image',
            },
        },
    ).json()

    assert len(generated['page']['generated_text'].split()) <= 90
    assert generated['overflow_created_page'] is not None
    assert generated['overflow_created_page']['page_number'] == 2
    assert generated['overflow_created_page']['generation_metadata']['auto_continued'] is True
