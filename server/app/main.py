from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import books, exports, pages
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


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}


app.include_router(books.router, prefix="/api")
app.include_router(pages.router, prefix="/api")
app.include_router(exports.router, prefix="/api")
