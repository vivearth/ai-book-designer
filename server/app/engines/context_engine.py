from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.models.entities import Book, Page


class ContextEngine:
    def build_context_packet(
        self,
        db: Session,
        *,
        book: Book,
        page: Page,
        instruction: str | None,
        target_words: int,
        allow_new_characters: bool,
        composition: str,
        word_budget_reason: str,
    ) -> dict[str, Any]:
        previous_pages = (
            db.query(Page)
            .filter(Page.book_id == book.id, Page.page_number < page.page_number)
            .order_by(Page.page_number.desc())
            .limit(5)
            .all()
        )
        previous_pages = list(reversed(previous_pages))
        memory = book.memory
        format_settings = book.format_settings or {}

        return {
            "book": {
                "id": book.id,
                "title": book.title,
                "topic": book.topic,
                "genre": book.genre,
                "tone": book.tone,
                "target_audience": book.target_audience,
                "writing_style": book.writing_style,
                "layout_template": book.layout_template,
                "format_settings": format_settings,
            },
            "memory": {
                "global_summary": memory.global_summary if memory else "",
                "characters": memory.characters if memory else [],
                "locations": memory.locations if memory else [],
                "timeline": memory.timeline if memory else [],
                "rules": memory.rules if memory else [],
                "unresolved_threads": memory.unresolved_threads if memory else [],
                "style_guide": memory.style_guide if memory else {},
            },
            "recent_pages": [
                {
                    "page_number": p.page_number,
                    "text": p.final_text or p.generated_text or p.user_text or "",
                    "status": p.status,
                }
                for p in previous_pages
            ],
            "current_page": {
                "page_number": page.page_number,
                "user_prompt": page.user_prompt,
                "user_text": page.user_text,
                "images": [
                    {
                        "filename": image.original_filename,
                        "caption": image.caption,
                    }
                    for image in page.images
                ],
            },
            "generation_constraints": {
                "instruction": instruction,
                "target_words": target_words,
                "allow_new_characters": allow_new_characters,
                "composition": composition,
                "selected_layout": format_settings.get("selected_layout_id") or book.layout_template,
                "image_count": len(page.images),
                "word_budget_reason": word_budget_reason,
            },
        }

    def to_generation_prompt(self, packet: dict[str, Any]) -> str:
        book = packet["book"]
        memory = packet["memory"]
        current_page = packet["current_page"]
        constraints = packet["generation_constraints"]

        genre = (book.get("genre") or "").strip().lower()
        if genre == "finance":
            genre_instruction = "Write clear finance-focused non-fiction prose with concrete business or investing context, credible terminology, and practical examples unless the page explicitly asks for fiction."
        elif genre == "marketing":
            genre_instruction = "Write marketing-focused non-fiction prose with positioning, audience, campaigns, customer understanding, or go-to-market framing unless the page explicitly asks for fiction."
        elif "fiction" in genre or genre in {"memoir", "children's book", "children’s book", "poetry"}:
            genre_instruction = "Write as book prose appropriate to the genre, staying narrative, immersive, and readable."
        else:
            genre_instruction = "Write structured, readable non-fiction prose suited to a professionally written book page."

        prompt_sections = [
            "You are writing one page of a book.",
            "Return only the finished book page prose.",
            "Do not mention the prompt, constraints, labels, system text, or analysis.",
            "Do not output JSON, bullet analysis, metadata, or section labels unless the page itself naturally needs them.",
            genre_instruction,
            f"Book title: {book.get('title') or 'Untitled'}",
            f"Book topic: {book.get('topic') or 'N/A'}",
            f"Genre or content direction: {book.get('genre') or 'N/A'}",
            f"Tone: {book.get('tone') or 'N/A'}",
            f"Writing style: {book.get('writing_style') or 'N/A'}",
            f"Selected layout: {constraints.get('selected_layout')}",
            f"Page composition: {constraints.get('composition')}",
            f"Target word count: about {constraints.get('target_words')} words",
            f"Word budget reason: {constraints.get('word_budget_reason')}",
            f"Allow new characters: {'yes' if constraints.get('allow_new_characters') else 'no'}",
            f"Instruction for this page: {constraints.get('instruction') or 'Polish the page and keep continuity.'}",
            "Book memory summary:",
            memory.get("global_summary") or "No summary yet.",
            "Known characters:",
            json.dumps(memory.get("characters") or [], ensure_ascii=False),
            "Known locations:",
            json.dumps(memory.get("locations") or [], ensure_ascii=False),
            "Timeline notes:",
            json.dumps(memory.get("timeline") or [], ensure_ascii=False),
            "Unresolved threads:",
            json.dumps(memory.get("unresolved_threads") or [], ensure_ascii=False),
            "Recent pages:",
            json.dumps(packet.get("recent_pages") or [], ensure_ascii=False, indent=2),
            "Current page input:",
            f"Page number: {current_page.get('page_number')}",
            f"Page direction: {current_page.get('user_prompt') or 'N/A'}",
            f"Rough text: {current_page.get('user_text') or 'N/A'}",
            f"Images attached: {len(current_page.get('images') or [])}",
            "Output rules:",
            "Return only the page itself as reader-facing prose.",
            "Do not write headings like BOOK PROFILE, CONSTRAINTS, TASK, or Draft page content.",
            "Do not explain what you are doing.",
        ]
        return "\n\n".join(prompt_sections)
