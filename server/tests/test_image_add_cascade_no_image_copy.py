from io import BytesIO
from PIL import Image


def _img_bytes(size=(120, 90)):
    b = BytesIO(); Image.new('RGB', size, color='red').save(b, format='PNG'); return b.getvalue()


def test_image_add_on_long_text_cascades_without_copying_image_to_next_page(client):
    book = client.post('/api/books', json={'title': 'Cascade Image'}).json()
    p1 = client.post(f"/api/books/{book['id']}/pages", json={'page_number': 1, 'generated_text': ' '.join(['alpha'] * 900)}).json()
    client.post(f"/api/books/{book['id']}/pages", json={'page_number': 2, 'generated_text': 'beta ' * 100}).json()

    img = client.post(f"/api/pages/{p1['id']}/images", files={'file': ('a.png', _img_bytes(), 'image/png')}).json()
    pages = client.get(f"/api/books/{book['id']}/pages").json()
    first = next(p for p in pages if p['id'] == p1['id'])
    second = next(p for p in pages if p['page_number'] == 2)

    assert len(pages) >= 2
    second_ids = [el.get('image_id') for el in second['layout_json'].get('elements', []) if el.get('type') == 'image']
    assert img['id'] not in second_ids
