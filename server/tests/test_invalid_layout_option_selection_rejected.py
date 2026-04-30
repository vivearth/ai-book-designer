
def test_invalid_layout_option_selection_rejected(client):
    book=client.post('/api/books',json={'title':'t','book_type_id':'custom'}).json()
    p1=client.post(f"/api/books/{book['id']}/pages",json={'page_number':1,'user_text':'hello world '*30}).json()
    p2=client.post(f"/api/books/{book['id']}/pages",json={'page_number':2,'user_text':'hello world '*30}).json()
    r1=client.post(f"/api/pages/{p1['id']}/layout-options",json={'preserve_text':True,'option_count':2}).json()['options'][0]
    resp=client.post(f"/api/pages/{p2['id']}/layout-options/{r1['id']}/select")
    assert resp.status_code in (400,404)
