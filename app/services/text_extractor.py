from __future__ import annotations

from pathlib import Path

from PyPDF2 import PdfReader

from app.config.app_settings import AppSettings
from app.services.ocr_service import OcrService


class TextExtractor:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.ocr_service = OcrService(settings.ocr)

    def extract_pdf_text(self, pdf_path: Path) -> str:
        return "\n".join(page for _, page in self.extract_pdf_pages_text(pdf_path)).strip()

    def extract_pdf_pages_text(self, pdf_path: Path) -> list[tuple[int, str]]:
        try:
            reader = PdfReader(str(pdf_path))
        except Exception:
            return []
        texts: list[tuple[int, str]] = []
        total_pages = min(len(reader.pages), self.settings.ocr.pdf_max_pages)
        for page_index in range(total_pages):
            try:
                texts.append((page_index + 1, reader.pages[page_index].extract_text() or ""))
            except Exception:
                continue
        return texts

    def extract_pdf_text_with_ocr(self, pdf_path: Path) -> str:
        return self.ocr_service.extract_text_from_pdf(
            pdf_path, max_pages=self.settings.ocr.pdf_max_pages
        )

    def extract_pdf_ocr_pages_text(self, pdf_path: Path) -> list[tuple[int, str]]:
        text = self.extract_pdf_text_with_ocr(pdf_path)
        if not text:
            return []
        return [(1, text)]

    def extract_image_text(self, image_path: Path) -> str:
        return self.ocr_service.extract_text_from_image(image_path)
