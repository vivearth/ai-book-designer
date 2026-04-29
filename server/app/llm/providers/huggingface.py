from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

import httpx

from app.core.config import Settings

from .base import BaseProvider
from .errors import ProviderConfigurationError, ProviderError, ProviderHTTPError, ProviderTimeoutError

logger = logging.getLogger(__name__)


class HuggingFaceProvider(BaseProvider):
    name = "hf"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _require_token(self) -> None:
        if not self.settings.hf_api_token or not self.settings.hf_api_token.strip():
            raise ProviderConfigurationError("HF_API_TOKEN is required when LLM_PROVIDER=hf.")

    def _format_prompt(self, prompt: str) -> str:
        # Keep template support for compatibility, but chat-completions uses messages.
        tpl = self.settings.hf_chat_template
        if tpl == "mistral":
            return f"<s>[INST] {prompt.strip()} [/INST]"
        if tpl == "llama":
            return f"<|begin_of_text|><|user|>\n{prompt.strip()}\n<|assistant|>"
        return prompt

    def _extract_generated(self, payload: Any) -> str:
        if isinstance(payload, dict):
            choices = payload.get("choices")
            if isinstance(choices, list) and choices:
                first = choices[0]
                if isinstance(first, dict):
                    msg = first.get("message")
                    if isinstance(msg, dict) and isinstance(msg.get("content"), str) and msg["content"].strip():
                        return msg["content"].strip()
                    if isinstance(first.get("text"), str) and first["text"].strip():
                        return first["text"].strip()
        preview = self._safe_preview(payload)
        raise ProviderError(f"HF chat response missing choices[0].message.content/text; body_preview={preview}")

    def _safe_preview(self, data: Any) -> str:
        try:
            if isinstance(data, (dict, list)):
                return json.dumps(data, ensure_ascii=False)[:400]
            return str(data)[:400]
        except Exception:
            return "<unavailable>"

    async def generate_text(self, prompt: str, *, temperature: float, model: str, purpose: str | None = None) -> str:
        _ = purpose
        self._require_token()
        url = f"{self.settings.hf_base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.settings.hf_api_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": self._format_prompt(prompt)}],
            "temperature": temperature,
            "max_tokens": self.settings.hf_max_new_tokens,
            "stream": False,
        }
        retriable_statuses = {503}
        handled_statuses = {401, 403, 404, 429, 500, 503}
        async with httpx.AsyncClient(timeout=httpx.Timeout(self.settings.hf_timeout_seconds)) as client:
            for idx in range(max(1, self.settings.hf_retry_attempts)):
                try:
                    resp = await client.post(url, headers=headers, json=payload)
                    if resp.status_code in retriable_statuses and idx < self.settings.hf_retry_attempts - 1:
                        wait = self.settings.hf_retry_backoff_seconds
                        try:
                            body = resp.json()
                            if isinstance(body, dict):
                                est = body.get("estimated_time")
                                if est is not None:
                                    wait = max(wait, min(float(est), 20.0))
                        except Exception:
                            pass
                        await asyncio.sleep(wait)
                        continue
                    if resp.status_code >= 400:
                        body_preview = (resp.text or "")[:400]
                        if not body_preview:
                            try:
                                body_preview = self._safe_preview(resp.json())
                            except Exception:
                                body_preview = "<empty error body>"
                        logger.warning("HF request failed status=%s body_preview=%s", resp.status_code, body_preview)
                        if resp.status_code in handled_statuses:
                            raise ProviderHTTPError("HF request failed", status=resp.status_code, body_preview=body_preview)
                        raise ProviderHTTPError("HF request failed", status=resp.status_code, body_preview=body_preview)
                    try:
                        parsed = resp.json()
                    except Exception:
                        raise ProviderError(f"HF response was not valid JSON; body_preview={(resp.text or '')[:400]}")
                    return self._extract_generated(parsed)
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
