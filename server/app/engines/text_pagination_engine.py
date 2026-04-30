from __future__ import annotations

import re


class TextPaginationEngine:
    def estimate_words_that_fit(self, text: str, target_words: int) -> int:
        word_count = len(text.split())
        return min(word_count, max(1, target_words))

    def split_on_sentence_boundary(self, text: str, max_words: int) -> tuple[str, str]:
        normalized = " ".join(text.split())
        if not normalized:
            return "", ""

        words = normalized.split()
        if len(words) <= max_words:
            return normalized, ""

        sentences = re.split(r"(?<=[.!?])\s+", normalized)
        current: list[str] = []
        count = 0

        for sentence in sentences:
            sentence_words = sentence.split()
            if not sentence_words:
                continue
            if count + len(sentence_words) <= max_words or not current:
                current.append(sentence)
                count += len(sentence_words)
            else:
                break

        if not current:
            return " ".join(words[:max_words]), " ".join(words[max_words:])

        current_text = " ".join(current).strip()
        if len(current_text.split()) < int(max_words * 0.5):
            return " ".join(words[:max_words]), " ".join(words[max_words:])

        consumed = len(current_text.split())
        return current_text, " ".join(words[consumed:]).strip()

    def split_text_for_page(self, text: str, target_words: int) -> tuple[str, str]:
        normalized = " ".join(text.split())
        words = normalized.split()
        budget = self.estimate_words_that_fit(normalized, target_words)
        if len(words) <= budget:
            return normalized, ""
        start = max(1, int(budget * 0.7))
        split_at = budget
        sentence_marks = {".", "!", "?", "।"}
        fallback_marks = {",", ";", ":"}
        for i in range(min(budget, len(words) - 1), start - 1, -1):
            token = words[i - 1].rstrip("\"')]}")
            if token and token[-1] in sentence_marks:
                split_at = i
                break
        else:
            for i in range(min(budget, len(words) - 1), start - 1, -1):
                token = words[i - 1].rstrip("\"')]}")
                if token and token[-1] in fallback_marks:
                    split_at = i
                    break
        current = " ".join(words[:split_at]).strip()
        overflow = " ".join(words[split_at:]).strip()
        return current, overflow
