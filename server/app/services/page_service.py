from __future__ import annotations

from fastapi import HTTPException, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.engines.context_engine import ContextEngine
from app.engines.layout_engine import LayoutEngine
from app.engines.llm_engine import LLMEngine
from app.engines.memory_engine import MemoryEngine
from app.models.entities import Book, Page, PageImage, new_id
from app.models.schemas import GenerationRequest, PageCreate, PageUpdate


class PageService:
    def __init__(self) -> None:
        self.context_engine = ContextEngine()
        self.layout_engine = LayoutEngine()
        self.memory_engine = MemoryEngine()
        self.llm_engine = LLMEngine()

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

    async def generate_page(self, db: Session, page_id: str, request: GenerationRequest) -> tuple[Page, dict, list[str]]:
        page = self.get_page(db, page_id)
        book = page.book
        self.memory_engine.ensure_memory(db, book)

        packet = self.context_engine.build_context_packet(
            db,
            book=book,
            page=page,
            instruction=request.instruction,
            target_words=request.target_words,
            allow_new_characters=request.allow_new_characters,
        )
        prompt = self.context_engine.to_generation_prompt(packet)
        generated = await self.llm_engine.generate_text(prompt)

        page.generated_text = generated
        page.status = "generated"
        page.layout_json = self.layout_engine.build_layout(book=book, page=page)
        self.memory_engine.update_after_page(db, book=book, page=page)
        notes = self._continuity_notes(book, page)
        db.commit()
        db.refresh(page)
        return page, packet, notes

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
