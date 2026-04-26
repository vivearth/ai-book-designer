from __future__ import annotations

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.engines.memory_engine import MemoryEngine
from app.models.entities import Book, new_id
from app.models.schemas import BookCreate, BookUpdate


DEFAULT_FORMAT_SETTINGS = {
    "selected_layout_id": "classic-novel",
    "layout_name": "Classic Novel",
    "page_size": "A5",
    "margin_style": "wide",
    "typography_style": "classic-serif",
    "image_policy": "minimal",
    "preview_scenarios": [
        {"id": "image-only", "title": "Image-only page", "description": "A full scene-setting visual page."},
        {"id": "text-with-image", "title": "Text with image", "description": "A balanced composition with visual support."},
        {"id": "text-only", "title": "Text-only page", "description": "Elegant uninterrupted reading pages."},
    ],
}


class BookService:
    def __init__(self) -> None:
        self.memory_engine = MemoryEngine()

    def create_book(self, db: Session, payload: BookCreate) -> Book:
        data = payload.model_dump()
        data["format_settings"] = self._normalize_format_settings(data.get("format_settings"))
        book = Book(**data)
        if not book.title:
            book.title = "Untitled"
        if not book.cover_source:
            book.cover_source = "generated"
        db.add(book)
        db.flush()
        self.memory_engine.ensure_memory(db, book)
        db.commit()
        db.refresh(book)
        return book

    def list_books(self, db: Session) -> list[Book]:
        return db.query(Book).order_by(Book.updated_at.desc()).all()

    def get_book(self, db: Session, book_id: str) -> Book:
        book = db.get(Book, book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        return book

    def update_book(self, db: Session, book_id: str, payload: BookUpdate) -> Book:
        book = self.get_book(db, book_id)
        updates = payload.model_dump(exclude_unset=True)
        if "format_settings" in updates:
            updates["format_settings"] = self._normalize_format_settings(updates.get("format_settings"))
        for key, value in updates.items():
            setattr(book, key, value)
        self.memory_engine.ensure_memory(db, book)
        if book.memory:
            book.memory.style_guide = {
                **(book.memory.style_guide or {}),
                "tone": book.tone,
                "target_audience": book.target_audience,
                "writing_style": book.writing_style,
            }
        db.commit()
        db.refresh(book)
        return book

    async def upload_cover(self, db: Session, book_id: str, file: UploadFile) -> Book:
        book = self.get_book(db, book_id)
        settings = get_settings()
        suffix = ""
        if file.filename and "." in file.filename:
            suffix = "." + file.filename.rsplit(".", maxsplit=1)[-1]
        stored_filename = f"{new_id('cover')}{suffix}"
        output_path = settings.upload_dir / stored_filename
        contents = await file.read()
        output_path.write_bytes(contents)

        book.cover_image_filename = stored_filename
        book.cover_original_filename = file.filename or stored_filename
        book.cover_content_type = file.content_type
        book.cover_source = "uploaded"
        db.commit()
        db.refresh(book)
        return book

    def _normalize_format_settings(self, raw: dict | None) -> dict:
        merged = {**DEFAULT_FORMAT_SETTINGS}
        if raw:
            merged.update(raw)
        preview_scenarios = merged.get("preview_scenarios") or DEFAULT_FORMAT_SETTINGS["preview_scenarios"]
        merged["preview_scenarios"] = preview_scenarios
        return merged
