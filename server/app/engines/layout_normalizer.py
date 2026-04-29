from __future__ import annotations
from app.engines.layout_engine import LayoutEngine
from app.engines.layout_validator import LayoutValidator
from app.models.entities import Page

class LayoutNormalizer:
    def __init__(self)->None:
        self.engine=LayoutEngine()
        self.validator=LayoutValidator()
    def normalize(self, page: Page) -> dict:
        layout=page.layout_json or {}
        text = page.final_text or page.generated_text or page.user_text or ""
        if isinstance(layout,dict) and layout.get('schema_version')==2 and isinstance(layout.get('elements'),list) and layout.get('elements'):
            result = self.validator.validate_layout(layout, page=page, text=text)
            layout['validation'] = result.to_dict()
            return layout
        rebuilt = self.engine.build_layout(book=page.book,page=page)
        rebuilt['validation'] = self.validator.validate_layout(rebuilt, page=page, text=text).to_dict()
        return rebuilt
