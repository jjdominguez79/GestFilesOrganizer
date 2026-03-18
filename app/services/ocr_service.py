from __future__ import annotations

from pathlib import Path

from app.config.app_settings import OcrSettings

try:
    import pytesseract
except ImportError:  # pragma: no cover
    pytesseract = None

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None

try:
    from pdf2image import convert_from_path
except ImportError:  # pragma: no cover
    convert_from_path = None


class OcrService:
    def __init__(self, settings: OcrSettings) -> None:
        self.settings = settings
        self.available = bool(
            settings.enabled and pytesseract and Image and convert_from_path
        )
        if self.available:
            pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd

    def extract_text_from_pdf(self, pdf_path: Path, max_pages: int | None = None) -> str:
        if not self.available:
            return ""
        pages = max_pages or self.settings.pdf_max_pages
        try:
            images = convert_from_path(str(pdf_path), first_page=1, last_page=pages)
        except Exception:
            return ""
        texts = []
        for image in images:
            try:
                texts.append(
                    pytesseract.image_to_string(image, lang=self.settings.languages)
                )
            except Exception:
                continue
        return "\n".join(texts).strip()

    def extract_text_from_image(self, image_path: Path) -> str:
        if not self.available:
            return ""
        try:
            image = Image.open(image_path)
            return pytesseract.image_to_string(image, lang=self.settings.languages).strip()
        except Exception:
            return ""
