from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseProvider(ABC):
    name: str

    @abstractmethod
    async def generate_text(self, prompt: str, *, temperature: float, model: str, purpose: str | None = None) -> str:
        raise NotImplementedError

    @abstractmethod
    async def get_status(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def warmup(self, model: str | None = None) -> dict[str, Any]:
        raise NotImplementedError
