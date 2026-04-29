from __future__ import annotations

import re
from typing import Any

from app.skills.base import SkillContext


LEAK_MARKERS = ["SYSTEM:", "BOOK PROFILE", "CONSTRAINTS", "TASK", "Return only", "Draft page content"]
GUIDANCE_LEAK_MARKERS = ["shape this into a polished page", "preserving continuity", "polished page"]


def _word_budget(target_words: int) -> tuple[int, int]:
    max_words = max(60, target_words)
    min_words = max(60, max_words - 40)
    return min_words, max_words


def _extract_terms(text: str, limit: int = 8) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for token in re.findall(r"[A-Za-z][A-Za-z\-']{2,}", text):
        low = token.lower()
        if low in seen:
            continue
        seen.add(low)
        out.append(token)
        if len(out) >= limit:
            break
    return out


def truncate_for_prompt(text: str, max_chars: int) -> tuple[str, bool]:
    if len(text) <= max_chars:
        return text, False
    return f"{text[: max_chars - 3]}...", True


async def build_page_plan(
    *,
    context: SkillContext,
    skill_kind: str,
    book_type: str,
    title: str,
    topic: str,
    previous_summary: str,
    direction: str,
    rough_notes: str,
    source_excerpts: str,
    target_words: int,
    composition: str,
    audience: str,
    objective: str,
    domain_instructions: str,
    few_shot: str,
    guidance_instruction: str = "",
    strict_quality: bool = False,
) -> str:
    topic, _ = truncate_for_prompt(topic or "", 400)
    previous_summary, _ = truncate_for_prompt(previous_summary or "", 800)
    rough_notes, _ = truncate_for_prompt(rough_notes or "", 1000)
    source_excerpts, _ = truncate_for_prompt(source_excerpts or "", 1500)
    min_words, max_words = _word_budget(target_words)
    prompt = f"""
Build a compact page plan with 3-6 beats only (no prose paragraphs).
Book type: {book_type}
Skill: {skill_kind}
Title: {title}
Topic: {topic}
Previous summary: {previous_summary}
Page direction: {direction}
Rough notes: {rough_notes}
Source excerpts: {source_excerpts}
Audience: {audience}
Objective: {objective}
Composition: {composition}
Generation guidance, not page content: {guidance_instruction}
Target visible page budget: {max_words} words (draft prose should be between {min_words} and {max_words}).

Rules:
- Return only bullet beats.
- No JSON.
- No prompt labels.
- No boilerplate.
- Do not quote or paraphrase generation guidance in page content.
{domain_instructions}
{few_shot}
{"Use stricter anti-repetition and source anchoring." if strict_quality else ""}
""".strip()
    plan, _ = await context.llm_engine.generate_text(prompt, temperature=0.3, purpose=skill_kind)
    return plan.strip()


async def write_page_from_plan(
    *,
    context: SkillContext,
    skill_kind: str,
    title: str,
    topic: str,
    direction: str,
    rough_notes: str,
    source_excerpts: str,
    target_words: int,
    composition: str,
    plan_text: str,
    domain_instructions: str,
    few_shot: str,
    guidance_instruction: str = "",
    strict_quality: bool = False,
) -> tuple[str, list[str]]:
    topic, _ = truncate_for_prompt(topic or "", 400)
    rough_notes, _ = truncate_for_prompt(rough_notes or "", 1000)
    source_excerpts, _ = truncate_for_prompt(source_excerpts or "", 1500)
    min_words, max_words = _word_budget(target_words)
    prompt = f"""
Write final reader-facing page prose using the page plan.
Title: {title}
Topic: {topic}
Page direction: {direction}
Rough notes: {rough_notes}
Source excerpts: {source_excerpts}
Composition: {composition}
Generation guidance, not page content: {guidance_instruction}
Plan beats:
{plan_text}

Target visible page budget: {max_words} words.
Write between {min_words} and {max_words} words.
Do not exceed {max_words} words.
Stop at a sentence boundary.
If content needs more room, leave continuation for the next page.
Return only page prose.
No JSON.
No SYSTEM/TASK labels.
No repeated sentences.
Do not quote, paraphrase, or begin the page with the generation guidance.
{domain_instructions}
{few_shot}
{"Use stricter style and avoid filler." if strict_quality else ""}
""".strip()
    return await context.llm_engine.generate_text(prompt, temperature=0.6, purpose=skill_kind)


