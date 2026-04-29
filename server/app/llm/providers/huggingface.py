from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import httpx

from app.core.config import Settings

from .base import BaseProvider
from .errors import ProviderConfigurationError, ProviderHTTPError, ProviderTimeoutError

logger = logging.getLogger(__name__)


class HuggingFaceProvider(BaseProvider):
    name = "hf"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _require_token(self) -> None:
        if not self.settings.hf_api_token or not self.settings.hf_api_token.strip():
            raise ProviderConfigurationError("HF_API_TOKEN is required when LLM_PROVIDER=hf.")

    def _extract_generated(self, payload: Any) -> str:
        if isinstance(payload, list) and payload and isinstance(payload[0], dict):
            return str(payload[0].get("generated_text") or "").strip()
        if isinstance(payload, dict):
            return str(payload.get("generated_text") or "").strip()
        return ""

    async def generate_text(self, prompt: str, *, temperature: float, model: str, purpose: str | None = None) -> str:
        _ = purpose
        self._require_token()
        url = f"{self.settings.hf_base_url.rstrip('/')}/{model}"
        headers = {"Authorization": f"Bearer {self.settings.hf_api_token}"}
        payload = {"inputs": prompt, "parameters": {"temperature": temperature, "max_new_tokens": self.settings.hf_max_new_tokens, "return_full_text": False}, "options": {"wait_for_model": True}}
        async with httpx.AsyncClient(timeout=httpx.Timeout(self.settings.hf_timeout_seconds)) as client:
            for idx in range(max(1, self.settings.hf_retry_attempts)):
                try:
                    resp = await client.post(url, headers=headers, json=payload)
                    if resp.status_code == 503 and idx < self.settings.hf_retry_attempts - 1:
                        wait = self.settings.hf_retry_backoff_seconds
                        try:
                            wait = max(wait, min(float((resp.json() or {}).get("estimated_time", wait)), 20.0))
                        except Exception:
                            pass
                        await asyncio.sleep(wait)
                        continue
                    if resp.status_code >= 400:
                        body = (resp.text or "")[:400]
                        logger.warning("HF request failed status=%s body_preview=%s", resp.status_code, body)
                        raise ProviderHTTPError("HF request failed", status=resp.status_code, body_preview=body)
                    return self._extract_generated(resp.json())
                except httpx.TimeoutException as exc:
                    raise ProviderTimeoutError(str(exc)) from exc
        raise ProviderHTTPError("HF inference unavailable after retries", status=503)

    async def get_status(self) -> dict[str, Any]:
        return {"available": bool(self.settings.hf_api_token)}

    async def warmup(self, model: str | None = None) -> dict[str, Any]:
        started = time.perf_counter()
        target_model = model or self.settings.hf_model
        text = await self.generate_text("ready?", temperature=0.0, model=target_model, purpose="quality")
        return {"provider": self.name, "model": target_model, "warmed": True, "elapsed_ms": int((time.perf_counter()-started)*1000), "response_preview": text[:80]}
