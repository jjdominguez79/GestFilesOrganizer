from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from app.config.app_settings import AppSettings
from app.models.records import ClientProcessResult, ProcessedDocument
from app.services.client_renamer import ClientRenamer
from app.services.date_extractor import DateExtractor
from app.services.folder_service import FolderService
from app.services.invoice_parser import InvoiceParser
from app.services.report_service import ReportService
from app.services.text_extractor import TextExtractor


LogCallback = Optional[Callable[[str], None]]
ProgressCallback = Optional[Callable[[int, int, str], None]]


class DocumentProcessor:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.folder_service = FolderService(settings)
        self.text_extractor = TextExtractor(settings)
        self.date_extractor = DateExtractor(settings, self.text_extractor)
        self.invoice_parser = InvoiceParser()
        self.report_service = ReportService(settings)
        self.client_renamer = ClientRenamer()

    @staticmethod
    def ensure_unique_name(destination: Path) -> Path:
        if not destination.exists():
            return destination
        base = destination.stem
        suffix = destination.suffix
        counter = 1
        while True:
            candidate = destination.with_name(f"{base}_{counter}{suffix}")
            if not candidate.exists():
                return candidate
            counter += 1

    def transfer_file(self, source: Path, destination: Path, move_files: bool) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination = self.ensure_unique_name(destination)
        if move_files:
            shutil.move(str(source), str(destination))
        else:
            shutil.copy2(source, destination)
        return destination

    @staticmethod
    def cleanup_empty_directories(base_folder: Path) -> None:
        for folder in sorted(base_folder.rglob("*"), key=lambda item: len(item.parts), reverse=True):
            if not folder.is_dir():
                continue
            try:
                if not any(folder.iterdir()):
                    folder.rmdir()
            except Exception:
                continue

    def process_client(
        self,
        client_folder: Path,
        move_files: bool,
        use_modified_fallback: bool,
        remove_underscore_marker: bool,
        log_callback: LogCallback = None,
        progress_callback: ProgressCallback = None,
    ) -> ClientProcessResult:
        candidates = self.folder_service.get_candidate_files(client_folder)
        documents: list[ProcessedDocument] = []
        error_count = 0
        total_candidates = len(candidates)
        active_client_folder = client_folder

        if log_callback:
            log_callback(f"===== CLIENTE: {client_folder.name} =====")
            log_callback(f"Archivos detectados: {total_candidates}")

        for index, file_path in enumerate(candidates, start=1):
            status_message = f"{client_folder.name} · {file_path.name}"
            try:
                record = self._process_file(
                    client_folder=active_client_folder,
                    file_path=file_path,
                    move_files=move_files,
                    use_modified_fallback=use_modified_fallback,
                )
                documents.append(record)
                if log_callback:
                    log_callback(
                        f"[{index}/{total_candidates}] {record.original_name} -> {record.final_path} "
                        f"({record.detection_method}; {record.status}; confianza={record.detection_confidence})"
                    )
                    if record.detection_decision:
                        log_callback(
                            f"    Fecha: {record.detected_date.strftime('%d/%m/%Y') if record.detected_date else 'N/D'} | "
                            f"etiqueta={record.detection_label or 'sin etiqueta'} | "
                            f"zona={record.detection_zone or 'desconocida'} | "
                            f"pagina={record.detection_page or '-'} | "
                            f"decision={record.detection_decision}"
                        )
            except Exception as exc:
                error_count += 1
                if log_callback:
                    log_callback(f"[ERROR] {file_path}: {exc}")
            finally:
                if progress_callback:
                    progress_callback(index, total_candidates, status_message)

        if move_files:
            self.cleanup_empty_directories(active_client_folder)

        renamed = False
        rename_message = ""
        if remove_underscore_marker and error_count == 0:
            try:
                active_client_folder, renamed, rename_message = self.client_renamer.safe_rename(active_client_folder)
                if log_callback:
                    log_callback(rename_message)
            except Exception as exc:
                rename_message = f"Error al renombrar '{client_folder.name}': {exc}"
                if log_callback:
                    log_callback(f"[ERROR] {rename_message}")
        elif remove_underscore_marker and error_count > 0:
            rename_message = "Renombrado omitido por errores críticos durante el procesamiento."
            if log_callback:
                log_callback(rename_message)

        if documents and active_client_folder != client_folder:
            self._synchronize_documents_with_client_folder(
                documents=documents,
                original_client_folder=client_folder,
                final_client_folder=active_client_folder,
            )

        report_path: Path | None = None
        if documents:
            try:
                report_path = self.report_service.generate_client_report(active_client_folder, documents)
                if log_callback:
                    log_callback(f"Excel generado en raíz de cliente: {report_path}")
            except Exception as exc:
                error_count += 1
                if log_callback:
                    log_callback(
                        f"[ERROR] No se pudo generar el Excel en la raíz de {active_client_folder.name}: {exc}"
                    )

        return ClientProcessResult(
            original_path=client_folder,
            final_client_path=active_client_folder,
            processed_documents=documents,
            total_candidates=total_candidates,
            processed_count=len(documents),
            error_count=error_count,
            renamed=renamed,
            rename_message=rename_message,
            report_path=report_path,
        )

    def _process_file(
        self,
        client_folder: Path,
        file_path: Path,
        move_files: bool,
        use_modified_fallback: bool,
    ) -> ProcessedDocument:
        detection = self.date_extractor.detect_date(file_path, use_modified_fallback)
        if detection.date:
            year = f"{detection.date.year}"
            year_month = f"{detection.date.year}-{detection.date.month:02d}"
            destination_folder = client_folder / year / year_month
        else:
            year = ""
            year_month = ""
            destination_folder = client_folder / "SIN_FECHA"

        destination = self.transfer_file(file_path, destination_folder / file_path.name, move_files)
        invoice_data = self.invoice_parser.parse(detection.extracted_text)
        notes_parts = []
        if not detection.extracted_text.strip():
            notes_parts.append("Sin texto útil para inferencia de factura.")
        if invoice_data.inferred_fields:
            notes_parts.append(f"Campos inferidos: {', '.join(invoice_data.inferred_fields)}")
        else:
            notes_parts.append("No se pudieron inferir campos de factura.")
        notes_parts.append(
            f"Fecha={detection.date.strftime('%d/%m/%Y') if detection.date else 'N/D'} | "
            f"confianza={detection.confidence} | etiqueta={detection.associated_label or 'sin etiqueta'} | "
            f"zona={detection.document_zone or 'desconocida'}"
        )
        if detection.requires_manual_review:
            notes_parts.append("Revisar fecha manualmente.")

        return ProcessedDocument(
            processed_at=datetime.now(),
            client_name=client_folder.name,
            original_name=file_path.name,
            final_name=destination.name,
            original_path=file_path,
            final_path=destination,
            file_type=file_path.suffix.lower().lstrip("."),
            detection_method=detection.method,
            detected_date=detection.date,
            detection_confidence=detection.confidence,
            detection_label=detection.associated_label,
            detection_context=detection.context_text,
            detection_zone=detection.document_zone,
            detection_page=detection.page,
            detection_decision=detection.decision_summary,
            requires_manual_review=detection.requires_manual_review,
            assigned_year=year,
            assigned_month=year_month,
            status="Procesado",
            notes=" | ".join(notes_parts),
            invoice_data=invoice_data,
        )

    @staticmethod
    def _synchronize_documents_with_client_folder(
        documents: list[ProcessedDocument],
        original_client_folder: Path,
        final_client_folder: Path,
    ) -> None:
        for document in documents:
            document.client_name = final_client_folder.name
            try:
                relative = document.final_path.relative_to(original_client_folder)
            except ValueError:
                continue
            document.final_path = final_client_folder / relative
