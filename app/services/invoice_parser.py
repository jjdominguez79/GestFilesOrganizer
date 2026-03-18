from __future__ import annotations

import re
from typing import Optional

from app.models.records import InvoiceData


AMOUNT_PATTERNS = {
    "taxable_base": [
        re.compile(r"base\s+imponible[\s:€]*([0-9][0-9\.\,]*)", re.IGNORECASE),
        re.compile(r"subtotal[\s:€]*([0-9][0-9\.\,]*)", re.IGNORECASE),
    ],
    "vat_amount": [
        re.compile(r"(?:cuota\s+iva|iva)[\s:€%]*([0-9][0-9\.\,]*)", re.IGNORECASE),
    ],
    "total_amount": [
        re.compile(r"(?:importe\s+total|total\s+factura|total)[\s:€]*([0-9][0-9\.\,]*)", re.IGNORECASE),
    ],
}


class InvoiceParser:
    CURRENCY_HINTS = {"EUR": "EUR", "€": "EUR", "USD": "USD", "$": "USD", "GBP": "GBP", "£": "GBP"}

    def parse(self, text: str) -> InvoiceData:
        if not text.strip():
            return InvoiceData()

        normalized = re.sub(r"[ \t]+", " ", text)
        lines = [line.strip() for line in normalized.splitlines() if line.strip()]
        invoice = InvoiceData()

        invoice.invoice_number = self._extract_invoice_number(normalized)
        invoice.issuer_tax_id = self._extract_tax_id(normalized)
        invoice.issuer = self._extract_issuer(lines, invoice.issuer_tax_id)
        invoice.taxable_base = self._extract_amount(normalized, "taxable_base")
        invoice.vat_amount = self._extract_amount(normalized, "vat_amount")
        invoice.total_amount = self._extract_amount(normalized, "total_amount")
        invoice.currency = self._extract_currency(normalized)

        invoice.inferred_fields = [
            name
            for name, value in (
                ("Número de factura", invoice.invoice_number),
                ("Emisor", invoice.issuer),
                ("NIF emisor", invoice.issuer_tax_id),
                ("Base imponible", invoice.taxable_base),
                ("Cuota IVA", invoice.vat_amount),
                ("Importe total", invoice.total_amount),
                ("Moneda", invoice.currency),
            )
            if value not in ("", None)
        ]
        return invoice

    def _extract_invoice_number(self, text: str) -> str:
        patterns = [
            re.compile(
                r"(?:factura|invoice|n[úu]mero\s+de\s+factura|n[ºo]\s*factura)[\s:#-]*([A-Z0-9][A-Z0-9\/\.-]{2,})",
                re.IGNORECASE,
            ),
            re.compile(r"\b(?:serie\s*[:#-]?\s*)?([A-Z]{1,4}[-/]?\d{3,})\b"),
        ]
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                return match.group(1).strip()
        return ""

    def _extract_tax_id(self, text: str) -> str:
        match = re.search(r"\b([A-Z]?\d{7,8}[A-Z]|\d{8}[A-Z]|[XYZ]\d{7}[A-Z])\b", text, re.IGNORECASE)
        return match.group(1).upper() if match else ""

    def _extract_issuer(self, lines: list[str], issuer_tax_id: str) -> str:
        for index, line in enumerate(lines[:12]):
            if "factura" in line.lower():
                window = lines[max(0, index - 3):index]
                for candidate in reversed(window):
                    if self._is_company_like(candidate):
                        return candidate
            if issuer_tax_id and issuer_tax_id in line.upper():
                for candidate in reversed(lines[max(0, index - 2):index + 1]):
                    if candidate.upper() == issuer_tax_id:
                        continue
                    if self._is_company_like(candidate):
                        return candidate
        for line in lines[:6]:
            if self._is_company_like(line):
                return line
        return ""

    @staticmethod
    def _is_company_like(value: str) -> bool:
        lowered = value.lower()
        if len(value) < 4 or any(token in lowered for token in ("www.", "@", "http")):
            return False
        return bool(
            re.search(
                r"(s\.l\.|s\.a\.|sl|sa|c\.b\.|scp|asesores|consultores|gesti[oó]n|servicios|holding|grupo|sociedad|empresa)",
                lowered,
            )
        ) or value == value.upper()

    def _extract_amount(self, text: str, field_name: str) -> Optional[float]:
        for pattern in AMOUNT_PATTERNS[field_name]:
            match = pattern.search(text)
            if match:
                return self._parse_decimal(match.group(1))
        return None

    def _extract_currency(self, text: str) -> str:
        for hint, currency in self.CURRENCY_HINTS.items():
            if hint in text:
                return currency
        return ""

    @staticmethod
    def _parse_decimal(value: str) -> Optional[float]:
        candidate = value.strip().replace(" ", "")
        if candidate.count(",") > 1 and "." not in candidate:
            candidate = candidate.replace(",", "")
        elif candidate.count(".") > 1 and "," not in candidate:
            candidate = candidate.replace(".", "")
        if "," in candidate and "." in candidate:
            if candidate.rfind(",") > candidate.rfind("."):
                candidate = candidate.replace(".", "").replace(",", ".")
            else:
                candidate = candidate.replace(",", "")
        else:
            candidate = candidate.replace(",", ".")
        try:
            return float(candidate)
        except ValueError:
            return None
