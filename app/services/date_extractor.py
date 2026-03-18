from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.services.text_extractor import TextExtractor


DATE_PATTERNS_DIRECT = [
    re.compile(r"\b(\d{2})[\/\-.](\d{2})[\/\-.](\d{4})\b"),
    re.compile(r"\b(\d{4})[\/\-.](\d{2})[\/\-.](\d{2})\b"),
]

DATE_PATTERNS_CONTEXT = [
    re.compile(
        r"(fecha(?:\s+de)?(?:\s+factura)?|fecha\s+emisi[oó]n|fecha\s+de\s+emisi[oó]n|fecha\s+expedici[oó]n|emitida\s+el)"
        r"[\s:.-]{0,15}"
        r"(\d{2}[\/\-.]\d{2}[\/\-.]\d{4}|\d{4}[\/\-.]\d{2}[\/\-.]\d{2})",
        re.IGNORECASE,
    ),
]

EXCLUSION_PATTERNS = [
    re.compile(r"vencimiento", re.IGNORECASE),
    re.compile(r"fecha\s+de\s+pago", re.IGNORECASE),
    re.compile(r"pedido", re.IGNORECASE),
    re.compile(r"albar[aá]n", re.IGNORECASE),
]


@dataclass(slots=True)
class DateDetectionResult:
    date: Optional[datetime]
    method: str
    extracted_text: str = ""


class DateExtractor:
    def __init__(self, text_extractor: TextExtractor) -> None:
        self.text_extractor = text_extractor

    @staticmethod
    def normalize_spaces(text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def parse_date(date_str: str) -> Optional[datetime]:
        for fmt in (
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%d.%m.%Y",
            "%Y/%m/%d",
            "%Y-%m-%d",
            "%Y.%m.%d",
        ):
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None

    @staticmethod
    def is_valid_date(value: datetime) -> bool:
        return 2000 <= value.year <= 2100

    def find_dates(self, text: str) -> list[tuple[datetime, int]]:
        normalized = self.normalize_spaces(text)
        results: list[tuple[datetime, int]] = []

        for pattern in DATE_PATTERNS_CONTEXT:
            for match in pattern.finditer(normalized):
                date_text = match.group(2)
                parsed = self.parse_date(date_text)
                if parsed and self.is_valid_date(parsed):
                    results.append((parsed, 100))

        for pattern in DATE_PATTERNS_DIRECT:
            for match in pattern.finditer(normalized):
                parsed = self.parse_date(match.group(0))
                if not parsed or not self.is_valid_date(parsed):
                    continue
                start = max(0, match.start() - 50)
                end = min(len(normalized), match.end() + 50)
                context = normalized[start:end].lower()
                score = 10
                if any(
                    token in context
                    for token in ("fecha", "factura", "emision", "emisión", "expedicion", "expedición")
                ):
                    score += 20
                if any(pattern.search(context) for pattern in EXCLUSION_PATTERNS):
                    score -= 20
                results.append((parsed, score))
        return results

    def choose_best_date(self, text: str) -> Optional[datetime]:
        dates = self.find_dates(text)
        if not dates:
            return None
        dates.sort(key=lambda item: (-item[1], item[0]))
        return dates[0][0]

    @staticmethod
    def modified_date(file_path: Path) -> datetime:
        return datetime.fromtimestamp(file_path.stat().st_mtime)

    def detect_date(self, file_path: Path, use_modified_fallback: bool) -> DateDetectionResult:
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            text = self.text_extractor.extract_pdf_text(file_path)
            date = self.choose_best_date(text)
            if date:
                return DateDetectionResult(date=date, method="PDF_TEXTO", extracted_text=text)

            ocr_text = self.text_extractor.extract_pdf_text_with_ocr(file_path)
            date = self.choose_best_date(ocr_text)
            if date:
                return DateDetectionResult(date=date, method="PDF_OCR", extracted_text=ocr_text)
            merged_text = "\n".join(part for part in (text, ocr_text) if part).strip()
            if use_modified_fallback:
                return DateDetectionResult(
                    date=self.modified_date(file_path),
                    method="FECHA_MODIFICACION",
                    extracted_text=merged_text,
                )
            return DateDetectionResult(date=None, method="SIN_FECHA", extracted_text=merged_text)

        if suffix in {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".gif", ".webp"}:
            text = self.text_extractor.extract_image_text(file_path)
            date = self.choose_best_date(text)
            if date:
                return DateDetectionResult(date=date, method="IMG_OCR", extracted_text=text)
            if use_modified_fallback:
                return DateDetectionResult(
                    date=self.modified_date(file_path),
                    method="FECHA_MODIFICACION",
                    extracted_text=text,
                )
            return DateDetectionResult(date=None, method="SIN_FECHA", extracted_text=text)

        if use_modified_fallback:
            return DateDetectionResult(
                date=self.modified_date(file_path),
                method="FECHA_MODIFICACION",
                extracted_text="",
            )
        return DateDetectionResult(date=None, method="SIN_FECHA", extracted_text="")
