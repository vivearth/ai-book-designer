from __future__ import annotations

from pathlib import Path
from textwrap import shorten

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.entities import Book, Page


class PdfEngine:
    def export_book(self, db: Session, *, book: Book) -> tuple[str, Path]:
        settings = get_settings()
        safe_title = "".join(ch if ch.isalnum() else "_" for ch in book.title.lower()).strip("_") or "untitled"
        filename = f"{safe_title}_{book.id}.pdf"
        output_path = settings.export_dir / filename

        doc = SimpleDocTemplate(str(output_path), pagesize=A4, title=book.title)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph(book.title or "Untitled", styles["Title"]))
        if book.topic:
            story.append(Spacer(1, 12))
            story.append(Paragraph(shorten(book.topic, width=600, placeholder="..."), styles["BodyText"]))
        story.append(PageBreak())

        pages = db.query(Page).filter(Page.book_id == book.id).order_by(Page.page_number.asc()).all()
        for page in pages:
            text = page.final_text or page.generated_text or page.user_text or ""
            story.append(Paragraph(f"Page {page.page_number}", styles["Heading2"]))
            story.append(Spacer(1, 8))

            for page_image in page.images[:2]:
                image_path = settings.upload_dir / page_image.stored_filename
                if image_path.exists():
                    try:
                        img = Image(str(image_path), width=240, height=160, kind="proportional")
                        story.append(img)
                        if page_image.caption:
                            story.append(Paragraph(page_image.caption, styles["Italic"]))
                        story.append(Spacer(1, 8))
                    except Exception:
                        story.append(Paragraph(f"[Image could not be rendered: {page_image.original_filename}]", styles["BodyText"]))

            for paragraph in [chunk.strip() for chunk in text.split("\n") if chunk.strip()]:
                story.append(Paragraph(paragraph, styles["BodyText"]))
                story.append(Spacer(1, 8))
            story.append(PageBreak())

        doc.build(story)
        return filename, output_path
