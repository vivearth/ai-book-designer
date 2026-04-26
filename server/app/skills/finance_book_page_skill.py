from __future__ import annotations

from app.skills.base import Skill, SkillContext, SkillResult


class FinanceBookPageSkill(Skill):
    skill_id = "finance_book_page"
    name = "Finance book page"
    description = "Generates finance-explainer content with conservative claim handling"
    version = "1.0"

    async def run(self, input: dict, context: SkillContext) -> SkillResult:  # noqa: A003
        goal = input.get("page_direction") or input.get("instruction") or "Explain financial priorities"
        target_words = input.get("target_words", 250)
        source_chunks = context.source_chunks or []
        source_text = " ".join(c.text for c in source_chunks[:3])

        if source_text.strip():
            text = (
                f"{goal}. The advisory material highlights working-capital discipline, forecast reliability, and scenario planning "
                "as linked capabilities. Better cash visibility does not remove uncertainty, but it improves the timing and quality "
                "of operating decisions by clarifying trade-offs earlier in the planning cycle."
            )
            warnings: list[str] = []
            refs = [{"source_asset_id": c.source_asset_id, "chunk_id": c.id, "reason": "finance-term match"} for c in source_chunks[:4]]
        else:
            text = (
                f"{goal}. In the absence of source evidence, this draft stays educational: finance teams benefit from transparent "
                "cash and forecast views because they can test assumptions and respond to risk signals sooner."
            )
            warnings = ["No grounded finance source was provided. Review assumptions before publication."]
            refs = []

        return SkillResult(
            output={
                "headline": "Cash visibility as a decision-quality capability",
                "body_text": " ".join(text.split()[:target_words]),
                "pull_quote": "Visibility does not eliminate volatility; it improves response quality.",
                "image_guidance": "Use a clean dashboard or planning-room visual without numeric claims.",
                "layout_intent": "finance_explainer",
                "source_refs": refs,
                "quality_notes": ["No fabricated percentages, returns, or investment promises."],
            },
            warnings=warnings,
        )
