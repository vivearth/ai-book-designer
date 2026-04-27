from __future__ import annotations

from app.skills.base import Skill, SkillContext, SkillResult
from app.skills.writing_flow import derive_page_seed, maybe_run_two_pass_page_generation


class FictionBookPageSkill(Skill):
    skill_id = "fiction_book_page"
    name = "Fiction book page"
    description = "Generates narrative fiction pages from page direction, rough notes, book context, and continuity"
    version = "1.0"

    async def run(self, input: dict, context: SkillContext) -> SkillResult:  # noqa: A003
        book = context.book
        page = context.page
        target_words = int(input.get("target_words") or 320)
        page_direction, rough_text, seed_reason = derive_page_seed(
            book_title=book.title if book else "",
            book_topic=book.topic if book else "",
            book_type=book.book_type_id if book else "fiction",
            page_number=page.page_number if page else 1,
            page_direction=input.get("page_direction") or "",
            rough_notes=input.get("rough_text") or "",
            audience=(context.project.audience if context.project else ""),
            objective=(context.project.objective if context.project else ""),
        )
        memory = (book.memory.global_summary if book and book.memory else "") if book else ""
        recent_pages = []
        if book and getattr(book, "pages", None):
            recent_pages = [p.generated_text or p.final_text or p.user_text or "" for p in book.pages[-2:]]
        recent_text = "\n".join([t for t in recent_pages if t]).strip()
        layout = ""
        if page and page.layout_json:
            layout = f"Composition: {page.layout_json.get('composition', 'text_only')}"

        text, notes, plan = await maybe_run_two_pass_page_generation(
            context=context,
            skill_kind="fiction",
            title=book.title if book else "Untitled",
            topic=book.topic if book else "",
            book_type=book.book_type_id if book else "fiction",
            previous_summary=f"{memory}\n{recent_text}".strip(),
            direction=page_direction,
            rough_notes=rough_text,
            source_excerpts="",
            target_words=target_words,
            composition=layout or "text_only",
            domain_instructions=(
                "Write immersive scene prose. Opening motion/emotion, concrete action beats, sensory detail, tension escalation, and a clean handoff end. "
                "Do not summarize abstractly. Do not use marketing/business language unless user notes explicitly require it."
            ),
            few_shot=(
                "Few-shot:\n"
                "Input direction: A chase through traffic. Rough notes: protagonist runs across wet roads, gunfire behind him, jumps from bridge into river.\n"
                "Output style: tense prose with roads, horns, gunshots, bridge, water, breath, fear."
            ),
            guidance_instruction=input.get("instruction") or "",
            strict_quality=bool(input.get("strict_quality")),
        )

        return SkillResult(
            output={
                "headline": f"Page {page.page_number}" if page else None,
                "body_text": text,
                "pull_quote": None,
                "image_guidance": "Use cinematic scene imagery only if it supports this page.",
                "layout_intent": "narrative_fiction",
                "source_refs": [],
                "quality_notes": ["Narrative scene generated from two-pass fiction flow."],
                "plan_summary": plan,
                "seed_reason": seed_reason,
            },
            notes=notes,
        )
