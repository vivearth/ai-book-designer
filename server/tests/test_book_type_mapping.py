from app.core.book_types import BOOK_TYPES, get_book_type_config


def test_book_type_mapping_defaults():
    assert get_book_type_config('fiction_novel').default_mode == 'classical'
    assert get_book_type_config('fiction_novel').default_skill == 'fiction_book_page'
    assert get_book_type_config('marketing_story').default_mode == 'expert'
    assert get_book_type_config('marketing_story').default_skill == 'marketing_book_page'
    assert get_book_type_config('finance_explainer').default_skill == 'finance_book_page'
    assert get_book_type_config('educational_how_to').default_skill == 'general_book_page'
    assert get_book_type_config('custom').default_skill == 'general_book_page'
    assert get_book_type_config('case_study_collection').source_policy in {'required', 'recommended'}
    assert get_book_type_config('childrens_illustrated_book').default_format == 'illustrated-story'
    assert get_book_type_config('unknown').id == 'custom'
    assert len(BOOK_TYPES) >= 9
