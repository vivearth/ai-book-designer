from app.engines.layout_engine import LayoutEngine
from app.engines.layout_validator import LayoutValidator


def test_default_text_only_layout_valid(client):
    book=client.post('/api/books',json={'title':'t','book_type_id':'custom'}).json()
    page=client.post(f"/api/books/{book['id']}/pages",json={'page_number':1,'user_text':'hello world '*20}).json()
    from app.services.page_service import PageService
    svc=PageService()
    db=svc  # not used
    client.patch(f"/api/pages/{page['id']}", json={'user_text': 'hello world '*20})
    got=client.get(f"/api/books/{book['id']}/pages").json()[0]
    assert got['layout_json']['layout_schema']=="page-layout-1"
    assert got['layout_json']['validation']['valid'] is True


def test_one_image_layout_valid_no_overlap(client):
    from io import BytesIO
    from PIL import Image
    book=client.post('/api/books',json={'title':'t','book_type_id':'custom'}).json()
    page=client.post(f"/api/books/{book['id']}/pages",json={'page_number':1,'user_text':'hello world '*20}).json()
    b=BytesIO(); Image.new('RGB',(30,30)).save(b,format='PNG'); b.seek(0)
    client.post(f"/api/pages/{page['id']}/images",files={'file':('a.png',b,'image/png')})
    got=client.get(f"/api/books/{book['id']}/pages").json()[0]
    assert got['layout_json']['validation']['valid'] is True


def test_two_image_layout_valid(client):
    from io import BytesIO
    from PIL import Image
    book=client.post('/api/books',json={'title':'t','book_type_id':'custom'}).json()
    page=client.post(f"/api/books/{book['id']}/pages",json={'page_number':1,'user_text':'hello world '*20}).json()
    for i in range(2):
      b=BytesIO(); Image.new('RGB',(30,30)).save(b,format='PNG'); b.seek(0)
      client.post(f"/api/pages/{page['id']}/images",files={'file':(f'a{i}.png',b,'image/png')})
    got=client.get(f"/api/books/{book['id']}/pages").json()[0]
    assert got['layout_json']['validation']['valid'] is True


def test_repaginate_saves_validated_schema_layouts(client):
    book=client.post('/api/books',json={'title':'t','book_type_id':'custom'}).json()
    long='word '*1200
    page=client.post(f"/api/books/{book['id']}/pages",json={'page_number':1,'user_text':long}).json()
    client.patch(f"/api/pages/{page['id']}",json={'user_text':long})
    pages=client.get(f"/api/books/{book['id']}/pages").json()
    assert all(p['layout_json'].get('layout_schema')=="page-layout-1" for p in pages)
    assert all((p['layout_json'].get('validation') or {}).get('valid') is True for p in pages)
