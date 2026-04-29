from __future__ import annotations

from app.models.entities import Book, Page


class PageCapacityEngine:
    def estimate_capacity_words(self, book: Book, page: Page, composition: str) -> int:
        layout_id = (book.format_settings or {}).get("selected_layout_id", book.layout_template)
        base = 220 if layout_id == "classic-novel" else 180
        if composition == "text-with-image":
            base = int(base * 0.62)
        elif composition in {"image-dominant", "image_only"}:
            base = int(base * 0.28)
        return max(40, int(base * 0.82))
