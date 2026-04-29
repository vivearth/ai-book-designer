from io import BytesIO

from PIL import Image


def _img_bytes(size=(2400, 1800), fmt='PNG'):
    img = Image.new('RGB', size, color=(120, 30, 220))
    bio = BytesIO()
    img.save(bio, format=fmt)
    bio.seek(0)
    return bio.getvalue()


def test_upload_rejects_non_image(client):
    book = client.post('/api/books', json={'title': 'T', 'book_type_id': 'custom'}).json()
    page = client.post(f"/api/books/{book['id']}/pages", json={'page_number': 1}).json()
    r = client.post(f"/api/pages/{page['id']}/images", files={'file': ('x.txt', b'notimage', 'text/plain')})
    assert r.status_code == 400


def test_upload_rejects_oversized(monkeypatch, client):
    from app.core.config import get_settings
    get_settings.cache_clear()
    monkeypatch.setenv('MAX_UPLOAD_IMAGE_BYTES', '10')
    book = client.post('/api/books', json={'title': 'T', 'book_type_id': 'custom'}).json()
    page = client.post(f"/api/books/{book['id']}/pages", json={'page_number': 1}).json()
    r = client.post(f"/api/pages/{page['id']}/images", files={'file': ('x.png', _img_bytes((20,20)), 'image/png')})
    assert r.status_code == 413
    monkeypatch.delenv('MAX_UPLOAD_IMAGE_BYTES', raising=False)
    get_settings.cache_clear()


def test_upload_optimizes_and_sets_generation_metadata(client):
    book = client.post('/api/books', json={'title': 'T', 'book_type_id': 'custom'}).json()
    page = client.post(f"/api/books/{book['id']}/pages", json={'page_number': 1, 'generated_text': 'word ' * 350}).json()
    r = client.post(f"/api/pages/{page['id']}/images", files={'file': ('x.png', _img_bytes(), 'image/png')})
    assert r.status_code == 200
    image = r.json()
    assert image['content_type'] in {'image/webp', 'image/png', 'image/jpeg'}
    pages = client.get(f"/api/books/{book['id']}/pages").json()
    p1 = [p for p in pages if p['page_number'] == 1][0]
    assert 'image_uploads' in p1['generation_metadata']
    assert image['id'] in p1['generation_metadata']['image_uploads']


def test_manual_text_edit_repaginates(client):
    book = client.post('/api/books', json={'title': 'T', 'book_type_id': 'fiction_novel'}).json()
    page1 = client.post(f"/api/books/{book['id']}/pages", json={'page_number': 1, 'generated_text': 'word ' * 500}).json()
    r = client.patch(f"/api/pages/{page1['id']}", json={'generated_text': 'word ' * 600})
    assert r.status_code == 200
    updated = r.json()
    assert 'pagination' in updated['generation_metadata']
