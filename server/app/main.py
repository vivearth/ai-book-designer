from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy import inspect, text

from app.api import books, exports, llm, pages, projects, sources, uploads
from app.core.config import get_settings
from app.core.database import Base, engine
from app.models import entities  # noqa: F401

settings = get_settings()
app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def ensure_dev_columns() -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if "books" in tables:
        existing = {column["name"] for column in inspector.get_columns("books")}
        statements = []
        for column, ddl in [
            ("format_settings", "ALTER TABLE books ADD COLUMN format_settings JSON"),
            ("cover_image_filename", "ALTER TABLE books ADD COLUMN cover_image_filename VARCHAR(255)"),
            ("cover_original_filename", "ALTER TABLE books ADD COLUMN cover_original_filename VARCHAR(255)"),
            ("cover_content_type", "ALTER TABLE books ADD COLUMN cover_content_type VARCHAR(120)"),
            ("cover_source", "ALTER TABLE books ADD COLUMN cover_source VARCHAR(40)"),
            ("project_id", "ALTER TABLE books ADD COLUMN project_id VARCHAR(80)"),
            ("book_type_id", "ALTER TABLE books ADD COLUMN book_type_id VARCHAR(80)"),
            ("creation_mode", "ALTER TABLE books ADD COLUMN creation_mode VARCHAR(40)"),
            ("objective", "ALTER TABLE books ADD COLUMN objective TEXT"),
        ]:
            if column not in existing:
                statements.append(ddl)
        if statements:
            with engine.begin() as connection:
                for statement in statements:
                    connection.execute(text(statement))
                connection.execute(text("UPDATE books SET cover_source = COALESCE(cover_source, 'generated')"))
                connection.execute(text("UPDATE books SET book_type_id = COALESCE(book_type_id, 'custom')"))
                connection.execute(text("UPDATE books SET creation_mode = COALESCE(creation_mode, 'classical')"))
    if "pages" in tables:
        existing_pages = {column["name"] for column in inspector.get_columns("pages")}
        if "generation_metadata" not in existing_pages:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE pages ADD COLUMN generation_metadata JSON"))
                connection.execute(text("UPDATE pages SET generation_metadata = '{}' WHERE generation_metadata IS NULL"))


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_dev_columns()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}


@app.get("/api/books/{book_id}/cover/generated.svg")
def generated_cover(book_id: str) -> Response:
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT title, topic, genre, layout_template FROM books WHERE id = :book_id"),
            {"book_id": book_id},
        ).mappings().first()
    if not result:
        raise HTTPException(status_code=404, detail="Book not found")

    title = (result["title"] or "Untitled")[:48]
    topic = (result["topic"] or result["genre"] or "A book in progress")[:80]
    layout = (result["layout_template"] or "classic").title()
    svg = f"""
    <svg xmlns='http://www.w3.org/2000/svg' width='900' height='1400' viewBox='0 0 900 1400'>
      <defs><linearGradient id='bg' x1='0%' y1='0%' x2='100%' y2='100%'><stop offset='0%' stop-color='#f7f0e6'/><stop offset='55%' stop-color='#eadcc8'/><stop offset='100%' stop-color='#c6a15b'/></linearGradient></defs>
      <rect width='900' height='1400' fill='url(#bg)' rx='42'/>
      <rect x='48' y='48' width='804' height='1304' rx='32' fill='rgba(255,250,241,0.46)' stroke='rgba(110,46,46,0.24)'/>
      <text x='96' y='910' font-family='Georgia, Times New Roman, serif' font-size='92' fill='#15120E' letter-spacing='-2'>{title}</text>
      <text x='100' y='1000' font-family='Arial, sans-serif' font-size='28' fill='#6E2E2E' letter-spacing='4'>{layout} EDITION</text>
      <text x='100' y='1060' font-family='Arial, sans-serif' font-size='28' fill='#7A6D5C'>{topic}</text>
    </svg>
    """.strip()
    return Response(content=svg, media_type="image/svg+xml")


app.include_router(books.router, prefix="/api")
app.include_router(pages.router, prefix="/api")
app.include_router(exports.router, prefix="/api")
app.include_router(uploads.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(sources.router, prefix="/api")
app.include_router(llm.router, prefix="/api")
