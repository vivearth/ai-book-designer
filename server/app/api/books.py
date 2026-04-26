from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.engines.pdf_engine import PdfEngine
from app.models.schemas import BookCreate, BookRead, BookUpdate, PdfExportResponse
from app.services.book_service import BookService

router = APIRouter(prefix="/books", tags=["books"])
service = BookService()
pdf_engine = PdfEngine()


@router.post("", response_model=BookRead)
def create_book(payload: BookCreate, db: Session = Depends(get_db)):
    return service.create_book(db, payload)


@router.get("", response_model=list[BookRead])
def list_books(db: Session = Depends(get_db)):
    return service.list_books(db)


@router.get("/{book_id}", response_model=BookRead)
def get_book(book_id: str, db: Session = Depends(get_db)):
    return service.get_book(db, book_id)


@router.patch("/{book_id}", response_model=BookRead)
def update_book(book_id: str, payload: BookUpdate, db: Session = Depends(get_db)):
    return service.update_book(db, book_id, payload)


@router.post("/{book_id}/export/pdf", response_model=PdfExportResponse)
def export_book_pdf(book_id: str, db: Session = Depends(get_db)):
    book = service.get_book(db, book_id)
    filename, _ = pdf_engine.export_book(db, book=book)
    return PdfExportResponse(book_id=book.id, filename=filename, download_url=f"/api/exports/{filename}")
