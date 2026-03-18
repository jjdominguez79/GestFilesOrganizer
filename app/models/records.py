from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass(slots=True)
class InvoiceData:
    invoice_number: str = ""
    issuer: str = ""
    issuer_tax_id: str = ""
    taxable_base: Optional[float] = None
    vat_amount: Optional[float] = None
    total_amount: Optional[float] = None
    currency: str = ""
    inferred_fields: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ProcessedDocument:
    processed_at: datetime
    client_name: str
    original_name: str
    final_name: str
    original_path: Path
    final_path: Path
    file_type: str
    detection_method: str
    detected_date: Optional[datetime]
    assigned_year: str
    assigned_month: str
    status: str
    notes: str
    invoice_data: InvoiceData = field(default_factory=InvoiceData)


@dataclass(slots=True)
class FolderScanResult:
    path: Path
    pending_marker: bool
    pending_count: int


@dataclass(slots=True)
class ClientProcessResult:
    original_path: Path
    final_client_path: Path
    processed_documents: list[ProcessedDocument]
    total_candidates: int
    processed_count: int
    error_count: int
    renamed: bool = False
    rename_message: str = ""
    report_path: Optional[Path] = None

    @property
    def was_successful(self) -> bool:
        return self.error_count == 0
