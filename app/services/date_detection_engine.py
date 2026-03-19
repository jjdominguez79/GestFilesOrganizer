from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime


DATE_REGEX = re.compile(
    r"\b("
    r"\d{2}[\/\-.]\d{2}[\/\-.]\d{4}"
    r"|"
    r"\d{4}[\/\-.]\d{2}[\/\-.]\d{2}"
    r")\b"
)

TABLE_SEPARATOR_REGEX = re.compile(r"(?:\s{3,}|\t|\|)")


@dataclass(frozen=True)
class DateDetectionConfig:
    positive_labels: tuple[str, ...]
    negative_labels: tuple[str, ...]
    strong_positive_labels: tuple[str, ...]
    strong_negative_labels: tuple[str, ...]
    weights: dict[str, int]
    low_confidence_threshold: int
    medium_confidence_threshold: int
    min_score_to_accept: int
    pages_to_analyze: int = 3


@dataclass(slots=True)
class PageText:
    page_number: int
    text: str


@dataclass(slots=True)
class DateCandidate:
    date: datetime
    date_text: str
    line_text: str
    page: int
    line_index: int
    zone: str
    label: str
    context_text: str
    score: int = 0
    reasons: list[str] = field(default_factory=list)

    def add_score(self, points: int, reason: str) -> None:
        self.score += points
        self.reasons.append(f"{points:+d} {reason}")


@dataclass(slots=True)
class DateSelection:
    detected_date: datetime | None
    method: str
    confidence: str
    confidence_score: int
    associated_label: str
    context_text: str
    page: int | None
    document_zone: str
    decision_summary: str
    candidates: list[DateCandidate] = field(default_factory=list)
    requires_manual_review: bool = False


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char)).lower()


