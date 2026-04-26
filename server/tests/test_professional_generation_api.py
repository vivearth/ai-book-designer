def assert_no_prompt_leakage(text: str):
    forbidden = ['SYSTEM:', 'BOOK PROFILE', 'CONSTRAINTS', 'TASK', 'Return only', "{'page_number'", 'Draft page content']
    assert all(marker not in text for marker in forbidden)


def assert_domain_alignment(text: str, terms: list[str]):
    lowered = text.lower()
    assert any(term.lower() in lowered for term in terms)


def assert_reasonable_word_count(text: str, min_words: int, max_words: int):
    wc = len(text.split())
    assert min_words <= wc <= max_words


def test_marketing_and_finance_generation(client):
    marketing_project = client.post('/api/projects', json={
        'name': 'Marketing Project', 'content_direction': 'Marketing', 'audience': 'CMOs', 'objective': 'Thought leadership from campaign material'
    }).json()
    client.post(f"/api/projects/{marketing_project['id']}/sources/text", json={
        'title': 'Campaign notes',
        'text': 'Our campaign reduced acquisition waste by improving messaging with buying committee pain points and CFO pressure.',
        'source_type': 'campaign',
    })
    book = client.post(f"/api/projects/{marketing_project['id']}/books", json={'title': 'B2B Messaging Systems'}).json()
    page = client.post(f"/api/books/{book['id']}/pages", json={'page_number': 1, 'user_prompt': 'Write opening page on messaging clarity'}).json()

    gen = client.post(f"/api/pages/{page['id']}/generate", json={'instruction': 'Write opening page about messaging clarity', 'auto_retrieve_sources': True}).json()
    text = gen['page']['generated_text']
    assert_domain_alignment(text, ['messaging', 'buyer', 'campaign', 'acquisition'])
    assert_no_prompt_leakage(text)
    assert_reasonable_word_count(text, 40, 550)
    assert gen['quality_report']['score'] >= 60

    finance_project = client.post('/api/projects', json={
        'name': 'Finance Project', 'content_direction': 'Finance', 'audience': 'CFOs', 'objective': 'Finance explainer from advisory notes'
    }).json()
    client.post(f"/api/projects/{finance_project['id']}/sources/text", json={
        'title': 'Finance note',
        'text': 'Working capital discipline, forecast reliability, and scenario planning improve cash visibility for decisions.',
    })
    fin_book = client.post(f"/api/projects/{finance_project['id']}/books", json={'title': 'Cash Visibility'}).json()
    fin_page = client.post(f"/api/books/{fin_book['id']}/pages", json={'page_number': 1, 'user_prompt': 'Explain cash visibility'}).json()
    fin_gen = client.post(f"/api/pages/{fin_page['id']}/generate", json={'instruction': 'Explain why cash visibility matters'}).json()
    fin_text = fin_gen['page']['generated_text']
    assert_domain_alignment(fin_text, ['cash', 'forecast', 'scenario', 'finance'])
    assert '27%' not in fin_text
    assert fin_gen['source_refs'] is not None


def test_no_source_generation_warning(client):
    project = client.post('/api/projects', json={'name': 'No Source', 'content_direction': 'Marketing'}).json()
    book = client.post(f"/api/projects/{project['id']}/books", json={'title': 'Trust'}).json()
    page = client.post(f"/api/books/{book['id']}/pages", json={'page_number': 1, 'user_prompt': 'Customer trust'}).json()
    gen = client.post(f"/api/pages/{page['id']}/generate", json={'instruction': 'Write about customer trust', 'auto_retrieve_sources': True}).json()
    assert gen['warnings']
