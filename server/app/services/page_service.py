from __future__ import annotations

from fastapi import HTTPException, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.book_types import get_book_type_config
from app.core.config import get_settings
from app.engines.context_engine import ContextEngine
from app.engines.layout_engine import LayoutEngine
from app.engines.llm_engine import LLMEngine
from app.engines.memory_engine import MemoryEngine
from app.engines.source_retrieval_engine import SourceRetrievalEngine
from app.models.entities import Book, BrandProfile, FormatProfile, Page, PageImage, Project, SourceChunk, new_id
from app.models.schemas import GenerationRequest, PageCreate, PageUpdate
from app.skills import build_skill_registry
from app.skills.base import SkillContext


class PageService:
    def __init__(self) -> None:
        self.context_engine = ContextEngine()
        self.layout_engine = LayoutEngine()
        self.memory_engine = MemoryEngine()
        self.llm_engine = LLMEngine()
        self.source_retrieval_engine = SourceRetrievalEngine()
        self.skill_registry = build_skill_registry()

    def get_book(self, db: Session, book_id: str) -> Book:
        book = db.get(Book, book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        return book

    def get_page(self, db: Session, page_id: str) -> Page:
        page = db.get(Page, page_id)
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
        return page

    def create_page(self, db: Session, book_id: str, payload: PageCreate) -> Page:
        self.get_book(db, book_id)
        page = Page(book_id=book_id, **payload.model_dump())
        db.add(page)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status_code=409, detail="Page number already exists for this book") from exc
        db.refresh(page)
        return page


    def create_next_page(self, db: Session, book_id: str, *, user_prompt: str | None = None, user_text: str | None = None) -> Page:
        self.get_book(db, book_id)
        last = db.query(Page).filter(Page.book_id == book_id).order_by(Page.page_number.desc()).first()
        next_number = (last.page_number if last else 0) + 1
        return self.create_page(db, book_id, PageCreate(page_number=next_number, user_prompt=user_prompt, user_text=user_text))
    def list_pages(self, db: Session, book_id: str) -> list[Page]:
        self.get_book(db, book_id)
        return db.query(Page).filter(Page.book_id == book_id).order_by(Page.page_number.asc()).all()

    def update_page(self, db: Session, page_id: str, payload: PageUpdate) -> Page:
        page = self.get_page(db, page_id)
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(page, key, value)
        if page.final_text or page.generated_text:
            page.layout_json = self.layout_engine.build_layout(book=page.book, page=page)
            self.memory_engine.update_after_page(db, book=page.book, page=page)
        db.commit()
        db.refresh(page)
        return page

    async def generate_page(self, db: Session, page_id: str, request: GenerationRequest) -> tuple[Page, dict, list[str], dict | None, list[dict], dict | None, list[str]]:
        page = self.get_page(db, page_id)
        book = page.book
        self.memory_engine.ensure_memory(db, book)
        project = db.get(Project, book.project_id) if book.project_id else None
        brand_profile = self._get_brand_profile(db, project)
        format_profile = self._get_format_profile(db, project)

        draft_layout = self.layout_engine.build_layout(book=book, page=page)
        composition = draft_layout.get("composition", "text_only")
        computed_target_words, word_budget_reason = self.layout_engine.estimate_target_words(book=book, page=page, composition=composition)
        target_words = request.target_words if request.target_words is not None else computed_target_words
        if request.target_words is not None:
            target_words = max(40, min(520, request.target_words))

        source_chunks = self._collect_source_chunks(db, book, page, request, project)
        warnings: list[str] = []

        skill_id = self._resolve_skill_id(request.skill_id, request.content_mode, project, book)
        if not source_chunks and skill_id in {"marketing_book_page", "finance_book_page"}:
            warnings.append("No source material was used for this professional generation.")
        skill = self.skill_registry.get(skill_id)
        if not skill:
            raise HTTPException(status_code=400, detail=f"Unknown skill_id: {skill_id}")

        ctx = SkillContext(
            db=db,
            project=project,
            book=book,
            page=page,
            brand_profile=brand_profile,
            format_profile=format_profile,
            source_chunks=source_chunks,
            llm_engine=self.llm_engine,
            layout_engine=self.layout_engine,
        )
        skill_result = await skill.run(
            {
                "instruction": request.instruction,
                "target_words": target_words,
                "page_direction": page.user_prompt or request.instruction,
                "rough_text": page.user_text or "",
            },
            ctx,
        )

        content = skill_result.output
        body = content.get("body_text") or ""
        body, sanitize_notes = self.llm_engine.sanitize_generated_page_text(body)
        warnings.extend(skill_result.warnings)
        warnings.extend(sanitize_notes)

        quality_skill = self.skill_registry.get("content_quality")
        quality_result = await quality_skill.run(
            {
                "generated_text": body,
                "target_words": target_words,
                "expected_content_direction": (project.content_direction if project else (book.genre or "")),
            },
            ctx,
        )
        quality_report = quality_result.output

        page.generated_text = body
        page.status = "generated"
        page.layout_json = self.layout_engine.build_layout(book=book, page=page)
        source_refs = content.get("source_refs", [])
        page.generation_metadata = {
            "skill_id": skill_id,
            "source_refs": source_refs,
            "quality_report": quality_report,
            "layout_intent": content.get("layout_intent"),
            "word_budget_reason": word_budget_reason,
        }
        self.memory_engine.update_after_page(db, book=book, page=page)

        packet = self.context_engine.build_context_packet(
            db,
            book=book,
            page=page,
            instruction=request.instruction,
            target_words=target_words,
            allow_new_characters=request.allow_new_characters,
            composition=composition,
            word_budget_reason=word_budget_reason,
        )

        notes = self._continuity_notes(book, page)
        notes.extend(skill_result.notes)
        notes.extend(quality_result.notes)

        db.commit()
        db.refresh(page)
        return page, packet, notes, content, source_refs, quality_report, warnings

    def approve_page(self, db: Session, page_id: str) -> Page:
        page = self.get_page(db, page_id)
        page.final_text = page.final_text or page.generated_text or page.user_text
        page.status = "approved"
        page.layout_json = self.layout_engine.build_layout(book=page.book, page=page)
        self.memory_engine.update_after_page(db, book=page.book, page=page)
        db.commit()
        db.refresh(page)
        return page

    async def upload_image(self, db: Session, page_id: str, file: UploadFile, caption: str | None = None) -> PageImage:
        page = self.get_page(db, page_id)
        settings = get_settings()
        suffix = ""
        if file.filename and "." in file.filename:
            suffix = "." + file.filename.rsplit(".", maxsplit=1)[-1]
        stored_filename = f"{new_id('upload')}{suffix}"
        output_path = settings.upload_dir / stored_filename
        contents = await file.read()
        output_path.write_bytes(contents)
        image = PageImage(
            page_id=page.id,
            original_filename=file.filename or stored_filename,
            stored_filename=stored_filename,
            content_type=file.content_type,
            caption=caption,
        )
        db.add(image)
        page.layout_json = self.layout_engine.build_layout(book=page.book, page=page)
        db.commit()
        db.refresh(image)
        return image

    def _resolve_skill_id(self, requested: str | None, content_mode: str | None, project: Project | None, book: Book) -> str:
        if requested:
            return requested

        config = get_book_type_config(getattr(book, "book_type_id", None))
        if getattr(book, "book_type_id", None) and book.book_type_id != "custom" and config.default_skill in self.skill_registry.list():
            return config.default_skill

        signal = (content_mode or (project.content_direction if project else None) or book.genre or "").lower().strip()

        if any(term in signal for term in ["finance", "cfo", "treasury", "cash"]):
            return "finance_book_page"
        if any(term in signal for term in ["marketing", "go-to-market", "gtm", "sales", "strategy", "leadership", "non-fiction", "nonfiction"]):
            return "marketing_book_page"
        if any(term in signal for term in ["fiction", "novel", "story", "children", "memoir", "poetry", "educational", "how-to"]):
            return "fiction_book_page"
        if project and any(term in (project.content_direction or "").lower() for term in ["marketing", "finance", "sales", "strategy"]):
            return "marketing_book_page"
        return "fiction_book_page"

    def _collect_source_chunks(self, db: Session, book: Book, page: Page, request: GenerationRequest, project: Project | None) -> list[SourceChunk]:
        if not project:
            return []
        chunks: list[SourceChunk] = []
        if request.selected_source_chunk_ids:
            chunks.extend(db.query(SourceChunk).filter(SourceChunk.id.in_(request.selected_source_chunk_ids)).all())
        if request.selected_source_asset_ids:
            chunks.extend(
                db.query(SourceChunk)
                .filter(SourceChunk.project_id == project.id)
                .filter(SourceChunk.source_asset_id.in_(request.selected_source_asset_ids))
                .all()
            )
        if request.auto_retrieve_sources:
            query = " ".join(filter(None, [page.user_prompt or "", page.user_text or "", book.topic or "", project.objective or ""]))
            chunks.extend(self.source_retrieval_engine.retrieve(db, project_id=project.id, query=query, limit=8))

        seen: set[str] = set()
        unique: list[SourceChunk] = []
        for chunk in chunks:
            if chunk.id not in seen:
                seen.add(chunk.id)
                unique.append(chunk)
        return unique[:10]

    def _get_brand_profile(self, db: Session, project: Project | None) -> BrandProfile | None:
        if not project:
            return None
        return (
            db.query(BrandProfile)
            .filter((BrandProfile.project_id == project.id) | (BrandProfile.project_id.is_(None)))
            .order_by(BrandProfile.created_at.asc())
            .first()
        )

    def _get_format_profile(self, db: Session, project: Project | None) -> FormatProfile | None:
        if not project:
            return None
        return (
            db.query(FormatProfile)
            .filter((FormatProfile.project_id == project.id) | (FormatProfile.project_id.is_(None)))
            .order_by(FormatProfile.created_at.asc())
            .first()
        )

    def _continuity_notes(self, book: Book, page: Page) -> list[str]:
        notes: list[str] = []
        text = page.generated_text or ""
        if book.tone and book.tone.lower() not in text.lower():
            notes.append("Tone was supplied as a constraint; review the output manually for tone consistency.")
        if not book.memory or not book.memory.global_summary:
            notes.append("Book memory is still thin. Add/approve more pages for stronger continuity.")
        if len(text.split()) > 700:
            notes.append("Generated page may be too long for a single page layout.")
        return notes
