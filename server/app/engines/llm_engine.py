from __future__ import annotations

import json
import re
from typing import Any

import httpx

from app.core.config import get_settings


class LLMEngine:
    """Provider adapter for local/mock generation.

    The product should depend on this interface, not on a specific model vendor.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    async def generate_text(self, prompt: str, *, temperature: float = 0.6) -> tuple[str, list[str]]:
        provider = self.settings.model_provider.lower().strip()
        notes: list[str] = []
        if provider == "ollama":
            try:
                text = await self._ollama_generate(prompt, temperature=temperature)
                sanitized, sanitize_notes = self.sanitize_generated_page_text(text)
                notes.extend(sanitize_notes)
                if sanitized.strip():
                    return sanitized, notes
                notes.append("Prompt leakage was detected and removed; mock generator was used as a recovery fallback.")
                return self._mock_generate(prompt), notes
            except Exception as exc:  # noqa: BLE001
                notes.append(f"Model provider failed; mock generator was used. Details: {exc}")
                return self._mock_generate(prompt), notes
        text = self._mock_generate(prompt)
        sanitized, sanitize_notes = self.sanitize_generated_page_text(text)
        notes.extend(sanitize_notes)
        return sanitized or text, notes

    async def generate_json(self, prompt: str) -> dict[str, Any]:
        response, _ = await self.generate_text(prompt, temperature=0.2)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"raw_response": response}

    async def _ollama_generate(self, prompt: str, *, temperature: float) -> str:
        url = f"{self.settings.ollama_base_url.rstrip('/')}/api/generate"
        payload = {
            "model": self.settings.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
        return data.get("response", "").strip()

    def sanitize_generated_page_text(self, text: str) -> tuple[str, list[str]]:
        notes: list[str] = []
        banned_markers = [
            "SYSTEM:",
            "BOOK PROFILE:",
            "BOOK MEMORY:",
            "RECENT CONTEXT:",
            "USER CURRENT PAGE INPUT:",
            "CONSTRAINTS:",
            "TASK:",
            "Return only",
            "Draft page content",
        ]
        cleaned_lines = []
        removed = False
        for line in text.splitlines():
            if any(line.strip().startswith(marker) for marker in banned_markers):
                removed = True
                continue
            if re.match(r"^[\[{].*[:].*[\]}]$", line.strip()):
                removed = True
                continue
            cleaned_lines.append(line)
        cleaned = "\n".join(cleaned_lines).strip()
        if removed:
            notes.append("Prompt leakage was detected and removed from generated text.")
        return cleaned, notes

    def _extract_field(self, prompt: str, label: str) -> str:
        match = re.search(rf"{re.escape(label)}: (.*)", prompt)
        return match.group(1).strip() if match else ""

    def _mock_generate(self, prompt: str) -> str:
        title = self._extract_field(prompt, "Book title") or "Untitled"
        topic = self._extract_field(prompt, "Book topic") or "the work ahead"
        genre = self._extract_field(prompt, "Genre or content direction").lower()
        direction = self._extract_field(prompt, "Page direction") or "the opening movement"
        rough_text = self._extract_field(prompt, "Rough text") or "The page is still a sketch."

        if genre == "finance":
            return (
                f"{direction} begins with a practical observation: markets rarely reward confusion for very long. "
                f"In this section, the reader is brought directly into {topic}, where the real question is not whether pressure exists, but how disciplined decisions are made inside it. "
                f"{rough_text} The prose should read like a confident finance book page, grounding abstract risk in tangible choices, trade-offs, and consequences. "
                f"By the end of the page, the reader should feel the shape of the problem clearly enough to keep moving deeper into {title}."
            )
        if genre == "marketing":
            return (
                f"{direction} opens on the moment before a message meets its audience. "
                f"Inside {title}, the point is not noise but relevance: {topic}. "
                f"{rough_text} The page reframes the raw material into persuasive, domain-aware prose, connecting audience tension, positioning, and the promise a brand must earn. "
                "It should feel purposeful, contemporary, and grounded in real go-to-market thinking rather than abstract slogan-writing."
            )
        if "fiction" in genre or genre in {"memoir", "children's book", "children’s book", "poetry"}:
            return (
                f"{direction} arrives without warning. {rough_text.capitalize()} The air feels charged, as though the page itself has been waiting for the scene to begin. "
                f"The prose leans into sensory detail and momentum while keeping the emotional thread of {topic} close to the surface. "
                f"By the close of the passage, {title} feels properly underway: tense, specific, and alive with the promise of what follows."
            )
        return (
            f"{direction} begins by clarifying the central idea at stake. {rough_text} "
            f"Rather than repeating planning notes, the page translates them into readable, book-like prose that serves {topic}. "
            f"It should feel composed and intentional, giving the reader one strong step forward inside {title} while preserving continuity for the pages that follow."
        )
