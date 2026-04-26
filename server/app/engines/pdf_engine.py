from __future__ import annotations

from pathlib import Path
from textwrap import shorten

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.entities import Book, Page


class PdfEngine:
    def export_book(self, db: Session, *, book: Book, approved_only: bool = False) -> tuple[str, Path]:
        settings = get_settings()
        safe_title = "".join(ch if ch.isalnum() else "_" for ch in book.title.lower()).strip("_") or "untitled"
        filename = f"{safe_title}_{book.id}.pdf"
        output_path = settings.export_dir / filename

        doc = SimpleDocTemplate(str(output_path), pagesize=A4, title=book.title)
        styles = getSampleStyleSheet()
        body_style = ParagraphStyle(
            "BookBody",
            parent=styles["BodyText"],
            fontName="Times-Roman",
            leading=18,
            fontSize=11,
            textColor=colors.HexColor("#241B14"),
        )
        title_style = ParagraphStyle(
            "CoverTitle",
            parent=styles["Title"],
            fontName="Times-Bold",
            fontSize=28,
            leading=36,
            textColor=colors.HexColor("#15120E"),
        )
        story = []

        cover_block = Table(
            [[Paragraph(book.title or "Untitled", title_style)], [Paragraph(shorten(book.topic or book.genre or "A book in progress", width=180, placeholder="..."), styles["Italic"])]],
            colWidths=[460],
        )
        cover_block.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7F0E6")),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#C6A15B")),
                    ("INNERPADDING", (0, 0), (-1, -1), 28),
                ]
            )
        )
        story.append(Spacer(1, 120))
        story.append(cover_block)
        story.append(Spacer(1, 24))
        story.append(Paragraph((book.format_settings or {}).get("layout_name", "Editorial layout"), styles["Heading3"]))
        story.append(PageBreak())

        pages_query = db.query(Page).filter(Page.book_id == book.id)
        if approved_only:
            pages_query = pages_query.filter(Page.status == "approved")
        pages = pages_query.order_by(Page.page_number.asc()).all()
        for page in pages:
            text = page.final_text or page.generated_text or page.user_text or ""
            story.append(Paragraph(f"Page {page.page_number}", styles["Heading2"]))
            story.append(Spacer(1, 8))

            for page_image in page.images[:2]:
                image_path = settings.upload_dir / page_image.stored_filename
                if image_path.exists():
                    try:
                        img = Image(str(image_path), width=260, height=180, kind="proportional")
                        story.append(img)
                        if page_image.caption:
                            story.append(Paragraph(page_image.caption, styles["Italic"]))
                        story.append(Spacer(1, 8))
                    except Exception:
                        story.append(Paragraph(f"[Image could not be rendered: {page_image.original_filename}]", styles["BodyText"]))

            for paragraph in [chunk.strip() for chunk in text.split("\n") if chunk.strip()]:
                story.append(Paragraph(paragraph, body_style))
                story.append(Spacer(1, 8))
            story.append(PageBreak())

        doc.build(story)
        return filename, output_path
