from __future__ import annotations

from app.engines.layout_validator import LayoutValidator
from app.models.entities import Book, Page


class PageCapacityEngine:
    def __init__(self) -> None:
        self.validator = LayoutValidator()

    def estimate_capacity_words(self, book: Book, page: Page, composition: str) -> int:
        layout = page.layout_json or {}
        elements = layout.get("elements") if isinstance(layout, dict) else None
        if isinstance(elements, list) and elements:
            cap = sum(self.validator.estimate_text_capacity(el, layout.get("typography")) for el in elements if el.get("type") == "text")
            if cap > 0:
                return max(40, cap)
        base = 400 if len(page.images) == 0 else 250
        if composition in {"image-dominant", "image_only"}:
            base = int(base * 0.5)
        return max(40, base)
