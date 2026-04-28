from __future__ import annotations

import json
import re
import time
from typing import Any

import httpx

from app.core.config import get_settings


class LLMEngine:
    """Provider adapter for local/mock generation.

    The product should depend on this interface, not on a specific model vendor.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    MODEL_PURPOSE_MAP = {
        "fiction": "fiction_llm_model",
        "marketing": "marketing_llm_model",
        "finance": "finance_llm_model",
        "general": "general_llm_model",
        "quality": "quality_llm_model",
    }

    async def generate_text(
        self,
        prompt: str,
        *,
        temperature: float = 0.6,
        model: str | None = None,
        purpose: str | None = None,
    ) -> tuple[str, list[str]]:
        provider = self.settings.model_provider.lower().strip()
        resolved_model, fallback_used = self.resolve_model(model=model, purpose=purpose)
        notes: list[str] = [f"provider={provider}", f"model={resolved_model}"]
        if fallback_used:
            notes.append(f"model_fallback={fallback_used}")
        started = time.perf_counter()
        if provider == "ollama":
            try:
                text = await self._ollama_generate(prompt, temperature=temperature, model=resolved_model, purpose=purpose)
                notes.append(f"llm_elapsed_ms={int((time.perf_counter() - started) * 1000)}")
                sanitized, sanitize_notes = self.sanitize_generated_page_text(text)
                notes.extend(sanitize_notes)
                if sanitized.strip():
                    return sanitized, notes
                notes.append("Prompt leakage was detected and removed; mock generator was used as a recovery fallback.")
                return self._mock_generate(prompt), notes
            except httpx.TimeoutException:
                notes.append(
                    f"Ollama timeout after {self.settings.ollama_timeout_seconds}s model={resolved_model} prompt_chars={len(prompt)}. "
                    "Try smaller model, lower OLLAMA_NUM_CTX/OLLAMA_NUM_PREDICT, or enable LLM_FAST_MODE/mock provider."
                )
                notes.append("Model provider timeout; mock generator was used as fallback.")
                return self._mock_generate(prompt), notes
            except httpx.HTTPStatusError as exc:
                body = exc.response.text[:400] if exc.response is not None else ""
                notes.append(
                    f"Ollama HTTP error status={exc.response.status_code if exc.response else 'unknown'} model={resolved_model} "
                    f"prompt_chars={len(prompt)} body={body}"
                )
                notes.append("Model provider failed; mock generator was used as fallback.")
                return self._mock_generate(prompt), notes
            except Exception as exc:  # noqa: BLE001
                notes.append(f"Model provider failed; mock generator was used. Details: {exc}")
                return self._mock_generate(prompt), notes
        text = self._mock_generate(prompt)
        notes.append(f"llm_elapsed_ms={int((time.perf_counter() - started) * 1000)}")
        sanitized, sanitize_notes = self.sanitize_generated_page_text(text)
        notes.extend(sanitize_notes)
        return sanitized or text, notes

    async def generate_json(self, prompt: str) -> dict[str, Any]:
        response, _ = await self.generate_text(prompt, temperature=0.2)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"raw_response": response}

    async def get_provider_status(self) -> dict[str, Any]:
        provider = self.settings.model_provider.lower().strip()
        if provider == "mock":
            return {
                "provider": "mock",
                "base_url": None,
                "model": self.settings.ollama_model,
                "available": True,
                "models": [],
                "recommendations": ["Mock provider active. Switch MODEL_PROVIDER=ollama to use local models."],
            }

        url = f"{self.settings.ollama_base_url.rstrip('/')}/api/tags"
        configured = [
            self.settings.ollama_model,
            self.settings.default_llm_model,
            self.settings.fiction_llm_model,
            self.settings.marketing_llm_model,
            self.settings.finance_llm_model,
            self.settings.general_llm_model,
            self.settings.quality_llm_model,
        ]
        configured_models = [m for m in configured if m]
        try:
            async with httpx.AsyncClient(timeout=min(8, self.settings.ollama_timeout_seconds)) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                payload = resp.json()
            models = [item.get("name") for item in payload.get("models", []) if item.get("name")]
            missing = [m for m in configured_models if m not in models]
            recommendations = []
            if missing:
                recommendations.append(f"Pull missing configured models: {', '.join(missing)}")
            return {
                "provider": "ollama",
                "base_url": self.settings.ollama_base_url,
                "model": self.settings.ollama_model,
                "available": True,
                "models": models,
                "recommendations": recommendations,
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "provider": "ollama",
                "base_url": self.settings.ollama_base_url,
                "model": self.settings.ollama_model,
                "available": False,
                "models": [],
                "recommendations": [f"Unable to reach Ollama /api/tags: {exc}"],
            }

    def resolve_model(self, *, model: str | None = None, purpose: str | None = None) -> tuple[str, str | None]:
        if model:
            return model, None
        purpose_key = (purpose or "").lower().strip()
        mapped_setting = self.MODEL_PURPOSE_MAP.get(purpose_key)
        if mapped_setting:
            configured = getattr(self.settings, mapped_setting, None)
            if configured:
                return configured, f"{purpose_key}->skill_specific"
        if self.settings.default_llm_model:
            return self.settings.default_llm_model, "default_llm_model"
        return self.settings.ollama_model, "ollama_model"

    def _infer_target_words(self, prompt: str) -> int | None:
        patterns = [r"Target visible page budget:\s*(\d+)", r"Target words:\s*(\d+)"]
        for pattern in patterns:
            match = re.search(pattern, prompt, flags=re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        return None

    def _compute_num_predict(self, *, prompt: str, purpose: str | None) -> int:
        inferred = self._infer_target_words(prompt)
        base = self.settings.ollama_num_predict
        if inferred:
            return max(120, min(base, inferred + 60))
        if (purpose or "") in {"quality"}:
            return min(base, 220)
        return base

    async def _ollama_generate(self, prompt: str, *, temperature: float, model: str, purpose: str | None = None) -> str:
        url = f"{self.settings.ollama_base_url.rstrip('/')}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": self.settings.ollama_stream,
            "keep_alive": self.settings.ollama_keep_alive,
            "options": {
                "temperature": temperature,
                "num_ctx": self.settings.ollama_num_ctx,
                "num_predict": self._compute_num_predict(prompt=prompt, purpose=purpose),
            },
        }
        timeout = httpx.Timeout(self.settings.ollama_timeout_seconds, connect=30.0, read=self.settings.ollama_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as client:
            if self.settings.ollama_stream:
                async with client.stream("POST", url, json=payload) as resp:
                    resp.raise_for_status()
                    chunks: list[str] = []
                    async for line in resp.aiter_lines():
                        if not line.strip():
                            continue
                        item = json.loads(line)
                        if item.get("response"):
                            chunks.append(item["response"])
                        if item.get("done"):
                            break
                return "".join(chunks).strip()

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
        target_words = self._extract_field(prompt, "Target words")

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
        if "fiction" in genre or any(g in genre for g in {"memoir", "children", "poetry", "novel", "story"}):
            base = (
                f"{direction} snaps into motion as the city closes around the protagonist. {rough_text} "
                "Shoes slap wet concrete, horns tear through traffic, and the railing of the bridge rattles under desperate hands. "
                "A shot cracks behind him, then another, and he dives over the edge before fear can finish the thought. "
                "The river hits like broken glass, cold and violent, and he disappears beneath the surface while the shouting above turns to echoes. "
                f"When he rises, coughing, the chase is still alive, and {title} keeps its pulse in every sentence."
            )
            words = base.split()
            try:
                target = max(200, int(float(target_words))) if target_words else 220
            except ValueError:
                target = 220
            filler_blocks = [
                "He cuts through lanes of stalled scooters, vaults crates near the slum road, and follows the dim lights under the bridge where the gunfire cannot aim cleanly.",
                "Each choice costs him speed or safety, and he keeps trading comfort for momentum because hesitation would end the story here.",
                "By the time he reaches the market stairs, the city has become a maze of tin roofs, shouting vendors, and rain-slick rails.",
            ]
            filler_idx = 0
            while len(words) < int(target * 0.85):
                words.extend(filler_blocks[filler_idx % len(filler_blocks)].split())
                filler_idx += 1
            return " ".join(words[:target])
        return (
            f"{direction} begins by clarifying the central idea at stake. {rough_text} "
            f"Rather than repeating planning notes, the page translates them into readable, book-like prose that serves {topic}. "
            f"It should feel composed and intentional, giving the reader one strong step forward inside {title} while preserving continuity for the pages that follow."
        )
