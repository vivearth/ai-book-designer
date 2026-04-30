from __future__ import annotations

from pathlib import Path
from textwrap import shorten

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.entities import Book, Page, PageImage


class PdfEngine:
    def export_book(self, db: Session, *, book: Book, approved_only: bool = False) -> tuple[str, Path]:
        settings = get_settings()
        safe_title = "".join(ch if ch.isalnum() else "_" for ch in book.title.lower()).strip("_") or "untitled"
        filename = f"{safe_title}_{book.id}.pdf"
        output_path = settings.export_dir / filename

        c = canvas.Canvas(str(output_path), pagesize=A4, pageCompression=0)
        self._render_cover(c, book)

        pages_query = db.query(Page).filter(Page.book_id == book.id)
        if approved_only:
            pages_query = pages_query.filter(Page.status == "approved")
        pages = pages_query.order_by(Page.page_number.asc()).all()
        for page in pages:
            self._render_layout_page(c, page, settings.upload_dir)

        c.save()
        return filename, output_path

    def _render_cover(self, c: canvas.Canvas, book: Book) -> None:
        w, h = A4
        c.setFillColor(colors.HexColor("#F7F0E6")); c.rect(0, 0, w, h, fill=1, stroke=0)
        inset = 48
        c.setFillColor(colors.white); c.roundRect(inset, inset, w - (inset * 2), h - (inset * 2), 10, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#8B4A43")); c.rect(inset + 16, inset + 16, 14, h - (inset * 2) - 32, fill=1, stroke=0)
        title = self._fit_title(book.title or "Untitled")
        c.setFillColor(colors.HexColor("#15120E"))
        c.setFont("Times-Bold", 34)
        c.drawString(inset + 48, h - 170, title)
        c.setFont("Times-Italic", 15)
        sub = shorten(book.topic or book.genre or "A book in progress", width=120, placeholder="...")
        c.drawString(inset + 48, h - 205, sub)
        c.setFont("Times-Roman", 12)
        c.drawString(inset + 48, h - 232, (book.format_settings or {}).get("layout_name", "Editorial layout"))
        c.showPage()

    def _fit_title(self, title: str) -> str:
        return shorten(title.replace("\n", " ").strip(), width=58, placeholder="...")

    def _render_layout_page(self, c: canvas.Canvas, page: Page, upload_dir: Path) -> None:
        layout = page.layout_json or {}
        if layout.get("layout_schema") != "page-layout-1":
            raise ValueError(f"Page {page.page_number} has invalid layout_json; regenerate layout before export.")
        page_meta = layout.get("page") or {}
        elements = layout.get("elements")
        if not isinstance(elements, list) or not page_meta.get("width") or not page_meta.get("height"):
            raise ValueError(f"Page {page.page_number} has invalid layout_json; regenerate layout before export.")
        validation = layout.get("validation") or {}
        if isinstance(validation, dict) and validation.get("valid") is False:
            raise ValueError(f"Page {page.page_number} has invalid layout_json; regenerate layout before export.")

        sheet_w, sheet_h = A4
        margin = 36
        layout_w = float(page_meta["width"])
        layout_h = float(page_meta["height"])
        scale = min((sheet_w - 2 * margin) / layout_w, (sheet_h - 2 * margin) / layout_h)
        render_w = layout_w * scale
        render_h = layout_h * scale
        origin_x = (sheet_w - render_w) / 2
        origin_y = (sheet_h - render_h) / 2

        c.setFillColor(colors.HexColor("#F7F0E6")); c.rect(0, 0, sheet_w, sheet_h, fill=1, stroke=0)
        c.setFillColor(colors.white); c.roundRect(origin_x, origin_y, render_w, render_h, 8, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#8B4A43")); c.rect(origin_x + 12, origin_y + 12, 10, max(24, render_h - 24), fill=1, stroke=0)


        typography = layout.get("typography") or {}
        body_size = float(typography.get("body_size", 11) or 11)
        line_height = float(typography.get("line_height", 1.5) or 1.5)

        used_images: set[str] = set()
        for element in sorted(elements, key=lambda e: e.get("z", 0)):
            self._render_element(c, element, page, origin_x, origin_y, layout_w, layout_h, scale, upload_dir, used_images, body_size, line_height)
        c.showPage()


    def _resolve_text_element_content(self, element: dict, page: Page) -> str:
        direct = element.get("text")
        if isinstance(direct, str) and direct.strip():
            return direct
        role = str(element.get("role") or "").lower()
        if role == "page_label":
            return f"PAGE {page.page_number}"
        source = str(element.get("text_source") or "").lower()
        if source == "final_text":
            return page.final_text or ""
        if source == "generated_text":
            return page.generated_text or ""
        if source == "user_text":
            return page.user_text or ""
        if role == "body" or element.get("id") == "text_main":
            return page.final_text or page.generated_text or page.user_text or ""
        return ""

    def _render_element(self, c, element, page, ox, oy, layout_w, layout_h, scale, upload_dir, used_images, body_size: float, line_height: float):
        box = element.get("box") or {}
        x, y, w, h = box.get("x"), box.get("y"), box.get("w"), box.get("h")
        if any(v is None for v in (x, y, w, h)):
            return
        pdf_x = ox + float(x) * scale
        pdf_y = oy + layout_h * scale - (float(y) + float(h)) * scale
        pdf_w = float(w) * scale
        pdf_h = float(h) * scale
        t = element.get("type")
        if t == "text":
            text = self._resolve_text_element_content(element, page)
            role = (element.get("role") or "").lower()
            if not text:
                return
            font = "Times-Bold" if role in {"page_label", "label", "title", "kicker"} else "Times-Roman"
            text_value = text.upper() if role == "page_label" else text
            self._draw_wrapped_text(c, text_value, pdf_x, pdf_y, pdf_w, pdf_h, max(8.0, body_size - 1.5) if role == "page_label" else body_size, line_height=line_height, font=font)
        elif t == "caption":
            caption = element.get("text") or ""
            if not caption and element.get("image_id"):
                img = self._resolve_image(page, element.get("image_id"), used_images)
                caption = img.caption if img else ""
            if caption:
                caption_size = max(8.0, body_size - 1.0)
                self._draw_wrapped_text(c, caption, pdf_x, pdf_y, pdf_w, pdf_h, caption_size, line_height=line_height, font="Times-Italic")
        elif t == "image":
            img = self._resolve_image(page, element.get("image_id"), used_images)
            if not img:
                return
            image_path = upload_dir / img.stored_filename
            if not image_path.exists():
                return
            fit = element.get("fit", "contain")
            self._draw_image(c, image_path, pdf_x, pdf_y, pdf_w, pdf_h, fit=fit)

    def _resolve_image(self, page: Page, image_id: str | None, used_images: set[str]) -> PageImage | None:
        if image_id:
            for image in page.images:
                if image.id == image_id:
                    used_images.add(image.id)
                    return image
            return None
        for image in page.images:
            if image.id not in used_images:
                used_images.add(image.id)
                return image
        return None

    def _draw_image(self, c, image_path: Path, x: float, y: float, w: float, h: float, *, fit: str = "contain") -> None:
        reader = ImageReader(str(image_path))
        iw, ih = reader.getSize()
        if iw <= 0 or ih <= 0:
            return
        scale = max(w / iw, h / ih) if fit == "cover" else min(w / iw, h / ih)
        dw, dh = iw * scale, ih * scale
        dx, dy = x + (w - dw) / 2, y + (h - dh) / 2
        c.saveState()
        path = c.beginPath()
        path.rect(x, y, w, h)
        c.clipPath(path, stroke=0, fill=0)
        c.drawImage(reader, dx, dy, width=dw, height=dh, preserveAspectRatio=False, mask="auto")
        c.restoreState()

    def _draw_wrapped_text(self, c, text: str, x: float, y: float, w: float, h: float, size: float, *, line_height: float = 1.45, font: str = "Times-Roman") -> None:
        c.setFillColor(colors.HexColor("#15120E")); c.setFont(font, size)
        lines = []
        for paragraph in (text or "").split("\n"):
            lines.extend(simpleSplit(paragraph, font, size, w))
            if paragraph.strip() == "":
                lines.append("")
        leading = size * max(1.0, line_height)
        max_lines = max(1, int(h // leading))
        for idx, line in enumerate(lines[:max_lines]):
            c.drawString(x, y + h - ((idx + 1) * leading), line)
