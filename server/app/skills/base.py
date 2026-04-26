from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SkillContext:
    db: Any
    project: Any = None
    book: Any = None
    page: Any = None
    brand_profile: Any = None
    format_profile: Any = None
    source_chunks: list[Any] = field(default_factory=list)
    llm_engine: Any = None
    layout_engine: Any = None


@dataclass
class SkillResult:
    output: dict[str, Any]
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class Skill:
    skill_id = "base"
    version = "1.0"
    name = "Base skill"
    description = "Base skill class"

    async def run(self, input: dict, context: SkillContext) -> SkillResult:  # noqa: A003
        raise NotImplementedError
