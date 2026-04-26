from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BookTypeConfig:
    id: str
    display_name: str
    description: str
    default_mode: str
    allowed_modes: tuple[str, ...]
    default_skill: str
    source_policy: str
    default_format: str
    default_tone: str


BOOK_TYPES: dict[str, BookTypeConfig] = {
    "fiction_novel": BookTypeConfig("fiction_novel", "Fiction Novel", "Long-form narrative fiction.", "classical", ("classical", "expert"), "fiction_book_page", "optional", "classic-novel", "immersive, literary, scene-driven"),
    "memoir_personal_story": BookTypeConfig("memoir_personal_story", "Memoir / Personal Story", "Personal narrative nonfiction.", "classical", ("classical", "expert"), "fiction_book_page", "optional", "classic-novel", "reflective, vivid, honest"),
    "childrens_illustrated_book": BookTypeConfig("childrens_illustrated_book", "Children’s Illustrated Book", "Short image-led story pages.", "classical", ("classical", "expert"), "fiction_book_page", "optional", "illustrated-story", "warm, playful, clear"),
    "marketing_story": BookTypeConfig("marketing_story", "Marketing Story / Brand Book", "Audience-aware business narrative.", "expert", ("expert", "classical"), "marketing_book_page", "recommended", "modern-editorial", "professional, audience-aware, evidence-led"),
    "finance_explainer": BookTypeConfig("finance_explainer", "Finance Explainer", "Practical finance clarity.", "expert", ("expert", "classical"), "finance_book_page", "recommended", "modern-editorial", "precise, practical, careful"),
    "thought_leadership": BookTypeConfig("thought_leadership", "Business Thought Leadership", "Point-of-view business writing.", "expert", ("expert", "classical"), "marketing_book_page", "recommended", "modern-editorial", "insightful, structured, practical"),
    "case_study_collection": BookTypeConfig("case_study_collection", "Case Study Collection", "Evidence-led case compendium.", "expert", ("expert",), "marketing_book_page", "required", "modern-editorial", "clear, practical, concrete"),
    "educational_how_to": BookTypeConfig("educational_how_to", "Educational / How-To Book", "Step-by-step practical teaching.", "classical", ("classical", "expert"), "fiction_book_page", "optional", "classic-novel", "clear, instructive, practical"),
    "custom": BookTypeConfig("custom", "Custom", "Custom purpose and style.", "classical", ("classical", "expert"), "fiction_book_page", "optional", "classic-novel", "balanced"),
}


def get_book_type_config(book_type_id: str | None) -> BookTypeConfig:
    if book_type_id and book_type_id in BOOK_TYPES:
        return BOOK_TYPES[book_type_id]
    return BOOK_TYPES["custom"]
