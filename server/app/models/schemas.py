from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class PreviewScenario(BaseModel):
    id: Literal["image_only", "text_with_image", "text_only"]
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


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    content_direction: str = "Marketing"
    audience: str | None = None
    objective: str | None = None
    status: str = "draft"


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    content_direction: str | None = None
    audience: str | None = None
    objective: str | None = None
    status: str | None = None


class BrandProfileRead(BaseModel):
    id: str
    project_id: str | None
    name: str
    tone: str
    writing_rules: list[Any]
    approved_terms: list[Any]
    banned_terms: list[Any]
    formatting_notes: dict[str, Any]
    disclaimer_notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FormatProfileRead(BaseModel):
    id: str
    project_id: str | None
    name: str
    layout_id: str
    page_size: str
    typography: dict[str, Any]
    margins: dict[str, Any]
    component_rules: dict[str, Any]
    image_policy: dict[str, Any]
    export_rules: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectRead(BaseModel):
    id: str
    name: str
    description: str | None
    content_direction: str
    audience: str | None
    objective: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    brand_profiles: list[BrandProfileRead] = []
    format_profiles: list[FormatProfileRead] = []

    model_config = {"from_attributes": True}


class BookCreate(BaseModel):
    project_id: str | None = None
    book_type_id: str = "custom"
    creation_mode: Literal["classical", "expert"] = "classical"
    objective: str | None = None
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
    project_id: str | None = None
    book_type_id: str | None = None
    creation_mode: Literal["classical", "expert"] | None = None
    objective: str | None = None
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
    generation_metadata: dict[str, Any] | None = None
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
    generation_metadata: dict[str, Any]
    selected_layout_option_id: str | None = None
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
    project_id: str | None
    book_type_id: str
    creation_mode: str
    objective: str | None
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


class SourceAssetRead(BaseModel):
    id: str
    project_id: str
    title: str
    original_filename: str | None
    stored_filename: str | None
    content_type: str | None
    source_type: str
    extracted_text: str | None
    summary: str | None
    tags: list[Any]
    asset_metadata: dict[str, Any]
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SourceChunkRead(BaseModel):
    id: str
    source_asset_id: str
    project_id: str
    chunk_index: int
    text: str
    summary: str | None
    token_estimate: int | None
    metadata_json: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class SourceTextCreate(BaseModel):
    title: str | None = None
    text: str
    source_type: str = "note"
    tags: list[str] = Field(default_factory=list)


class PageCapacityHint(BaseModel):
    visible_text_area_width_px: float
    visible_text_area_height_px: float
    font_family: str
    font_size_px: float
    line_height_px: float
    estimated_chars_per_line: int
    estimated_lines: int
    estimated_words: int
    composition: str


class GenerationRequest(BaseModel):
    instruction: str | None = None
    target_words: int | None = None
    allow_new_characters: bool = False
    skill_id: str | None = None
    selected_source_asset_ids: list[str] = Field(default_factory=list)
    selected_source_chunk_ids: list[str] = Field(default_factory=list)
    auto_retrieve_sources: bool = True
    content_mode: str | None = None
    quality_threshold: int = 70
    page_capacity_hint: PageCapacityHint | None = None


class GenerationResponse(BaseModel):
    page: PageRead
    context_packet: dict[str, Any]
    continuity_notes: list[str]
    skill_output: dict[str, Any] | None = None
    source_refs: list[dict[str, Any]] = Field(default_factory=list)
    quality_report: dict[str, Any] | None = None
    warnings: list[str] = Field(default_factory=list)
    overflow_created_page: PageRead | None = None
    overflow_warning: str | None = None


class LayoutOptionsGenerateRequest(BaseModel):
    preserve_text: bool = True
    option_count: int = 2
    page_capacity_hint: PageCapacityHint | None = None
    instructions: str | None = None


class PageLayoutOptionRead(BaseModel):
    id: str
    page_id: str
    option_index: int
    label: str
    layout_json: dict[str, Any]
    preview_metadata: dict[str, Any]
    rationale: str | None
    created_at: datetime
    selected_at: datetime | None

    model_config = {"from_attributes": True}


class LayoutOptionsResponse(BaseModel):
    page_id: str
    options: list[PageLayoutOptionRead] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class DeletePageResponse(BaseModel):
    deleted_page_id: str
    book_id: str
    deleted_page_number: int
    pages: list[PageRead] = Field(default_factory=list)


class PdfExportResponse(BaseModel):
    book_id: str
    filename: str
    download_url: str


class PdfExportRequest(BaseModel):
    approved_only: bool = False


class DraftGenerationRequest(BaseModel):
    target_page_count: int | None = None
    chapter_count: int | None = None
    source_asset_ids: list[str] = Field(default_factory=list)
    instructions: str | None = None
    book_type_id: str | None = None
    creation_mode: Literal["classical", "expert"] = "expert"


class DraftGenerationResponse(BaseModel):
    book_plan: dict[str, Any]
    created_pages: list[PageRead]
    warnings: list[str] = Field(default_factory=list)
    source_summary: dict[str, Any] = Field(default_factory=dict)
