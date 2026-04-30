def test_delete_middle_page_renumbers_and_clears_continuation_refs(client):
    book = client.post('/api/books', json={'title': 'Delete Page'}).json()
    p1 = client.post(f"/api/books/{book['id']}/pages", json={'page_number': 1, 'generated_text': 'first'}).json()
    p2 = client.post(f"/api/books/{book['id']}/pages", json={'page_number': 2, 'generated_text': 'second sentence for layout option generation.'}).json()
    p3 = client.post(f"/api/books/{book['id']}/pages", json={'page_number': 3, 'generated_text': 'third'}).json()

    client.patch(f"/api/pages/{p3['id']}", json={'generation_metadata': {'continued_from_page_id': p2['id'], 'pagination': {'continued_from_page_id': p2['id']}}})
    result = client.delete(f"/api/pages/{p2['id']}").json()

    assert result['deleted_page_id'] == p2['id']
    nums = [p['page_number'] for p in result['pages']]
    assert nums == [1, 2]
    moved = next(p for p in result['pages'] if p['id'] == p3['id'])
    assert moved['generation_metadata'].get('continued_from_page_id') is None
    assert (moved['generation_metadata'].get('pagination') or {}).get('continued_from_page_id') is None
