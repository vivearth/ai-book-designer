from __future__ import annotations

from app.skills.base import Skill, SkillContext, SkillResult


class FictionBookPageSkill(Skill):
    skill_id = "fiction_book_page"
    name = "Fiction book page"
    description = "Generates narrative fiction pages from page direction, rough notes, book context, and continuity"
    version = "1.0"

    def _expand_mock(self, seed: str, target_words: int, direction: str, rough_text: str) -> str:
        paragraphs = [
            seed.strip(),
            (
                f"{direction} keeps tightening as the street noise rises and every decision has to be made in motion. "
                f"{rough_text} The scene stays close to the body: breath, impact, split-second choices, and the fear of losing one step."
            ),
            "Traffic blurs into horns, shouting, and braking metal while the protagonist pushes through gaps that were never meant for escape.",
            "By the end of the beat, the danger is still active, but the character has earned one fragile breath before the next turn.",
        ]
        result = "\n\n".join([p for p in paragraphs if p])
        words = result.split()
        while len(words) < max(120, int(target_words * 0.7)):
            words.extend((paragraphs[1] + " " + paragraphs[2]).split())
        return " ".join(words[: max(140, int(target_words * 0.95))])

    async def run(self, input: dict, context: SkillContext) -> SkillResult:  # noqa: A003
        book = context.book
        page = context.page
        target_words = int(input.get("target_words") or 320)
        page_direction = input.get("page_direction") or input.get("instruction") or "Continue the scene"
        rough_text = input.get("rough_text") or ""
        memory = (book.memory.global_summary if book and book.memory else "") if book else ""
        recent_pages = []
        if book and getattr(book, "pages", None):
            recent_pages = [p.generated_text or p.final_text or p.user_text or "" for p in book.pages[-2:]]
        recent_text = "\n".join([t for t in recent_pages if t]).strip()
        layout = ""
        if page and page.layout_json:
            layout = f"Composition: {page.layout_json.get('composition', 'text_only')}"

        prompt = f"""
Write narrative fiction prose for a book page.

Book title: {book.title if book else 'Untitled'}
Book topic: {book.topic if book else ''}
Genre or content direction: {book.genre if book else 'fiction'}
Page direction: {page_direction}
Rough text: {rough_text}
Target words: {target_words}
Book memory: {memory}
Recent pages: {recent_text}
{layout}

Requirements:
- Return only reader-facing prose.
- No JSON, labels, or system text.
- Preserve named entities from rough text.
- Keep continuity with memory and recent pages.
- Use sensory detail and clear action.
- Keep prose compact enough to fit a single designed book page.
- Do not repeat sentences or phrase blocks to pad length.
""".strip()

        generated, notes = await context.llm_engine.generate_text(prompt, temperature=0.75)
        text = generated.strip()

        provider = context.llm_engine.settings.model_provider.lower().strip()
        min_words = max(120, int(target_words * 0.5))
        if len(text.split()) < min_words:
            if provider == "mock":
                text = self._expand_mock(text, target_words, page_direction, rough_text)
            else:
                revise_prompt = prompt + "\n\nThe previous draft was too short. Expand the same scene to the target word budget while staying concrete and coherent."
                revised, more_notes = await context.llm_engine.generate_text(revise_prompt, temperature=0.7)
                notes.extend(more_notes)
                if len(revised.split()) > len(text.split()):
                    text = revised

        return SkillResult(
            output={
                "headline": None,
                "body_text": text,
                "pull_quote": None,
                "image_guidance": "Use cinematic scene imagery only if it supports this page.",
                "layout_intent": "narrative_fiction",
                "source_refs": [],
                "quality_notes": ["Narrative scene generated from prompt, memory, and continuity context."],
            },
            notes=notes,
        )
