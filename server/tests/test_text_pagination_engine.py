from app.engines.text_pagination_engine import TextPaginationEngine


def test_split_text_for_page_respects_target_and_keeps_overflow():
    engine = TextPaginationEngine()
    sentence = "This is a long sentence designed for pagination behavior testing."
    text = " ".join([sentence for _ in range(70)])

    current, overflow = engine.split_text_for_page(text, 250)

    assert len(current.split()) <= 260
    assert overflow
    assert current.strip().endswith('.')
