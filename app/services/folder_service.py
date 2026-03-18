from __future__ import annotations

import re
from pathlib import Path

from app.config.app_settings import AppSettings
from app.models.records import FolderScanResult


class FolderService:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings

    @staticmethod
    def file_is_already_organized(client_folder: Path, file_path: Path) -> bool:
        try:
            relative = file_path.relative_to(client_folder)
        except ValueError:
            return False

        parts = relative.parts
        if "SIN_FECHA" in parts:
            return True

        if len(parts) >= 3:
            year = parts[0]
            year_month = parts[1]
            if re.fullmatch(r"\d{4}", year) and re.fullmatch(r"\d{4}-\d{2}", year_month):
                return True
        return False

    def get_candidate_files(self, client_folder: Path) -> list[Path]:
        files: list[Path] = []
        for path in client_folder.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in self.settings.valid_extensions:
                continue
            if self.file_is_already_organized(client_folder, path):
                continue
            files.append(path)
        return files

    def scan_clients(self, root_folder: Path) -> list[FolderScanResult]:
        results: list[FolderScanResult] = []
        for child in sorted((p for p in root_folder.iterdir() if p.is_dir()), key=lambda item: item.name.lower()):
            pending_count = len(self.get_candidate_files(child))
            results.append(
                FolderScanResult(
                    path=child,
                    pending_marker="_" in child.name,
                    pending_count=pending_count,
                )
            )
        return results
