from __future__ import annotations

import re
from collections import Counter

from sqlalchemy.orm import Session

from app.models.entities import Project, SourceChunk


class SourceRetrievalEngine:
    def _keywords(self, text: str) -> set[str]:
        words = re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", (text or "").lower())
        stop = {"the", "and", "that", "with", "this", "from", "have", "into", "about", "your", "for"}
        return {w for w in words if w not in stop}

    def retrieve(self, db: Session, *, project_id: str, query: str, limit: int = 8) -> list[SourceChunk]:
        chunks = db.query(SourceChunk).filter(SourceChunk.project_id == project_id).all()
        if not chunks:
            return []
        query_terms = self._keywords(query)
        project = db.get(Project, project_id)
        direction = (project.content_direction.lower() if project else "")

        scored: list[tuple[int, SourceChunk]] = []
        for chunk in chunks:
            chunk_terms = self._keywords(chunk.text)
            overlap = len(query_terms.intersection(chunk_terms))
            tag_tokens = {str(t).lower() for t in (chunk.source_asset.tags or [])}
            bonus = 2 if direction and direction in tag_tokens else 0
            scored.append((overlap + bonus, chunk))
        scored.sort(key=lambda x: x[0], reverse=True)

        best = [chunk for score, chunk in scored if score > 0][:limit]
        if best:
            return best

        # fallback: return most recent chunks when keyword overlap is weak
        recent = Counter({c.id: c.chunk_index for c in chunks})
        _ = recent
        return sorted(chunks, key=lambda c: c.created_at, reverse=True)[: min(limit, len(chunks))]
