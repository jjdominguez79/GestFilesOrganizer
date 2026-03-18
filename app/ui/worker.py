from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from app.config.app_settings import AppSettings
from app.services.document_processor import DocumentProcessor
from app.services.folder_service import FolderService


class ProcessingWorker(QThread):
    log_message = Signal(str)
    global_progress = Signal(int, int)
    client_progress = Signal(str, int, int)
    client_finished = Signal(object)
    finished_summary = Signal(int, int, int)
    failed = Signal(str)

    def __init__(
        self,
        settings: AppSettings,
        client_paths: list[Path],
        move_files: bool,
        use_modified_fallback: bool,
        remove_underscore_marker: bool,
    ) -> None:
        super().__init__()
        self.settings = settings
        self.client_paths = client_paths
        self.move_files = move_files
        self.use_modified_fallback = use_modified_fallback
        self.remove_underscore_marker = remove_underscore_marker
        self.document_processor = DocumentProcessor(settings)
        self.folder_service = FolderService(settings)

    def run(self) -> None:
        try:
            total_files = sum(len(self.folder_service.get_candidate_files(path)) for path in self.client_paths)
            processed_total = 0
            error_total = 0
            current_global = 0
            self.global_progress.emit(0, max(total_files, 1))
            self.log_message.emit(f"Clientes seleccionados: {len(self.client_paths)}")
            self.log_message.emit(f"Archivos pendientes detectados: {total_files}")

            for client_path in self.client_paths:
                def progress_callback(current: int, total: int, _message: str) -> None:
                    nonlocal current_global
                    current_global += 1
                    self.client_progress.emit(client_path.name, current, total)
                    self.global_progress.emit(current_global, max(total_files, 1))

                result = self.document_processor.process_client(
                    client_folder=client_path,
                    move_files=self.move_files,
                    use_modified_fallback=self.use_modified_fallback,
                    remove_underscore_marker=self.remove_underscore_marker,
                    log_callback=self.log_message.emit,
                    progress_callback=progress_callback,
                )
                processed_total += result.processed_count
                error_total += result.error_count
                self.client_finished.emit(result)
            self.finished_summary.emit(processed_total, total_files, error_total)
        except Exception as exc:
            self.failed.emit(str(exc))
