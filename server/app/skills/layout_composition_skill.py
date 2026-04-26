from __future__ import annotations

from app.skills.base import Skill, SkillContext, SkillResult


class LayoutCompositionSkill(Skill):
    skill_id = "layout_composition"
    name = "Layout composition"
    description = "Computes layout composition and word budget"
    version = "1.0"

    async def run(self, input: dict, context: SkillContext) -> SkillResult:  # noqa: A003
        layout_json = context.layout_engine.build_layout(book=context.book, page=context.page)
        return SkillResult(
            output={
                "layout_json": layout_json,
                "composition": layout_json.get("composition"),
                "image_slots": layout_json.get("image_policy", {}).get("count", 0),
                "word_budget": layout_json.get("target_words"),
                "reason": layout_json.get("word_budget_reason"),
            }
        )
