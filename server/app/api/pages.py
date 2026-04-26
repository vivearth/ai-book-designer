from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.schemas import GenerationRequest, GenerationResponse, PageCreate, PageImageRead, PageRead, PageUpdate
from app.services.page_service import PageService

router = APIRouter(tags=["pages"])
service = PageService()


@router.post("/books/{book_id}/pages", response_model=PageRead)
def create_page(book_id: str, payload: PageCreate, db: Session = Depends(get_db)):
    return service.create_page(db, book_id, payload)


@router.get("/books/{book_id}/pages", response_model=list[PageRead])
def list_pages(book_id: str, db: Session = Depends(get_db)):
    return service.list_pages(db, book_id)


@router.patch("/pages/{page_id}", response_model=PageRead)
def update_page(page_id: str, payload: PageUpdate, db: Session = Depends(get_db)):
    return service.update_page(db, page_id, payload)


@router.post("/pages/{page_id}/generate", response_model=GenerationResponse)
async def generate_page(page_id: str, payload: GenerationRequest, db: Session = Depends(get_db)):
    page, packet, notes = await service.generate_page(db, page_id, payload)
    return GenerationResponse(page=page, context_packet=packet, continuity_notes=notes)


@router.post("/pages/{page_id}/approve", response_model=PageRead)
def approve_page(page_id: str, db: Session = Depends(get_db)):
    return service.approve_page(db, page_id)


@router.post("/pages/{page_id}/images", response_model=PageImageRead)
async def upload_page_image(
    page_id: str,
    file: UploadFile = File(...),
    caption: str | None = Form(None),
    db: Session = Depends(get_db),
):
    return await service.upload_image(db, page_id, file, caption)
