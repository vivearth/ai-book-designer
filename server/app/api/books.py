from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.engines.pdf_engine import PdfEngine
from app.models.schemas import BookCreate, BookRead, BookUpdate, DraftGenerationRequest, DraftGenerationResponse, PdfExportRequest, PdfExportResponse
from app.services.book_service import BookService
from app.services.draft_generation_service import DraftGenerationService

router = APIRouter(prefix="/books", tags=["books"])
service = BookService()
draft_service = DraftGenerationService()
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


@router.post("/{book_id}/cover", response_model=BookRead)
async def upload_book_cover(book_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    return await service.upload_cover(db, book_id, file)


@router.post("/{book_id}/draft/generate", response_model=DraftGenerationResponse)
async def generate_book_draft(book_id: str, payload: DraftGenerationRequest, db: Session = Depends(get_db)):
    book = service.get_book(db, book_id)
    plan, created_pages, warnings, summary = await draft_service.generate_draft(db, book, payload)
    return DraftGenerationResponse(book_plan=plan, created_pages=created_pages, warnings=warnings, source_summary=summary)


@router.post("/{book_id}/export/pdf", response_model=PdfExportResponse)
def export_book_pdf(book_id: str, payload: PdfExportRequest, db: Session = Depends(get_db)):
    book = service.get_book(db, book_id)
    try:
        filename, _ = pdf_engine.export_book(db, book=book, approved_only=payload.approved_only)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return PdfExportResponse(book_id=book.id, filename=filename, download_url=f"/api/exports/{filename}")
