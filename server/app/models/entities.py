from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


class Book(Base):
    __tablename__ = "books"

    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id("book"))
    title: Mapped[str] = mapped_column(String(255), default="Untitled")
    topic: Mapped[str | None] = mapped_column(Text, nullable=True)
    genre: Mapped[str | None] = mapped_column(String(120), nullable=True)
    tone: Mapped[str | None] = mapped_column(String(120), nullable=True)
    target_audience: Mapped[str | None] = mapped_column(String(160), nullable=True)
    writing_style: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_size: Mapped[str] = mapped_column(String(60), default="A4")
    layout_template: Mapped[str] = mapped_column(String(80), default="classic")
    status: Mapped[str] = mapped_column(String(40), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    pages: Mapped[list[Page]] = relationship(back_populates="book", cascade="all, delete-orphan", order_by="Page.page_number")
    memory: Mapped[BookMemory | None] = relationship(back_populates="book", cascade="all, delete-orphan", uselist=False)


class Page(Base):
    __tablename__ = "pages"
    __table_args__ = (UniqueConstraint("book_id", "page_number", name="uq_book_page_number"),)

    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id("page"))
    book_id: Mapped[str] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), index=True)
    page_number: Mapped[int] = mapped_column(Integer)
    user_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    layout_json: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(40), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    book: Mapped[Book] = relationship(back_populates="pages")
    images: Mapped[list[PageImage]] = relationship(back_populates="page", cascade="all, delete-orphan")


class PageImage(Base):
    __tablename__ = "page_images"

    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id("img"))
    page_id: Mapped[str] = mapped_column(ForeignKey("pages.id", ondelete="CASCADE"), index=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    stored_filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    page: Mapped[Page] = relationship(back_populates="images")


class BookMemory(Base):
    __tablename__ = "book_memories"

    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id("mem"))
    book_id: Mapped[str] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), unique=True, index=True)
    global_summary: Mapped[str] = mapped_column(Text, default="")
    characters: Mapped[list] = mapped_column(JSON, default=list)
    locations: Mapped[list] = mapped_column(JSON, default=list)
    timeline: Mapped[list] = mapped_column(JSON, default=list)
    rules: Mapped[list] = mapped_column(JSON, default=list)
    unresolved_threads: Mapped[list] = mapped_column(JSON, default=list)
    style_guide: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    book: Mapped[Book] = relationship(back_populates="memory")
