from app.services.page_service import PageService


def test_active_text_field_and_continuation_prefix_helpers_do_not_crash(client):
    service = PageService()
    book = client.post('/api/books', json={'title': 'Helpers'}).json()
    p = client.post(f"/api/books/{book['id']}/pages", json={'page_number': 1, 'user_text': 'draft text'}).json()

    class _Page:
        pass

    page = _Page()
    page.final_text = None
    page.generated_text = 'generated'
    page.user_text = 'user'
    page.generation_metadata = {'continued_from_page_id': p['id']}

    assert service._active_text_field(page) == 'generated_text'
    assert service._existing_continuation_prefix(page) == 'generated'
    page.generation_metadata = {}
    assert service._existing_continuation_prefix(page) is None
