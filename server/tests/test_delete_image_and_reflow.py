from PIL import Image
from io import BytesIO


def _img_bytes(size=(80, 60)):
    b = BytesIO(); Image.new('RGB', size, color='blue').save(b, format='PNG'); return b.getvalue()


def test_delete_image_rebuilds_layout_and_metadata(client):
    book = client.post('/api/books', json={'title': 'Delete Image'}).json()
    page = client.post(f"/api/books/{book['id']}/pages", json={'page_number': 1, 'generated_text': ' '.join(['word'] * 500)}).json()
    uploaded = client.post(f"/api/pages/{page['id']}/images", files={'file': ('x.png', _img_bytes(), 'image/png')}).json()

    after_delete = client.delete(f"/api/pages/{page['id']}/images/{uploaded['id']}").json()

    assert after_delete['images'] == []
    assert after_delete['layout_json']['composition'] == 'text_only'
    image_ids = [el.get('image_id') for el in after_delete['layout_json'].get('elements', []) if el.get('type') == 'image']
    assert uploaded['id'] not in image_ids
    uploads = (after_delete.get('generation_metadata') or {}).get('image_uploads') or {}
    assert uploaded['id'] not in uploads
