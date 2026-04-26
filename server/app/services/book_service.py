from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.engines.memory_engine import MemoryEngine
from app.models.entities import Book
from app.models.schemas import BookCreate, BookUpdate


class BookService:
    def __init__(self) -> None:
        self.memory_engine = MemoryEngine()

    def create_book(self, db: Session, payload: BookCreate) -> Book:
        book = Book(**payload.model_dump())
        if not book.title:
            book.title = "Untitled"
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
        for key, value in payload.model_dump(exclude_unset=True).items():
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
