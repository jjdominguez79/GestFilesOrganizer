from __future__ import annotations

from datetime import datetime
from pathlib import Path


class LogBuffer:
    def __init__(self) -> None:
        self.lines: list[str] = []

    def add(self, message: str) -> str:
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {message}"
        self.lines.append(line)
        return line

    def export(self, destination: Path) -> Path:
        destination.write_text("\n".join(self.lines), encoding="utf-8")
        return destination
