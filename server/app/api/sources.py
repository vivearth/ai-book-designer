from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.schemas import SourceAssetRead, SourceChunkRead, SourceTextCreate
from app.services.source_service import SourceService

router = APIRouter(tags=["sources"])
service = SourceService()


@router.post("/projects/{project_id}/sources", response_model=SourceAssetRead)
async def upload_source(
    project_id: str,
    file: UploadFile = File(...),
    title: str | None = Form(None),
    source_type: str | None = Form(None),
    tags: str | None = Form(None),
    db: Session = Depends(get_db),
):
    return await service.upload_source(db, project_id, file, title=title, source_type=source_type, tags=tags)


@router.post("/projects/{project_id}/sources/text", response_model=SourceAssetRead)
def create_text_source(project_id: str, payload: SourceTextCreate, db: Session = Depends(get_db)):
    return service.create_text_source(db, project_id, payload)


@router.get("/projects/{project_id}/sources", response_model=list[SourceAssetRead])
def list_project_sources(project_id: str, db: Session = Depends(get_db)):
    return service.list_sources(db, project_id)


@router.get("/sources/{source_id}", response_model=SourceAssetRead)
def get_source(source_id: str, db: Session = Depends(get_db)):
    return service.get_source(db, source_id)


@router.delete("/sources/{source_id}")
def delete_source(source_id: str, db: Session = Depends(get_db)):
    service.delete_source(db, source_id)
    return {"deleted": True}


@router.post("/sources/{source_id}/process", response_model=SourceAssetRead)
def process_source(source_id: str, db: Session = Depends(get_db)):
    return service.process_source(db, source_id)


@router.get("/projects/{project_id}/source-chunks", response_model=list[SourceChunkRead])
def query_chunks(project_id: str, query: str | None = Query(default=None), db: Session = Depends(get_db)):
    return service.query_chunks(db, project_id, query)
