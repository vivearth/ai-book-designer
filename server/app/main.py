from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy import inspect, text

from app.api import books, exports, pages, uploads
from app.core.config import get_settings
from app.core.database import Base, engine
from app.models import entities  # noqa: F401 - import models before create_all

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
    if "books" not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns("books")}
    statements = []
    if "format_settings" not in existing:
        statements.append("ALTER TABLE books ADD COLUMN format_settings JSON")
    if "cover_image_filename" not in existing:
        statements.append("ALTER TABLE books ADD COLUMN cover_image_filename VARCHAR(255)")
    if "cover_original_filename" not in existing:
        statements.append("ALTER TABLE books ADD COLUMN cover_original_filename VARCHAR(255)")
    if "cover_content_type" not in existing:
        statements.append("ALTER TABLE books ADD COLUMN cover_content_type VARCHAR(120)")
    if "cover_source" not in existing:
        statements.append("ALTER TABLE books ADD COLUMN cover_source VARCHAR(40)")
    if statements:
        with engine.begin() as connection:
            for statement in statements:
                connection.execute(text(statement))
            connection.execute(text("UPDATE books SET cover_source = COALESCE(cover_source, 'generated')"))


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
      <defs>
        <linearGradient id='bg' x1='0%' y1='0%' x2='100%' y2='100%'>
          <stop offset='0%' stop-color='#f7f0e6'/>
          <stop offset='55%' stop-color='#eadcc8'/>
          <stop offset='100%' stop-color='#c6a15b'/>
        </linearGradient>
        <filter id='grain'>
          <feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/>
          <feColorMatrix type='saturate' values='0'/>
          <feComponentTransfer>
            <feFuncA type='table' tableValues='0 0 0.04 0.08'/>
          </feComponentTransfer>
        </filter>
      </defs>
      <rect width='900' height='1400' fill='url(#bg)' rx='42'/>
      <rect x='48' y='48' width='804' height='1304' rx='32' fill='rgba(255,250,241,0.46)' stroke='rgba(110,46,46,0.24)'/>
      <rect width='900' height='1400' filter='url(#grain)' opacity='0.25'/>
      <path d='M180 190 C360 120, 610 120, 735 220 C685 270, 595 320, 505 390 C410 460, 350 560, 270 640 C235 590, 205 520, 180 430 C155 340, 155 250, 180 190Z' fill='rgba(110,46,46,0.74)'/>
      <path d='M620 720 C700 760, 765 840, 770 930 C775 1020, 730 1110, 640 1185 C575 1130, 520 1045, 470 960 C545 905, 575 810, 620 720Z' fill='rgba(104,115,93,0.72)'/>
      <text x='96' y='910' font-family='Georgia, Times New Roman, serif' font-size='92' fill='#15120E' letter-spacing='-2'>
        {title}
      </text>
      <text x='100' y='1000' font-family='Arial, sans-serif' font-size='28' fill='#6E2E2E' letter-spacing='4'>
        {layout} EDITION
      </text>
      <text x='100' y='1060' font-family='Arial, sans-serif' font-size='28' fill='#7A6D5C'>
        {topic}
      </text>
    </svg>
    """.strip()
    return Response(content=svg, media_type="image/svg+xml")


app.include_router(books.router, prefix="/api")
app.include_router(pages.router, prefix="/api")
app.include_router(exports.router, prefix="/api")
app.include_router(uploads.router, prefix="/api")
