from app.engines.text_quality_engine import TextQualityEngine


def test_repeated_sentences_are_removed_with_warning():
    engine = TextQualityEngine()
    repeated = "Every breath burns. Every breath burns. Every breath burns. The bridge shakes. The bridge shakes."

    cleaned, notes = engine.remove_repeated_sentences(repeated)

    assert cleaned.count("Every breath burns.") == 1
    assert cleaned.count("The bridge shakes.") == 1
    assert any("Repeated generated sentences were removed." in note for note in notes)
