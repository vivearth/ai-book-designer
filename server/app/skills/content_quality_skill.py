from __future__ import annotations

import re

from app.skills.base import Skill, SkillContext, SkillResult


class ContentQualitySkill(Skill):
    skill_id = "content_quality"
    name = "Content quality"
    description = "Heuristic quality evaluation for professional page generation"
    version = "1.0"

    def _has_prompt_leakage(self, text: str) -> bool:
        markers = ["SYSTEM:", "BOOK PROFILE", "CONSTRAINTS", "TASK", "Return only", "Draft page content", "{'page_number'", '"task"']
        return any(m.lower() in text.lower() for m in markers)

    async def run(self, input: dict, context: SkillContext) -> SkillResult:  # noqa: A003
        text = input.get("generated_text", "")
        target_words = int(input.get("target_words") or 260)
        direction = (input.get("expected_content_direction") or "").lower()
        source_chunks = context.source_chunks or []
        source_text = " ".join(chunk.text.lower() for chunk in source_chunks)

        flags = {
            "prompt_leakage": self._has_prompt_leakage(text),
            "too_generic": False,
            "off_domain": False,
            "unsupported_claims": False,
            "missing_source_usage": False,
            "too_short": False,
            "too_long": False,
            "wrong_tone": False,
        }
        issues: list[str] = []
        fixes: list[str] = []
        score = 92

        words = re.findall(r"\b\w+\b", text)
        wc = len(words)
        if wc < max(40, int(target_words * 0.45)):
            flags["too_short"] = True
            score -= 15
            issues.append("Draft is shorter than expected word budget.")
        if wc > int(target_words * 1.8):
            flags["too_long"] = True
            score -= 12
            issues.append("Draft exceeds expected page budget.")

        if flags["prompt_leakage"]:
            score -= 45
            issues.append("Prompt leakage markers detected.")
            fixes.append("Regenerate and strip system/context labels.")

        if direction == "marketing" and not re.search(r"marketing|messag|buyer|campaign|position|go-to-market|audience", text.lower()):
            flags["off_domain"] = True
            score -= 20
            issues.append("Expected marketing vocabulary is weak.")
        if direction == "finance" and not re.search(r"finance|cash|forecast|capital|scenario|operating|risk|decision", text.lower()):
            flags["off_domain"] = True
            score -= 20
            issues.append("Expected finance vocabulary is weak.")

        if re.search(r"\b\d+\s*%|\$\s*\d|\b\d{2,}\b", text) and source_text:
            nums = set(re.findall(r"\b\d+(?:\.\d+)?\b", text))
            src_nums = set(re.findall(r"\b\d+(?:\.\d+)?\b", source_text))
            if nums - src_nums:
                flags["unsupported_claims"] = True
                score -= 18
                issues.append("Numeric claim appears unsupported by sources.")

        if source_chunks and len(set(text.lower().split()).intersection(set(source_text.split()))) < 3:
            flags["missing_source_usage"] = True
            score -= 15
            issues.append("Weak overlap with provided source material.")

        if re.search(r"in today's world|it is important to note|journey|heroic", text.lower()):
            flags["too_generic"] = True
            score -= 8

        score = max(0, min(100, score))
        return SkillResult(output={"score": score, "flags": flags, "issues": issues, "suggested_fixes": fixes})
