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


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id("proj"))
    name: Mapped[str] = mapped_column(String(255), default="Untitled Project")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_direction: Mapped[str] = mapped_column(String(120), default="Marketing")
    audience: Mapped[str | None] = mapped_column(String(255), nullable=True)
    objective: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    books: Mapped[list[Book]] = relationship(back_populates="project")
    brand_profiles: Mapped[list[BrandProfile]] = relationship(back_populates="project", cascade="all, delete-orphan")
    format_profiles: Mapped[list[FormatProfile]] = relationship(back_populates="project", cascade="all, delete-orphan")
    source_assets: Mapped[list[SourceAsset]] = relationship(back_populates="project", cascade="all, delete-orphan")


class BrandProfile(Base):
    __tablename__ = "brand_profiles"

    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id("brand"))
    project_id: Mapped[str | None] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(120), default="Professional advisory")
    tone: Mapped[str] = mapped_column(String(255), default="confident, clear, evidence-led, useful")
    writing_rules: Mapped[list] = mapped_column(JSON, default=list)
    approved_terms: Mapped[list] = mapped_column(JSON, default=list)
    banned_terms: Mapped[list] = mapped_column(JSON, default=list)
    formatting_notes: Mapped[dict] = mapped_column(JSON, default=dict)
    disclaimer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    project: Mapped[Project | None] = relationship(back_populates="brand_profiles")


class FormatProfile(Base):
    __tablename__ = "format_profiles"

    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id("fmt"))
    project_id: Mapped[str | None] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(120), default="Professional default")
    layout_id: Mapped[str] = mapped_column(String(80), default="modern-editorial")
    page_size: Mapped[str] = mapped_column(String(60), default="A4")
    typography: Mapped[dict] = mapped_column(JSON, default=dict)
    margins: Mapped[dict] = mapped_column(JSON, default=dict)
    component_rules: Mapped[dict] = mapped_column(JSON, default=dict)
    image_policy: Mapped[dict] = mapped_column(JSON, default=dict)
    export_rules: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    project: Mapped[Project | None] = relationship(back_populates="format_profiles")


class Book(Base):
    __tablename__ = "books"

    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id("book"))
    project_id: Mapped[str | None] = mapped_column(ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    book_type_id: Mapped[str] = mapped_column(String(80), default="custom")
    creation_mode: Mapped[str] = mapped_column(String(40), default="classical")
    objective: Mapped[str | None] = mapped_column(Text, nullable=True)
    title: Mapped[str] = mapped_column(String(255), default="Untitled")
    topic: Mapped[str | None] = mapped_column(Text, nullable=True)
    genre: Mapped[str | None] = mapped_column(String(120), nullable=True)
    tone: Mapped[str | None] = mapped_column(String(120), nullable=True)
    target_audience: Mapped[str | None] = mapped_column(String(160), nullable=True)
    writing_style: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_size: Mapped[str] = mapped_column(String(60), default="A4")
    layout_template: Mapped[str] = mapped_column(String(80), default="classic")
    format_settings: Mapped[dict] = mapped_column(JSON, default=dict)
    cover_image_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cover_original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cover_content_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    cover_source: Mapped[str | None] = mapped_column(String(40), nullable=True, default="generated")
    status: Mapped[str] = mapped_column(String(40), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    project: Mapped[Project | None] = relationship(back_populates="books")
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
    generation_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    selected_layout_option_id: Mapped[str | None] = mapped_column(ForeignKey("page_layout_options.id", ondelete="SET NULL"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(40), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    book: Mapped[Book] = relationship(back_populates="pages")
    images: Mapped[list[PageImage]] = relationship(back_populates="page", cascade="all, delete-orphan")
    layout_options: Mapped[list[PageLayoutOption]] = relationship(back_populates="page", cascade="all, delete-orphan", foreign_keys="PageLayoutOption.page_id")
    selected_layout_option: Mapped[PageLayoutOption | None] = relationship(foreign_keys=[selected_layout_option_id], post_update=True)


class PageLayoutOption(Base):
    __tablename__ = "page_layout_options"
    __table_args__ = (UniqueConstraint("page_id", "option_index", name="uq_page_layout_option_index"),)

    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id("plo"))
    page_id: Mapped[str] = mapped_column(ForeignKey("pages.id", ondelete="CASCADE"), index=True)
    option_index: Mapped[int] = mapped_column(Integer)
    label: Mapped[str] = mapped_column(String(80))
    layout_json: Mapped[dict] = mapped_column(JSON, default=dict)
    preview_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    selected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    page: Mapped[Page] = relationship(back_populates="layout_options", foreign_keys=[page_id])




class SourceAsset(Base):
    __tablename__ = "source_assets"

    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id("src"))
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255), default="Untitled source")
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stored_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    source_type: Mapped[str] = mapped_column(String(80), default="other")
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    asset_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(40), default="uploaded")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    project: Mapped[Project] = relationship(back_populates="source_assets")
    chunks: Mapped[list[SourceChunk]] = relationship(back_populates="source_asset", cascade="all, delete-orphan")


class SourceChunk(Base):
    __tablename__ = "source_chunks"
    __table_args__ = (UniqueConstraint("source_asset_id", "chunk_index", name="uq_asset_chunk_index"),)

    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id("chunk"))
    source_asset_id: Mapped[str] = mapped_column(ForeignKey("source_assets.id", ondelete="CASCADE"), index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_estimate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    source_asset: Mapped[SourceAsset] = relationship(back_populates="chunks")


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
