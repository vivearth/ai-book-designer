from __future__ import annotations

from app.models.entities import Book, Page


class LayoutEngine:
    PAGE_SIZES = {"A4": (595, 842), "A5": (420, 595), "square": (700, 700)}

    def build_layout(self, *, book: Book, page: Page, variant: str | None = None) -> dict:
        text = page.final_text or page.generated_text or page.user_text or ""
        words = len(text.split())
        image_ids = [img.id for img in page.images]
        image_count = len(image_ids)
        width, height = self.PAGE_SIZES.get((book.page_size or "A4"), self.PAGE_SIZES["A4"])
        safe = {"x": 36, "y": 36, "w": width - 72, "h": height - 72}
        variant = variant or self._default_variant(image_count, words)
        elements = self._build_elements(variant, safe, image_ids)
        return {
            "schema_version": 2,
            "page": {"width": width, "height": height, "unit": "pt", "safe_area": safe},
            "composition": "text_with_image" if image_count else "text_only",
            "variant": variant,
            "typography": {"body_size": 11, "line_height": 1.5},
            "elements": elements,
        }

    def _default_variant(self, image_count: int, words: int) -> str:
        if image_count == 0:
            return "text_only_classic"
        if image_count == 1:
            return "one_image_top_text_bottom" if words < 120 else "one_image_left_text_right"
        if image_count == 2:
            return "two_image_grid_top_text_bottom"
        return "three_plus_gallery_with_text_block"

    def _build_elements(self, variant: str, safe: dict, image_ids: list[str]) -> list[dict]:
        x, y, w, h = safe["x"], safe["y"], safe["w"], safe["h"]
        g = 12
        els: list[dict] = []
        if variant in {"text_only_classic","text_dominant_with_image_aside"}:
            els.append({"id": "text_main", "type": "text", "role": "body", "box": {"x": x, "y": y, "w": w, "h": h}, "z": 20, "overflow": "continue", "text_source": "generated_text"})
            return els
        if variant == "one_image_top_text_bottom":
            els.append({"id": "image_1", "type": "image", "role": "hero", "image_id": image_ids[0], "box": {"x": x, "y": y, "w": w, "h": h * 0.42}, "z": 10, "fit": "cover"})
            els.append({"id": "text_main", "type": "text", "role": "body", "box": {"x": x, "y": y + h * 0.42 + g, "w": w, "h": h * 0.58 - g}, "z": 20, "overflow": "continue", "text_source": "generated_text"})
            return els
        if variant in {"one_image_left_text_right","one_image_inline_pullout"}:
            iw = w * 0.38
            els.append({"id": "image_1", "type": "image", "role": "illustration", "image_id": image_ids[0], "box": {"x": x, "y": y, "w": iw, "h": h}, "z": 10, "fit": "contain"})
            els.append({"id": "text_main", "type": "text", "role": "body", "box": {"x": x + iw + g, "y": y, "w": w - iw - g, "h": h}, "z": 20, "overflow": "continue", "text_source": "generated_text"})
            return els
        if variant == "one_image_right_text_left":
            iw = w * 0.38
            els.append({"id": "text_main", "type": "text", "role": "body", "box": {"x": x, "y": y, "w": w - iw - g, "h": h}, "z": 20, "overflow": "continue", "text_source": "generated_text"})
            els.append({"id": "image_1", "type": "image", "role": "illustration", "image_id": image_ids[0], "box": {"x": x + w - iw, "y": y, "w": iw, "h": h}, "z": 10, "fit": "contain"})
            return els
        if not image_ids:
            els.append({"id": "text_main", "type": "text", "role": "body", "box": {"x": x, "y": y, "w": w, "h": h}, "z": 20, "overflow": "continue", "text_source": "generated_text"})
            return els
        # fallback multi-image
        rows = 1 if len(image_ids) <= 2 else 2
        img_h = h * 0.4
        img_w = (w - g * (min(len(image_ids), 2)-1)) / min(len(image_ids), 2)
        for idx, iid in enumerate(image_ids[:3]):
            col = idx % 2
            row = idx // 2
            els.append({"id": f"image_{idx+1}", "type": "image", "role": "illustration", "image_id": iid, "box": {"x": x + col * (img_w + g), "y": y + row * (img_h/rows + g), "w": img_w, "h": img_h/rows}, "z": 10, "fit": "cover"})
        text_y = y + img_h + g
        els.append({"id": "text_main", "type": "text", "role": "body", "box": {"x": x, "y": text_y, "w": w, "h": h - (text_y - y)}, "z": 20, "overflow": "continue", "text_source": "generated_text"})
        return els

    def estimate_target_words(self, *, book: Book, page: Page, composition: str | None = None) -> tuple[int, str]:
        target = 260 if len(page.images) else 420
        return target, "deterministic template-based capacity estimate"
