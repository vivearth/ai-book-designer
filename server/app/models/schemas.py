from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class PreviewScenario(BaseModel):
    id: Literal["image-only", "text-with-image", "text-only"]
    title: str
    description: str


class FormatSettings(BaseModel):
    selected_layout_id: Literal["classic-novel", "illustrated-story", "modern-editorial"] = "classic-novel"
    layout_name: str = "Classic Novel"
    page_size: str = "A5"
    margin_style: str = "wide"
    typography_style: str = "classic-serif"
    image_policy: str = "minimal"
    preview_scenarios: list[PreviewScenario] = Field(default_factory=list)


class BookCreate(BaseModel):
    title: str | None = Field(default="Untitled")
    topic: str | None = None
    genre: str | None = None
    tone: str | None = None
    target_audience: str | None = None
    writing_style: str | None = None
    page_size: str = "A4"
    layout_template: str = "classic"
    format_settings: FormatSettings | dict[str, Any] | None = None


class BookUpdate(BaseModel):
    title: str | None = None
    topic: str | None = None
    genre: str | None = None
    tone: str | None = None
    target_audience: str | None = None
    writing_style: str | None = None
    page_size: str | None = None
    layout_template: str | None = None
    status: str | None = None
    format_settings: FormatSettings | dict[str, Any] | None = None
    cover_image_filename: str | None = None
    cover_original_filename: str | None = None
    cover_content_type: str | None = None
    cover_source: str | None = None


class PageImageRead(BaseModel):
    id: str
    original_filename: str
    stored_filename: str
    content_type: str | None
    caption: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PageCreate(BaseModel):
    page_number: int
    user_prompt: str | None = None
    user_text: str | None = None


class PageUpdate(BaseModel):
    user_prompt: str | None = None
    user_text: str | None = None
    generated_text: str | None = None
    final_text: str | None = None
    layout_json: dict[str, Any] | None = None
    status: str | None = None


class PageRead(BaseModel):
    id: str
    book_id: str
    page_number: int
    user_prompt: str | None
    user_text: str | None
    generated_text: str | None
    final_text: str | None
    layout_json: dict[str, Any]
    status: str
    created_at: datetime
    updated_at: datetime
    images: list[PageImageRead] = []

    model_config = {"from_attributes": True}


class BookMemoryRead(BaseModel):
    global_summary: str
    characters: list[Any]
    locations: list[Any]
    timeline: list[Any]
    rules: list[Any]
    unresolved_threads: list[Any]
    style_guide: dict[str, Any]

    model_config = {"from_attributes": True}


class BookRead(BaseModel):
    id: str
    title: str
    topic: str | None
    genre: str | None
    tone: str | None
    target_audience: str | None
    writing_style: str | None
    page_size: str
    layout_template: str
    status: str
    created_at: datetime
    updated_at: datetime
    memory: BookMemoryRead | None = None
    format_settings: dict[str, Any] | None = None
    cover_image_filename: str | None = None
    cover_original_filename: str | None = None
    cover_content_type: str | None = None
    cover_source: str | None = None

    model_config = {"from_attributes": True}


class GenerationRequest(BaseModel):
    instruction: str | None = None
    target_words: int | None = None
    allow_new_characters: bool = False


class GenerationResponse(BaseModel):
    page: PageRead
    context_packet: dict[str, Any]
    continuity_notes: list[str]


class PdfExportResponse(BaseModel):
    book_id: str
    filename: str
    download_url: str
