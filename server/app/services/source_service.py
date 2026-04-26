from __future__ import annotations

import re
from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.entities import Project, SourceAsset, SourceChunk, new_id
from app.models.schemas import SourceTextCreate


class SourceService:
    def _parse_tags(self, tags: str | None) -> list[str]:
        if not tags:
            return []
        return [t.strip() for t in tags.split(",") if t.strip()]

    def _chunk_text(self, text: str, *, words_per_chunk: int = 220) -> list[str]:
        clean = re.sub(r"\s+", " ", text or "").strip()
        if not clean:
            return []
        words = clean.split()
        return [" ".join(words[i : i + words_per_chunk]) for i in range(0, len(words), words_per_chunk)]

    def create_text_source(self, db: Session, project_id: str, payload: SourceTextCreate) -> SourceAsset:
        project = db.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        source = SourceAsset(
            project_id=project_id,
            title=payload.title or "Pasted note",
            original_filename=None,
            content_type="text/plain",
            source_type=payload.source_type,
            extracted_text=payload.text,
            tags=payload.tags,
            status="uploaded",
        )
        db.add(source)
        db.commit()
        db.refresh(source)
        return source

    async def upload_source(
        self,
        db: Session,
        project_id: str,
        file: UploadFile,
        *,
        title: str | None = None,
        source_type: str | None = None,
        tags: str | None = None,
    ) -> SourceAsset:
        project = db.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        suffix = Path(file.filename or "upload.bin").suffix
        stored_filename = f"{new_id('srcfile')}{suffix}"
        output_path = get_settings().upload_dir / stored_filename
        contents = await file.read()
        output_path.write_bytes(contents)

        resolved_type = (source_type or self._infer_source_type(file.filename or "")).lower()
        source = SourceAsset(
            project_id=project_id,
            title=title or Path(file.filename or "Source file").stem,
            original_filename=file.filename,
            stored_filename=stored_filename,
            content_type=file.content_type,
            source_type=resolved_type,
            tags=self._parse_tags(tags),
            status="uploaded",
        )
        db.add(source)
        db.commit()
        db.refresh(source)
        return source

    def list_sources(self, db: Session, project_id: str) -> list[SourceAsset]:
        return db.query(SourceAsset).filter(SourceAsset.project_id == project_id).order_by(SourceAsset.updated_at.desc()).all()

    def get_source(self, db: Session, source_id: str) -> SourceAsset:
        source = db.get(SourceAsset, source_id)
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")
        return source

    def delete_source(self, db: Session, source_id: str) -> None:
        source = self.get_source(db, source_id)
        db.delete(source)
        db.commit()

    def process_source(self, db: Session, source_id: str) -> SourceAsset:
        source = self.get_source(db, source_id)
        text = source.extracted_text or ""

        if not text and source.stored_filename:
            file_path = get_settings().upload_dir / source.stored_filename
            if source.source_type in {"text", "note", "campaign", "case_study", "web_copy", "other"} or (source.original_filename or "").endswith(".txt"):
                text = file_path.read_text(errors="ignore")
            elif source.source_type == "markdown" or (source.original_filename or "").endswith(".md"):
                text = file_path.read_text(errors="ignore")
            elif source.source_type == "pdf" or (source.original_filename or "").endswith(".pdf"):
                try:
                    from pypdf import PdfReader  # type: ignore
                    reader = PdfReader(str(file_path))
                    pages = [p.extract_text() or "" for p in reader.pages]
                    text = "\n".join(pages)
                except Exception:
                    source.status = "failed"
                    source.summary = "PDF extraction requires optional pypdf dependency."
                    db.commit()
                    db.refresh(source)
                    return source
            elif source.source_type == "image":
                source.summary = source.summary or "Image uploaded. OCR/vision analysis is not enabled yet."
                source.status = "processed"
                db.commit()
                db.refresh(source)
                return source

        if not text.strip():
            source.status = "failed"
            source.summary = "No extractable text was found."
            db.commit()
            db.refresh(source)
            return source

        db.query(SourceChunk).filter(SourceChunk.source_asset_id == source.id).delete()
        chunks = self._chunk_text(text)
        for idx, chunk in enumerate(chunks):
            db.add(
                SourceChunk(
                    source_asset_id=source.id,
                    project_id=source.project_id,
                    chunk_index=idx,
                    text=chunk,
                    summary=" ".join(chunk.split()[:24]),
                    token_estimate=max(1, len(chunk.split()) * 3 // 4),
                    metadata_json={},
                )
            )
        source.extracted_text = text
        source.summary = " ".join(text.split()[:45])
        source.status = "processed"
        db.commit()
        db.refresh(source)
        return source

    def query_chunks(self, db: Session, project_id: str, query: str | None = None) -> list[SourceChunk]:
        q = db.query(SourceChunk).filter(SourceChunk.project_id == project_id)
        if query:
            q = q.filter(SourceChunk.text.ilike(f"%{query}%"))
        return q.order_by(SourceChunk.created_at.desc()).limit(50).all()

    def _infer_source_type(self, filename: str) -> str:
        ext = Path(filename).suffix.lower()
        if ext == ".pdf":
            return "pdf"
        if ext == ".md":
            return "markdown"
        if ext in {".txt", ".log"}:
            return "text"
        if ext in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
            return "image"
        return "other"
