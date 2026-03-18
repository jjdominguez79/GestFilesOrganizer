from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


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
    owner_name: str = "Wolters Kluwer"
    suite_name: str = "A3 Software de Gestión"
    product_name: str = "Gest2A3Eco"
    tagline: str = "Entorno de trabajo para asesorías y despachos profesionales"
    description: str = "Panel documental con organización por cliente y control operativo orientado a trabajo administrativo intensivo."
    support_phone: str = "900 11 11 66"
    support_portal: str = "a3responde / Área clientes"
    website: str = "wolterskluwer.com/es-es/solutions/a3"


@dataclass(frozen=True)
class AppSettings:
    app_name: str = "GestFiles Organizer"
    company_name: str = "Despacho Profesional"
    valid_extensions: set[str] = field(default_factory=lambda: set(VALID_EXTENSIONS))
    report_base_name: str = "Facturas procesadas"
    ocr: OcrSettings = field(default_factory=OcrSettings)
    branding: BrandingSettings = field(default_factory=BrandingSettings)

    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[2]


SETTINGS = AppSettings()
