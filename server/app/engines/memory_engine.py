from __future__ import annotations

import re

from sqlalchemy.orm import Session

from app.models.entities import Book, BookMemory, Page


class MemoryEngine:
    def ensure_memory(self, db: Session, book: Book) -> BookMemory:
        if book.memory:
            return book.memory
        memory = BookMemory(
            book_id=book.id,
            global_summary=book.topic or "",
            style_guide={
                "tone": book.tone,
                "target_audience": book.target_audience,
                "writing_style": book.writing_style,
            },
        )
        db.add(memory)
        db.flush()
        return memory

    def update_after_page(self, db: Session, *, book: Book, page: Page) -> BookMemory:
        memory = self.ensure_memory(db, book)
        text = page.final_text or page.generated_text or page.user_text or ""
        if not text.strip():
            return memory

        memory.global_summary = self._rolling_summary(memory.global_summary, page.page_number, text)
        memory.characters = self._merge_items(memory.characters, self._extract_candidate_names(text))
        memory.locations = self._merge_items(memory.locations, self._extract_locations(text))
        memory.timeline = self._append_timeline(memory.timeline, page.page_number, text)
        memory.unresolved_threads = self._merge_items(memory.unresolved_threads, self._extract_threads(text))
        memory.style_guide = {
            **(memory.style_guide or {}),
            "tone": book.tone,
            "target_audience": book.target_audience,
            "writing_style": book.writing_style,
        }
        db.flush()
        return memory

    def _rolling_summary(self, current: str, page_number: int, text: str) -> str:
        snippet = " ".join(text.split())[:500]
        addition = f"Page {page_number}: {snippet}"
        if not current:
            return addition
        combined = f"{current}\n{addition}"
        # Keep memory compact for POC. Later replace with LLM summarization.
        return combined[-3500:]

    def _extract_candidate_names(self, text: str) -> list[dict]:
        names = sorted(set(re.findall(r"\b[A-Z][a-z]{2,}\b", text)))
        stopwords = {"This", "That", "The", "And", "But", "Page", "Draft", "User", "Book"}
        return [{"name": name, "notes": "candidate character/entity"} for name in names if name not in stopwords][:20]

    def _extract_locations(self, text: str) -> list[dict]:
        markers = ["palace", "forest", "city", "village", "room", "school", "temple", "river", "mountain", "observatory"]
        lower = text.lower()
        return [{"name": marker, "notes": "mentioned location"} for marker in markers if marker in lower]

    def _extract_threads(self, text: str) -> list[dict]:
        lower = text.lower()
        cues = ["mystery", "promise", "secret", "missing", "unresolved", "question", "fear", "threat"]
        return [{"thread": cue, "notes": "possible unresolved narrative thread"} for cue in cues if cue in lower]

    def _append_timeline(self, timeline: list, page_number: int, text: str) -> list:
        event = {"page": page_number, "event": " ".join(text.split())[:240]}
        return [*timeline[-100:], event]

    def _merge_items(self, existing: list, new_items: list) -> list:
        seen = {str(item).lower() for item in existing}
        merged = list(existing)
        for item in new_items:
            key = str(item).lower()
            if key not in seen:
                merged.append(item)
                seen.add(key)
        return merged[-100:]
