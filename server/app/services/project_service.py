from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.entities import BrandProfile, Book, FormatProfile, Project
from app.models.schemas import BookCreate, ProjectCreate, ProjectUpdate
from app.services.book_service import BookService


DEFAULT_WRITING_RULES = [
    "avoid hype",
    "avoid unsupported claims",
    "write for senior professionals",
    "prefer clarity over cleverness",
    "use practical examples",
    "avoid fictional storytelling unless requested",
]


class ProjectService:
    def __init__(self) -> None:
        self.book_service = BookService()

    def create_project(self, db: Session, payload: ProjectCreate) -> Project:
        project = Project(**payload.model_dump())
        db.add(project)
        db.flush()

        brand = BrandProfile(
            project_id=project.id,
            name="Professional advisory",
            tone="confident, clear, evidence-led, useful",
            writing_rules=DEFAULT_WRITING_RULES,
            approved_terms=[],
            banned_terms=[],
            formatting_notes={},
        )
        fmt = FormatProfile(
            project_id=project.id,
            name="Professional editorial",
            layout_id="modern-editorial",
            page_size="A4",
            typography={"body_font": "Serif", "heading_font": "Sans"},
            margins={"top": 46, "right": 50, "bottom": 46, "left": 50},
            component_rules={"pull_quote": "enabled"},
            image_policy={"preferred": "balanced"},
            export_rules={"include_source_notes": False},
        )
        db.add_all([brand, fmt])
        db.commit()
        db.refresh(project)
        return project

    def list_projects(self, db: Session) -> list[Project]:
        return db.query(Project).order_by(Project.updated_at.desc()).all()

    def get_project(self, db: Session, project_id: str) -> Project:
        project = db.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project

    def update_project(self, db: Session, project_id: str, payload: ProjectUpdate) -> Project:
        project = self.get_project(db, project_id)
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(project, key, value)
        db.commit()
        db.refresh(project)
        return project

    def create_book_under_project(self, db: Session, project_id: str, payload: BookCreate) -> Book:
        project = self.get_project(db, project_id)
        data = payload.model_dump()
        data["project_id"] = project.id
        if not data.get("genre"):
            data["genre"] = project.content_direction
        if not data.get("target_audience"):
            data["target_audience"] = project.audience
        if not data.get("topic"):
            data["topic"] = project.objective
        return self.book_service.create_book(db, BookCreate(**data))

    def list_books_under_project(self, db: Session, project_id: str) -> list[Book]:
        self.get_project(db, project_id)
        return db.query(Book).filter(Book.project_id == project_id).order_by(Book.updated_at.desc()).all()
