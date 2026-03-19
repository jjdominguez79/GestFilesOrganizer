from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.config.app_settings import AppSettings
from app.config.theme import THEME, build_stylesheet
from app.models.records import ClientProcessResult, FolderScanResult
from app.services.folder_service import FolderService
from app.ui.worker import ProcessingWorker
from app.utils.logging_utils import LogBuffer


BASE_STATUS_LABELS = {
    "pending": "Pendiente",
    "selected": "Seleccionado",
    "processing": "Procesando",
    "processed": "Procesado",
    "error": "Error",
    "idle": "Sin pendientes",
}


class MainWindow(QMainWindow):
    def __init__(self, settings: AppSettings) -> None:
        super().__init__()
        self.settings = settings
        self.folder_service = FolderService(settings)
        self.log_buffer = LogBuffer()
        self.scan_results: list[FolderScanResult] = []
        self.client_item_map: dict[str, QTreeWidgetItem] = {}
        self.client_states: dict[str, str] = {}
        self.worker: ProcessingWorker | None = None

        self.setWindowTitle(
            f"{self.settings.branding.product_name} | {self.settings.branding.owner_name}"
        )
        self.setMinimumSize(THEME.window_min_width, THEME.window_min_height)
        self.setStyleSheet(build_stylesheet())
        self._build_ui()

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("AppShell")
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(20, 20, 20, 20)
        root_layout.setSpacing(16)

        root_layout.addWidget(self._build_hero())
        root_layout.addLayout(self._build_metrics_row())

        workspace_splitter = QSplitter(Qt.Horizontal)
        workspace_splitter.setChildrenCollapsible(False)
        workspace_splitter.addWidget(self._build_workspace_panel())
        workspace_splitter.addWidget(self._build_execution_panel())
        workspace_splitter.setSizes([980, 520])
        root_layout.addWidget(workspace_splitter, 1)

    def _build_hero(self) -> QWidget:
        hero = QFrame()
        hero.setObjectName("HeroCard")
        layout = QHBoxLayout(hero)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(22)

        logo = QLabel("GF")
        logo.setObjectName("HeroLogo")
        logo.setAlignment(Qt.AlignCenter)
        logo.setFixedSize(74, 74)
        layout.addWidget(logo, 0, Qt.AlignTop)

        text_column = QVBoxLayout()
        text_column.setSpacing(6)

        suite = QLabel(self.settings.branding.owner_name)
        suite.setObjectName("HeroEyebrow")
        text_column.addWidget(suite)

        title = QLabel(self.settings.branding.product_name)
        title.setObjectName("HeroTitle")
        text_column.addWidget(title)

        subtitle = QLabel(
            "Organización documental, trazabilidad de fecha fiscal y control operativo para despacho profesional."
        )
        subtitle.setObjectName("HeroSubtitle")
        subtitle.setWordWrap(True)
        text_column.addWidget(subtitle)

        badges = QHBoxLayout()
        badges.setSpacing(10)
        for label in ("Panel de clientes", "Clasificación por año/mes", "Auditoría de fecha"):
            chip = QLabel(label)
            chip.setObjectName("HeroChip")
            badges.addWidget(chip)
        badges.addStretch(1)
        text_column.addLayout(badges)
        layout.addLayout(text_column, 1)

        side = QFrame()
        side.setObjectName("HeroSideCard")
        side_layout = QVBoxLayout(side)
        side_layout.setContentsMargins(16, 14, 16, 14)
        side_layout.setSpacing(8)
        side_layout.addWidget(self._build_side_metric("Canal", "Despacho / Backoffice"))
        side_layout.addWidget(self._build_side_metric("OCR", "Opcional y limitado"))
        side_layout.addWidget(self._build_side_metric("Reporte", "Excel por cliente"))
        layout.addWidget(side, 0, Qt.AlignTop)
        return hero

    def _build_side_metric(self, title: str, value: str) -> QWidget:
        block = QWidget()
        layout = QVBoxLayout(block)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        title_label = QLabel(title)
        title_label.setObjectName("MiniMetricTitle")
        value_label = QLabel(value)
        value_label.setObjectName("MiniMetricValue")
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        return block

    def _build_metrics_row(self):
        layout = QHBoxLayout()
        layout.setSpacing(14)
        self.metric_clients = self._build_metric_card("Clientes", "0", "carpetas cargadas")
        self.metric_pending = self._build_metric_card("Pendientes", "0", "archivos por ordenar")
        self.metric_selected = self._build_metric_card("Selección", "0", "clientes listos")
        self.metric_manual = self._build_metric_card("Revisión", "0", "fechas a revisar")
        for card in (
            self.metric_clients["frame"],
            self.metric_pending["frame"],
            self.metric_selected["frame"],
            self.metric_manual["frame"],
        ):
            layout.addWidget(card, 1)
        return layout

    def _build_metric_card(self, title: str, value: str, subtitle: str) -> dict[str, QWidget]:
        frame = QFrame()
        frame.setObjectName("MetricCard")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)
        title_label = QLabel(title)
        title_label.setObjectName("MetricTitle")
        value_label = QLabel(value)
        value_label.setObjectName("MetricValue")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("MetricSubtitle")
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addWidget(subtitle_label)
        return {"frame": frame, "value": value_label}

    def _build_workspace_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.addWidget(self._build_controls_panel())
        layout.addWidget(self._build_clients_panel(), 1)
        return panel

    def _build_controls_panel(self) -> QWidget:
        card = QFrame()
        card.setObjectName("PanelCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)

        header_row = QHBoxLayout()
        title = QLabel("Centro de operaciones")
        title.setObjectName("SectionTitle")
        header_row.addWidget(title)
        header_row.addStretch(1)
        self.summary_status = QLabel("Listo")
        self.summary_status.setObjectName("StatusBadgeNeutral")
        header_row.addWidget(self.summary_status)
        layout.addLayout(header_row)

        description = QLabel(
            "Selecciona la carpeta raíz, escanea clientes y lanza el proceso con filtros y opciones de archivo."
        )
        description.setObjectName("MutedLabel")
        description.setWordWrap(True)
        layout.addWidget(description)

        root_grid = QGridLayout()
        root_grid.setHorizontalSpacing(10)
        root_grid.setVerticalSpacing(10)

        root_label = QLabel("Carpeta raíz")
        root_label.setObjectName("FieldLabel")
        root_grid.addWidget(root_label, 0, 0)

        self.root_input = QLineEdit()
        self.root_input.setPlaceholderText("Ruta principal de clientes")
        root_grid.addWidget(self.root_input, 1, 0, 1, 3)

        browse_button = QPushButton("Explorar")
        browse_button.clicked.connect(self.select_root_folder)
        root_grid.addWidget(browse_button, 1, 3)

        scan_button = QPushButton("Cargar clientes")
        scan_button.setObjectName("PrimaryButton")
        scan_button.clicked.connect(self.scan_clients)
        root_grid.addWidget(scan_button, 1, 4)
        layout.addLayout(root_grid)

        actions = QHBoxLayout()
        actions.setSpacing(10)

        mark_all = QPushButton("Marcar todos")
        mark_all.clicked.connect(self.mark_all)
        actions.addWidget(mark_all)

        unmark_all = QPushButton("Desmarcar")
        unmark_all.clicked.connect(self.unmark_all)
        actions.addWidget(unmark_all)

        only_pending = QPushButton("Marcar solo con _")
        only_pending.clicked.connect(self.mark_only_pending_marker)
        actions.addWidget(only_pending)

        refresh = QPushButton("Refrescar")
        refresh.clicked.connect(self.scan_clients)
        actions.addWidget(refresh)

        self.process_button = QPushButton("Procesar seleccionados")
        self.process_button.setObjectName("AccentButton")
        self.process_button.clicked.connect(self.start_processing)
        actions.addWidget(self.process_button)
        layout.addLayout(actions)

        options_grid = QGridLayout()
        options_grid.setHorizontalSpacing(14)
        options_grid.setVerticalSpacing(10)

        options_title = QLabel("Opciones del proceso")
        options_title.setObjectName("SectionTitle")
        options_grid.addWidget(options_title, 0, 0, 1, 2)

        self.move_files_checkbox = QCheckBox("Mover archivos en lugar de copiar")
        self.move_files_checkbox.setChecked(True)
        options_grid.addWidget(self.move_files_checkbox, 1, 0)

        self.modified_date_checkbox = QCheckBox("Usar fecha de modificación como fallback")
        self.modified_date_checkbox.setChecked(True)
        options_grid.addWidget(self.modified_date_checkbox, 1, 1)

        self.auto_select_checkbox = QCheckBox("Seleccionar automáticamente carpetas con '_'")
        self.auto_select_checkbox.setChecked(True)
        self.auto_select_checkbox.stateChanged.connect(self.refresh_client_tree)
        options_grid.addWidget(self.auto_select_checkbox, 2, 0)

        self.remove_marker_checkbox = QCheckBox("Quitar '_' del nombre al finalizar")
        self.remove_marker_checkbox.setChecked(True)
        options_grid.addWidget(self.remove_marker_checkbox, 2, 1)
        layout.addLayout(options_grid)
        return card

    def _build_clients_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("PanelCard")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        top_row = QHBoxLayout()
        title = QLabel("Módulo de clientes")
        title.setObjectName("SectionTitle")
        top_row.addWidget(title)
        top_row.addStretch(1)
        self.only_marker_checkbox = QCheckBox("Solo carpetas con '_'")
        self.only_marker_checkbox.stateChanged.connect(self.refresh_client_tree)
        top_row.addWidget(self.only_marker_checkbox)
        layout.addLayout(top_row)

        subtitle = QLabel(
            "Vista operativa de clientes, pendientes y estado del lote. La selección se refleja directamente en el estado."
        )
        subtitle.setObjectName("MutedLabel")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        self.client_tree = QTreeWidget()
        self.client_tree.setHeaderLabels(["Sel.", "Cliente", "Pendientes", "Estado", "Ruta"])
        self.client_tree.setAlternatingRowColors(True)
        self.client_tree.setRootIsDecorated(False)
        self.client_tree.itemChanged.connect(self._handle_item_changed)
        self.client_tree.setUniformRowHeights(True)
        self.client_tree.setColumnWidth(0, 60)
        self.client_tree.setColumnWidth(1, 260)
        self.client_tree.setColumnWidth(2, 90)
        self.client_tree.setColumnWidth(3, 130)
        layout.addWidget(self.client_tree, 1)
        return panel

    def _build_execution_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.addWidget(self._build_progress_panel())
        layout.addWidget(self._build_log_panel(), 1)
        return panel

    def _build_progress_panel(self) -> QWidget:
        card = QFrame()
        card.setObjectName("PanelCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel("Seguimiento de ejecución")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        self.general_status = QLabel("Lote general: listo")
        self.general_status.setObjectName("MutedLabel")
        layout.addWidget(self.general_status)

        self.general_progress = QProgressBar()
        layout.addWidget(self.general_progress)

        self.client_status = QLabel("Cliente actual: -")
        self.client_status.setObjectName("MutedLabel")
        layout.addWidget(self.client_status)

        self.client_progress = QProgressBar()
        layout.addWidget(self.client_progress)

        summary_grid = QGridLayout()
        summary_grid.setHorizontalSpacing(14)
        summary_grid.setVerticalSpacing(10)
        self.run_processed = self._build_inline_metric("Procesados", "0")
        self.run_errors = self._build_inline_metric("Errores", "0")
        self.run_reviews = self._build_inline_metric("Revisión manual", "0")
        self.run_last = self._build_inline_metric("Última actividad", "-")
        cards = (self.run_processed, self.run_errors, self.run_reviews, self.run_last)
        for index, metric in enumerate(cards):
            summary_grid.addWidget(metric["frame"], index // 2, index % 2)
        layout.addLayout(summary_grid)
        return card

    def _build_inline_metric(self, title: str, value: str) -> dict[str, QWidget]:
        frame = QFrame()
        frame.setObjectName("InlineMetricCard")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(2)
        title_label = QLabel(title)
        title_label.setObjectName("MiniMetricTitle")
        value_label = QLabel(value)
        value_label.setObjectName("MiniMetricValue")
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        return {"frame": frame, "value": value_label}

    def _build_log_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("PanelCard")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        top_row = QHBoxLayout()
        title = QLabel("Actividad reciente y log")
        title.setObjectName("SectionTitle")
        top_row.addWidget(title)
        top_row.addStretch(1)
        export_button = QPushButton("Exportar log")
        export_button.clicked.connect(self.export_log)
        top_row.addWidget(export_button)
        layout.addLayout(top_row)

        helper = QLabel(
            "Se registran decisiones de fecha, incidencias por archivo y resumen de fin de ejecución."
        )
        helper.setObjectName("MutedLabel")
        helper.setWordWrap(True)
        layout.addWidget(helper)

        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.log_output, 1)
        return panel

    def append_log(self, message: str) -> None:
        line = self.log_buffer.add(message)
        self.log_output.appendPlainText(line)
        self.run_last["value"].setText(datetime.now().strftime("%H:%M:%S"))

    def select_root_folder(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, "Selecciona la carpeta raíz de clientes")
        if selected:
            self.root_input.setText(selected)

    def scan_clients(self) -> None:
        root_text = self.root_input.text().strip()
        if not root_text:
            QMessageBox.warning(self, "Aviso", "Selecciona primero una carpeta raíz.")
            return
        root_path = Path(root_text)
        if not root_path.exists() or not root_path.is_dir():
            QMessageBox.critical(self, "Error", "La carpeta raíz no existe o no es válida.")
            return

        self.scan_results = self.folder_service.scan_clients(root_path)
        self.client_states = {
            str(result.path): ("pending" if result.pending_count else "idle")
            for result in self.scan_results
        }
        self.refresh_client_tree()
        self.append_log(f"Carpetas cargadas: {len(self.scan_results)}")
        self._set_summary_badge("Clientes escaneados", "neutral")

    def refresh_client_tree(self) -> None:
        self.client_tree.blockSignals(True)
        self.client_tree.clear()
        self.client_item_map.clear()
        show_only_marker = self.only_marker_checkbox.isChecked()
        auto_select_marker = self.auto_select_checkbox.isChecked()

        for scan_result in self.scan_results:
            if show_only_marker and not scan_result.pending_marker:
                continue

            path_key = str(scan_result.path)
            default_state = self.client_states.get(path_key, "pending" if scan_result.pending_count else "idle")
            item = QTreeWidgetItem(self.client_tree)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            checked = auto_select_marker and scan_result.pending_marker and default_state not in {"processed", "error"}
            if self.client_states.get(path_key) == "selected":
                checked = True
            item.setCheckState(0, Qt.Checked if checked else Qt.Unchecked)
            item.setText(1, scan_result.path.name)
            item.setText(2, str(scan_result.pending_count))
            item.setText(4, str(scan_result.path))
            item.setData(0, Qt.UserRole, path_key)
            self.client_item_map[path_key] = item
            state = self._derive_state(path_key, scan_result.pending_count, item.checkState(0) == Qt.Checked)
            self.client_states[path_key] = state
            self._apply_status_visuals(item, state)

        self.client_tree.blockSignals(False)
        self._update_summary_labels()

    def _derive_state(self, path_key: str, pending_count: int, is_checked: bool) -> str:
        current = self.client_states.get(path_key)
        if current in {"processing", "processed", "error"}:
            return current
        if pending_count == 0:
            return "idle"
        return "selected" if is_checked else "pending"

    def _handle_item_changed(self, item: QTreeWidgetItem, _column: int) -> None:
        path_key = item.data(0, Qt.UserRole)
        if not path_key:
            return
        pending_count = int(item.text(2) or "0")
        state = self._derive_state(path_key, pending_count, item.checkState(0) == Qt.Checked)
        self.client_states[path_key] = state
        self._apply_status_visuals(item, state)
        self._update_summary_labels()

    def _update_summary_labels(self) -> None:
        selected = self.get_selected_client_paths()
        pending_total = sum(result.pending_count for result in self.scan_results)
        self.metric_clients["value"].setText(str(len(self.scan_results)))
        self.metric_pending["value"].setText(str(pending_total))
        self.metric_selected["value"].setText(str(len(selected)))

    def _set_summary_badge(self, text: str, tone: str) -> None:
        object_name = {
            "neutral": "StatusBadgeNeutral",
            "processing": "StatusBadgeInfo",
            "success": "StatusBadgeSuccess",
            "error": "StatusBadgeError",
        }.get(tone, "StatusBadgeNeutral")
        self.summary_status.setObjectName(object_name)
        self.summary_status.setText(text)
        self.summary_status.style().unpolish(self.summary_status)
        self.summary_status.style().polish(self.summary_status)

    def get_selected_client_paths(self) -> list[Path]:
        selected_paths: list[Path] = []
        for path_str, item in self.client_item_map.items():
            if item.checkState(0) == Qt.Checked:
                selected_paths.append(Path(path_str))
        return selected_paths

    def mark_all(self) -> None:
        for item in self.client_item_map.values():
            item.setCheckState(0, Qt.Checked)
        self._update_summary_labels()

    def unmark_all(self) -> None:
        for item in self.client_item_map.values():
            item.setCheckState(0, Qt.Unchecked)
        self._update_summary_labels()

    def mark_only_pending_marker(self) -> None:
        for scan_result in self.scan_results:
            item = self.client_item_map.get(str(scan_result.path))
            if item:
                item.setCheckState(0, Qt.Checked if scan_result.pending_marker else Qt.Unchecked)
        self._update_summary_labels()

    def start_processing(self) -> None:
        selected_paths = self.get_selected_client_paths()
        if not selected_paths:
            QMessageBox.warning(self, "Aviso", "No hay carpetas de cliente seleccionadas.")
            return

        confirmation = QMessageBox.question(
            self,
            "Confirmación",
            f"Se van a procesar {len(selected_paths)} carpetas de cliente.\n\n¿Deseas continuar?",
        )
        if confirmation != QMessageBox.Yes:
            return

        self.process_button.setEnabled(False)
        self.general_progress.setValue(0)
        self.client_progress.setValue(0)
        self.general_status.setText("Lote general: preparando proceso")
        self.client_status.setText("Cliente actual: -")
        self.run_processed["value"].setText("0")
        self.run_errors["value"].setText("0")
        self.run_reviews["value"].setText("0")
        self.metric_manual["value"].setText("0")
        self._set_summary_badge("En ejecución", "processing")
        self.append_log("=== INICIO DEL PROCESO ===")

        self.worker = ProcessingWorker(
            settings=self.settings,
            client_paths=selected_paths,
            move_files=self.move_files_checkbox.isChecked(),
            use_modified_fallback=self.modified_date_checkbox.isChecked(),
            remove_underscore_marker=self.remove_marker_checkbox.isChecked(),
        )
        self.worker.log_message.connect(self.append_log)
        self.worker.global_progress.connect(self._update_global_progress)
        self.worker.client_progress.connect(self._update_client_progress)
        self.worker.client_finished.connect(self._handle_client_finished)
        self.worker.finished_summary.connect(self._handle_processing_finished)
        self.worker.failed.connect(self._handle_processing_failed)
        self.worker.start()

        for path in selected_paths:
            path_key = str(path)
            self.client_states[path_key] = "processing"
            item = self.client_item_map.get(path_key)
            if item:
                self._apply_status_visuals(item, "processing")

    def _update_global_progress(self, current: int, maximum: int) -> None:
        self.general_progress.setMaximum(maximum)
        self.general_progress.setValue(current)
        self.general_status.setText(f"Lote general: {current}/{maximum} archivos")

    def _update_client_progress(self, client_name: str, current: int, total: int) -> None:
        self.client_progress.setMaximum(max(total, 1))
        self.client_progress.setValue(current)
        self.client_status.setText(f"Cliente actual: {client_name} ({current}/{total})")

    def _handle_client_finished(self, result: ClientProcessResult) -> None:
        old_key = str(result.original_path)
        new_key = str(result.final_client_path)
        item = self.client_item_map.get(old_key)
        if item:
            item.setText(1, result.final_client_path.name)
            item.setText(2, "0")
            item.setText(4, str(result.final_client_path))
            state = "error" if result.error_count else "processed"
            self.client_states.pop(old_key, None)
            self.client_states[new_key] = state
            if old_key != new_key:
                self.client_item_map.pop(old_key, None)
                self.client_item_map[new_key] = item
                item.setData(0, Qt.UserRole, new_key)
            self._apply_status_visuals(item, state)

        manual_reviews = sum(1 for doc in result.processed_documents if doc.requires_manual_review)
        self.run_processed["value"].setText(str(int(self.run_processed["value"].text()) + result.processed_count))
        self.run_errors["value"].setText(str(int(self.run_errors["value"].text()) + result.error_count))
        self.run_reviews["value"].setText(str(int(self.run_reviews["value"].text()) + manual_reviews))
        self.metric_manual["value"].setText(self.run_reviews["value"].text())

        self.append_log(
            f"Cliente finalizado: {result.final_client_path.name} | procesados={result.processed_count} | "
            f"errores={result.error_count} | revision={manual_reviews}"
        )
        self._update_summary_labels()

    def _handle_processing_finished(self, processed_total: int, total_files: int, error_total: int) -> None:
        self.process_button.setEnabled(True)
        self._set_summary_badge("Finalizado", "success")
        self.general_status.setText(f"Lote general: finalizado ({processed_total}/{total_files})")
        self.client_status.setText("Cliente actual: completado")
        self.append_log("=== PROCESO FINALIZADO ===")
        self.append_log(f"Total procesados: {processed_total}")
        self.append_log(f"Total errores: {error_total}")
        QMessageBox.information(
            self,
            "Proceso finalizado",
            f"Archivos procesados: {processed_total}\nErrores: {error_total}",
        )
        self.scan_clients()

    def _handle_processing_failed(self, error_message: str) -> None:
        self.process_button.setEnabled(True)
        self._set_summary_badge("Error general", "error")
        self.append_log(f"[ERROR GENERAL] {error_message}")
        QMessageBox.critical(self, "Error", error_message)

    def _apply_status_visuals(self, item: QTreeWidgetItem, status: str) -> None:
        palette = {
            "pending": (THEME.colors["pending"], THEME.colors["pending_soft"]),
            "selected": (THEME.colors["selected"], THEME.colors["selected_soft"]),
            "processing": (THEME.colors["processing"], THEME.colors["processing_soft"]),
            "processed": (THEME.colors["processed"], THEME.colors["processed_soft"]),
            "error": (THEME.colors["error"], THEME.colors["error_soft"]),
            "idle": (THEME.colors["muted"], THEME.colors["surface_alt"]),
        }
        text_color, background = palette.get(status, (THEME.colors["text"], THEME.colors["surface_alt"]))
        item.setText(3, BASE_STATUS_LABELS.get(status, status.title()))
        item.setForeground(3, QColor(text_color))
        item.setBackground(3, QColor(background))
        item.setForeground(2, QColor(THEME.colors["text"]))

    def export_log(self) -> None:
        if not self.log_buffer.lines:
            QMessageBox.information(self, "Log", "Todavía no hay entradas de log para exportar.")
            return
        suggested = f"log_proceso_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.txt"
        destination, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar log",
            str(Path.cwd() / suggested),
            "Text files (*.txt)",
        )
        if not destination:
            return
        output = self.log_buffer.export(Path(destination))
        QMessageBox.information(self, "Log exportado", f"Log guardado en:\n{output}")


def build_application(settings: AppSettings) -> QApplication:
    app = QApplication.instance() or QApplication([])
    app.setApplicationName(settings.app_name)
    return app
