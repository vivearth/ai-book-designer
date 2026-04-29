from __future__ import annotations
from app.engines.layout_engine import LayoutEngine
from app.models.entities import Page

class LayoutNormalizer:
    def __init__(self)->None:
        self.engine=LayoutEngine()
    def normalize(self, page: Page) -> dict:
        layout=page.layout_json or {}
        if isinstance(layout,dict) and layout.get('schema_version')==2 and isinstance(layout.get('elements'),list) and layout.get('elements'):
            return layout
        return self.engine.build_layout(book=page.book,page=page)
