from __future__ import annotations

import unittest

from app.config.app_settings import DateScoringSettings
from app.services.date_detection_engine import InvoiceDateDetector, PageText


class InvoiceDateDetectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.detector = InvoiceDateDetector(DateScoringSettings().to_config())

    def test_prefers_invoice_date_over_period_and_charge_date(self) -> None:
        text = """
        FACTURA ELECTRICA
        Fecha factura: 15/02/2025
        Periodo facturado: 01/01/2025 a 31/01/2025
        Fecha de cargo: 20/02/2025
        """
        selection = self.detector.detect([PageText(1, text)], "PDF_TEXTO")
        self.assertIsNotNone(selection.detected_date)
        self.assertEqual(selection.detected_date.strftime("%d/%m/%Y"), "15/02/2025")
        self.assertIn("fecha factura", selection.associated_label)
        self.assertIn("etiqueta fiscal principal", selection.decision_summary)

    def test_prefers_header_date_over_detail_dates(self) -> None:
        text = """
        FACTURA TELEFONIA
        18/03/2025
        Cliente: ACME

        Detalle de consumos
        Llamada 01/03/2025 09:10
        Llamada 02/03/2025 10:10
        Historico de cargos 05/03/2025
        """
        selection = self.detector.detect([PageText(1, text)], "PDF_TEXTO")
        self.assertIsNotNone(selection.detected_date)
        self.assertEqual(selection.detected_date.strftime("%d/%m/%Y"), "18/03/2025")
        self.assertIn(selection.document_zone, {"header", "top"})

    def test_returns_low_confidence_when_only_period_is_present(self) -> None:
        text = """
        Servicio prestado
        Periodo: 01/03/2025 - 31/03/2025
        Consumo del ciclo actual
        """
        selection = self.detector.detect([PageText(1, text)], "PDF_TEXTO")
        self.assertIsNone(selection.detected_date)
        self.assertTrue(selection.requires_manual_review)
        self.assertIn("umbral minimo", selection.decision_summary.lower())

    def test_emission_date_beats_due_date(self) -> None:
        text = """
        Seguro de comercio
        Fecha de emisión: 08/01/2025
        Fecha de vencimiento: 31/01/2025
        """
        selection = self.detector.detect([PageText(1, text)], "PDF_TEXTO")
        self.assertIsNotNone(selection.detected_date)
        self.assertEqual(selection.detected_date.strftime("%d/%m/%Y"), "08/01/2025")
        self.assertIn("fecha de emision", selection.associated_label)


if __name__ == "__main__":
    unittest.main()
