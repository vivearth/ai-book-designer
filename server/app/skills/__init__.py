from app.skills.content_quality_skill import ContentQualitySkill
from app.skills.finance_book_page_skill import FinanceBookPageSkill
from app.skills.general_book_page_skill import GeneralBookPageSkill
from app.skills.fiction_book_page_skill import FictionBookPageSkill
from app.skills.layout_composition_skill import LayoutCompositionSkill
from app.skills.marketing_book_page_skill import MarketingBookPageSkill
from app.skills.registry import SkillRegistry


def build_skill_registry() -> SkillRegistry:
    reg = SkillRegistry()
    reg.register(MarketingBookPageSkill())
    reg.register(FinanceBookPageSkill())
    reg.register(FictionBookPageSkill())
    reg.register(GeneralBookPageSkill())
    reg.register(LayoutCompositionSkill())
    reg.register(ContentQualitySkill())
    return reg
