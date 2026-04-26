def assert_no_prompt_leakage(text: str):
    forbidden = ['SYSTEM:', 'BOOK PROFILE', 'CONSTRAINTS', 'TASK', 'Return only', "{'page_number'", 'Draft page content']
    assert all(marker not in text for marker in forbidden)


def test_fiction_routing_and_output(client):
    book = client.post('/api/books', json={'title': 'Shantaram Run', 'genre': 'Fiction', 'topic': 'Mumbai underworld chase'}).json()
    page = client.post(f"/api/books/{book['id']}/pages", json={
        'page_number': 1,
        'user_prompt': 'A chase sequence',
        'user_text': 'running across roads, traffic, slums, bridges, Shantaram jumps off the bridge into water and people are shooting at him',
    }).json()
    gen = client.post(f"/api/pages/{page['id']}/generate", json={'instruction': 'Write the chase sequence', 'content_mode': 'fiction', 'target_words': 420}).json()
    text = gen['page']['generated_text'].lower()

    assert any(term in text for term in ['chase', 'road', 'traffic', 'bridge', 'water', 'shoot', 'shantaram'])
    for banned in ['messaging clarity', 'buyers', 'positioning', 'campaign language', 'sales narratives', 'source evidence']:
        assert banned not in text
    assert gen['page']['generation_metadata']['skill_id'] == 'fiction_book_page'
    assert_no_prompt_leakage(gen['page']['generated_text'])
    assert len(gen['page']['generated_text'].split()) >= 180
    assert not any('No source material' in w for w in gen['warnings'])


def test_marketing_routing(client):
    project = client.post('/api/projects', json={'name': 'Marketing', 'content_direction': 'Marketing'}).json()
    book = client.post(f"/api/projects/{project['id']}/books", json={'title': 'Demand Engine'}).json()
    page = client.post(f"/api/books/{book['id']}/pages", json={'page_number': 1, 'user_prompt': 'Messaging clarity page'}).json()
    gen = client.post(f"/api/pages/{page['id']}/generate", json={'instruction': 'Write a GTM positioning page', 'content_mode': 'marketing'}).json()

    assert gen['page']['generation_metadata']['skill_id'] == 'marketing_book_page'
    assert any(term in gen['page']['generated_text'].lower() for term in ['messaging', 'buyer', 'campaign', 'position'])


def test_finance_routing(client):
    project = client.post('/api/projects', json={'name': 'Finance', 'content_direction': 'Finance'}).json()
    book = client.post(f"/api/projects/{project['id']}/books", json={'title': 'Cash Control'}).json()
    page = client.post(f"/api/books/{book['id']}/pages", json={'page_number': 1, 'user_prompt': 'Cash visibility'}).json()
    gen = client.post(f"/api/pages/{page['id']}/generate", json={'instruction': 'Explain cash visibility', 'content_mode': 'finance'}).json()

    assert gen['page']['generation_metadata']['skill_id'] == 'finance_book_page'
    assert any(term in gen['page']['generated_text'].lower() for term in ['cash', 'forecast', 'scenario', 'finance'])


def test_explicit_skill_override(client):
    book = client.post('/api/books', json={'title': 'Fictional', 'genre': 'Fiction'}).json()
    page = client.post(f"/api/books/{book['id']}/pages", json={'page_number': 1, 'user_prompt': 'Scene'}).json()
    gen = client.post(f"/api/pages/{page['id']}/generate", json={'instruction': 'Override to marketing', 'skill_id': 'marketing_book_page'}).json()
    assert gen['page']['generation_metadata']['skill_id'] == 'marketing_book_page'


def test_no_source_warning_domain_specific(client):
    fiction = client.post('/api/books', json={'title': 'No Source Story', 'genre': 'Fiction'}).json()
    fiction_page = client.post(f"/api/books/{fiction['id']}/pages", json={'page_number': 1, 'user_prompt': 'Night pursuit'}).json()
    fiction_gen = client.post(f"/api/pages/{fiction_page['id']}/generate", json={'instruction': 'write scene', 'content_mode': 'fiction'}).json()
    assert not any('No source material' in w for w in fiction_gen['warnings'])

    marketing = client.post('/api/books', json={'title': 'No Source Marketing', 'genre': 'Marketing'}).json()
    marketing_page = client.post(f"/api/books/{marketing['id']}/pages", json={'page_number': 1, 'user_prompt': 'Positioning'}).json()
    marketing_gen = client.post(f"/api/pages/{marketing_page['id']}/generate", json={'instruction': 'write page', 'content_mode': 'marketing'}).json()
    assert any('No source material' in w for w in marketing_gen['warnings'])
