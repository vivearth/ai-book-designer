from app.engines.page_capacity_engine import PageCapacityEngine
from app.models.entities import Book, Page


def test_capacity_uses_validation_capacity():
    engine = PageCapacityEngine()
    book = Book(title='t', book_type_id='custom')
    page = Page(page_number=1, book=book)
    page.layout_json = {'schema_version': 2, 'validation': {'estimated_text_capacity_words': 333}}
    assert engine.estimate_capacity_words(book, page, 'text_only') == 333


def test_capacity_uses_text_boxes_without_validation():
    engine = PageCapacityEngine()
    book = Book(title='t', book_type_id='custom')
    page = Page(page_number=1, book=book)
    page.layout_json = {'schema_version': 2, 'typography': {'body_size': 11, 'line_height': 1.5}, 'elements': [{'id': 'text_main', 'type': 'text', 'box': {'x': 0, 'y': 0, 'w': 500, 'h': 700}}]}
    assert engine.estimate_capacity_words(book, page, 'text_only') > 40
