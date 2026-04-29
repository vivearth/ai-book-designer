from __future__ import annotations

from dataclasses import dataclass

from app.engines.llm_engine import LLMEngine
from app.engines.layout_engine import LayoutEngine
from app.models.entities import Book, Page


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

    async def generate_options(self, payload: LayoutOptionInput) -> list[dict]:
        option_specs = self._resolve_option_specs(payload.image_count)
        options: list[dict] = []
        for idx, spec in enumerate(option_specs, start=1):
            options.append(self._build_option(payload, idx, spec))

        rationales = await self._maybe_enhance_rationales(payload, options)
        for idx, rationale in rationales.items():
            options[idx]["rationale"] = rationale
            options[idx]["layout_json"]["rationale"] = rationale
        return options

    def _resolve_option_specs(self, image_count: int) -> list[dict]:
        if image_count <= 0:
            return [
                {
                    "variant": "classic_text_page",
                    "composition": "text_only",
                    "visual_intent": "Calm, book-like reading rhythm with strong margins.",
                    "headline_behavior": "minimal",
                    "density": "comfortable",
                    "text_area": {"x": 0.14, "y": 0.12, "w": 0.72, "h": 0.78, "columns": 1},
                    "image_slots": [],
                    "typography": {"scale": "book", "body_size": 11, "line_height": 1.62, "heading_weight": 600},
                    "margins": {"top": 72, "right": 80, "bottom": 72, "left": 80},
                    "rationale": "Text-first composition optimized for uninterrupted reading.",
                },
                {
                    "variant": "editorial_text_page",
                    "composition": "text_only",
                    "visual_intent": "Editorial hierarchy with assertive heading and denser body flow.",
                    "headline_behavior": "headline_subhead",
                    "density": "balanced-dense",
                    "text_area": {"x": 0.11, "y": 0.2, "w": 0.78, "h": 0.68, "columns": 1},
                    "image_slots": [],
                    "typography": {"scale": "editorial", "body_size": 10.6, "line_height": 1.5, "heading_weight": 700},
                    "margins": {"top": 56, "right": 62, "bottom": 56, "left": 62},
                    "rationale": "Adds stronger headline treatment while preserving readable prose density.",
                },
            ]
        if image_count == 1:
            return [
                {
                    "variant": "image_top_text_bottom",
                    "composition": "hero_image_with_text",
                    "visual_intent": "Image-led opening with text grounded below the hero visual.",
                    "headline_behavior": "optional_over_image",
                    "density": "balanced",
                    "text_area": {"x": 0.09, "y": 0.58, "w": 0.82, "h": 0.31, "columns": 1},
                    "image_slots": [{"x": 0.09, "y": 0.1, "w": 0.82, "h": 0.42, "fit": "cover"}],
                    "typography": {"scale": "narrative", "body_size": 10.8, "line_height": 1.52, "heading_weight": 650},
                    "margins": {"top": 44, "right": 48, "bottom": 50, "left": 48},
                    "rationale": "Prioritizes visual mood first, then readable body copy.",
                },
                {
                    "variant": "image_side_text_flow",
                    "composition": "text_with_image",
                    "visual_intent": "Split layout balancing narrative text with side image anchor.",
                    "headline_behavior": "inline_heading",
                    "density": "comfortable",
                    "text_area": {"x": 0.09, "y": 0.14, "w": 0.53, "h": 0.74, "columns": 1},
                    "image_slots": [{"x": 0.66, "y": 0.2, "w": 0.25, "h": 0.5, "fit": "cover"}],
                    "typography": {"scale": "book", "body_size": 10.9, "line_height": 1.58, "heading_weight": 600},
                    "margins": {"top": 52, "right": 54, "bottom": 52, "left": 54},
                    "rationale": "Keeps text dominant while using the image as a secondary visual anchor.",
                },
            ]

        return [
            {
                "variant": "full_bleed_image_with_caption",
                "composition": "image_grid_with_text",
                "visual_intent": "Immersive visual plate with compact caption/story strip.",
                "headline_behavior": "caption_led",
                "density": "light",
                "text_area": {"x": 0.08, "y": 0.78, "w": 0.84, "h": 0.14, "columns": 1},
                "image_slots": [{"x": 0.02, "y": 0.02, "w": 0.96, "h": 0.7, "fit": "cover"}],
                "typography": {"scale": "display", "body_size": 10.2, "line_height": 1.42, "heading_weight": 700},
                "margins": {"top": 24, "right": 26, "bottom": 28, "left": 26},
                "rationale": "Gives priority to visuals with concise narrative support.",
            },
            {
                "variant": "framed_image_with_story_panel",
                "composition": "image_grid_with_text",
                "visual_intent": "Gallery-like framed images paired with a stronger text panel.",
                "headline_behavior": "story_panel_heading",
                "density": "balanced",
                "text_area": {"x": 0.07, "y": 0.62, "w": 0.86, "h": 0.27, "columns": 1},
                "image_slots": [
                    {"x": 0.08, "y": 0.1, "w": 0.4, "h": 0.42, "fit": "cover"},
                    {"x": 0.52, "y": 0.1, "w": 0.4, "h": 0.42, "fit": "cover"},
                ],
                "typography": {"scale": "editorial", "body_size": 10.5, "line_height": 1.46, "heading_weight": 650},
                "margins": {"top": 36, "right": 42, "bottom": 42, "left": 42},
                "rationale": "Balances multiple images with a dedicated narrative panel.",
            },
        ]

    def _build_option(self, payload: LayoutOptionInput, option_index: int, spec: dict) -> dict:
        target_words, reason = self.layout_engine.estimate_target_words(
            book=payload.book,
            page=payload.page,
            composition=spec["composition"],
        )
        if payload.page_capacity_hint and payload.page_capacity_hint.get("estimated_words"):
            target_words = min(target_words, int(payload.page_capacity_hint["estimated_words"]))
        text_words = len((payload.text or "").split())
        warning = ""
        if text_words > target_words:
            warning = "Text may continue to next page."

        layout_json = {
            "composition": spec["composition"],
            "variant": spec["variant"],
            "visual_intent": spec["visual_intent"],
            "text_area": spec["text_area"],
            "image_slots": spec["image_slots"],
            "typography": spec["typography"],
            "margins": spec["margins"],
            "headline_behavior": spec["headline_behavior"],
            "density": spec["density"],
            "estimated_word_capacity": target_words,
            "word_budget_reason": reason,
            "estimated_text_words": text_words,
            "overflow_warning": warning or None,
        }

        return {
            "option_index": option_index,
            "label": "Option A" if option_index == 1 else "Option B",
            "layout_json": layout_json,
            "preview_metadata": {
                "variant": spec["variant"],
                "visual_intent": spec["visual_intent"],
                "estimated_word_capacity": target_words,
                "overflow_warning": warning or None,
            },
            "rationale": spec["rationale"],
        }

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
