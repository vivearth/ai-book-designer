from __future__ import annotations

from fastapi import APIRouter

from app.engines.llm_engine import LLMEngine

router = APIRouter(prefix="/llm", tags=["llm"])
engine = LLMEngine()


@router.get("/status")
async def llm_status():
    return await engine.get_provider_status()


@router.post("/warmup")
async def llm_warmup():
    return await engine.warmup_model()
