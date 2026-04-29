from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

from app.core.config import get_settings
from app.llm.factory import create_provider
from app.llm.providers.errors import ProviderConfigurationError, ProviderError, ProviderHTTPError, ProviderTimeoutError

logger = logging.getLogger(__name__)


class LLMEngine:
    MODEL_PURPOSE_MAP = {
        "fiction": "fiction_llm_model",
        "marketing": "marketing_llm_model",
        "finance": "finance_llm_model",
        "general": "general_llm_model",
        "quality": "quality_llm_model",
    }

    def __init__(self) -> None:
        self.settings = get_settings()
        self.provider = create_provider(self.settings, mock_generator=self._mock_generate)
        logger.info(
            "LLMEngine initialized provider=%s provider_class=%s provider_default_model=%s hf_token_configured=%s",
            self.settings.active_llm_provider,
            self.provider.__class__.__name__,
            self._provider_default_model(),
            bool((self.settings.hf_api_token or "").strip()),
        )

    async def generate_text(self, prompt: str, *, temperature: float = 0.6, model: str | None = None, purpose: str | None = None) -> tuple[str, list[str]]:
        resolved_model, source = self.resolve_model(model=model, purpose=purpose)
        notes = [f"provider={self.provider.name}", f"model={resolved_model}", f"model_source={source}"]
        started = time.perf_counter()
        logger.info("LLM generate_text provider=%s model=%s purpose=%s prompt_len=%s temperature=%s fallback=%s", self.provider.name, resolved_model, purpose, len(prompt or ""), temperature, self.settings.llm_fallback_to_mock_on_provider_error)
        try:
            text = await self.provider.generate_text(prompt, temperature=temperature, model=resolved_model, purpose=purpose)
        except ProviderConfigurationError:
            raise
        except (ProviderTimeoutError, ProviderHTTPError, ProviderError, Exception) as exc:
            msg = f"LLM provider {self.provider.name} failed for model {resolved_model}: {str(exc)[:400]}"
            if self.provider.name in {"hf", "ollama"} and not self.settings.llm_fallback_to_mock_on_provider_error:
                raise ProviderError(msg) from exc
            notes.extend(["fallback_used=true", f"fallback_reason={str(exc)[:400]}"])
            logger.warning("%s; fallback_to_mock=true", msg)
            return self._mock_generate(prompt), notes
        notes.append(f"llm_elapsed_ms={int((time.perf_counter() - started) * 1000)}")
        sanitized, sanitize_notes = self.sanitize_generated_page_text(text)
        notes.extend(sanitize_notes)
        if sanitized.strip():
            return sanitized, notes
        notes.append("Prompt leakage was detected and removed; mock generator was used as a recovery fallback.")
        return self._mock_generate(prompt), notes

    async def generate_json(self, prompt: str) -> dict[str, Any]:
        response, _ = await self.generate_text(prompt, temperature=0.2)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"raw_response": response}


    async def warmup_model(self, model: str | None = None) -> dict[str, Any]:
        started = time.perf_counter()
        result = await self.provider.warmup(model=model)
        result.setdefault("elapsed_ms", int((time.perf_counter() - started) * 1000))
        return result

    async def get_provider_status(self) -> dict[str, Any]:
        status = await self.provider.get_status()
        resolved_general_model, _ = self.resolve_model(purpose="general")
        status.update({
            "provider": self.settings.active_llm_provider,
            "provider_class": self.provider.__class__.__name__,
            "active_model_default": self._provider_default_model(),
            "resolved_general_model": resolved_general_model,
            "hf_token_configured": bool((self.settings.hf_api_token or "").strip()),
            "hf_base_url": self.settings.hf_base_url,
            "fallback_to_mock_enabled": self.settings.llm_fallback_to_mock_on_provider_error,
        })
        return status

    def resolve_model(self, *, model: str | None = None, purpose: str | None = None) -> tuple[str, str]:
        if model:
            return model, "explicit"
        mapped = self.MODEL_PURPOSE_MAP.get((purpose or "").lower().strip())
        if mapped:
            configured = getattr(self.settings, mapped, None)
            if configured:
                return configured, "skill_specific"
        if self.settings.default_llm_model:
            return self.settings.default_llm_model, "default_llm_model"
        if self.provider.name == "hf":
            return self.settings.hf_model, "hf_model"
        if self.provider.name == "ollama":
            return self.settings.ollama_model, "ollama_model"
        return "mock", "mock_default"

    def _provider_default_model(self) -> str:
        if self.provider.name == "hf":
            return self.settings.hf_model
        if self.provider.name == "ollama":
            return self.settings.ollama_model
        return "mock"

    def sanitize_generated_page_text(self, text: str) -> tuple[str, list[str]]:
        notes=[]
        banned_markers=["SYSTEM:","BOOK PROFILE:","BOOK MEMORY:","RECENT CONTEXT:","USER CURRENT PAGE INPUT:","CONSTRAINTS:","TASK:","Return only","Draft page content"]
        cleaned_lines=[]; removed=False
        for line in text.splitlines():
            if any(line.strip().startswith(marker) for marker in banned_markers): removed=True; continue
            if re.match(r"^[\[{].*[:].*[\]}]$", line.strip()): removed=True; continue
            cleaned_lines.append(line)
        cleaned="\n".join(cleaned_lines).strip()
        if removed: notes.append("Prompt leakage was detected and removed from generated text.")
        return cleaned, notes

    def _extract_field(self, prompt: str, label: str) -> str:
        match = re.search(rf"{re.escape(label)}: (.*)", prompt)
        return match.group(1).strip() if match else ""

    def _mock_generate(self, prompt: str) -> str:
        return "Mock content fallback output."
