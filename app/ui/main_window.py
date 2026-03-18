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


STATUS_LABELS = {
    "pending": "Pendiente",
    "processing": "En proceso",
    "processed": "Procesado",
    "error": "Error",
}


class MainWindow(QMainWindow):
    def __init__(self, settings: AppSettings) -> None:
        super().__init__()
        self.settings = settings
        self.folder_service = FolderService(settings)
        self.log_buffer = LogBuffer()
        self.scan_results: list[FolderScanResult] = []
        self.client_item_map: dict[str, QTreeWidgetItem] = {}
        self.worker: ProcessingWorker | None = None

        self.setWindowTitle(
            f"{self.settings.branding.product_name} | {self.settings.branding.owner_name}"
        )
        self.setMinimumSize(THEME.window_min_width, THEME.window_min_height)
        self.setStyleSheet(build_stylesheet())
        self._build_ui()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(18, 18, 18, 18)
        root_layout.setSpacing(18)

        root_layout.addWidget(self._build_sidebar(), 0)
        root_layout.addWidget(self._build_content(), 1)

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(300)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)

        brand = QFrame()
        brand.setObjectName("BrandBlock")
        brand_layout = QVBoxLayout(brand)
        brand_layout.setContentsMargins(18, 18, 18, 18)
        brand_layout.setSpacing(10)

        logo = QLabel("a3")
        logo.setObjectName("BrandLogo")
        logo.setAlignment(Qt.AlignCenter)
        logo.setFixedSize(72, 48)
        brand_layout.addWidget(logo, 0, Qt.AlignLeft)

        pill = QLabel(self.settings.branding.suite_name)
        pill.setObjectName("BrandPill")
        pill.setAlignment(Qt.AlignCenter)
        brand_layout.addWidget(pill, 0, Qt.AlignLeft)

        brand_owner = QLabel(self.settings.branding.owner_name)
        brand_owner.setObjectName("BrandOwner")
        brand_layout.addWidget(brand_owner)

        brand_title = QLabel(self.settings.branding.product_name)
        brand_title.setObjectName("BrandProduct")
        brand_layout.addWidget(brand_title)

        brand_subtitle = QLabel(self.settings.branding.tagline)
        brand_subtitle.setObjectName("BrandTagline")
        brand_subtitle.setWordWrap(True)
        brand_layout.addWidget(brand_subtitle)

        brand_description = QLabel(self.settings.branding.description)
        brand_description.setObjectName("BrandTagline")
        brand_description.setWordWrap(True)
        brand_layout.addWidget(brand_description)

        brand_info_card = QFrame()
        brand_info_card.setObjectName("BrandInfoCard")
        info_layout = QGridLayout(brand_info_card)
        info_layout.setContentsMargins(12, 12, 12, 12)
        info_layout.setHorizontalSpacing(10)
        info_layout.setVerticalSpacing(8)

        phone_title = QLabel("Atención comercial")
        phone_title.setObjectName("InfoTitle")
        phone_value = QLabel(self.settings.branding.support_phone)
        phone_value.setObjectName("InfoValue")

        portal_title = QLabel("Soporte")
        portal_title.setObjectName("InfoTitle")
        portal_value = QLabel(self.settings.branding.support_portal)
        portal_value.setObjectName("InfoValue")
        portal_value.setWordWrap(True)

        web_title = QLabel("Web")
        web_title.setObjectName("InfoTitle")
        web_value = QLabel(self.settings.branding.website)
        web_value.setObjectName("InfoValue")
        web_value.setWordWrap(True)

        info_layout.addWidget(phone_title, 0, 0)
        info_layout.addWidget(phone_value, 1, 0)
        info_layout.addWidget(portal_title, 0, 1)
        info_layout.addWidget(portal_value, 1, 1)
        info_layout.addWidget(web_title, 2, 0, 1, 2)
        info_layout.addWidget(web_value, 3, 0, 1, 2)
        brand_layout.addWidget(brand_info_card)
        layout.addWidget(brand)

        summary = QFrame()
        summary.setObjectName("SummaryCard")
        summary_layout = QVBoxLayout(summary)
        summary_layout.setContentsMargins(16, 16, 16, 16)
        summary_layout.setSpacing(10)

        title = QLabel("Resumen de operación")
        title.setObjectName("SectionTitle")
        summary_layout.addWidget(title)

        self.summary_clients = QLabel("Clientes cargados: 0")
        self.summary_clients.setObjectName("MutedLabel")
        summary_layout.addWidget(self.summary_clients)

        self.summary_pending = QLabel("Pendientes: 0")
        self.summary_pending.setObjectName("MutedLabel")
        summary_layout.addWidget(self.summary_pending)

        self.summary_selected = QLabel("Seleccionados: 0")
        self.summary_selected.setObjectName("MutedLabel")
        summary_layout.addWidget(self.summary_selected)

        self.summary_status = QLabel("Estado: listo")
        self.summary_status.setObjectName("MutedLabel")
        summary_layout.addWidget(self.summary_status)
        layout.addWidget(summary)

        options = QFrame()
        options.setObjectName("SummaryCard")
        options_layout = QVBoxLayout(options)
        options_layout.setContentsMargins(16, 16, 16, 16)
        options_layout.setSpacing(12)

        options_title = QLabel("Opciones")
        options_title.setObjectName("SectionTitle")
        options_layout.addWidget(options_title)

        self.move_files_checkbox = QCheckBox("Mover archivos en lugar de copiar")
        self.move_files_checkbox.setChecked(True)
        options_layout.addWidget(self.move_files_checkbox)

        self.modified_date_checkbox = QCheckBox("Usar fecha de modificación como fallback")
        self.modified_date_checkbox.setChecked(True)
        options_layout.addWidget(self.modified_date_checkbox)

        self.auto_select_checkbox = QCheckBox("Marcar automáticamente carpetas con '_'")
        self.auto_select_checkbox.setChecked(True)
        options_layout.addWidget(self.auto_select_checkbox)

        self.remove_marker_checkbox = QCheckBox("Quitar _ del nombre al finalizar")
        self.remove_marker_checkbox.setChecked(True)
        options_layout.addWidget(self.remove_marker_checkbox)
        layout.addWidget(options)

        layout.addStretch(1)
        return sidebar

    def _build_content(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        layout.addWidget(self._build_top_card())
        layout.addWidget(self._build_progress_card())

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self._build_clients_panel())
        splitter.addWidget(self._build_log_panel())
        splitter.setSizes([720, 540])
        layout.addWidget(splitter, 1)
        return container

    def _build_top_card(self) -> QWidget:
        card = QFrame()
        card.setObjectName("TopCard")
        layout = QGridLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(10)

        headline = QLabel("Panel principal")
        headline.setObjectName("Headline")
        layout.addWidget(headline, 0, 0, 1, 4)

        subtitle = QLabel("Selecciona la carpeta raíz, escanea clientes y ejecuta el procesamiento con control visual.")
        subtitle.setObjectName("MutedLabel")
        layout.addWidget(subtitle, 1, 0, 1, 4)

        self.root_input = QLineEdit()
        self.root_input.setPlaceholderText("Carpeta raíz de clientes")
        layout.addWidget(self.root_input, 2, 0, 1, 2)

        browse_button = QPushButton("Examinar")
        browse_button.clicked.connect(self.select_root_folder)
        layout.addWidget(browse_button, 2, 2)

        scan_button = QPushButton("Escanear")
        scan_button.setObjectName("AccentButton")
        scan_button.clicked.connect(self.scan_clients)
        layout.addWidget(scan_button, 2, 3)

        mark_all = QPushButton("Marcar todos")
        mark_all.clicked.connect(self.mark_all)
        layout.addWidget(mark_all, 3, 0)

        unmark_all = QPushButton("Desmarcar todos")
        unmark_all.clicked.connect(self.unmark_all)
        layout.addWidget(unmark_all, 3, 1)

        only_pending = QPushButton("Solo carpetas con _")
        only_pending.clicked.connect(self.mark_only_pending_marker)
        layout.addWidget(only_pending, 3, 2)

        self.process_button = QPushButton("Procesar seleccionados")
        self.process_button.setObjectName("PrimaryButton")
        self.process_button.clicked.connect(self.start_processing)
        layout.addWidget(self.process_button, 3, 3)

        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        return card

    def _build_progress_card(self) -> QWidget:
        card = QFrame()
        card.setObjectName("PanelCard")
        layout = QGridLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setHorizontalSpacing(14)

        title = QLabel("Seguimiento")
        title.setObjectName("SectionTitle")
        layout.addWidget(title, 0, 0, 1, 2)

        self.general_status = QLabel("General: listo")
        self.general_status.setObjectName("MutedLabel")
        layout.addWidget(self.general_status, 1, 0)

        self.client_status = QLabel("Cliente actual: -")
        self.client_status.setObjectName("MutedLabel")
        layout.addWidget(self.client_status, 1, 1)

        self.general_progress = QProgressBar()
        layout.addWidget(self.general_progress, 2, 0)

        self.client_progress = QProgressBar()
        layout.addWidget(self.client_progress, 2, 1)
        return card

    def _build_clients_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("PanelCard")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QLabel("Clientes detectados")
        header.setObjectName("SectionTitle")
        layout.addWidget(header)

        self.only_marker_checkbox = QCheckBox("Mostrar solo carpetas con '_'")
        self.only_marker_checkbox.stateChanged.connect(self.refresh_client_tree)
        layout.addWidget(self.only_marker_checkbox)

        self.client_tree = QTreeWidget()
        self.client_tree.setHeaderLabels(["Procesar", "Cliente", "Pendiente", "Estado", "Ruta"])
        self.client_tree.itemChanged.connect(self._handle_item_changed)
        layout.addWidget(self.client_tree, 1)
        return panel

    def _build_log_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("PanelCard")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        top_row = QHBoxLayout()
        header = QLabel("Log de proceso")
        header.setObjectName("SectionTitle")
        top_row.addWidget(header)
        top_row.addStretch(1)

        export_button = QPushButton("Exportar log")
        export_button.clicked.connect(self.export_log)
        top_row.addWidget(export_button)
        layout.addLayout(top_row)

        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.log_output, 1)
        return panel

    def append_log(self, message: str) -> None:
        line = self.log_buffer.add(message)
        self.log_output.appendPlainText(line)

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
        self.refresh_client_tree()
        self.append_log(f"Carpetas cargadas: {len(self.scan_results)}")
        self.summary_status.setText("Estado: clientes escaneados")

    def refresh_client_tree(self) -> None:
        self.client_tree.blockSignals(True)
        self.client_tree.clear()
        self.client_item_map.clear()
        show_only_marker = self.only_marker_checkbox.isChecked()
        auto_select_marker = self.auto_select_checkbox.isChecked()

        for scan_result in self.scan_results:
            if show_only_marker and not scan_result.pending_marker:
                continue

            item = QTreeWidgetItem(self.client_tree)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            item.setCheckState(0, Qt.Checked if auto_select_marker and scan_result.pending_marker else Qt.Unchecked)
            item.setText(1, scan_result.path.name)
            item.setText(2, str(scan_result.pending_count))
            item.setText(3, STATUS_LABELS["pending"] if scan_result.pending_count else "Sin pendientes")
            item.setText(4, str(scan_result.path))
            item.setData(0, Qt.UserRole, str(scan_result.path))
            self._apply_status_color(item, "pending" if scan_result.pending_count else "processed")
            self.client_item_map[str(scan_result.path)] = item

        self.client_tree.resizeColumnToContents(0)
        self.client_tree.resizeColumnToContents(1)
        self.client_tree.resizeColumnToContents(2)
        self.client_tree.resizeColumnToContents(3)
        self.client_tree.blockSignals(False)
        self._update_summary_labels()

    def _handle_item_changed(self, _item: QTreeWidgetItem, _column: int) -> None:
        self._update_summary_labels()

    def _update_summary_labels(self) -> None:
        selected = self.get_selected_client_paths()
        pending_total = sum(result.pending_count for result in self.scan_results)
        self.summary_clients.setText(f"Clientes cargados: {len(self.scan_results)}")
        self.summary_pending.setText(f"Pendientes: {pending_total}")
        self.summary_selected.setText(f"Seleccionados: {len(selected)}")

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
        self.general_status.setText("General: preparando proceso")
        self.client_status.setText("Cliente actual: -")
        self.summary_status.setText("Estado: en proceso")
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
            item = self.client_item_map.get(str(path))
            if item:
                item.setText(3, STATUS_LABELS["processing"])
                self._apply_status_color(item, "processing")

    def _update_global_progress(self, current: int, maximum: int) -> None:
        self.general_progress.setMaximum(maximum)
        self.general_progress.setValue(current)
        self.general_status.setText(f"General: {current}/{maximum} archivos")

    def _update_client_progress(self, client_name: str, current: int, total: int) -> None:
        self.client_progress.setMaximum(max(total, 1))
        self.client_progress.setValue(current)
        self.client_status.setText(f"Cliente actual: {client_name} ({current}/{total})")

    def _handle_client_finished(self, result: ClientProcessResult) -> None:
        old_item = self.client_item_map.get(str(result.original_path))
        if old_item:
            old_item.setText(1, result.final_client_path.name)
            old_item.setText(2, "0")
            old_item.setText(4, str(result.final_client_path))
            if result.error_count:
                old_item.setText(3, STATUS_LABELS["error"])
                self._apply_status_color(old_item, "error")
            else:
                old_item.setText(3, STATUS_LABELS["processed"])
                self._apply_status_color(old_item, "processed")
            if str(result.original_path) != str(result.final_client_path):
                self.client_item_map.pop(str(result.original_path), None)
                self.client_item_map[str(result.final_client_path)] = old_item
        self.append_log(
            f"Cliente finalizado: {result.final_client_path.name} | procesados={result.processed_count} | errores={result.error_count}"
        )
        self._update_summary_labels()

    def _handle_processing_finished(self, processed_total: int, total_files: int, error_total: int) -> None:
        self.process_button.setEnabled(True)
        self.summary_status.setText("Estado: finalizado")
        self.general_status.setText(f"General: finalizado ({processed_total}/{total_files})")
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
        self.summary_status.setText("Estado: error general")
        self.append_log(f"[ERROR GENERAL] {error_message}")
        QMessageBox.critical(self, "Error", error_message)

    def _apply_status_color(self, item: QTreeWidgetItem, status: str) -> None:
        palette = {
            "pending": QColor(THEME.colors["pending"]),
            "processing": QColor(THEME.colors["processing"]),
            "processed": QColor(THEME.colors["processed"]),
            "error": QColor(THEME.colors["error"]),
        }
        color = palette.get(status, QColor(THEME.colors["text"]))
        item.setForeground(3, color)

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
