from io import BytesIO


def test_layout_options_with_image(client):
    book = client.post('/api/books', json={'title': 'Image Layout Test'}).json()
    page = client.post(
        f"/api/books/{book['id']}/pages",
        json={'page_number': 1, 'user_text': 'Caption and short narrative around an image.'},
    ).json()

    upload = client.post(
        f"/api/pages/{page['id']}/images",
        files={'file': ('photo.png', BytesIO(b'fake-image-data'), 'image/png')},
    )
    assert upload.status_code == 200

    generated = client.post(f"/api/pages/{page['id']}/layout-options", json={'option_count': 2}).json()
    variants = [option['layout_json']['variant'] for option in generated['options']]

    assert any('image_' in variant for variant in variants)
    assert len(set(variants)) == 2
