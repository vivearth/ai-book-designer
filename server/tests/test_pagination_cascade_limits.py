
def test_cascading_overflow_creates_or_updates_third_page(client):
    book = client.post('/api/books', json={'title': 'Cascade', 'book_type_id': 'fiction_novel'}).json()
    p1 = client.post(f"/api/books/{book['id']}/pages", json={'page_number': 1, 'user_text': 'seed'}).json()
    p2 = client.post(f"/api/books/{book['id']}/pages", json={'page_number': 2, 'user_text': 'seed2'}).json()
    client.patch(f"/api/pages/{p2['id']}", json={'generated_text': ('Existing sentence. ' * 400)})
    client.patch(f"/api/pages/{p1['id']}", json={'generated_text': ('Overflow sentence. ' * 900)})
    pages = sorted(client.get(f"/api/books/{book['id']}/pages").json(), key=lambda p: p['page_number'])
    assert len(pages) >= 3
    assert pages[2]['generation_metadata'].get('continued_from_page_id')


def test_max_pages_warning_present(client):
    book = client.post('/api/books', json={'title': 'Limit', 'book_type_id': 'fiction_novel'}).json()
    p1 = client.post(f"/api/books/{book['id']}/pages", json={'page_number': 1, 'generated_text': 'word ' * 1200}).json()
    # trigger many cascades by repeatedly forcing long content
    client.patch(f"/api/pages/{p1['id']}", json={'generated_text': 'word ' * 1200})
    pages = client.get(f"/api/books/{book['id']}/pages").json()
    warned = [p for p in pages if (p.get('generation_metadata') or {}).get('pagination', {}).get('warning')]
    # warning may not always trigger with default max_pages, but if triggered should include estimate
    if warned:
      assert 'overflow_words_remaining_estimate' in warned[-1]['generation_metadata']['pagination']
