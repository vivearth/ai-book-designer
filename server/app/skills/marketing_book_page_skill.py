from __future__ import annotations

from app.skills.base import Skill, SkillContext, SkillResult
from app.skills.writing_flow import derive_page_seed, maybe_run_two_pass_page_generation


class MarketingBookPageSkill(Skill):
    skill_id = "marketing_book_page"
    name = "Marketing book page"
    description = "Generates a professional marketing page using source grounding"
    version = "1.0"

    async def run(self, input: dict, context: SkillContext) -> SkillResult:  # noqa: A003
        target_words = input.get("target_words", 260)
        page_goal, rough, seed_reason = derive_page_seed(
            book_title=context.book.title if context.book else "",
            book_topic=context.book.topic if context.book else "",
            book_type=context.book.book_type_id if context.book else "marketing",
            page_number=context.page.page_number if context.page else 1,
            page_direction=input.get("page_direction") or "",
            rough_notes=input.get("rough_text") or "",
            audience=(context.project.audience if context.project else ""),
            objective=(context.project.objective if context.project else ""),
        )
        source_chunks = context.source_chunks or []
        source_text = " ".join(chunk.text for chunk in source_chunks[:3])

        body, notes, plan, prompt_meta = await maybe_run_two_pass_page_generation(
            context=context,
            skill_kind="marketing",
            title=context.book.title if context.book else "Untitled",
            topic=context.book.topic if context.book else "",
            book_type=context.book.book_type_id if context.book else "marketing",
            previous_summary=(context.book.memory.global_summary if (context.book and context.book.memory) else ""),
            direction=page_goal,
            rough_notes=rough,
            source_excerpts=source_text,
            target_words=int(target_words),
            composition=(context.page.layout_json or {}).get("composition", "text_only") if context.page else "text_only",
            audience=(context.project.audience if context.project else ""),
            objective=(context.project.objective if context.project else ""),
            domain_instructions=(
                "Use source-backed professional prose with structure: insight, source-backed context, implication, practical takeaway. "
                "Never invent exact metrics/customer names/numbers. Avoid generic filler and avoid fictional scene narration."
            ),
            few_shot=(
                "Few-shot source: campaign focused on reducing acquisition waste by aligning messaging with buying committee pain points.\n"
                "Goal: why messaging clarity matters in B2B growth.\n"
                "Output: professional, source-concept grounded page."
            ),
            guidance_instruction=input.get("instruction") or "",
            strict_quality=bool(input.get("strict_quality")),
        )
        refs = [{"source_asset_id": c.source_asset_id, "chunk_id": c.id, "reason": "keyword overlap"} for c in source_chunks[:4]]
        warnings: list[str] = []
        if not source_text.strip():
            warnings.append("No source chunks were available; output is conceptual and should be validated.")
        return SkillResult(
            output={
                "headline": "Why messaging clarity compounds growth decisions",
                "body_text": body,
                "pull_quote": "Clarity is a commercial operating choice, not a copywriting preference.",
                "image_guidance": "Use a clean strategy workshop or campaign-planning visual.",
                "layout_intent": "professional_marketing",
                "source_refs": refs,
                "quality_notes": ["Avoid unsupported claims and keep statements evidence-led."],
                "plan_summary": plan,
                "seed_reason": seed_reason,
                "prompt_meta": prompt_meta,
            },
            notes=notes,
            warnings=warnings,
        )
