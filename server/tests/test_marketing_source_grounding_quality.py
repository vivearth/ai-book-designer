import re


def test_marketing_source_grounding_quality(client):
    project = client.post('/api/projects', json={'name': 'MKT', 'content_direction': 'Marketing', 'objective': 'B2B growth'}).json()
    source = client.post(
        f"/api/projects/{project['id']}/sources/text",
        json={
            'title': 'Notes',
            'text': 'Campaign focused on reducing acquisition waste by aligning messaging with buying committee pain points and clear proof points.',
        },
    ).json()
    client.post(f"/api/sources/{source['id']}/process")

    book = client.post(f"/api/projects/{project['id']}/books", json={'title': 'Marketing Story', 'book_type_id': 'marketing_story'}).json()
    page = client.post(f"/api/books/{book['id']}/pages", json={'page_number': 1, 'user_prompt': 'Why messaging clarity matters'}).json()
    gen = client.post(f"/api/pages/{page['id']}/generate", json={'instruction': 'Professional page', 'content_mode': 'marketing'}).json()
    text = gen['page']['generated_text'].lower()

    assert gen['page']['generation_metadata']['skill_id'] == 'marketing_book_page'
    assert any(term in text for term in ['buying', 'committee', 'acquisition', 'messaging', 'proof'])
    assert not any(term in text for term in ['gunfire', 'bridge', 'chase', 'protagonist'])
    assert not re.search(r'\b\d+\s*%|\$\s*\d+|\b\d{3,}\b', text)
    assert all(marker not in text for marker in ['system:', 'constraints', 'task', 'return only', 'draft page content'])
