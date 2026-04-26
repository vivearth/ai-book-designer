from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.schemas import BookCreate, BookRead, ProjectCreate, ProjectRead, ProjectUpdate
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])
service = ProjectService()


@router.post("", response_model=ProjectRead)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    return service.create_project(db, payload)


@router.get("", response_model=list[ProjectRead])
def list_projects(db: Session = Depends(get_db)):
    return service.list_projects(db)


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: str, db: Session = Depends(get_db)):
    return service.get_project(db, project_id)


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(project_id: str, payload: ProjectUpdate, db: Session = Depends(get_db)):
    return service.update_project(db, project_id, payload)


@router.post("/{project_id}/books", response_model=BookRead)
def create_project_book(project_id: str, payload: BookCreate, db: Session = Depends(get_db)):
    return service.create_book_under_project(db, project_id, payload)


@router.get("/{project_id}/books", response_model=list[BookRead])
def list_project_books(project_id: str, db: Session = Depends(get_db)):
    return service.list_books_under_project(db, project_id)
