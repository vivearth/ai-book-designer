from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.book_types import get_book_type_config
from app.models.entities import Book, Page, SourceAsset
from app.models.schemas import DraftGenerationRequest, GenerationRequest, PageCreate
from app.services.page_service import PageService


class DraftGenerationService:
    def __init__(self) -> None:
        self.page_service = PageService()

    async def generate_draft(self, db: Session, book: Book, payload: DraftGenerationRequest) -> tuple[dict, list[Page], list[str], dict]:
        config = get_book_type_config(payload.book_type_id or book.book_type_id)
        page_count = payload.target_page_count or self._default_page_count(config.id)
        page_count = max(1, min(30, page_count))

        selected_assets = (
            db.query(SourceAsset).filter(SourceAsset.project_id == book.project_id).filter(SourceAsset.id.in_(payload.source_asset_ids)).all()
            if (payload.source_asset_ids and book.project_id)
            else []
        )
        warnings: list[str] = []
        if config.source_policy in {"recommended", "required"} and not selected_assets:
            warnings.append("Draft was generated without selected source assets.")

        plan = {"title": book.title, "book_type_id": config.id, "mode": payload.creation_mode, "target_page_count": page_count, "chapters": []}
        goals = self._page_goals(config.id, page_count)
        created_pages: list[Page] = []

        # clear existing pages only if empty draft requested? keep existing and append from next page
        existing_count = db.query(Page).filter(Page.book_id == book.id).count()
        start_number = (db.query(Page).filter(Page.book_id == book.id).order_by(Page.page_number.desc()).first().page_number if existing_count else 0)
        if existing_count:
            warnings.append(f"Draft pages were appended after existing {existing_count} page(s).")

        for idx, goal in enumerate(goals, start=1):
            last = db.query(Page).filter(Page.book_id == book.id).order_by(Page.page_number.desc()).first()
            page_number = (last.page_number if last else 0) + 1
            page = self.page_service.create_page(db, book.id, PageCreate(page_number=page_number, user_prompt=goal, user_text=payload.instructions or ""))
            req = GenerationRequest(
                instruction=goal,
                content_mode=config.id,
                skill_id=config.default_skill,
                auto_retrieve_sources=True,
                selected_source_asset_ids=payload.source_asset_ids,
                target_words=260 if config.default_format == "modern-editorial" else 360,
            )
            generated_page, _, _, _, _, _, _, _, _ = await self.page_service.generate_page(db, page.id, req)
            created_pages.append(generated_page)

        summary = {"selected_source_count": len(selected_assets), "selected_source_titles": [a.title for a in selected_assets[:8]]}
        return plan, created_pages, warnings, summary

    def _default_page_count(self, book_type_id: str) -> int:
        return {
            "marketing_story": 8,
            "finance_explainer": 8,
            "thought_leadership": 10,
            "case_study_collection": 10,
            "fiction_novel": 5,
        }.get(book_type_id, 6)

    def _page_goals(self, book_type_id: str, page_count: int) -> list[str]:
        templates = {
            "marketing_story": [
                "Define the customer and market problem",
                "Explain why the old approach fails",
                "Present the core insight from source material",
                "Show audience and business implications",
                "Introduce the strategic approach",
                "Describe proof points and campaign evidence",
                "Provide a practical framework",
                "Close with an executive perspective",
            ],
            "finance_explainer": [
                "Define the core financial challenge",
                "Explain the operational context",
                "Clarify metrics and assumptions",
                "Connect analysis to decisions",
                "Provide a practical planning framework",
                "Discuss risk and caution",
                "Give a scenario-based example",
                "Close with synthesis and next actions",
            ],
            "fiction_novel": ["Opening scene", "Character conflict", "Escalation", "Turning point", "Hook into next chapter"],
        }
        base = templates.get(book_type_id) or [f"Develop section {i}" for i in range(1, page_count + 1)]
        if len(base) >= page_count:
            return base[:page_count]
        out = base.copy()
        while len(out) < page_count:
            out.append(f"Develop section {len(out)+1}")
        return out
