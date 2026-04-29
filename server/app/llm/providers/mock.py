from __future__ import annotations

from typing import Any

from .base import BaseProvider


class MockProvider(BaseProvider):
    name = "mock"

    async def generate_text(self, prompt: str, *, temperature: float, model: str, purpose: str | None = None) -> str:
        _ = (temperature, model, purpose)
        return f"Mock draft generated from prompt ({len(prompt)} chars)."

    async def get_status(self) -> dict[str, Any]:
        return {
            "provider": "mock",
            "base_url": None,
            "configured_model": None,
            "available": True,
            "models": [],
            "configured_model_present": True,
            "warmup_recommended": False,
            "recommendations": ["Mock provider active. Switch LLM_PROVIDER to ollama or hf."],
        }

    async def warmup(self, model: str | None = None) -> dict[str, Any]:
        _ = model
        return {"provider": "mock", "warmed": True, "message": "Mock provider does not require warmup."}