class InvoiceDateDetector:
    def __init__(self, config: DateDetectionConfig) -> None:
        self.config = config
        self._positive_tokens = tuple(normalize_text(token) for token in config.positive_labels)
        self._negative_tokens = tuple(normalize_text(token) for token in config.negative_labels)
        self._strong_positive_tokens = tuple(normalize_text(token) for token in config.strong_positive_labels)
        self._strong_negative_tokens = tuple(normalize_text(token) for token in config.strong_negative_labels)

    def detect(self, pages: list[PageText], method: str) -> DateSelection:
        candidates = self.collect_candidates(pages)
        if not candidates:
            return DateSelection(
                detected_date=None,
                method=method,
                confidence="none",
                confidence_score=0,
                associated_label="",
                context_text="",
                page=None,
                document_zone="sin_texto",
                decision_summary="No se encontraron fechas candidatas en el texto analizado.",
                candidates=[],
                requires_manual_review=False,
            )

        self.score_candidates(candidates)
        candidates.sort(key=self._candidate_sort_key, reverse=True)
        winner = candidates[0]
        accepted = winner.score >= self.config.min_score_to_accept
        confidence = self._confidence_from_score(winner.score if accepted else 0)
        requires_review = confidence == "low" or not accepted
        method_suffix = method if accepted else f"{method}_BAJA_CONFIANZA"
        decision_summary = "; ".join(winner.reasons[:6]) if winner.reasons else "Sin trazabilidad disponible."
        if not accepted:
            decision_summary = (
                "La mejor fecha candidata no supera el umbral minimo. "
                f"Candidata={winner.date_text} score={winner.score}. {decision_summary}"
            )

        return DateSelection(
            detected_date=winner.date if accepted else None,
            method=method_suffix,
            confidence=confidence,
            confidence_score=winner.score if accepted else 0,
            associated_label=winner.label,
            context_text=winner.context_text,
            page=winner.page,
            document_zone=winner.zone,
            decision_summary=decision_summary,
            candidates=candidates,
            requires_manual_review=requires_review,
        )

    def collect_candidates(self, pages: list[PageText]) -> list[DateCandidate]:
        candidates: list[DateCandidate] = []
        for page in pages[: self.config.pages_to_analyze]:
            lines = [line.strip() for line in page.text.splitlines()]
            visible_lines = [line for line in lines if line]
            total_lines = max(len(visible_lines), 1)
            for line_index, line in enumerate(visible_lines):
                for match in DATE_REGEX.finditer(line):
                    parsed = self._parse_date(match.group(1))
                    if not parsed or not self._is_valid_date(parsed):
                        continue
                    zone = self._infer_zone(line_index, total_lines, line)
                    context = self._build_context(visible_lines, line_index)
                    label = self._find_best_label(context)
                    candidates.append(
                        DateCandidate(
                            date=parsed,
                            date_text=match.group(1),
                            line_text=line,
                            page=page.page_number,
                            line_index=line_index,
                            zone=zone,
                            label=label,
                            context_text=context,
                        )
                    )
        return candidates

    def score_candidates(self, candidates: list[DateCandidate]) -> None:
        for candidate in candidates:
            context_normalized = normalize_text(candidate.context_text)
            line_normalized = normalize_text(candidate.line_text)
            label_normalized = normalize_text(candidate.label)

            candidate.add_score(self.config.weights["base"], "base por coincidencia de fecha valida")

            if candidate.zone in self.config.weights:
                candidate.add_score(self.config.weights[candidate.zone], f"zona {candidate.zone}")

            if candidate.page == 1:
                candidate.add_score(self.config.weights["first_page"], "primera pagina")

            if candidate.line_index <= 5:
                candidate.add_score(self.config.weights["top_lines"], "primeras lineas")

            if label_normalized:
                candidate.add_score(self.config.weights["label_detected"], f"etiqueta detectada '{candidate.label}'")

            if label_normalized in self._strong_positive_tokens:
                candidate.add_score(self.config.weights["strong_positive_label"], "etiqueta fiscal principal")
            elif label_normalized in self._positive_tokens:
                candidate.add_score(self.config.weights["positive_label"], "etiqueta positiva")

            if label_normalized in self._strong_negative_tokens:
                candidate.add_score(self.config.weights["strong_negative_label"], "etiqueta secundaria penalizada")
            elif label_normalized in self._negative_tokens:
                candidate.add_score(self.config.weights["negative_label"], "etiqueta negativa")

            positive_hits = sum(1 for token in self._positive_tokens if token and token in context_normalized)
            negative_hits = sum(1 for token in self._negative_tokens if token and token in context_normalized)
            strong_negative_hits = sum(1 for token in self._strong_negative_tokens if token and token in context_normalized)
            strong_positive_hits = sum(1 for token in self._strong_positive_tokens if token and token in context_normalized)
            if strong_positive_hits:
                candidate.add_score(
                    self.config.weights["positive_context"] * strong_positive_hits,
                    "contexto con expresiones de emision/factura",
                )
            elif positive_hits:
                candidate.add_score(
                    self.config.weights["positive_context"] * positive_hits,
                    "contexto cercano con etiquetas positivas",
                )
            if negative_hits:
                candidate.add_score(
                    self.config.weights["negative_context"] * negative_hits,
                    "contexto cercano con etiquetas no fiscales",
                )
            if strong_negative_hits:
                candidate.add_score(
                    self.config.weights["strong_negative_context"] * strong_negative_hits,
                    "contexto dominado por vencimiento/periodo/cargo",
                )

            if self._looks_like_range(line_normalized, candidate.date_text):
                candidate.add_score(self.config.weights["date_range_penalty"], "fecha dentro de intervalo o periodo")

            if self._looks_like_table(candidate.context_text):
                candidate.add_score(self.config.weights["table_penalty"], "bloque con aspecto de tabla/detalle")

            if re.search(r"\b(?:factura|invoice)\b", context_normalized):
                candidate.add_score(self.config.weights["invoice_hint"], "referencia explicita a factura")

            if re.search(r"\b(?:consumo|lectura|historico|detalle|operacion|abono|remesa|adeudo)\b", context_normalized):
                candidate.add_score(
                    self.config.weights["detail_penalty"],
                    "contexto de detalle operativo o historico",
                )

    @staticmethod
    def _candidate_sort_key(candidate: DateCandidate) -> tuple[int, int, int, int]:
        zone_priority = {"header": 4, "top": 3, "party_block": 2, "body": 1, "table": 0, "footer": -1}
        return (candidate.score, zone_priority.get(candidate.zone, 0), -candidate.page, -candidate.line_index)

    def _confidence_from_score(self, score: int) -> str:
        if score >= self.config.medium_confidence_threshold:
            return "high"
        if score >= self.config.low_confidence_threshold:
            return "medium"
        if score > 0:
            return "low"
        return "none"

    def _infer_zone(self, line_index: int, total_lines: int, line: str) -> str:
        if line_index <= 2:
            return "header"
        if line_index <= 8:
            return "top"
        if line_index >= max(total_lines - 3, 0):
            return "footer"
        if self._looks_like_table(line):
            return "table"
        lowered = normalize_text(line)
        if re.search(r"\b(?:nif|cif|cliente|titular|domicilio|razon social|direccion)\b", lowered):
            return "party_block"
        return "body"

    def _find_best_label(self, context: str) -> str:
        context_normalized = normalize_text(context)
        for token in self._strong_positive_tokens:
            if token in context_normalized:
                return token
        for token in self._positive_tokens:
            if token in context_normalized:
                return token
        for token in self._strong_negative_tokens:
            if token in context_normalized:
                return token
        for token in self._negative_tokens:
            if token in context_normalized:
                return token
        return ""

    @staticmethod
    def _build_context(lines: list[str], index: int) -> str:
        start = max(0, index - 1)
        end = min(len(lines), index + 2)
        return "\n".join(lines[start:end]).strip()

    @staticmethod
    def _parse_date(date_str: str) -> datetime | None:
        for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%Y/%m/%d", "%Y-%m-%d", "%Y.%m.%d"):
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None

    @staticmethod
    def _is_valid_date(value: datetime) -> bool:
        return 2000 <= value.year <= 2100

    @staticmethod
    def _looks_like_range(text: str, date_text: str) -> bool:
        escaped = re.escape(date_text)
        patterns = (
            rf"{escaped}\s*(?:a|-|al|hasta)\s*\d{{2}}[\/\-.]\d{{2}}[\/\-.]\d{{4}}",
            rf"\d{{2}}[\/\-.]\d{{2}}[\/\-.]\d{{4}}\s*(?:a|-|al|hasta)\s*{escaped}",
        )
        lowered = normalize_text(text)
        return any(re.search(pattern, lowered) for pattern in patterns) or bool(
            re.search(r"\b(?:periodo|desde|hasta|ciclo|periodo facturado)\b", lowered)
        )

    @staticmethod
    def _looks_like_table(text: str) -> bool:
        lines = [line for line in text.splitlines() if line.strip()]
        if any(TABLE_SEPARATOR_REGEX.search(line) for line in lines):
            return True
        if len(lines) >= 2 and sum(line.count("  ") for line in lines) >= 3:
            return True
        return False
