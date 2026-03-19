from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.services.date_detection_engine import DateDetectionConfig


VALID_EXTENSIONS = {
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
    ".tif",
    ".tiff",
    ".bmp",
    ".gif",
    ".webp",
}


@dataclass(frozen=True)
class OcrSettings:
    enabled: bool = False
    tesseract_cmd: str = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    pdf_max_pages: int = 3
    languages: str = "spa+eng"


@dataclass(frozen=True)
class BrandingSettings:
    owner_name: str = "Asesoría Gestinem S.L."
    suite_name: str = "Gestinem"
    product_name: str = "GestFiles Organizer"
    tagline: str = "Gestión documental para despacho profesional"
    description: str = "Panel operativo para organizar documentación de clientes, mantener trazabilidad por ejecución y acelerar el trabajo interno del despacho."
    support_phone: str = "691 474 519"
    support_portal: str = "Portal Gestinem / Atención directa"
    website: str = "www.gestinem.es"


@dataclass(frozen=True)
class DateScoringSettings:
    positive_labels: tuple[str, ...] = (
        "fecha factura",
        "fecha de factura",
        "fecha emision",
        "fecha de emision",
        "emitida el",
        "expedida el",
        "fecha expedicion",
        "fecha documento",
        "invoice date",
        "date of issue",
    )
    negative_labels: tuple[str, ...] = (
        "vencimiento",
        "fecha de pago",
        "cargo en cuenta",
        "periodo",
        "desde",
        "hasta",
        "consumo",
        "lectura anterior",
        "lectura actual",
        "detalle",
        "operacion",
        "valor",
        "abono",
        "remesa",
        "adeudo",
        "fecha de cobro",
        "fecha de cargo",
        "servicio prestado",
        "periodo facturado",
        "ciclo",
        "historico",
    )
    strong_positive_labels: tuple[str, ...] = (
        "fecha factura",
        "fecha de factura",
        "fecha emision",
        "fecha de emision",
        "invoice date",
        "date of issue",
    )
    strong_negative_labels: tuple[str, ...] = (
        "vencimiento",
        "fecha de pago",
        "fecha de cargo",
        "fecha de cobro",
        "periodo facturado",
        "cargo en cuenta",
        "servicio prestado",
        "historico",
    )
    weights: dict[str, int] = field(
        default_factory=lambda: {
            "base": 15,
            "header": 40,
            "top": 28,
            "party_block": 14,
            "body": 8,
            "table": -30,
            "footer": -18,
            "first_page": 14,
            "top_lines": 18,
            "label_detected": 12,
            "strong_positive_label": 80,
            "positive_label": 38,
            "strong_negative_label": -90,
            "negative_label": -42,
            "positive_context": 10,
            "negative_context": -12,
            "strong_negative_context": -25,
            "date_range_penalty": -35,
            "table_penalty": -20,
            "detail_penalty": -18,
            "invoice_hint": 12,
        }
    )
    low_confidence_threshold: int = 45
    medium_confidence_threshold: int = 95
    min_score_to_accept: int = 28
    pages_to_analyze: int = 3

    def to_config(self) -> DateDetectionConfig:
        return DateDetectionConfig(
            positive_labels=self.positive_labels,
            negative_labels=self.negative_labels,
            strong_positive_labels=self.strong_positive_labels,
            strong_negative_labels=self.strong_negative_labels,
            weights=self.weights,
            low_confidence_threshold=self.low_confidence_threshold,
            medium_confidence_threshold=self.medium_confidence_threshold,
            min_score_to_accept=self.min_score_to_accept,
            pages_to_analyze=self.pages_to_analyze,
        )


@dataclass(frozen=True)
class AppSettings:
    app_name: str = "GestFiles Organizer"
    company_name: str = "Asesoría Gestinem S.L."
    valid_extensions: set[str] = field(default_factory=lambda: set(VALID_EXTENSIONS))
    report_base_name: str = "Facturas procesadas"
    ocr: OcrSettings = field(default_factory=OcrSettings)
    branding: BrandingSettings = field(default_factory=BrandingSettings)
    date_detection: DateScoringSettings = field(default_factory=DateScoringSettings)

    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[2]


SETTINGS = AppSettings()
