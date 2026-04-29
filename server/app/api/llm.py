from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.engines.llm_engine import LLMEngine

router = APIRouter(prefix="/llm", tags=["llm"])
engine = LLMEngine()


class LLMTestRequest(BaseModel):
    prompt: str = "Say hello in one sentence."


@router.get("/status")
async def llm_status():
    return await engine.get_provider_status()


@router.post("/warmup")
async def llm_warmup():
    return await engine.warmup_model()


@router.post('/test-generate')
async def llm_test_generate(payload: LLMTestRequest):
    text, notes = await engine.generate_text(payload.prompt, purpose='general', temperature=0.1)
    model, _ = engine.resolve_model(purpose='general')
    return {"text": text, "provider": engine.provider.name, "model": model, "notes": notes, "fallback_used": any('fallback_used=true' in n for n in notes)}
