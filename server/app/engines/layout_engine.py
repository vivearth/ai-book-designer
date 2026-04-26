from __future__ import annotations

from app.models.entities import Book, Page


class LayoutEngine:
    def build_layout(self, *, book: Book, page: Page) -> dict:
        image_count = len(page.images)
        text = page.final_text or page.generated_text or page.user_text or ""
        word_count = len(text.split())
        format_settings = book.format_settings or {}
        layout_id = format_settings.get("selected_layout_id") or book.layout_template

        if image_count == 0:
            composition = "text_only"
        elif image_count == 1 and layout_id == "illustrated-story":
            composition = "hero_image_with_text"
        elif image_count == 1 and word_count < 140:
            composition = "hero_image_with_text"
        elif image_count == 1:
            composition = "text_with_image"
        else:
            composition = "image_grid_with_text"

        typography = self._typography_for_layout(layout_id)
        margins = self._margins_for_layout(layout_id)
        target_words, reason = self.estimate_target_words(book=book, page=page, composition=composition)

        return {
            "template": layout_id,
            "page_size": format_settings.get("page_size") or book.page_size,
            "composition": composition,
            "typography": typography,
            "margins": margins,
            "image_policy": {
                "count": image_count,
                "fit": "contain",
                "caption": "show_when_available",
            },
            "estimated_word_count": word_count,
            "target_words": target_words,
            "word_budget_reason": reason,
        }

    def estimate_target_words(self, *, book: Book, page: Page, composition: str | None = None) -> tuple[int, str]:
        format_settings = book.format_settings or {}
        layout_id = format_settings.get("selected_layout_id") or book.layout_template
        page_size = (format_settings.get("page_size") or book.page_size or "A4").lower()
        image_count = len(page.images)
        resolved_composition = composition or self.build_layout(book=book, page=page).get("composition", "text_only")

        budgets = {
            "classic-novel": {"text_only": 470, "text_with_image": 270, "hero_image_with_text": 80, "image_grid_with_text": 110},
            "illustrated-story": {"text_only": 220, "text_with_image": 130, "hero_image_with_text": 45, "image_grid_with_text": 60},
            "modern-editorial": {"text_only": 360, "text_with_image": 210, "hero_image_with_text": 60, "image_grid_with_text": 90},
        }
        size_adjustment = {"a5": 0, "square": -30, "a4": 25}.get(page_size, 0)
        target = budgets.get(layout_id, budgets["classic-novel"]).get(resolved_composition, 320) + size_adjustment
        target = max(40, min(520, target))

        if layout_id == "classic-novel":
            reason = "classic-novel prioritizes prose density and generous margins"
        elif layout_id == "illustrated-story":
            reason = "illustrated-story reserves more of the page for artwork and breathing room"
        else:
            reason = "modern-editorial balances structured text with visual hierarchy"

        if image_count == 0 and resolved_composition == "text_only":
            reason += "; no images were attached so the page can carry more complete text"
        elif image_count > 0:
            reason += f"; {image_count} image(s) reduce the available text area"

        return target, reason

    def _typography_for_layout(self, layout_id: str) -> dict:
        if layout_id == "illustrated-story":
            return {"body_font": "Georgia", "heading_font": "Georgia", "body_size": 10.5, "line_height": 1.55}
        if layout_id == "modern-editorial":
            return {"body_font": "Serif", "heading_font": "Sans", "body_size": 10.8, "line_height": 1.45}
        return {"body_font": "Serif", "heading_font": "Serif", "body_size": 11, "line_height": 1.65}

    def _margins_for_layout(self, layout_id: str) -> dict:
        if layout_id == "illustrated-story":
            return {"top": 42, "right": 42, "bottom": 42, "left": 42}
        if layout_id == "modern-editorial":
            return {"top": 46, "right": 50, "bottom": 46, "left": 50}
        return {"top": 58, "right": 64, "bottom": 58, "left": 64}
