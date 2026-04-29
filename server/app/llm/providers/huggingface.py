from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx

from app.core.config import Settings

from .base import BaseProvider
from .errors import ProviderConfigurationError, ProviderHTTPError, ProviderTimeoutError


class HuggingFaceProvider(BaseProvider):
    name = "hf"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _require_token(self) -> None:
        if not self.settings.hf_api_token or not self.settings.hf_api_token.strip():
            raise ProviderConfigurationError("HF_API_TOKEN is required when LLM_PROVIDER=hf.")

    def _format_prompt(self, prompt: str) -> str:
        tpl = self.settings.hf_chat_template
        if tpl == "mistral":
            return f"<s>[INST] {prompt.strip()} [/INST]"
        if tpl == "llama":
            return f"<|begin_of_text|><|user|>\n{prompt.strip()}\n<|assistant|>"
        return prompt

    def _extract_generated(self, payload: Any) -> str:
        if isinstance(payload, list) and payload:
            for item in payload:
                if isinstance(item, dict) and item.get("generated_text"):
                    return str(item["generated_text"]).strip()
        if isinstance(payload, dict):
            if payload.get("generated_text"):
                return str(payload["generated_text"]).strip()
            if isinstance(payload.get("data"), list):
                for item in payload["data"]:
                    if isinstance(item, dict) and item.get("generated_text"):
                        return str(item["generated_text"]).strip()
        return ""

    async def generate_text(self, prompt: str, *, temperature: float, model: str, purpose: str | None = None) -> str:
        _ = purpose
        self._require_token()
        url = f"{self.settings.hf_base_url.rstrip('/')}/{model}"
        headers = {"Authorization": f"Bearer {self.settings.hf_api_token}"} if self.settings.hf_api_token else {}
        payload = {
            "inputs": self._format_prompt(prompt),
            "parameters": {"temperature": temperature, "max_new_tokens": self.settings.hf_max_new_tokens, "return_full_text": False},
            "options": {"wait_for_model": True},
        }
        timeout = httpx.Timeout(self.settings.hf_timeout_seconds)
        attempts = max(1, self.settings.hf_retry_attempts)
        backoff = self.settings.hf_retry_backoff_seconds
        async with httpx.AsyncClient(timeout=timeout) as client:
            for idx in range(attempts):
                try:
                    resp = await client.post(url, headers=headers, json=payload)
                    if resp.status_code == 503 and idx < attempts - 1:
                        estimated = min(float(resp.json().get("estimated_time", backoff)), 20.0)
                        await asyncio.sleep(max(backoff, estimated))
                        continue
                    resp.raise_for_status()
                    return self._extract_generated(resp.json())
                except httpx.TimeoutException as exc:
                    raise ProviderTimeoutError(str(exc)) from exc
                except httpx.HTTPStatusError as exc:
                    if exc.response.status_code == 503 and idx < attempts - 1:
                        await asyncio.sleep(backoff)
                        continue
                    raise ProviderHTTPError(exc.response.text[:400]) from exc
        raise ProviderHTTPError("HF inference unavailable after retries")

    async def get_status(self) -> dict[str, Any]:
        return {
            "provider": self.name,
            "base_url": self.settings.hf_base_url,
            "configured_model": self.settings.hf_model,
            "token_configured": bool(self.settings.hf_api_token),
            "available": bool(self.settings.hf_api_token),
            "models": [self.settings.hf_model],
            "configured_model_present": bool(self.settings.hf_model),
            "warmup_recommended": False,
            "recommendations": [] if self.settings.hf_api_token else ["Set HF_API_TOKEN to enable Hugging Face Inference API."],
        }

    async def warmup(self, model: str | None = None) -> dict[str, Any]:
        started = time.perf_counter()
        target_model = model or self.settings.hf_model
        text = await self.generate_text("ready?", temperature=0.0, model=target_model, purpose="quality")
        return {"provider": self.name, "model": target_model, "warmed": True, "elapsed_ms": int((time.perf_counter()-started)*1000), "response_preview": text[:80]}
