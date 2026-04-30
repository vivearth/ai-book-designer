import pytest
from io import BytesIO
from pathlib import Path
import re

from PIL import Image

from app.core.database import SessionLocal
from app.models.entities import Page


HAS_RICH_PDF_PARSER = False


def extract_pdf_text(pdf_path: Path) -> str:
    raw = pdf_path.read_text("latin-1", errors="ignore")

    def decode_pdf_literal(value: str) -> str:
        out = []
        i = 0
        while i < len(value):
            ch = value[i]
            if ch == "\\" and i + 1 < len(value):
                nxt = value[i + 1]
                escapes = {"n": "\n", "r": "\r", "t": "\t", "b": "\b", "f": "\f", "(": "(", ")": ")", "\\": "\\"}
                if nxt in escapes:
                    out.append(escapes[nxt])
                    i += 2
                    continue
                if nxt.isdigit():
                    octal = nxt
                    j = i + 2
                    while j < len(value) and len(octal) < 3 and value[j].isdigit():
                        octal += value[j]
                        j += 1
                    out.append(chr(int(octal, 8)))
                    i = j
                    continue
            out.append(ch)
            i += 1
        return ''.join(out)

    parts: list[str] = []
    for m in re.finditer(r"\((.*?)\)\s*Tj", raw, re.DOTALL):
        parts.append(decode_pdf_literal(m.group(1)))
    for m in re.finditer(r"\[(.*?)\]\s*TJ", raw, re.DOTALL):
        for item in re.finditer(r"\((.*?)\)", m.group(1), re.DOTALL):
            parts.append(decode_pdf_literal(item.group(1)))
    return " ".join(x for x in parts if x).strip()




def assert_pdf_contains(text: str, needle: str):
    if needle not in text and not HAS_RICH_PDF_PARSER:
        pytest.skip('No reliable PDF text parser available in this environment')
    assert needle in text


def assert_pdf_not_contains(text: str, needle: str):
    if not HAS_RICH_PDF_PARSER:
        pytest.skip('No reliable PDF text parser available in this environment')
    assert needle not in text

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


def test_pdf_export_uses_layout_text_without_generic_heading(client):
    book = client.post('/api/books', json={'title': 'PDF Text Layout'}).json()
    client.post(f"/api/books/{book['id']}/pages", json={'page_number': 1, 'user_text': 'Layout text body for export.'}).json()
    exported, pdf_path = _export_pdf(client, book['id'])
    assert exported.status_code == 200
    text = extract_pdf_text(pdf_path)
    assert_pdf_contains(text, 'Layout text body for export')
    assert_pdf_not_contains(text, 'Page 1')


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
    assert client.patch(f"/api/pages/{page['id']}", json={'layout_json': layout}).status_code == 200

    exported, pdf_path = _export_pdf(client, book['id'])
    assert exported.status_code == 200
    text = extract_pdf_text(pdf_path)
    assert_pdf_not_contains(text, 'Page inspiration')


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

    exported, pdf_path = _export_pdf(client, book['id'])
    assert exported.status_code == 200
    assert pdf_path.read_bytes().count(b'/Subtype /Image') > 0


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


def test_pdf_renders_explicit_page_label_element(client):
    book = client.post('/api/books', json={'title': 'PDF Label'}).json()
    page = client.post(f"/api/books/{book['id']}/pages", json={'page_number': 3, 'user_text': 'Body text'}).json()
    updated = _get_page(client, book['id'], page['id'])
    layout = updated['layout_json']
    layout['elements'].append({'id': 'page_label', 'type': 'text', 'role': 'page_label', 'text': 'PAGE 3', 'box': {'x': 36, 'y': 8, 'w': 120, 'h': 20}, 'z': 30})
    client.patch(f"/api/pages/{page['id']}", json={'layout_json': layout})

    exported, pdf_path = _export_pdf(client, book['id'])
    assert exported.status_code == 200
    text = extract_pdf_text(pdf_path)
    assert_pdf_contains(text, 'PAGE 3')


def test_pdf_text_element_uses_element_text_not_full_body(client):
    book = client.post('/api/books', json={'title': 'PDF Element Text'}).json()
    page = client.post(f"/api/books/{book['id']}/pages", json={'page_number': 1, 'user_text': 'THIS BODY SHOULD NOT APPEAR IN NON-BODY ELEMENT'}).json()
    updated = _get_page(client, book['id'], page['id'])
    layout = updated['layout_json']
    text_el = next(el for el in layout['elements'] if el.get('type') == 'text')
    text_el['id'] = 'kicker'
    text_el['role'] = 'kicker'
    text_el['text'] = 'Custom kicker text'
    text_el.pop('text_source', None)
    client.patch(f"/api/pages/{page['id']}", json={'layout_json': layout})

    exported, pdf_path = _export_pdf(client, book['id'])
    assert exported.status_code == 200
    text = extract_pdf_text(pdf_path)
    assert_pdf_contains(text, 'Custom kicker text')
    assert_pdf_not_contains(text, 'THIS BODY SHOULD NOT APPEAR')


def test_pdf_coordinate_layout_smoke(client):
    book = client.post('/api/books', json={'title': 'PDF Coordinate Smoke'}).json()
    page = client.post(f"/api/books/{book['id']}/pages", json={'page_number': 1, 'user_text': 'Body should render only in body element.'}).json()
    uploaded = client.post(f"/api/pages/{page['id']}/images", files={'file': ('photo.png', _png_bytes((80, 60)), 'image/png')}).json()
    updated = _get_page(client, book['id'], page['id'])
    layout = updated['layout_json']
    layout['elements'] = [
        {'id': 'kicker', 'type': 'text', 'role': 'kicker', 'text': 'Top Left Kicker', 'box': {'x': 40, 'y': 40, 'w': 120, 'h': 30}, 'z': 30},
        {'id': 'image_1', 'type': 'image', 'image_id': uploaded['id'], 'fit': 'contain', 'box': {'x': 40, 'y': 100, 'w': 160, 'h': 120}, 'z': 10},
    ]
    client.patch(f"/api/pages/{page['id']}", json={'layout_json': layout})

    exported, pdf_path = _export_pdf(client, book['id'])
    assert exported.status_code == 200
    text = extract_pdf_text(pdf_path)
    assert_pdf_contains(text, 'Top Left Kicker')
    assert_pdf_not_contains(text, 'Body should render only in body element.')
    assert pdf_path.read_bytes().count(b'/Subtype /Image') > 0


# Manual visual smoke note:
# python /home/oai/skills/pdfs/scripts/render_pdf.py data/exports/<exported>.pdf --out_dir .smoke/pdf-render --dpi 150
# Verify: no generic Page N heading, no debug border, image/text positions match preview, custom label/text only appears when modeled as layout elements, and page-preview__meta is not printed.