def _mock_fiction(direction: str, rough: str, target_words: int) -> str:
    terms = _extract_terms(rough + " " + direction, 6)
    actor = next((t for t in terms if t[0].isupper()), "the protagonist")
    beats = [
        f"{actor} bolts into the road as traffic screams past and rain needles his face.",
        "Gunfire cracks behind him, close enough to shave sparks off metal rails and signs.",
        "He cuts through the slum lanes, slipping on wet stone, then grabs the bridge rail with both hands.",
        "Another shot breaks the air, so he throws himself over the edge and drops into dark water.",
        "The river punches the breath from his chest, but he surfaces and keeps moving before the shooters can track him.",
        "A taxi skids sideways, horns blare, and market carts tip as he darts between handlebars and shouting drivers.",
        "He stumbles once, palms scraping asphalt, then uses the impact to launch forward instead of slowing down.",
        "Under the bridge lights, faces blur into shadows and every echo sounds like footsteps gaining on him.",
        "He stays low, coughing river water, and chooses alleys where the crowd can hide his next move.",
        "By the time he reaches the far embankment, fear is still loud, but his focus is louder.",
    ]
    return _fit_words(beats, target_words)


def _mock_marketing(direction: str, rough: str, source: str, target_words: int) -> str:
    source_terms = _extract_terms(source or rough, 7)
    anchor = ", ".join(source_terms[:3]) if source_terms else "buyer pain, message clarity, and proof"
    beats = [
        f"{direction} starts with one operational truth: teams lose momentum when the message ignores real buying friction.",
        f"The source material points to {anchor} as practical signals for shaping campaigns that reduce acquisition waste.",
        "When positioning reflects committee concerns, sales and marketing can carry one coherent narrative through the funnel.",
        "The immediate takeaway is to map stakeholder pain points, align proof to each concern, and review language for clarity before launch.",
    ]
    return _fit_words(beats, target_words)


def _mock_finance(direction: str, rough: str, source: str, target_words: int) -> str:
    terms = _extract_terms(source or rough, 7)
    anchor = ", ".join(terms[:3]) if terms else "working capital, forecast reliability, and scenario planning"
    beats = [
        f"{direction} frames finance as a decision-discipline problem rather than a forecasting contest.",
        f"Across the available material, {anchor} appear as linked capabilities that support better planning under uncertainty.",
        "Clear assumptions help teams compare options early, surface risk sooner, and coordinate operating responses without overclaiming certainty.",
        "A practical next step is to standardize review cadence, document key assumptions, and update scenarios when business conditions shift.",
    ]
    return _fit_words(beats, target_words)


def _mock_general(direction: str, rough: str, topic: str, target_words: int) -> str:
    beats = [
        f"{direction} introduces {topic or 'the core concept'} in plain language and keeps the scope practical.",
        f"{rough or 'The section explains what the concept is, why it matters, and how to apply it step by step.'}",
        "A short example makes the idea concrete, then the page closes with a takeaway the reader can use immediately.",
    ]
    return _fit_words(beats, target_words)


def _fit_words(sentences: list[str], target_words: int) -> str:
    target = max(70, min(target_words + 30, int(target_words * 1.15)))
    min_target = max(60, min(target - 5, target_words + 15))
    words: list[str] = []
    idx = 0
    variations = [
        "The momentum shifts again.",
        "He adjusts before panic can settle.",
        "The scene tightens with each turn.",
        "Noise and danger keep closing in.",
        "There is no safe pause, only movement.",
    ]
    while len(words) < min_target:
        base = sentences[idx % len(sentences)]
        if idx >= len(sentences):
            sentence = f"{variations[idx % len(variations)]} {base.lower()}"
        else:
            sentence = base
        words.extend(sentence.split())
        idx += 1
    text = " ".join(words[:target])
    text = re.sub(r"\s+", " ", text).strip()
    for marker in LEAK_MARKERS:
        text = text.replace(marker, "")
    return text


