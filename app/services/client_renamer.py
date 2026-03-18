from __future__ import annotations

import re
from pathlib import Path


class ClientRenamer:
    def build_target_name(self, original_name: str) -> str:
        cleaned = original_name.replace("_", "")
        cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
        return cleaned or original_name.strip()

    def safe_rename(self, folder_path: Path) -> tuple[Path, bool, str]:
        if "_" not in folder_path.name:
            return folder_path, False, "La carpeta no contiene '_' y no requiere renombrado."

        base_target = self.build_target_name(folder_path.name)
        candidate = folder_path.with_name(base_target)
        if candidate == folder_path:
            return folder_path, False, "El nombre resultante coincide con el actual."

        if candidate.exists():
            candidate = folder_path.with_name(f"{base_target} (procesado)")
            counter = 2
            while candidate.exists():
                candidate = folder_path.with_name(f"{base_target} (procesado {counter})")
                counter += 1

        folder_path.rename(candidate)
        return candidate, True, f"Renombrada: '{folder_path.name}' -> '{candidate.name}'"
