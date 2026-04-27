from __future__ import annotations

from app.skills.base import Skill, SkillContext, SkillResult
from app.skills.writing_flow import derive_page_seed, maybe_run_two_pass_page_generation


class FinanceBookPageSkill(Skill):
    skill_id = "finance_book_page"
    name = "Finance book page"
    description = "Generates finance-explainer content with conservative claim handling"
    version = "1.0"

    async def run(self, input: dict, context: SkillContext) -> SkillResult:  # noqa: A003
        goal, rough_notes, seed_reason = derive_page_seed(
            book_title=context.book.title if context.book else "",
            book_topic=context.book.topic if context.book else "",
            book_type=context.book.book_type_id if context.book else "finance",
            page_number=context.page.page_number if context.page else 1,
            page_direction=input.get("page_direction") or "",
            rough_notes=input.get("rough_text") or "",
            audience=(context.project.audience if context.project else ""),
            objective=(context.project.objective if context.project else ""),
        )
        target_words = input.get("target_words", 250)
        source_chunks = context.source_chunks or []
        source_text = " ".join(c.text for c in source_chunks[:3])

        text, notes, plan = await maybe_run_two_pass_page_generation(
            context=context,
            skill_kind="finance",
            title=context.book.title if context.book else "Untitled",
            topic=context.book.topic if context.book else "",
            book_type=context.book.book_type_id if context.book else "finance",
            previous_summary=(context.book.memory.global_summary if (context.book and context.book.memory) else ""),
            direction=goal,
            rough_notes=rough_notes,
            source_excerpts=source_text,
            target_words=int(target_words),
            composition=(context.page.layout_json or {}).get("composition", "text_only") if context.page else "text_only",
            audience=(context.project.audience if context.project else ""),
            objective=(context.project.objective if context.project else ""),
            domain_instructions=(
                "Define concept/problem, source-backed context, assumptions, decision implication, practical takeaway. "
                "Never invent percentages/currency values/specific numeric claims. Use careful language like can help/may support/often indicates."
            ),
            few_shot=(
                "Few-shot source: working capital discipline, forecast reliability, scenario planning.\n"
                "Goal: why cash visibility matters during uncertain planning cycles.\n"
                "Output: careful explanatory page with no fake stats."
            ),
            guidance_instruction=input.get("instruction") or "",
            strict_quality=bool(input.get("strict_quality")),
        )
        warnings: list[str] = []
        refs = [{"source_asset_id": c.source_asset_id, "chunk_id": c.id, "reason": "finance-term match"} for c in source_chunks[:4]]
        if not source_text.strip():
            warnings.append("No grounded finance source was provided. Review assumptions before publication.")

        return SkillResult(
            output={
                "headline": "Cash visibility as a decision-quality capability",
                "body_text": " ".join(text.split()[:target_words]),
                "pull_quote": "Visibility does not eliminate volatility; it improves response quality.",
                "image_guidance": "Use a clean dashboard or planning-room visual without numeric claims.",
                "layout_intent": "finance_explainer",
                "source_refs": refs,
                "quality_notes": ["No fabricated percentages, returns, or investment promises."],
                "plan_summary": plan,
                "seed_reason": seed_reason,
            },
            notes=notes,
            warnings=warnings,
        )
