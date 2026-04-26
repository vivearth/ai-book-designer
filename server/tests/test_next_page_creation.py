def test_next_page_creation_and_duplicate_rejection(client):
    book = client.post('/api/books', json={'title': 'Linear', 'book_type_id': 'fiction_novel'}).json()
    p1 = client.post(f"/api/books/{book['id']}/pages", json={'page_number': 1}).json()
    assert p1['page_number'] == 1

    p2 = client.post(f"/api/books/{book['id']}/pages/next", json={}).json()
    assert p2['page_number'] == 2

    dup = client.post(f"/api/books/{book['id']}/pages", json={'page_number': 2})
    assert dup.status_code == 409
