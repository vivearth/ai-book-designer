from __future__ import annotations

import re
import hashlib
from io import BytesIO
from pathlib import Path

from fastapi import HTTPException, UploadFile
from PIL import Image, ImageOps
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.book_types import get_book_type_config
from app.core.config import get_settings
from app.engines.context_engine import ContextEngine
from app.engines.layout_engine import LayoutEngine
from app.engines.layout_option_engine import LayoutOptionEngine, LayoutOptionInput
from app.engines.layout_validator import LayoutValidator
from app.engines.page_capacity_engine import PageCapacityEngine
from app.engines.llm_engine import LLMEngine
from app.engines.memory_engine import MemoryEngine
from app.engines.source_retrieval_engine import SourceRetrievalEngine
from app.engines.text_pagination_engine import TextPaginationEngine
from app.engines.text_quality_engine import TextQualityEngine
from app.models.entities import Book, BrandProfile, FormatProfile, Page, PageImage, PageLayoutOption, Project, SourceChunk, new_id, utc_now
from app.models.schemas import GenerationRequest, LayoutOptionsGenerateRequest, PageCreate, PageUpdate
from app.skills import build_skill_registry
from app.skills.base import SkillContext


class PageService:
    def __init__(self) -> None:
        self.context_engine = ContextEngine()
        self.layout_engine = LayoutEngine()
        self.memory_engine = MemoryEngine()
        self.layout_option_engine = LayoutOptionEngine()
        self.layout_validator = LayoutValidator()
        self.llm_engine = LLMEngine()
        self.source_retrieval_engine = SourceRetrievalEngine()
        self.text_quality_engine = TextQualityEngine()
        self.pagination_engine = TextPaginationEngine()
        self.page_capacity_engine = PageCapacityEngine()
        self.skill_registry = build_skill_registry()

    def get_book(self, db: Session, book_id: str) -> Book:
        book = db.get(Book, book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        return book

    def get_page(self, db: Session, page_id: str) -> Page:
        page = db.get(Page, page_id)
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
        return page

    def create_page(self, db: Session, book_id: str, payload: PageCreate) -> Page:
        book = self.get_book(db, book_id)
        page = Page(book_id=book_id, **payload.model_dump())
        page.layout_json = self._validated_layout(book, page)
        layout_validation = self.layout_validator.validate_layout(page.layout_json)
        if not layout_validation.valid:
            raise HTTPException(status_code=500, detail="Could not initialize a valid page layout")
        db.add(page)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status_code=409, detail="Page number already exists for this book") from exc
        db.refresh(page)
        return page


    def create_next_page(self, db: Session, book_id: str, *, user_prompt: str | None = None, user_text: str | None = None) -> Page:
        self.get_book(db, book_id)
        last = db.query(Page).filter(Page.book_id == book_id).order_by(Page.page_number.desc()).first()
        next_number = (last.page_number if last else 0) + 1
        return self.create_page(db, book_id, PageCreate(page_number=next_number, user_prompt=user_prompt, user_text=user_text))
    def list_pages(self, db: Session, book_id: str) -> list[Page]:
        self.get_book(db, book_id)
        return db.query(Page).filter(Page.book_id == book_id).order_by(Page.page_number.asc()).all()

    def update_page(self, db: Session, page_id: str, payload: PageUpdate) -> Page:
        page = self.get_page(db, page_id)
        updates = payload.model_dump(exclude_unset=True)
        text_fields = {"user_text", "generated_text", "final_text"}
        text_changed = any(field in updates for field in text_fields)
        for key, value in updates.items():
            setattr(page, key, value)
        if not page.selected_layout_option_id:
            page.layout_json = self._validated_layout(page.book, page)
        if text_changed:
            db.query(PageLayoutOption).filter(PageLayoutOption.page_id == page.id).delete()
            page.selected_layout_option_id = None
            self.repaginate_from_page(db, page, reason="manual_text_edit")
        if page.final_text or page.generated_text:
            self.memory_engine.update_after_page(db, book=page.book, page=page)
        db.commit()
        db.refresh(page)
        return page

    async def generate_page(self, db: Session, page_id: str, request: GenerationRequest) -> tuple[Page, dict, list[str], dict | None, list[dict], dict | None, list[str], Page | None, str | None]:
        page = self.get_page(db, page_id)
        book = page.book
        self.memory_engine.ensure_memory(db, book)
        project = db.get(Project, book.project_id) if book.project_id else None
        brand_profile = self._get_brand_profile(db, project)
        format_profile = self._get_format_profile(db, project)

        draft_layout = self.layout_engine.build_layout(book=book, page=page)
        composition = draft_layout.get("composition", "text_only")
        computed_target_words, word_budget_reason = self.layout_engine.estimate_target_words(book=book, page=page, composition=composition)
        computed_target_words = min(computed_target_words, self.page_capacity_engine.estimate_capacity_words(book, page, composition))
        target_words = request.target_words if request.target_words is not None else computed_target_words
        if request.page_capacity_hint:
            hinted = max(40, min(520, int(request.page_capacity_hint.estimated_words)))
            target_words = min(target_words, hinted)
            word_budget_reason = f"{word_budget_reason}; clamped by page capacity hint at {hinted} words for {request.page_capacity_hint.composition}"
        elif request.target_words is not None:
            target_words = max(40, min(520, request.target_words))

        source_chunks = self._collect_source_chunks(db, book, page, request, project)
        warnings: list[str] = []

        skill_id = self._resolve_skill_id(request.skill_id, request.content_mode, project, book)
        if not source_chunks and skill_id in {"marketing_book_page", "finance_book_page"}:
            warnings.append("No source material was used for this professional generation.")
        skill = self.skill_registry.get(skill_id)
        if not skill:
            raise HTTPException(status_code=400, detail=f"Unknown skill_id: {skill_id}")

        ctx = SkillContext(
            db=db,
            project=project,
            book=book,
            page=page,
            brand_profile=brand_profile,
            format_profile=format_profile,
            source_chunks=source_chunks,
            llm_engine=self.llm_engine,
            layout_engine=self.layout_engine,
        )
        skill_result = await skill.run(
            {
                "instruction": request.instruction,
                "target_words": target_words,
                "page_direction": page.user_prompt or "",
                "rough_text": page.user_text or "",
            },
            ctx,
        )

        content = skill_result.output
        body = content.get("body_text") or ""
        if request.instruction and any(token in body.lower() for token in ["shape this into a polished page", "preserving continuity", "return only"]):
            warnings.append("Guidance leakage was detected in generated content and was cleaned.")
            for marker in ["Shape this into a polished page", "preserving continuity", "Return only"]:
                body = re.sub(re.escape(marker), "", body, flags=re.IGNORECASE)
        body, sanitize_notes = self.llm_engine.sanitize_generated_page_text(body)
        deduped_body, repetition_notes = self.text_quality_engine.remove_repeated_sentences(body)
        body = deduped_body or body
        warnings.extend(skill_result.warnings)
        warnings.extend(sanitize_notes)
        warnings.extend(repetition_notes)

        overflow_created_page: Page | None = None
        overflow_warning: str | None = None

        quality_skill = self.skill_registry.get("content_quality")
        quality_result = await quality_skill.run(
            {
                "generated_text": body,
                "target_words": target_words,
                "expected_content_direction": (project.content_direction if project else (book.genre or "")),
                "user_prompt": page.user_prompt or "",
                "user_text": page.user_text or "",
            },
            ctx,
        )
        quality_report = quality_result.output
        severe_flags = quality_report.get("flags", {})
        should_retry = any(
            severe_flags.get(flag)
            for flag in ["prompt_leakage", "off_domain", "unsupported_claims", "repetition"]
        )
        if self.llm_engine.settings.llm_fast_mode:
            should_retry = False
        if should_retry and self.llm_engine.settings.active_llm_provider.lower().strip() != "mock":
            retry_result = await skill.run(
                {
                    "instruction": request.instruction,
                    "target_words": target_words,
                    "page_direction": page.user_prompt or "",
                    "rough_text": page.user_text or "",
                    "strict_quality": True,
                },
                ctx,
            )
            retry_body = retry_result.output.get("body_text") or ""
            retry_body, retry_sanitize_notes = self.llm_engine.sanitize_generated_page_text(retry_body)
            retry_body, retry_repetition_notes = self.text_quality_engine.remove_repeated_sentences(retry_body)
            retry_quality = await quality_skill.run(
                {
                    "generated_text": retry_body,
                    "target_words": target_words,
                    "expected_content_direction": (project.content_direction if project else (book.genre or "")),
                    "user_prompt": page.user_prompt or "",
                    "user_text": page.user_text or "",
                },
                ctx,
            )
            if retry_quality.output.get("score", 0) >= quality_report.get("score", 0):
                content = retry_result.output
                body = retry_body
                skill_result.notes.extend(retry_result.notes)
                quality_report = retry_quality.output
                warnings.extend(retry_result.warnings)
                warnings.extend(retry_sanitize_notes)
                warnings.extend(retry_repetition_notes)
                warnings.append("One strict-quality regeneration pass was used.")

        continuation_prefix = self._existing_continuation_prefix(page)
        if continuation_prefix:
            body = f"{continuation_prefix}\n\n{body}".strip()
            warnings.append("Existing continuation text was preserved before newly generated content.")
        page.generated_text = body
        page.status = "generated"
        db.query(PageLayoutOption).filter(PageLayoutOption.page_id == page.id).delete()
        page.selected_layout_option_id = None
        if not page.selected_layout_option_id:
            page.layout_json = self._validated_layout(book, page)
        pre_md = dict(page.generation_metadata or {})
        pre_md["target_words"] = target_words
        page.generation_metadata = pre_md
        existing_next = db.query(Page).filter(Page.book_id == book.id, Page.page_number == page.page_number + 1).first()
        repagination_result = self.repaginate_from_page(db, page, reason="generate_page_fit")
        if repagination_result["created_pages"]:
            overflow_created_page = repagination_result["created_pages"][0]
        else:
            candidate_next = db.query(Page).filter(Page.book_id == book.id, Page.page_number == page.page_number + 1).first()
            if existing_next is None and candidate_next and (candidate_next.generation_metadata or {}).get("continued_from_page_id") == page.id:
                overflow_created_page = candidate_next
            elif repagination_result["updated_existing_pages"] and existing_next is not None:
                overflow_warning = "Generated text overflow was merged into existing next page."
                warnings.append(overflow_warning)
        source_refs = content.get("source_refs", [])
        llm_notes = [n for n in (skill_result.notes or []) if isinstance(n, str) and (n.startswith("provider=") or n.startswith("model=") or n.startswith("model_source=") or n.startswith("llm_elapsed_ms=") or "fallback" in n.lower())]
        metadata = dict(page.generation_metadata or {})
        metadata.update({
            "skill_id": skill_id,
            "llm_provider": self.llm_engine.provider.name,
            "llm_model": next((n.split("=",1)[1] for n in llm_notes if n.startswith("model=")), None),
            "llm_notes": llm_notes,
            "llm_elapsed_ms": next((int(n.split("=",1)[1]) for n in llm_notes if n.startswith("llm_elapsed_ms=")), None),
            "llm_fallback_used": any("fallback_used=true" in n for n in llm_notes),
            "llm_error": next((n for n in llm_notes if n.startswith("fallback_reason=")), None),
            "source_refs": source_refs,
            "quality_report": quality_report,
            "headline": content.get("headline"),
            "pull_quote": content.get("pull_quote"),
            "layout_intent": content.get("layout_intent"),
            "seed_reason": content.get("seed_reason"),
            "prompt_length_chars": (content.get("prompt_meta") or {}).get("prompt_length_chars"),
            "prompt_truncated": (content.get("prompt_meta") or {}).get("prompt_truncated"),
            "target_words": target_words,
            "page_capacity_hint": request.page_capacity_hint.model_dump() if request.page_capacity_hint else None,
            "word_budget_reason": word_budget_reason,
            "overflow_text": None,
        })
        page.generation_metadata = metadata
        self.memory_engine.update_after_page(db, book=book, page=page)

        packet = self.context_engine.build_context_packet(
            db,
            book=book,
            page=page,
            instruction=request.instruction,
            target_words=target_words,
            allow_new_characters=request.allow_new_characters,
            composition=composition,
            word_budget_reason=word_budget_reason,
        )

        notes = self._continuity_notes(book, page)
        notes.extend(skill_result.notes)
        notes.extend(quality_result.notes)

        db.commit()
        db.refresh(page)
        return page, packet, notes, content, source_refs, quality_report, warnings, overflow_created_page, overflow_warning



    async def generate_layout_options(self, db: Session, page_id: str, request: LayoutOptionsGenerateRequest) -> tuple[Page, list[PageLayoutOption], list[str]]:
        page = self.get_page(db, page_id)
        if request.option_count != 2:
            raise HTTPException(status_code=400, detail="MVP currently supports exactly 2 layout options.")

        text = (page.final_text or page.generated_text or page.user_text or "").strip()
        if not text and len(page.images) == 0:
            raise HTTPException(status_code=400, detail="Add page text or image before generating layout options.")

        options_payload = await self.layout_option_engine.generate_options(
            LayoutOptionInput(
                book=page.book,
                page=page,
                text=text,
                image_count=len(page.images),
                page_capacity_hint=request.page_capacity_hint.model_dump() if request.page_capacity_hint else None,
                instructions=request.instructions,
            )
        )

        db.query(PageLayoutOption).filter(PageLayoutOption.page_id == page.id).delete()
        saved_options: list[PageLayoutOption] = []
        for payload in options_payload:
            option = PageLayoutOption(
                page_id=page.id,
                option_index=payload["option_index"],
                label=payload["label"],
                layout_json=payload["layout_json"],
                preview_metadata=payload["preview_metadata"],
                rationale=payload.get("rationale"),
            )
            db.add(option)
            saved_options.append(option)

        metadata = dict(page.generation_metadata or {})
        metadata["layout_options"] = {
            "generated_at": utc_now().isoformat(),
            "preserve_text": request.preserve_text,
            "source_text_field": "final_text" if page.final_text else ("generated_text" if page.generated_text else "user_text"),
        }
        page.generation_metadata = metadata
        db.commit()
        db.refresh(page)
        for option in saved_options:
            db.refresh(option)

        return page, sorted(saved_options, key=lambda item: item.option_index), []

    def list_layout_options(self, db: Session, page_id: str) -> list[PageLayoutOption]:
        page = self.get_page(db, page_id)
        return db.query(PageLayoutOption).filter(PageLayoutOption.page_id == page.id).order_by(PageLayoutOption.option_index.asc()).all()

    def select_layout_option(self, db: Session, page_id: str, option_id: str) -> Page:
        page = self.get_page(db, page_id)
        option = db.get(PageLayoutOption, option_id)
        if not option or option.page_id != page.id:
            raise HTTPException(status_code=404, detail="Layout option not found for this page")

        option.selected_at = utc_now()
        page.selected_layout_option_id = option.id
        selected_layout = dict(option.layout_json or {})
        self.layout_validator.assert_valid_layout(selected_layout, page=page, text=(page.final_text or page.generated_text or page.user_text or ""))
        page.layout_json = selected_layout
        page.layout_json["layout_option_id"] = option.id
        metadata = dict(page.generation_metadata or {})
        metadata["selected_layout_option_id"] = option.id
        metadata["selected_layout_option_label"] = option.label
        page.generation_metadata = metadata
        result = self.repaginate_from_page(db, page, reason="layout_option_selected")
        if result["warnings"]:
            metadata = dict(page.generation_metadata or {})
            metadata["layout_option_notice"] = "; ".join(result["warnings"])
            page.generation_metadata = metadata
        db.commit()
        db.refresh(page)
        return page


    def _validated_layout(self, book: Book, page: Page, variant: str | None = None) -> dict:
        text = page.final_text or page.generated_text or page.user_text or ""
        image_count = len(page.images)
        fallback_variants = [
            variant,
            None,
            "text_only_classic" if image_count == 0 else None,
            "one_image_top_text_bottom" if image_count == 1 else None,
            "two_image_grid_top_text_bottom" if image_count == 2 else None,
            "three_plus_gallery_with_text_block" if image_count >= 3 else None,
        ]
        errors: list[dict] = []
        seen: set[str] = set()
        for candidate in [v for v in fallback_variants if v is not None or v is None]:
            key = "__default__" if candidate is None else candidate
            if key in seen:
                continue
            seen.add(key)
            layout = self.layout_engine.build_layout(book=book, page=page, variant=candidate)
            result = self.layout_validator.validate_layout(layout, page=page, text=text)
            layout["validation"] = result.to_dict()
            if result.valid:
                return layout
            errors.append({"variant": candidate or "default", "errors": result.errors})
        raise HTTPException(status_code=400, detail={"message": "Unable to build a valid layout", "attempts": errors})

    def approve_page(self, db: Session, page_id: str) -> Page:
        page = self.get_page(db, page_id)
        page.final_text = page.final_text or page.generated_text or page.user_text
        page.status = "approved"
        if not page.selected_layout_option_id:
            page.layout_json = self._validated_layout(page.book, page)
        self.memory_engine.update_after_page(db, book=page.book, page=page)
        db.commit()
        db.refresh(page)
        return page

    async def upload_image(self, db: Session, page_id: str, file: UploadFile, caption: str | None = None) -> PageImage:
        page = self.get_page(db, page_id)
        settings = get_settings()
        contents = await file.read()
        if not (file.content_type or "").startswith("image/"):
            raise HTTPException(status_code=400, detail="Only image uploads are allowed.")
        if len(contents) > settings.max_upload_image_bytes:
            raise HTTPException(status_code=413, detail=f"Image upload exceeds max size of {settings.max_upload_image_bytes} bytes.")
        original_size = len(contents)
        sha256 = hashlib.sha256(contents).hexdigest()
        metadata = dict(page.generation_metadata or {})
        uploads = dict(metadata.get("image_uploads") or {})
        existing = next((image_id for image_id, info in uploads.items() if info.get("sha256") == sha256), None)
        if existing:
            existing_image = db.get(PageImage, existing)
            if existing_image and existing_image.page_id == page.id:
                return existing_image
        try:
            img = Image.open(BytesIO(contents))
            img = ImageOps.exif_transpose(img)
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Invalid image payload.") from exc
        max_dim = max(img.width, img.height)
        if max_dim > settings.max_stored_image_dimension:
            scale = settings.max_stored_image_dimension / max_dim
            img = img.resize((int(img.width * scale), int(img.height * scale)))
        fmt = settings.preferred_image_format.lower().strip()
        has_alpha = img.mode in ("RGBA", "LA") or ("transparency" in img.info)
        if fmt == "webp":
            ext, save_fmt = "webp", "WEBP"
        elif has_alpha:
            ext, save_fmt = "png", "PNG"
        else:
            ext, save_fmt = "jpg", "JPEG"
        if save_fmt == "JPEG" and img.mode != "RGB":
            img = img.convert("RGB")
        suffix = f".{ext}"
        stored_filename = f"{new_id('upload')}{suffix}"
        output_path = settings.upload_dir / stored_filename
        output = BytesIO()
        save_kwargs = {"quality": settings.image_webp_quality if save_fmt == "WEBP" else settings.image_jpeg_quality}
        if save_fmt == "PNG":
            save_kwargs = {}
        img.save(output, format=save_fmt, **save_kwargs)
        output_path.write_bytes(output.getvalue())
        image = PageImage(
            page_id=page.id,
            original_filename=file.filename or stored_filename,
            stored_filename=stored_filename,
            content_type=f"image/{ext if ext != 'jpg' else 'jpeg'}",
            caption=caption,
        )
        db.add(image)
        db.flush()
        db.expire(page, ["images"])
        uploads[image.id] = {
            "sha256": sha256,
            "width": img.width,
            "height": img.height,
            "optimized_size_bytes": len(output.getvalue()),
            "original_size_bytes": original_size,
            "stored_filename": stored_filename,
            "content_type": image.content_type,
            "original_content_type": file.content_type,
        }
        metadata["image_uploads"] = uploads
        page.generation_metadata = metadata
        db.query(PageLayoutOption).filter(PageLayoutOption.page_id == page.id).delete()
        page.selected_layout_option_id = None
        if not page.selected_layout_option_id:
            page.layout_json = self._validated_layout(page.book, page)
        self.repaginate_from_page(db, page, reason="image_added")
        db.commit()
        db.refresh(image)
        return image

    def _maybe_delete_file(self, stored_filename: str | None) -> None:
        if not stored_filename:
            return
        path = Path(get_settings().upload_dir) / stored_filename
        if path.exists():
            path.unlink()

    def delete_image(self, db: Session, page_id: str, image_id: str) -> Page:
        page = self.get_page(db, page_id)
        image = db.get(PageImage, image_id)
        if not image or image.page_id != page.id:
            raise HTTPException(status_code=404, detail="Image not found for this page")
        stored_filename = image.stored_filename
        db.delete(image)
        db.flush()
        db.expire(page, ["images"])
        if stored_filename and db.query(PageImage).filter(PageImage.stored_filename == stored_filename).count() == 0:
            self._maybe_delete_file(stored_filename)
        md = dict(page.generation_metadata or {})
        uploads = dict(md.get("image_uploads") or {})
        uploads.pop(image_id, None)
        md["image_uploads"] = uploads
        page.generation_metadata = md
        db.query(PageLayoutOption).filter(PageLayoutOption.page_id == page.id).delete()
        page.selected_layout_option_id = None
        page.layout_json = self._validated_layout(page.book, page)
        self.repaginate_from_page(db, page, reason="image_deleted")
        db.commit()
        db.refresh(page)
        return page

    def delete_page(self, db: Session, page_id: str) -> dict:
        page = self.get_page(db, page_id)
        book_id = page.book_id
        for image in list(page.images):
            stored_filename = image.stored_filename
            db.delete(image)
            db.flush()
            if stored_filename and db.query(PageImage).filter(PageImage.stored_filename == stored_filename).count() == 0:
                self._maybe_delete_file(stored_filename)
        db.query(PageLayoutOption).filter(PageLayoutOption.page_id == page.id).delete()
        deleted_num = page.page_number
        deleted_id = page.id
        db.delete(page)
        db.flush()
        remaining = db.query(Page).filter(Page.book_id == book_id).order_by(Page.page_number.asc()).all()
        for idx, p in enumerate(remaining, start=1):
            p.page_number = idx
            md = dict(p.generation_metadata or {})
            if md.get("continued_from_page_id") == deleted_id:
                md.pop("continued_from_page_id", None)
            if md.get("continued_to_page_id") == deleted_id:
                md.pop("continued_to_page_id", None)
            pag = dict(md.get("pagination") or {})
            if pag.get("continued_from_page_id") == deleted_id:
                pag.pop("continued_from_page_id", None)
            if pag.get("continued_to_page_id") == deleted_id:
                pag.pop("continued_to_page_id", None)
            md["pagination"] = pag
            p.generation_metadata = md
            if not p.selected_layout_option_id:
                p.layout_json = self._validated_layout(p.book, p)
        db.flush()
        db.commit()
        return {"deleted_page_id": deleted_id, "book_id": book_id, "pages": remaining, "deleted_page_number": deleted_num}

    def repaginate_from_page(self, db: Session, page: Page, reason: str, max_pages: int = 20) -> dict:
        current = page
        created_pages: list[Page] = []
        updated_existing_pages: list[Page] = []
        warnings: list[str] = []
        for idx in range(max_pages):
            active_field = self._active_text_field(current)
            text = (getattr(current, active_field) or "").strip()
            if not text:
                return {"created_pages": created_pages, "updated_existing_pages": updated_existing_pages, "warnings": warnings}
            composition = (current.layout_json or {}).get("composition", "text_only")
            capacity = self.page_capacity_engine.estimate_capacity_words(current.book, current, composition)
            if reason == "generate_page_fit":
                t = (current.generation_metadata or {}).get("target_words")
                if isinstance(t, int) and t > 0:
                    capacity = min(capacity, t)
            current_text, overflow_text = self.pagination_engine.split_text_for_page(text, capacity)
            setattr(current, active_field, current_text)
            if not current.selected_layout_option_id:
                current.layout_json = self._validated_layout(current.book, current)
            md = dict(current.generation_metadata or {})
            md["pagination"] = {"estimated_capacity_words": capacity, "actual_words_on_page": len(current_text.split()), "overflow_words": len(overflow_text.split()) if overflow_text else 0, "pagination_reason": reason}
            current.generation_metadata = md
            if not overflow_text.strip():
                return {"created_pages": created_pages, "updated_existing_pages": updated_existing_pages, "warnings": warnings}
            next_page = db.query(Page).filter(Page.book_id == current.book_id, Page.page_number == current.page_number + 1).first()
            if not next_page:
                next_page = self.create_page(db, current.book_id, PageCreate(page_number=current.page_number + 1, user_prompt=f"Continuation from page {current.page_number}"))
                created_pages.append(next_page)
            else:
                updated_existing_pages.append(next_page)
            self._prepend_overflow_to_page(next_page, overflow_text, active_field, reason, current.id)
            cur_meta = dict(current.generation_metadata or {})
            cur_meta["continued_to_page_id"] = next_page.id
            current.generation_metadata = cur_meta
            cur_pag = dict((current.generation_metadata or {}).get("pagination") or {})
            cur_pag["continued_to_page_id"] = next_page.id
            cur_meta["pagination"] = cur_pag
            current.generation_metadata = cur_meta
            next_md = dict(next_page.generation_metadata or {})
            next_md.update({"continued_from_page_id": current.id, "auto_continued": True, "repaginated_due_to": reason, "overflow_source_page_id": current.id})
            next_page.generation_metadata = next_md
            if not next_page.selected_layout_option_id:
                next_page.layout_json = self._validated_layout(next_page.book, next_page)
            current = next_page
            if idx == max_pages - 1 and overflow_text.strip():
                final_md = dict(current.generation_metadata or {})
                pagination = dict(final_md.get("pagination") or {})
                pagination["warning"] = f"Repagination stopped after {max_pages} pages; overflow may remain."
                pagination["overflow_words_remaining_estimate"] = len(overflow_text.split())
                final_md["pagination"] = pagination
                current.generation_metadata = final_md
                warnings.append(pagination["warning"])
        return {"created_pages": created_pages, "updated_existing_pages": updated_existing_pages, "warnings": warnings}

    def _prepend_overflow_to_page(self, target_page: Page, overflow_text: str, source_field: str, reason: str, source_page_id: str) -> str:
        overflow = overflow_text.strip()
        if not overflow:
            return source_field
        if target_page.final_text:
            field = "final_text"
        elif target_page.generated_text:
            field = "generated_text"
        elif target_page.user_text:
            field = "user_text"
        elif source_field in {"final_text", "generated_text"}:
            field = "generated_text"
            target_page.status = "generated"
        else:
            field = "user_text"
        existing = getattr(target_page, field) or ""
        setattr(target_page, field, f"{overflow}\n\n{existing}".strip())
        meta = dict(target_page.generation_metadata or {})
        meta.update({"continued_from_page_id": source_page_id, "auto_continued": True, "repaginated_due_to": reason, "overflow_source_page_id": source_page_id})
        target_page.generation_metadata = meta
        return field

    def _resolve_skill_id(self, requested: str | None, content_mode: str | None, project: Project | None, book: Book) -> str:
        if requested:
            return requested

        config = get_book_type_config(getattr(book, "book_type_id", None))
        signal = (content_mode or (project.content_direction if project else None) or book.genre or "").lower().strip()

        if getattr(book, "book_type_id", None) and book.book_type_id != "custom" and config.default_skill in self.skill_registry.list():
            return config.default_skill

        if any(term in signal for term in ["finance", "cfo", "treasury", "cash"]):
            return "finance_book_page"
        if any(term in signal for term in ["marketing", "go-to-market", "gtm", "sales", "strategy", "leadership", "non-fiction", "nonfiction"]):
            return "marketing_book_page"
        if any(term in signal for term in ["fiction", "novel", "story", "children", "memoir", "poetry"]):
            return "fiction_book_page"
        if any(term in signal for term in ["educational", "how-to", "guide", "manual", "custom", "general"]):
            return "general_book_page"
        if project and any(term in (project.content_direction or "").lower() for term in ["marketing", "finance", "sales", "strategy"]):
            return "marketing_book_page"
        if book.book_type_id == "custom":
            return "general_book_page"
        return "fiction_book_page"

    def _collect_source_chunks(self, db: Session, book: Book, page: Page, request: GenerationRequest, project: Project | None) -> list[SourceChunk]:
        if not project:
            return []
        chunks: list[SourceChunk] = []
        if request.selected_source_chunk_ids:
            chunks.extend(db.query(SourceChunk).filter(SourceChunk.id.in_(request.selected_source_chunk_ids)).all())
        if request.selected_source_asset_ids:
            chunks.extend(
                db.query(SourceChunk)
                .filter(SourceChunk.project_id == project.id)
                .filter(SourceChunk.source_asset_id.in_(request.selected_source_asset_ids))
                .all()
            )
        if request.auto_retrieve_sources:
            query = " ".join(filter(None, [page.user_prompt or "", page.user_text or "", book.topic or "", project.objective or ""]))
            chunks.extend(self.source_retrieval_engine.retrieve(db, project_id=project.id, query=query, limit=8))

        seen: set[str] = set()
        unique: list[SourceChunk] = []
        for chunk in chunks:
            if chunk.id not in seen:
                seen.add(chunk.id)
                unique.append(chunk)
        return unique[:10]

    def _get_brand_profile(self, db: Session, project: Project | None) -> BrandProfile | None:
        if not project:
            return None
        return (
            db.query(BrandProfile)
            .filter((BrandProfile.project_id == project.id) | (BrandProfile.project_id.is_(None)))
            .order_by(BrandProfile.created_at.asc())
            .first()
        )

    def _get_format_profile(self, db: Session, project: Project | None) -> FormatProfile | None:
        if not project:
            return None
        return (
            db.query(FormatProfile)
            .filter((FormatProfile.project_id == project.id) | (FormatProfile.project_id.is_(None)))
            .order_by(FormatProfile.created_at.asc())
            .first()
        )

    def _continuity_notes(self, book: Book, page: Page) -> list[str]:
        notes: list[str] = []
        text = page.generated_text or ""
        if book.tone and book.tone.lower() not in text.lower():
            notes.append("Tone was supplied as a constraint; review the output manually for tone consistency.")
        if not book.memory or not book.memory.global_summary:
            notes.append("Book memory is still thin. Add/approve more pages for stronger continuity.")
        if len(text.split()) > 700:
            notes.append("Generated page may be too long for a single page layout.")
        return notes
    def _active_text_field(self, page: Page) -> str:
        return "final_text" if page.final_text else ("generated_text" if page.generated_text else "user_text")

    def _existing_continuation_prefix(self, page: Page) -> str | None:
        md = dict(page.generation_metadata or {})
        if not md.get("continued_from_page_id"):
            return None
        existing = (getattr(page, self._active_text_field(page)) or "").strip()
        return existing or None
