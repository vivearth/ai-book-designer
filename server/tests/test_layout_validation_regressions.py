from io import BytesIO


def _mk_png():
    from PIL import Image
    b = BytesIO(); Image.new('RGB',(32,32),(255,0,0)).save(b,format='PNG'); b.seek(0); return b


def test_new_page_has_no_images_when_previous_page_has_image(client):
    book=client.post('/api/books',json={'title':'t','book_type_id':'custom'}).json()
    p1=client.post(f"/api/books/{book['id']}/pages",json={'page_number':1}).json()
    client.post(f"/api/pages/{p1['id']}/images",files={'file':('a.png',_mk_png(),'image/png')})
    p2=client.post(f"/api/books/{book['id']}/pages",json={'page_number':2}).json()
    got=client.get(f"/api/books/{book['id']}/pages").json()
    assert [p for p in got if p['id']==p2['id']][0]['images']==[]


def test_upload_image_mutates_only_target_page(client):
    book=client.post('/api/books',json={'title':'t','book_type_id':'custom'}).json()
    p1=client.post(f"/api/books/{book['id']}/pages",json={'page_number':1}).json()
    p2=client.post(f"/api/books/{book['id']}/pages",json={'page_number':2}).json()
    client.post(f"/api/pages/{p1['id']}/images",files={'file':('a.png',_mk_png(),'image/png')})
    pages=client.get(f"/api/books/{book['id']}/pages").json()
    assert len([p for p in pages if p['id']==p1['id']][0]['images'])==1
    assert len([p for p in pages if p['id']==p2['id']][0]['images'])==0


def test_layout_option_generation_returns_two_valid_options(client):
    book=client.post('/api/books',json={'title':'t','book_type_id':'custom'}).json()
    page=client.post(f"/api/books/{book['id']}/pages",json={'page_number':1,'user_text':'alpha beta gamma '*80}).json()
    client.post(f"/api/pages/{page['id']}/images",files={'file':('a.png',_mk_png(),'image/png')})
    r=client.post(f"/api/pages/{page['id']}/layout-options",json={'preserve_text':True,'option_count':2})
    assert r.status_code==200
    opts=r.json()['options']; assert len(opts)==2
    assert all(o['preview_metadata']['validation']['valid'] for o in opts)


def test_old_layout_without_elements_is_rebuilt_on_write_only(client):
    book=client.post('/api/books',json={'title':'t','book_type_id':'custom'}).json()
    page=client.post(f"/api/books/{book['id']}/pages",json={'page_number':1,'user_text':'x y z'}).json()
    client.patch(f"/api/pages/{page['id']}",json={'layout_json':{'text_area':{'x':0.1}}})
    got=client.get(f"/api/books/{book['id']}/pages").json()[0]
    assert got['layout_json'].get('layout_schema') == 'page-layout-1'