async def maybe_run_two_pass_page_generation(
    *,
    context: SkillContext,
    skill_kind: str,
    title: str,
    topic: str,
    book_type: str,
    previous_summary: str,
    direction: str,
    rough_notes: str,
    source_excerpts: str,
    target_words: int,
    composition: str,
    audience: str = "",
    objective: str = "",
    domain_instructions: str = "",
    few_shot: str = "",
    guidance_instruction: str = "",
    strict_quality: bool = False,
) -> tuple[str, list[str], str, dict[str, Any]]:
    previous_summary, was_prev_truncated = truncate_for_prompt(previous_summary or "", 800)
    rough_notes, was_rough_truncated = truncate_for_prompt(rough_notes or "", 1000)
    source_excerpts, was_source_truncated = truncate_for_prompt(source_excerpts or "", 1500)
    prompt_meta = {
        "prompt_length_chars": len(previous_summary) + len(rough_notes) + len(source_excerpts) + len(topic or "") + len(direction or ""),
        "prompt_truncated": bool(was_prev_truncated or was_rough_truncated or was_source_truncated),
    }
    if context.llm_engine is None:
        provider = "mock"
    else:
        provider = context.llm_engine.settings.active_llm_provider.lower().strip()
    if context.llm_engine and (context.llm_engine.settings.llm_fast_mode or not context.llm_engine.settings.llm_two_pass_enabled):
        prose, notes = await write_page_from_plan(
            context=context,
            skill_kind=skill_kind,
            title=title,
            topic=topic,
            direction=direction,
            rough_notes=rough_notes,
            source_excerpts=source_excerpts,
            target_words=target_words,
            composition=composition,
            plan_text="Use the page direction and available context directly.",
            domain_instructions=domain_instructions,
            few_shot="",
            guidance_instruction=guidance_instruction,
            strict_quality=strict_quality,
        )
        return prose, notes + ["llm_mode=fast_one_pass"], "fast_mode_no_plan", prompt_meta
    if provider == "mock":
        if skill_kind == "fiction":
            return _mock_fiction(direction, rough_notes, target_words), ["provider=mock", "two_pass=mock"], "mock_plan", prompt_meta
        if skill_kind == "marketing":
            return _mock_marketing(direction, rough_notes, source_excerpts, target_words), ["provider=mock", "two_pass=mock"], "mock_plan", prompt_meta
        if skill_kind == "finance":
            return _mock_finance(direction, rough_notes, source_excerpts, target_words), ["provider=mock", "two_pass=mock"], "mock_plan", prompt_meta
        return _mock_general(direction, rough_notes, topic, target_words), ["provider=mock", "two_pass=mock"], "mock_plan", prompt_meta

    plan = await build_page_plan(
        context=context,
        skill_kind=skill_kind,
        book_type=book_type,
        title=title,
        topic=topic,
        previous_summary=previous_summary,
        direction=direction,
        rough_notes=rough_notes,
        source_excerpts=source_excerpts,
        target_words=target_words,
        composition=composition,
        audience=audience,
        objective=objective,
        domain_instructions=domain_instructions,
        few_shot=few_shot,
        guidance_instruction=guidance_instruction,
        strict_quality=strict_quality,
    )
    prose, notes = await write_page_from_plan(
        context=context,
        skill_kind=skill_kind,
        title=title,
        topic=topic,
        direction=direction,
        rough_notes=rough_notes,
        source_excerpts=source_excerpts,
        target_words=target_words,
        composition=composition,
        plan_text=plan,
        domain_instructions=domain_instructions,
        few_shot=few_shot,
        guidance_instruction=guidance_instruction,
        strict_quality=strict_quality,
    )
    lower = prose.lower()
    if any(marker in lower for marker in GUIDANCE_LEAK_MARKERS):
        cleaned = prose
        for marker in GUIDANCE_LEAK_MARKERS:
            cleaned = re.sub(re.escape(marker), "", cleaned, flags=re.IGNORECASE)
        prose = re.sub(r"\s+", " ", cleaned).strip()
        notes.append("Guidance leakage detected and cleaned from generated prose.")
    return prose, notes, plan, prompt_meta


def derive_page_seed(
    *,
    book_title: str,
    book_topic: str,
    book_type: str,
    page_number: int,
    page_direction: str,
    rough_notes: str,
    audience: str = "",
    objective: str = "",
) -> tuple[str, str, str]:
    direction = (page_direction or "").strip()
    rough = (rough_notes or "").strip()
    if direction or rough:
        return direction or "Continue the book", rough, "user_provided_page_inputs"
    if "fiction" in book_type or "novel" in book_type or "memoir" in book_type:
        return f"Open page {page_number} of {book_title or 'the story'}", f"Setting seed: {book_topic or book_title or 'A character enters a tense moment.'}", "title_topic_seed_fiction"
    professional_seed = " ".join(part for part in [book_topic, objective, audience] if part).strip()
    if professional_seed:
        return f"Open page {page_number} of {book_title or 'the book'}", professional_seed, "title_topic_seed_professional"
    return f"Opening page {page_number}", f"Theme seed from {book_title or 'book concept'}", "minimal_fallback_seed"
