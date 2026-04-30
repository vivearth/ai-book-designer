import pytest
from io import BytesIO
from pathlib import Path

from PIL import Image

from app.core.database import SessionLocal
from app.models.entities import Page


def _png_bytes(size=(50, 50), color=(0, 150, 220)):
    img = Image.new("RGB", size, color)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _get_page(client, book_id: str, page_id: str) -> dict:
    pages = client.get(f"/api/books/{book_id}/pages").json()
    return next(p for p in pages if p["id"] == page_id)


def _export_pdf(client, book_id: str):
    exported = client.post(f"/api/books/{book_id}/export/pdf", json={"approved_only": False})
    payload = exported.json() if exported.status_code == 200 else None
    pdf_path = (Path("data/exports") / payload["filename"]) if payload else None
    return exported, pdf_path


def _export_pdf_bytes(client, book_id: str) -> bytes:
    exported, pdf_path = _export_pdf(client, book_id)
    assert exported.status_code == 200
    assert pdf_path is not None and pdf_path.exists()
    return pdf_path.read_bytes()


def test_pdf_export_uses_layout_text_without_generic_heading(client):
    book = client.post('/api/books', json={'title': 'PDF Text Layout'}).json()
    client.post(f"/api/books/{book['id']}/pages", json={'page_number': 1, 'user_text': 'Layout text body for export.'}).json()
    pdf_bytes = _export_pdf_bytes(client, book['id'])
    assert b'Page 1' not in pdf_bytes


def test_pdf_export_does_not_render_image_without_layout_image_element(client):
    book = client.post('/api/books', json={'title': 'PDF No Image Element'}).json()
    page = client.post(f"/api/books/{book['id']}/pages", json={'page_number': 1, 'user_text': 'Text only page.'}).json()
    client.post(f"/api/pages/{page['id']}/images", files={'file': ('photo.png', _png_bytes(), 'image/png')})

    updated = _get_page(client, book['id'], page['id'])
    layout = updated['layout_json']
    text_el = next(el for el in layout['elements'] if el.get('type') == 'text')
    layout['composition'] = 'text_only'
    layout['image_policy'] = {'allow_omit_images': True}
    layout['elements'] = [text_el]
    patched = client.patch(f"/api/pages/{page['id']}", json={'layout_json': layout})
    assert patched.status_code == 200

    pdf_bytes = _export_pdf_bytes(client, book['id'])
    assert b'Page inspiration' not in pdf_bytes


def test_pdf_export_renders_image_when_layout_has_image_element(client):
    book = client.post('/api/books', json={'title': 'PDF With Image Element'}).json()
    page = client.post(f"/api/books/{book['id']}/pages", json={'page_number': 1, 'user_text': 'Text with image.'}).json()
    uploaded = client.post(f"/api/pages/{page['id']}/images", files={'file': ('photo.png', _png_bytes(), 'image/png')}).json()

    updated = _get_page(client, book['id'], page['id'])
    layout = updated['layout_json']
    image_elements = [el for el in layout['elements'] if el.get('type') == 'image']
    if not image_elements:
        layout['elements'].insert(0, {'id': 'image_1', 'type': 'image', 'image_id': uploaded['id'], 'fit': 'contain', 'box': {'x': 48, 'y': 48, 'w': 220, 'h': 180}, 'z': 10})
    else:
        image_elements[0]['image_id'] = uploaded['id']
    client.patch(f"/api/pages/{page['id']}", json={'layout_json': layout})

    pdf_bytes = _export_pdf_bytes(client, book['id'])
    assert pdf_bytes.count(b'/Subtype /Image') > 0


def test_pdf_export_rejects_invalid_layout(client):
    book = client.post('/api/books', json={'title': 'PDF Invalid Layout'}).json()
    page = client.post(f"/api/books/{book['id']}/pages", json={'page_number': 1, 'user_text': 'bad layout'}).json()

    with SessionLocal() as db:
        row = db.query(Page).filter(Page.id == page['id']).first()
        row.layout_json = {}
        db.commit()

    exported, _ = _export_pdf(client, book["id"])
    assert exported.status_code == 400
    assert "Page 1 has invalid layout_json" in exported.text


def test_cover_title_fit_with_long_title(client):
    long_title = 'This is an extremely long cover title that should be shortened so it does not overflow cover rendering area'
    book = client.post('/api/books', json={'title': long_title}).json()
    client.post(f"/api/books/{book['id']}/pages", json={'page_number': 1, 'user_text': 'hello'})

    pdf_bytes = _export_pdf_bytes(client, book['id'])
    assert b'This is an extremely long cover title' not in pdf_bytes


# Manual visual smoke note:
# 1) Generate a page with image + text, export PDF, render PDF pages to PNGs.
# 2) Confirm there is no generic heading, no safe-area debug border, and element placement matches preview.
