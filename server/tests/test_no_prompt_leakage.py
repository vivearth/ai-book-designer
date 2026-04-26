FORBIDDEN = ['SYSTEM:', 'CONSTRAINTS', 'TASK', 'BOOK PROFILE', 'USER CURRENT PAGE INPUT', 'Draft page content', "{'page_number'"]


def test_no_prompt_leakage_marketing_and_fiction(client):
    fiction = client.post('/api/books', json={'title': 'Leak check', 'book_type_id': 'fiction_novel'}).json()
    page = client.post(f"/api/books/{fiction['id']}/pages", json={'page_number': 1, 'user_prompt': 'Night chase'}).json()
    text = client.post(f"/api/pages/{page['id']}/generate", json={'instruction': 'Write chase scene', 'content_mode': 'fiction_novel'}).json()['page']['generated_text']
    assert all(token not in text for token in FORBIDDEN)
