from __future__ import annotations

from app.models.entities import Book, Page


class LayoutEngine:
    def build_layout(self, *, book: Book, page: Page) -> dict:
        image_count = len(page.images)
        text = page.final_text or page.generated_text or page.user_text or ""
        word_count = len(text.split())

        if image_count == 0:
            composition = "text_only"
        elif image_count == 1 and word_count < 180:
            composition = "hero_image_with_text"
        elif image_count == 1:
            composition = "image_top_text_bottom"
        else:
            composition = "image_grid_with_text"

        return {
            "template": book.layout_template,
            "page_size": book.page_size,
            "composition": composition,
            "typography": {
                "body_font": "Serif",
                "heading_font": "Serif",
                "body_size": 11,
                "line_height": 1.35,
            },
            "margins": {
                "top": 54,
                "right": 54,
                "bottom": 54,
                "left": 54,
            },
            "image_policy": {
                "count": image_count,
                "fit": "contain",
                "caption": "show_when_available",
            },
            "estimated_word_count": word_count,
        }
