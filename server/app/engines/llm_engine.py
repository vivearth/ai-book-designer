from __future__ import annotations

import json
from typing import Any

import httpx

from app.core.config import get_settings


class LLMEngine:
    """Provider adapter for local/mock generation.

    The product should depend on this interface, not on a specific model vendor.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    async def generate_text(self, prompt: str, *, temperature: float = 0.6) -> str:
        provider = self.settings.model_provider.lower().strip()
        if provider == "ollama":
            try:
                return await self._ollama_generate(prompt, temperature=temperature)
            except Exception as exc:  # noqa: BLE001 - POC fallback should be forgiving
                return self._mock_generate(prompt, warning=str(exc))
        return self._mock_generate(prompt)

    async def generate_json(self, prompt: str) -> dict[str, Any]:
        response = await self.generate_text(prompt, temperature=0.2)
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

    def _mock_generate(self, prompt: str, warning: str | None = None) -> str:
        # The mock keeps the POC fully runnable without cloud/API/model dependencies.
        marker = "USER CURRENT PAGE INPUT:"
        user_part = prompt.split(marker, maxsplit=1)[-1].strip() if marker in prompt else prompt[-1500:]
        warning_text = f"\n\n[Mock fallback note: {warning}]" if warning else ""
        return (
            "This page continues the book using the supplied notes while preserving the existing tone, "
            "characters, timeline, and unresolved threads.\n\n"
            "Draft page content:\n"
            f"{user_part[:1200]}\n\n"
            "The scene should be tightened during review, but the generated draft is intentionally structured "
            "as a coherent book page rather than raw notes."
            f"{warning_text}"
        )
