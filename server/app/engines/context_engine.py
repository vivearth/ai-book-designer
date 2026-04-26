from __future__ import annotations

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
            },
        }

    def to_generation_prompt(self, packet: dict[str, Any]) -> str:
        return f"""
SYSTEM:
You are an AI book design assistant. Generate one polished book page from the user's rough page input.
Preserve continuity. Do not contradict the book memory. Do not freely change the genre or tone.
If information is insufficient, infer conservatively from the existing context.

BOOK PROFILE:
{packet["book"]}

BOOK MEMORY:
{packet["memory"]}

RECENT CONTEXT:
{packet["recent_pages"]}

USER CURRENT PAGE INPUT:
{packet["current_page"]}

CONSTRAINTS:
{packet["generation_constraints"]}

TASK:
Return only the page text. Keep it suitable for a formatted book page.
""".strip()
