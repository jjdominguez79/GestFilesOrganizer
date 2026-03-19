from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from app.config.app_settings import AppSettings
from app.services.date_detection_engine import InvoiceDateDetector, PageText
from app.services.text_extractor import TextExtractor


@dataclass(slots=True)
class DateDetectionResult:
    date: datetime | None
    method: str
    extracted_text: str = ""
    confidence: str = "none"
    confidence_score: int = 0
    associated_label: str = ""
    context_text: str = ""
    page: int | None = None
    document_zone: str = ""
    decision_summary: str = ""
    requires_manual_review: bool = False


class DateExtractor:
    def __init__(self, settings: AppSettings, text_extractor: TextExtractor) -> None:
        self.settings = settings
        self.text_extractor = text_extractor
        self.detector = InvoiceDateDetector(settings.date_detection.to_config())

    @staticmethod
    def modified_date(file_path: Path) -> datetime:
        return datetime.fromtimestamp(file_path.stat().st_mtime)

    @staticmethod
    def _merge_page_text(pages: list[PageText]) -> str:
        return "\n".join(page.text for page in pages if page.text.strip()).strip()

    @staticmethod
    def _to_page_text(items: list[tuple[int, str]]) -> list[PageText]:
        return [PageText(page_number=page_number, text=text) for page_number, text in items if text.strip()]

    def detect_date(self, file_path: Path, use_modified_fallback: bool) -> DateDetectionResult:
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            pdf_pages = self._to_page_text(self.text_extractor.extract_pdf_pages_text(file_path))
            pdf_selection = self.detector.detect(pdf_pages, method="PDF_TEXTO")
            merged_pdf_text = self._merge_page_text(pdf_pages)
            if pdf_selection.detected_date:
                return DateDetectionResult(
                    date=pdf_selection.detected_date,
                    method=pdf_selection.method,
                    extracted_text=merged_pdf_text,
                    confidence=pdf_selection.confidence,
                    confidence_score=pdf_selection.confidence_score,
                    associated_label=pdf_selection.associated_label,
                    context_text=pdf_selection.context_text,
                    page=pdf_selection.page,
                    document_zone=pdf_selection.document_zone,
                    decision_summary=pdf_selection.decision_summary,
                    requires_manual_review=pdf_selection.requires_manual_review,
                )

            ocr_pages = self._to_page_text(self.text_extractor.extract_pdf_ocr_pages_text(file_path))
            ocr_selection = self.detector.detect(ocr_pages, method="PDF_OCR")
            merged_ocr_text = self._merge_page_text(ocr_pages)
            if ocr_selection.detected_date:
                return DateDetectionResult(
                    date=ocr_selection.detected_date,
                    method=ocr_selection.method,
                    extracted_text="\n".join(part for part in (merged_pdf_text, merged_ocr_text) if part).strip(),
                    confidence=ocr_selection.confidence,
                    confidence_score=ocr_selection.confidence_score,
                    associated_label=ocr_selection.associated_label,
                    context_text=ocr_selection.context_text,
                    page=ocr_selection.page,
                    document_zone=ocr_selection.document_zone,
                    decision_summary=ocr_selection.decision_summary,
                    requires_manual_review=ocr_selection.requires_manual_review,
                )

            merged_text = "\n".join(part for part in (merged_pdf_text, merged_ocr_text) if part).strip()
            if use_modified_fallback:
                return DateDetectionResult(
                    date=self.modified_date(file_path),
                    method="FECHA_MODIFICACION",
                    extracted_text=merged_text,
                    confidence="fallback",
                    confidence_score=0,
                    associated_label="fecha_modificacion",
                    context_text="Fallback a fecha de modificacion del archivo.",
                    page=None,
                    document_zone="filesystem",
                    decision_summary="No se encontro una fecha documental fiable y se utilizo la fecha de modificacion.",
                    requires_manual_review=True,
                )
            return DateDetectionResult(
                date=None,
                method="SIN_FECHA",
                extracted_text=merged_text,
                confidence="none",
                confidence_score=0,
                associated_label="",
                context_text="",
                page=None,
                document_zone="sin_fecha",
                decision_summary="No se encontro ninguna fecha fiscal con confianza suficiente.",
                requires_manual_review=True,
            )

        if suffix in {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".gif", ".webp"}:
            image_text = self.text_extractor.extract_image_text(file_path)
            image_pages = [PageText(page_number=1, text=image_text)] if image_text.strip() else []
            selection = self.detector.detect(image_pages, method="IMG_OCR")
            if selection.detected_date:
                return DateDetectionResult(
                    date=selection.detected_date,
                    method=selection.method,
                    extracted_text=image_text,
                    confidence=selection.confidence,
                    confidence_score=selection.confidence_score,
                    associated_label=selection.associated_label,
                    context_text=selection.context_text,
                    page=selection.page,
                    document_zone=selection.document_zone,
                    decision_summary=selection.decision_summary,
                    requires_manual_review=selection.requires_manual_review,
                )
            if use_modified_fallback:
                return DateDetectionResult(
                    date=self.modified_date(file_path),
                    method="FECHA_MODIFICACION",
                    extracted_text=image_text,
                    confidence="fallback",
                    confidence_score=0,
                    associated_label="fecha_modificacion",
                    context_text="Fallback a fecha de modificacion del archivo.",
                    page=None,
                    document_zone="filesystem",
                    decision_summary="No se encontro fecha en OCR y se utilizo la fecha de modificacion.",
                    requires_manual_review=True,
                )
            return DateDetectionResult(
                date=None,
                method="SIN_FECHA",
                extracted_text=image_text,
                confidence="none",
                confidence_score=0,
                associated_label="",
                context_text="",
                page=None,
                document_zone="sin_fecha",
                decision_summary="No se encontro fecha fiscal en la imagen.",
                requires_manual_review=True,
            )

        if use_modified_fallback:
            return DateDetectionResult(
                date=self.modified_date(file_path),
                method="FECHA_MODIFICACION",
                extracted_text="",
                confidence="fallback",
                confidence_score=0,
                associated_label="fecha_modificacion",
                context_text="Fallback por tipo de archivo no analizable.",
                page=None,
                document_zone="filesystem",
                decision_summary="Tipo de archivo no analizable; se usa fecha de modificacion.",
                requires_manual_review=True,
            )
        return DateDetectionResult(
            date=None,
            method="SIN_FECHA",
            extracted_text="",
            confidence="none",
            confidence_score=0,
            associated_label="",
            context_text="",
            page=None,
            document_zone="sin_fecha",
            decision_summary="Tipo de archivo no analizable y sin fallback activado.",
            requires_manual_review=True,
        )
