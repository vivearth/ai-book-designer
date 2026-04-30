from app.engines.text_pagination_engine import TextPaginationEngine


def test_sentence_boundary_preferred_and_preserves_words():
    e = TextPaginationEngine()
    text = "One short sentence. Two short sentence. Three short sentence."
    current, overflow = e.split_text_for_page(text, 6)
    assert current.endswith('.')
    assert (current + ' ' + overflow).split() == ' '.join(text.split()).split()


def test_comma_fallback_when_no_sentence_mark():
    e = TextPaginationEngine()
    text = "alpha beta gamma, delta epsilon zeta, eta theta iota"
    current, overflow = e.split_text_for_page(text, 6)
    assert current.endswith(',')
    assert (current + ' ' + overflow).split() == text.split()


def test_word_split_fallback_for_long_sentence():
    e = TextPaginationEngine()
    text = ' '.join(['token'] * 40)
    current, overflow = e.split_text_for_page(text, 10)
    assert len(current.split()) == 10
    assert (current + ' ' + overflow).split() == text.split()
