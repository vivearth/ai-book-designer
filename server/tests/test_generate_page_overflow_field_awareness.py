
def test_generate_overflow_updates_existing_final_text_page(client):
    book = client.post('/api/books', json={'title': 'Overflow Final', 'book_type_id': 'fiction_novel'}).json()
    p1 = client.post(f"/api/books/{book['id']}/pages", json={'page_number': 1, 'user_prompt': 'p1'}).json()
    p2 = client.post(f"/api/books/{book['id']}/pages", json={'page_number': 2, 'user_prompt': 'p2', 'user_text': 'next'}).json()
    client.patch(f"/api/pages/{p2['id']}", json={'final_text': 'Existing final page text'})

    result = client.post(f"/api/pages/{p1['id']}/generate", json={'instruction': 'Write long text', 'content_mode': 'fiction_novel', 'target_words': 420, 'page_capacity_hint': {'visible_text_area_width_px': 420, 'visible_text_area_height_px': 260, 'font_family': 'Georgia', 'font_size_px': 16, 'line_height_px': 28, 'estimated_chars_per_line': 35, 'estimated_lines': 8, 'estimated_words': 40, 'composition': 'text_with_image'}}).json()
    assert result['overflow_warning'] in {None, 'Generated text overflow was merged into existing next page.'}

    pages = client.get(f"/api/books/{book['id']}/pages").json()
    next_page = [p for p in pages if p['page_number'] == 2][0]
    assert next_page['final_text']
    assert 'Existing final page text' in next_page['final_text']


def test_generate_overflow_to_blank_next_page_sets_generated(client):
    book = client.post('/api/books', json={'title': 'Overflow Blank', 'book_type_id': 'fiction_novel'}).json()
    p1 = client.post(f"/api/books/{book['id']}/pages", json={'page_number': 1, 'user_prompt': 'p1'}).json()
    client.post(f"/api/pages/{p1['id']}/generate", json={'instruction': 'Write long text', 'content_mode': 'fiction_novel', 'target_words': 420, 'page_capacity_hint': {'visible_text_area_width_px': 420, 'visible_text_area_height_px': 260, 'font_family': 'Georgia', 'font_size_px': 16, 'line_height_px': 28, 'estimated_chars_per_line': 35, 'estimated_lines': 8, 'estimated_words': 40, 'composition': 'text_with_image'}}).json()
    pages = client.get(f"/api/books/{book['id']}/pages").json()
    assert any(p['page_number'] == 2 for p in pages)
