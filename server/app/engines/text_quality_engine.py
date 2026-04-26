from __future__ import annotations

import re


class TextQualityEngine:
    def remove_repeated_sentences(self, text: str) -> tuple[str, list[str]]:
        notes: list[str] = []
        normalized = " ".join(text.split())
        if not normalized:
            return "", notes

        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", normalized) if s.strip()]
        if not sentences:
            return normalized, notes

        seen: set[str] = set()
        counts: dict[str, int] = {}
        deduped: list[str] = []
        removed_count = 0
        previous = ""

        for sentence in sentences:
            key = sentence.lower()
            counts[key] = counts.get(key, 0) + 1
            if key in seen:
                removed_count += 1
                continue
            if previous and key == previous:
                removed_count += 1
                continue
            seen.add(key)
            deduped.append(sentence)
            previous = key

        total = len(sentences)
        if any(v >= 3 for v in counts.values()):
            notes.append("A sentence was repeated three or more times and was cleaned.")
        phrase_repeat = re.search(r"(\b\w+\b(?:\s+\b\w+\b){2,6})\s+\1", normalized.lower())
        if phrase_repeat:
            notes.append("Repeated adjacent phrase blocks were detected.")
        if total and (removed_count / total) > 0.2:
            notes.append("Repeated generated sentences were removed.")

        return " ".join(deduped), notes
