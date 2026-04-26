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
        budget = self.estimate_words_that_fit(text, target_words)
        return self.split_on_sentence_boundary(text, budget)
