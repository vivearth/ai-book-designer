from __future__ import annotations

from dataclasses import dataclass

from app.engines.llm_engine import LLMEngine
from app.engines.layout_engine import LayoutEngine
from app.models.entities import Book, Page
from app.engines.layout_validator import LayoutValidator


@dataclass
class LayoutOptionInput:
    book: Book
    page: Page
    text: str
    image_count: int
    page_capacity_hint: dict | None = None
    instructions: str | None = None


class LayoutOptionEngine:
    def __init__(self) -> None:
        self.layout_engine = LayoutEngine()
        self.llm_engine = LLMEngine()
        self.validator = LayoutValidator()

    async def generate_options(self, payload: LayoutOptionInput) -> list[dict]:
        variants = self._variants_for_image_count(payload.image_count)
        out: list[dict] = []
        for idx, variant in enumerate(variants, start=1):
            layout_json = self.layout_engine.build_layout(book=payload.book, page=payload.page, variant=variant)
            result = self.validator.validate_layout(layout_json, page=payload.page, text=payload.text)
            if not result.valid:
                layout_json = self.layout_engine.build_layout(book=payload.book, page=payload.page)
                result = self.validator.validate_layout(layout_json, page=payload.page, text=payload.text)
            layout_json["validation"] = result.to_dict()
            out.append({
                "option_index": idx,
                "label": "Option A" if idx == 1 else "Option B",
                "layout_json": layout_json,
                "preview_metadata": {"variant": layout_json.get("variant"), "validation": result.to_dict()},
                "rationale": f"{layout_json.get('variant')} uses deterministic non-overlapping boxes.",
            })
        return out

    def _variants_for_image_count(self, image_count: int) -> list[str]:
        if image_count <= 0:
            return ["text_only_classic", "text_dominant_with_image_aside"]
        if image_count == 1:
            return ["one_image_top_text_bottom", "one_image_right_text_left"]
        if image_count == 2:
            return ["two_image_grid_top_text_bottom", "two_image_stack_left_text_right"]
        return ["three_plus_gallery_with_text_block", "image_dominant_caption_page"]

    async def _maybe_enhance_rationales(self, payload: LayoutOptionInput, options: list[dict]) -> dict[int, str]:
        provider = self.llm_engine.settings.active_llm_provider.lower().strip()
        if provider != "ollama":
            return {}
        if self.llm_engine.settings.llm_fast_mode:
            return {}
        if not (payload.instructions or "").strip():
            return {}
        prompt = (
            "Suggest one short rationale sentence for each layout option. "
            "Do not rewrite page text. Respond as JSON with keys option_1 and option_2.\n"
            f"Text words: {len(payload.text.split())}. Image count: {payload.image_count}.\n"
            f"Option 1 variant: {options[0]['layout_json']['variant']}.\n"
            f"Option 2 variant: {options[1]['layout_json']['variant']}.\n"
            f"Optional instructions: {(payload.instructions or '').strip()}"
        )
        try:
            response = await self.llm_engine.generate_json(prompt)
            out: dict[int, str] = {}
            if isinstance(response.get("option_1"), str) and response["option_1"].strip():
                out[0] = response["option_1"].strip()
            if isinstance(response.get("option_2"), str) and response["option_2"].strip():
                out[1] = response["option_2"].strip()
            return out
        except Exception:
            return {}
