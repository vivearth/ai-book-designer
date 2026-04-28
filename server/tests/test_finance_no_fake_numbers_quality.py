import re


def test_finance_no_fake_numbers_quality(client):
    project = client.post('/api/projects', json={'name': 'FIN', 'content_direction': 'Finance'}).json()
    source = client.post(
        f"/api/projects/{project['id']}/sources/text",
        json={
            'title': 'Finance source',
            'text': 'Working capital discipline, forecast reliability, and scenario planning improve cash visibility during uncertain planning cycles.',
        },
    ).json()
    client.post(f"/api/sources/{source['id']}/process")

    book = client.post(f"/api/projects/{project['id']}/books", json={'title': 'Finance Explainer', 'book_type_id': 'finance_explainer'}).json()
    page = client.post(f"/api/books/{book['id']}/pages", json={'page_number': 1, 'user_prompt': 'Cash visibility under uncertainty'}).json()
    gen = client.post(f"/api/pages/{page['id']}/generate", json={'instruction': 'Explain carefully', 'content_mode': 'finance'}).json()
    text = gen['page']['generated_text'].lower()

    assert gen['page']['generation_metadata']['skill_id'] == 'finance_book_page'
    assert any(term in text for term in ['working', 'capital', 'forecast', 'scenario', 'cash'])
    assert not re.search(r'\b\d+\s*%|\$\s*\d+|\b\d{3,}\b', text)
    assert all(marker not in text for marker in ['system:', 'constraints', 'task', 'return only', 'draft page content'])
