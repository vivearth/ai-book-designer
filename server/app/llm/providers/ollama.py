from __future__ import annotations

import json
import re
from typing import Any

import httpx

from app.core.config import Settings

from .base import BaseProvider
from .errors import ProviderHTTPError, ProviderTimeoutError


class OllamaProvider(BaseProvider):
    name = "ollama"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _infer_target_words(self, prompt: str) -> int | None:
        for pattern in [r"Target visible page budget:\s*(\d+)", r"Target words:\s*(\d+)"]:
            m = re.search(pattern, prompt, flags=re.IGNORECASE)
            if m:
                try:
                    return int(m.group(1))
                except ValueError:
                    pass
        return None

    def _compute_num_predict(self, *, prompt: str, purpose: str | None) -> int:
        inferred = self._infer_target_words(prompt)
        base = self.settings.ollama_num_predict
        if inferred:
            return max(120, min(base, inferred + 60))
        if (purpose or "") in {"quality"}:
            return min(base, 220)
        return base

    async def generate_text(self, prompt: str, *, temperature: float, model: str, purpose: str | None = None) -> str:
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
        try:
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
                return resp.json().get("response", "").strip()
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError(str(exc)) from exc
        except httpx.HTTPStatusError as exc:
            raise ProviderHTTPError(exc.response.text[:400] if exc.response is not None else str(exc)) from exc

    async def get_status(self) -> dict[str, Any]:
        url = f"{self.settings.ollama_base_url.rstrip('/')}/api/tags"
        configured = [self.settings.ollama_model, self.settings.default_llm_model, self.settings.fiction_llm_model, self.settings.marketing_llm_model, self.settings.finance_llm_model, self.settings.general_llm_model, self.settings.quality_llm_model]
        configured_models = [m for m in configured if m]
        try:
            async with httpx.AsyncClient(timeout=min(8, self.settings.ollama_timeout_seconds)) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                payload = resp.json()
            models = [item.get("name") for item in payload.get("models", []) if item.get("name")]
            missing = [m for m in configured_models if m not in models]
            rec = [f"Pull missing configured models: {', '.join(missing)}"] if missing else []
            return {"provider": "ollama", "base_url": self.settings.ollama_base_url, "configured_model": self.settings.ollama_model, "available": True, "models": models, "configured_model_present": self.settings.ollama_model in models, "warmup_recommended": self.settings.ollama_model in models, "recommendations": rec}
        except Exception as exc:  # noqa: BLE001
            return {"provider": "ollama", "base_url": self.settings.ollama_base_url, "configured_model": self.settings.ollama_model, "available": False, "models": [], "configured_model_present": False, "warmup_recommended": True, "recommendations": [f"Unable to reach Ollama /api/tags: {exc}"]}

    async def warmup(self, model: str | None = None) -> dict[str, Any]:
        target_model = model or self.settings.ollama_model
        text = await self.generate_text("Warm up the model. Reply with one word: ready", temperature=0.0, model=target_model, purpose="quality")
        return {"provider": "ollama", "model": target_model, "warmed": True, "response_preview": text[:80]}
