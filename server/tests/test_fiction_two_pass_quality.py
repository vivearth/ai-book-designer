import re

FORBIDDEN = ['SYSTEM:', 'BOOK PROFILE', 'CONSTRAINTS', 'TASK', 'USER CURRENT PAGE INPUT', 'Return only', 'Draft page content']


def _has_threepeat(text: str) -> bool:
    sentences = [s.strip().lower() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
    return any(sentences.count(s) >= 3 for s in set(sentences))


def test_fiction_two_pass_quality(client):
    book = client.post('/api/books', json={'title': 'Shantaram Run', 'book_type_id': 'fiction_novel'}).json()
    page = client.post(
        f"/api/books/{book['id']}/pages",
        json={
            'page_number': 1,
            'user_prompt': 'A chase sequence',
            'user_text': 'running across roads, traffic, slums, bridges, Shantaram jumps off the bridge into water and people are shooting at him',
        },
    ).json()

    gen = client.post(f"/api/pages/{page['id']}/generate", json={'instruction': 'Write page', 'content_mode': 'fiction'}).json()
    text = gen['page']['generated_text']
    low = text.lower()

    assert gen['page']['generation_metadata']['skill_id'] == 'fiction_book_page'
    assert ('shantaram' in low) or ('protagonist' in low)
    assert ('bridge' in low) or ('water' in low)
    assert ('traffic' in low) or ('road' in low)
    assert ('shoot' in low) or ('gunfire' in low)
    for bad in ['buyers', 'positioning', 'campaign language', 'sales narratives', 'messaging clarity']:
        assert bad not in low
    assert not _has_threepeat(text)
    assert all(token not in text for token in FORBIDDEN)
