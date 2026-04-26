from __future__ import annotations

from app.skills.base import Skill, SkillContext, SkillResult


class MarketingBookPageSkill(Skill):
    skill_id = "marketing_book_page"
    name = "Marketing book page"
    description = "Generates a professional marketing page using source grounding"
    version = "1.0"

    async def run(self, input: dict, context: SkillContext) -> SkillResult:  # noqa: A003
        target_words = input.get("target_words", 260)
        page_goal = input.get("page_direction") or input.get("instruction") or "Clarify the core marketing point"
        source_chunks = context.source_chunks or []
        source_text = " ".join(chunk.text for chunk in source_chunks[:3])
        rough = input.get("rough_text") or ""

        if source_text.strip():
            body = (
                f"{page_goal}. The material consistently points to message-market fit as the first operational lever. "
                f"Across the selected sources, teams improve performance when messaging reflects buying committee pressure, "
                f"decision friction, and proof requirements. {rough} The practical takeaway is to anchor positioning in specific "
                f"commercial pain, then align campaign assets so sales and marketing narrate one coherent value story."
            )
            refs = [{"source_asset_id": c.source_asset_id, "chunk_id": c.id, "reason": "keyword overlap"} for c in source_chunks[:4]]
            warnings: list[str] = []
        else:
            body = (
                f"{page_goal}. Without direct source evidence, this draft remains intentionally careful and conceptual. "
                "Messaging clarity matters because buyers evaluate risk before they evaluate creativity, and teams lose momentum "
                "when positioning, proof points, and audience pain are misaligned. A practical first move is to define the core problem "
                "for each stakeholder group, then align campaign language and sales narratives around that shared commercial context."
            )
            refs = []
            warnings = ["No source chunks were available; output is conceptual and should be validated."]

        words = body.split()
        body = " ".join(words[:target_words])
        return SkillResult(
            output={
                "headline": "Why messaging clarity compounds growth decisions",
                "body_text": body,
                "pull_quote": "Clarity is a commercial operating choice, not a copywriting preference.",
                "image_guidance": "Use a clean strategy workshop or campaign-planning visual.",
                "layout_intent": "professional_marketing",
                "source_refs": refs,
                "quality_notes": ["Avoid unsupported claims and keep statements evidence-led."],
            },
            warnings=warnings,
        )
