from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BookTypeConfig:
    id: str
    short_label: str
    display_name: str
    description: str
    recommended_mode: str
    allowed_modes: tuple[str, ...]
    default_skill: str
    source_policy: str
    default_format: str
    default_tone: str
    discouraged_modes: tuple[str, ...] = ()
    hard_disabled_modes: tuple[str, ...] = ()


BOOK_TYPES: dict[str, BookTypeConfig] = {
    "fiction_novel": BookTypeConfig("fiction_novel", "Novel", "Fiction Novel", "Long-form narrative fiction.", "classical", ("classical", "expert"), default_skill="fiction_book_page", source_policy="optional", default_format="classic-novel", default_tone="immersive, literary, scene-driven"),
    "memoir_personal_story": BookTypeConfig("memoir_personal_story", "Memoir", "Memoir / Personal Story", "Personal narrative nonfiction.", "classical", ("classical", "expert"), default_skill="fiction_book_page", source_policy="optional", default_format="classic-novel", default_tone="reflective, vivid, honest"),
    "childrens_illustrated_book": BookTypeConfig("childrens_illustrated_book", "Illustrated", "Children’s Illustrated Book", "Short image-led story pages.", "classical", ("classical", "expert"), default_skill="fiction_book_page", source_policy="optional", default_format="illustrated-story", default_tone="warm, playful, clear"),
    "marketing_story": BookTypeConfig("marketing_story", "Marketing", "Marketing Story / Brand Book", "Audience-aware business narrative.", "expert", ("expert", "classical"), default_skill="marketing_book_page", source_policy="recommended", default_format="modern-editorial", default_tone="professional, audience-aware, evidence-led"),
    "finance_explainer": BookTypeConfig("finance_explainer", "Finance", "Finance Explainer", "Practical finance clarity.", "expert", ("expert", "classical"), default_skill="finance_book_page", source_policy="recommended", default_format="modern-editorial", default_tone="precise, practical, careful"),
    "thought_leadership": BookTypeConfig("thought_leadership", "Leadership", "Business Thought Leadership", "Point-of-view business writing.", "expert", ("expert", "classical"), default_skill="general_book_page", source_policy="recommended", default_format="modern-editorial", default_tone="insightful, structured, practical"),
    "case_study_collection": BookTypeConfig("case_study_collection", "Case Study", "Case Study Collection", "Evidence-led case compendium.", "expert", ("expert", "classical"), discouraged_modes=("classical",), default_skill="marketing_book_page", source_policy="required", default_format="modern-editorial", default_tone="clear, practical, concrete"),
    "educational_how_to": BookTypeConfig("educational_how_to", "Guide", "Educational / How-To Book", "Step-by-step practical teaching.", "classical", ("classical", "expert"), default_skill="general_book_page", source_policy="optional", default_format="classic-novel", default_tone="clear, instructive, practical"),
    "custom": BookTypeConfig("custom", "Custom", "Custom", "Custom purpose and style.", "classical", ("classical", "expert"), default_skill="general_book_page", source_policy="optional", default_format="classic-novel", default_tone="balanced"),
}


def get_book_type_config(book_type_id: str | None) -> BookTypeConfig:
    if book_type_id and book_type_id in BOOK_TYPES:
        return BOOK_TYPES[book_type_id]
    return BOOK_TYPES["custom"]
