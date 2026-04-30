from __future__ import annotations

from app.engines.layout_validator import LayoutValidator
from app.models.entities import Book, Page


class PageCapacityEngine:
    def __init__(self) -> None:
        self.validator = LayoutValidator()

    def estimate_capacity_words(self, book: Book, page: Page, composition: str) -> int:
        layout = page.layout_json or {}
        if isinstance(layout, dict):
            validation = layout.get("validation") or {}
            cap_from_validation = validation.get("estimated_text_capacity_words")
            if isinstance(cap_from_validation, (int, float)) and cap_from_validation > 0:
                return max(40, int(cap_from_validation))
            elements = layout.get("elements")
            if isinstance(elements, list) and elements:
                cap = sum(self.validator.estimate_text_capacity(el, layout.get("typography")) for el in elements if el.get("type") == "text")
                if cap > 0:
                    return max(40, cap)
        base = 400 if len(page.images) == 0 else 250
        if composition in {"image-dominant", "image_only"}:
            base = int(base * 0.5)
        return max(40, base)
