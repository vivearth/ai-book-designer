import asyncio

from app.skills import build_skill_registry
from app.skills.base import SkillContext


def test_registry_and_skill_output():
    registry = build_skill_registry()
    listed = registry.list()
    assert 'marketing_book_page' in listed
    assert 'finance_book_page' in listed
    assert 'content_quality' in listed

    skill = registry.get('marketing_book_page')
    result = asyncio.run(skill.run({'page_direction': 'Explain messaging clarity', 'target_words': 120}, SkillContext(db=None, source_chunks=[])))
    assert result.output['body_text']
    assert 'layout_intent' in result.output
