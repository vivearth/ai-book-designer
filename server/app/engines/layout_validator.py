from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

from fastapi import HTTPException


@dataclass
class LayoutValidationResult:
    valid: bool
    errors: list[str]
    warnings: list[str]
    estimated_text_capacity_words: int
    estimated_text_words: int
    overflow_words: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class LayoutValidator:
    def __init__(self, *, min_gutter: float = 12.0) -> None:
        self.min_gutter = min_gutter

    def boxes_overlap(self, a: dict, b: dict, min_gap: float = 0) -> bool:
        ax1, ay1, ax2, ay2 = a["x"], a["y"], a["x"] + a["w"], a["y"] + a["h"]
        bx1, by1, bx2, by2 = b["x"], b["y"], b["x"] + b["w"], b["y"] + b["h"]
        return not (ax2 + min_gap <= bx1 or bx2 + min_gap <= ax1 or ay2 + min_gap <= by1 or by2 + min_gap <= ay1)

    def estimate_text_capacity(self, element: dict, typography: dict | None) -> int:
        box = element.get("box") or {}
        w, h = float(box.get("w", 0)), float(box.get("h", 0))
        if w <= 0 or h <= 0:
            return 0
        body_size = float((typography or {}).get("body_size", 11))
        line_height = float((typography or {}).get("line_height", 1.5))
        chars_per_line = max(8, int(w / max(4.0, body_size * 0.52)))
        lines = max(1, int(h / max(10.0, body_size * line_height)))
        return max(0, int((chars_per_line * lines) / 5.2))

    def validate_layout(self, layout_json: dict, *, page=None, text: str = "") -> LayoutValidationResult:
        errors: list[str] = []
        warnings: list[str] = []
        if not isinstance(layout_json, dict):
            return LayoutValidationResult(False, ["layout_json must be an object"], [], 0, len(text.split()), 0)
        page_def = layout_json.get("page") or {}
        safe = page_def.get("safe_area") or {"x": 0, "y": 0, "w": page_def.get("width", 1), "h": page_def.get("height", 1)}
        elements = layout_json.get("elements") or []
        if not isinstance(elements, list):
            errors.append("elements must be an array")
            elements = []

        image_elements, text_elements = [], []
        for el in elements:
            if not all(k in el for k in ("id", "type", "box")):
                errors.append("every element must include id, type, box")
                continue
            b = el.get("box") or {}
            if any(k not in b for k in ("x", "y", "w", "h")) or b.get("w", 0) <= 0 or b.get("h", 0) <= 0:
                errors.append(f"element {el.get('id')} has invalid box")
                continue
            if not el.get("bleed"):
                inside = b["x"] >= safe["x"] and b["y"] >= safe["y"] and b["x"] + b["w"] <= safe["x"] + safe["w"] and b["y"] + b["h"] <= safe["y"] + safe["h"]
                if not inside:
                    errors.append(f"element {el['id']} is outside safe area")
            if el.get("type") == "image":
                image_elements.append(el)
            if el.get("type") in {"text", "caption"}:
                text_elements.append(el)

        for t in text_elements:
            for i in image_elements:
                if self.boxes_overlap(t["box"], i["box"], self.min_gutter):
                    errors.append(f"text/caption element {t['id']} overlaps image {i['id']}")
        for i, a in enumerate(text_elements):
            for b in text_elements[i+1:]:
                if self.boxes_overlap(a["box"], b["box"], 0):
                    errors.append(f"text elements {a['id']} and {b['id']} overlap")
        for i, a in enumerate(image_elements):
            for b in image_elements[i+1:]:
                if self.boxes_overlap(a["box"], b["box"], 0):
                    errors.append(f"image elements {a['id']} and {b['id']} overlap")

        page_images = {img.id for img in getattr(page, "images", [])} if page else set()
        if page is not None:
            if page_images and not image_elements:
                warnings.append("page has images but layout has no image elements")
            if not page_images and image_elements:
                errors.append("layout contains image elements but page has no images")
            for el in image_elements:
                image_id = el.get("image_id")
                if image_id not in page_images:
                    errors.append(f"image_id {image_id} does not belong to this page")

        if text.strip() and not any(e.get("type") == "text" for e in elements):
            errors.append("text exists but no text element present")

        cap = sum(self.estimate_text_capacity(el, layout_json.get("typography") or el.get("style")) for el in elements if el.get("type") == "text")
        words = len(text.split())
        overflow = max(0, words - cap)
        if overflow > 0:
            warnings.append("Text may continue to next page.")

        return LayoutValidationResult(not errors, errors, warnings, cap, words, overflow)

    def assert_valid_layout(self, layout_json: dict, *, page=None, text: str = "") -> LayoutValidationResult:
        result = self.validate_layout(layout_json, page=page, text=text)
        if not result.valid:
            raise HTTPException(status_code=400, detail={"message": "Invalid layout", "errors": result.errors})
        return result
