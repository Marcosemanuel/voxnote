from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from PySide6.QtCore import QByteArray, QSize, Qt, QThread, QUrl, Signal, Slot
from PySide6.QtGui import QBrush, QCloseEvent, QColor, QDragEnterEvent, QDropEvent, QFont, QIcon, QPainter, QPixmap
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLayout,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSlider,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from transcritor.audio import AudioValidationError, inspect_audio
from transcritor.database import Database
from transcritor.domain import MODEL_PROFILES, STATUS_LABELS, AudioInfo, JobStatus, format_duration
from transcritor.engine import TranscriptionController
from transcritor.exporters import export_transcript
from transcritor.hardware import detect_hardware
from transcritor.models import ModelManager
from transcritor.paths import AppPaths
from transcritor.resources import bundled_path
from transcritor.workers import ModelDownloadWorker, TranscriptionWorker

LOG = logging.getLogger(__name__)

STYLE = """
QWidget { font-family: 'Manrope'; font-size: 16px; font-weight: 400; line-height: 24px; color: #2b2b2b; }
QMainWindow, QWidget#root { background: #f5f5f3; }
QFrame#sidebar { background: #fbfaf8; border: 0; border-right: 1px solid #e7e7e3; }
QWidget#brandLockup { background: transparent; }
QLabel#brandName { color: #111111; font-size: 18px; font-weight: 700; letter-spacing: 0.4px; }
QLabel#sidebarStatus, QFrame#hardwareCard {
  color: #2b2b2b; background: #ffffff; border: 1px solid #e7e7e3;
  border-radius: 16px; padding: 14px; font-size: 12px; font-weight: 500; line-height: 16px;
}
QFrame#card, QFrame#configPanel { background: #ffffff; border: 1px solid #e7e7e3; border-radius: 20px; }
QLabel#title { color: #111111; font-size: 32px; font-weight: 700; line-height: 40px; letter-spacing: -0.5px; }
QLabel#sectionTitle { color: #111111; font-size: 20px; font-weight: 600; line-height: 28px; letter-spacing: -0.2px; }
QLabel#subtitle { color: #2b2b2b; font-size: 16px; font-weight: 600; line-height: 24px; }
QLabel#secondaryText { color: #5d5d5d; font-size: 14px; font-weight: 400; line-height: 20px; }
QLabel#formLabel { color: #2b2b2b; font-size: 13px; font-weight: 600; line-height: 18px; letter-spacing: 0.2px; }
QLabel#caption { color: #5d5d5d; font-size: 12px; font-weight: 500; line-height: 16px; letter-spacing: 0.2px; }
QLabel#timestamp { color: #5d5d5d; font-size: 12px; font-weight: 500; line-height: 16px; }
QLabel#transcriptionText { color: #2b2b2b; font-size: 16px; font-weight: 400; line-height: 26px; }
QLabel#cardTitle { color: #111111; font-size: 24px; font-weight: 700; line-height: 32px; letter-spacing: -0.3px; }
QLabel#cardBody { color: #2b2b2b; font-size: 16px; font-weight: 400; line-height: 24px; }
QLabel#infoLabel { color: #2b2b2b; font-size: 15px; font-weight: 600; line-height: 22px; }
QLabel#infoValue { color: #2b2b2b; font-size: 15px; font-weight: 400; line-height: 22px; }
QLabel#iconBadge { background: #eef4ff; border-radius: 24px; }
QLabel#recommendationValue { color: #1769ff; font-size: 15px; font-weight: 600; line-height: 22px; }
QFrame#divider { background: #e7e7e3; min-height: 1px; max-height: 1px; border: 0; }
QFrame#footerBar { background: transparent; border-top: 1px solid #e7e7e3; }
QFrame#drop { background: #ffffff; border: 2px dashed #9bbef8; border-radius: 20px; }
QPushButton {
  min-height: 44px; padding: 0 18px; border-radius: 12px; border: 1px solid #d9d9d6;
  background: #ffffff; color: #2b2b2b; font-size: 14px; font-weight: 600; line-height: 20px; letter-spacing: 0.2px;
}
QPushButton:hover { background: #f7f7f5; border-color: #3b82f6; }
QPushButton#primary { background: #3b82f6; color: white; border: 0; font-weight: 600; padding: 0 20px; }
QPushButton#primary:hover { background: #2563eb; }
QPushButton#outlineAction { color: #1769ff; border-color: #9bbef8; background: #ffffff; }
QPushButton#outlineAction:hover { background: #eef4ff; border-color: #3b82f6; }
QPushButton#iconAction { min-width: 44px; max-width: 44px; padding: 0; color: #1769ff; }
QPushButton#dangerIcon { min-width: 44px; max-width: 44px; padding: 0; color: #c63b3b; border-color: #f1caca; }
QPushButton#nav {
  color: #2b2b2b; background: transparent; border: 0; border-radius: 10px;
  text-align: left; padding-left: 16px; font-size: 14px; font-weight: 500; line-height: 20px;
}
QPushButton#nav:hover { background: #ffffff; color: #111111; }
QPushButton#nav:checked { background: #eef4ff; color: #2563eb; border-left: 3px solid #3b82f6; font-weight: 600; }
QPushButton#danger { color: #b13b3b; border-color: #ebc6c6; }
QLineEdit, QComboBox, QPlainTextEdit {
  min-height: 46px; background: #ffffff; border: 1px solid #deded9;
  border-radius: 12px; padding: 6px 14px; color: #111111; font-size: 16px; font-weight: 400; line-height: 24px;
}
QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus { border: 2px solid #3b82f6; background: #ffffff; }
QTableWidget {
  background: #ffffff; border: 1px solid #e7e7e3; border-radius: 20px;
  gridline-color: #f0f0ed; selection-background-color: #eef4ff; selection-color: #111111;
  font-size: 14px; font-weight: 400; line-height: 20px;
}
QTableWidget::item { padding: 10px 12px; border-bottom: 1px solid #f0f0ed; }
QListWidget {
  background: #ffffff; color: #2b2b2b; border: 1px solid #e7e7e3; border-radius: 16px;
  padding: 5px; font-size: 14px; font-weight: 400; line-height: 20px;
}
QListWidget::item { min-height: 34px; padding: 7px; border-bottom: 1px solid #f0f0ed; }
QHeaderView::section {
  background: #fbfaf8; color: #2b2b2b; border: 0; border-bottom: 1px solid #e7e7e3;
  padding: 14px 12px; font-size: 14px; font-weight: 600; line-height: 20px;
}
QTextBrowser#content {
  background: #ffffff; color: #2b2b2b; border: 1px solid #e7e7e3;
  border-radius: 20px; padding: 30px; font-size: 16px; font-weight: 400; line-height: 24px;
}
QTextBrowser#content h2 { color: #111111; font-size: 20px; font-weight: 600; line-height: 28px; }
QTextBrowser#content p { color: #2b2b2b; font-size: 16px; font-weight: 400; line-height: 24px; }
QProgressBar {
  min-height: 12px; border: 0; border-radius: 6px; background: #d9d9d6;
  text-align: center; color: #ffffff; font-size: 12px; font-weight: 500; line-height: 16px;
}
QProgressBar::chunk { background: #3b82f6; border-radius: 6px; }
QProgressBar#tableProgress {
  min-height: 4px; max-height: 4px; border-radius: 2px; background: #e5e9ee;
}
QProgressBar#tableProgress::chunk { border-radius: 2px; background: #1769ff; }
QLabel#success { color: #157347; }
QLabel#warning { color: #9a6500; }
"""


def interface_font(
    pixel_size: int, weight: QFont.Weight, *, letter_spacing: float = 0.0, tabular: bool = False
) -> QFont:
    """Create a Manrope font with the exact metrics used by special Qt items."""
    font = QFont("Manrope")
    font.setPixelSize(pixel_size)
    font.setWeight(weight)
    if letter_spacing:
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, letter_spacing)
    if tabular:
        font.setFeature(QFont.Tag.fromString("tnum"), 1)
    return font


def card(layout: QLayout) -> QFrame:
    frame = QFrame()
    frame.setObjectName("card")
    frame.setLayout(layout)
    elevate(frame)
    return frame


def elevate(widget: QWidget, blur_radius: int = 28, offset_y: int = 8, alpha: int = 18) -> None:
    """Apply the soft, low-contrast elevation defined by the Voxnote visual system."""
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur_radius)
    shadow.setOffset(0, offset_y)
    shadow.setColor(QColor(17, 17, 17, alpha))
    widget.setGraphicsEffect(shadow)


def add_asset_icon(button: QPushButton, asset_path: str, size: int = 20) -> None:
    """Load legacy raster icons without preserving their captured empty margins."""
    pixmap = QPixmap(str(bundled_path(asset_path)))
    image = pixmap.toImage()
    left, top, right, bottom = image.width(), image.height(), -1, -1
    for y in range(image.height()):
        for x in range(image.width()):
            color = image.pixelColor(x, y)
            if color.alpha() > 12 and min(color.red(), color.green(), color.blue()) < 235:
                left, top = min(left, x), min(top, y)
                right, bottom = max(right, x), max(bottom, y)
    if right >= left and bottom >= top:
        pixmap = pixmap.copy(left, top, right - left + 1, bottom - top + 1)
    button.setIcon(QIcon(pixmap))
    button.setIconSize(QSize(size, size))


def vector_icon(asset_path: str, color: str, size: int) -> QIcon:
    svg_data = bundled_path(asset_path).read_text(encoding="utf-8").replace("currentColor", color)
    renderer = QSvgRenderer(QByteArray(svg_data.encode("utf-8")))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)


def add_vector_icon(button: QPushButton, asset_path: str, color: str = "#2b2b2b", size: int = 22) -> None:
    button.setIcon(vector_icon(asset_path, color, size))
    button.setIconSize(QSize(size, size))


def icon_badge(parent: QWidget, asset_path: str) -> QLabel:
    badge = QLabel(parent)
    badge.setObjectName("iconBadge")
    badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
    badge.setFixedSize(48, 48)
    badge.setPixmap(vector_icon(asset_path, "#1769ff", 26).pixmap(26, 26))
    return badge


def asset_label(parent: QWidget, asset_path: str, size: int) -> QLabel:
    label = QLabel(parent)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setFixedSize(size, size)
    label.setPixmap(QPixmap(str(bundled_path(asset_path))).scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio))
    return label


def vector_label(parent: QWidget, asset_path: str, color: str, size: int) -> QLabel:
    label = QLabel(parent)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setFixedSize(size, size)
    label.setPixmap(vector_icon(asset_path, color, size).pixmap(size, size))
    return label


class DropFrame(QFrame):
    files_dropped = Signal(list)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("drop")
        self.setAcceptDrops(True)
        self.setMinimumHeight(238)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)
        title = QLabel("Arraste seus arquivos de áudio aqui")
        title.setObjectName("sectionTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle = QLabel("ou use o botão abaixo")
        subtitle.setObjectName("caption")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.choose = QPushButton("Selecionar arquivos")
        self.choose.setObjectName("primary")
        formats = QLabel("MP3, WAV, M4A, AAC, FLAC, OGG, OPUS, WMA, AIFF e WEBM")
        formats.setObjectName("caption")
        layout.addWidget(
            vector_label(self, "assets/icons/lucide/audio-lines.svg", "#1769ff", 44),
            alignment=Qt.AlignmentFlag.AlignCenter,
        )
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(self.choose, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(formats)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        self.files_dropped.emit([url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()])


class NewPage(QWidget):
    start_requested = Signal(list, str, str, str)

    def __init__(self, hardware_text: str, recommended: str):
        super().__init__()
        self.files: list[AudioInfo] = []
        root = QVBoxLayout(self)
        root.setContentsMargins(48, 40, 48, 32)
        root.setSpacing(24)
        title = QLabel("Nova transcrição")
        title.setObjectName("title")
        root.addWidget(title)
        self.drop = DropFrame()
        upload_layout = QVBoxLayout()
        upload_layout.setContentsMargins(20, 20, 20, 20)
        upload_layout.addWidget(self.drop)
        self.upload_panel = card(upload_layout)
        root.addWidget(self.upload_panel)
        self.file_list = QListWidget()
        self.file_list.setMaximumHeight(145)
        self.file_list.setFont(interface_font(14, QFont.Weight.Normal, tabular=True))
        self.file_list.hide()
        root.addWidget(self.file_list)
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form.setHorizontalSpacing(34)
        form.setVerticalSpacing(16)
        self.language = QComboBox()
        self.language.addItem("Português (Brasil)", "pt")
        self.language.addItem("Detectar automaticamente", None)
        self.language.addItem("Inglês", "en")
        self.language.addItem("Espanhol", "es")
        self.quality = QComboBox()
        for label in MODEL_PROFILES:
            self.quality.addItem(label)
        self.quality.setCurrentText(recommended)
        self.glossary = QPlainTextEdit()
        self.glossary.setPlaceholderText("Nomes, siglas e termos técnicos — um por linha (opcional)")
        self.glossary.setMaximumHeight(80)
        for label, widget in (("Idioma", self.language), ("Qualidade", self.quality), ("Glossário", self.glossary)):
            form_label = QLabel(label)
            form_label.setObjectName("formLabel")
            form_label.setMinimumWidth(120)
            form.addRow(form_label, widget)
        section_title = QLabel("Configurações")
        section_title.setObjectName("sectionTitle")
        root.addWidget(section_title)
        root.addLayout(form)
        recommendation = QLabel(hardware_text)
        recommendation.setObjectName("success")
        recommendation.setWordWrap(True)
        root.addWidget(recommendation)
        root.addStretch()
        footer = QFrame()
        footer.setObjectName("footerBar")
        actions = QHBoxLayout(footer)
        actions.setContentsMargins(0, 20, 0, 0)
        privacy = QLabel("Processamento local. O áudio não é enviado para a internet.")
        privacy.setObjectName("secondaryText")
        self.start = QPushButton("Iniciar transcrição")
        self.start.setObjectName("primary")
        self.start.setEnabled(False)
        actions.addWidget(privacy)
        actions.addStretch()
        actions.addWidget(self.start)
        root.addWidget(footer)
        self.drop.choose.clicked.connect(self.choose_files)
        self.drop.files_dropped.connect(self.add_files)
        self.start.clicked.connect(self.emit_start)

    def choose_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Selecionar áudios",
            "",
            "Áudios (*.mp3 *.wav *.m4a *.aac *.flac *.ogg *.opus *.wma *.aiff *.aif *.webm)",
        )
        self.add_files(paths)

    def add_files(self, paths: list[str]) -> None:
        errors: list[str] = []
        known = {item.path.resolve() for item in self.files}
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            for value in paths:
                try:
                    info = inspect_audio(Path(value))
                    if info.path.resolve() not in known:
                        self.files.append(info)
                        known.add(info.path.resolve())
                except AudioValidationError as exc:
                    errors.append(f"{Path(value).name}: {exc}")
        finally:
            QApplication.restoreOverrideCursor()
        self.refresh()
        if errors:
            QMessageBox.warning(self, "Alguns arquivos não foram adicionados", "\n\n".join(errors))

    def refresh(self) -> None:
        self.file_list.clear()
        for info in self.files:
            self.file_list.addItem(
                f"{info.path.name}   •   {format_duration(info.duration)}   •   {info.size / 1024**2:.1f} MB"
            )
        self.file_list.setVisible(bool(self.files))
        self.start.setEnabled(bool(self.files))

    def emit_start(self) -> None:
        glossary = ", ".join(line.strip() for line in self.glossary.toPlainText().splitlines() if line.strip())
        self.start_requested.emit(self.files.copy(), self.language.currentData(), self.quality.currentText(), glossary)

    def clear(self) -> None:
        self.files.clear()
        self.glossary.clear()
        self.refresh()


class ProgressPage(QWidget):
    pause_requested = Signal()
    cancel_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 40, 48, 32)
        layout.setSpacing(22)
        title = QLabel("Transcrição em andamento")
        title.setObjectName("title")
        self.file = QLabel("Preparando...")
        self.file.setObjectName("sectionTitle")
        self.detail = QLabel("O modelo será baixado automaticamente se necessário.")
        self.detail.setObjectName("secondaryText")
        self.bar = QProgressBar()
        self.bar.setRange(0, 1000)
        self.progress_text = QLabel("0%")
        self.progress_text.setObjectName("timestamp")
        self.progress_text.setFont(interface_font(12, QFont.Weight.Medium, tabular=True))
        self.latest = QLabel("Aguardando o primeiro trecho...")
        self.latest.setObjectName("transcriptionText")
        self.latest.setWordWrap(True)
        self.latest.setMinimumHeight(90)
        self.saved = QLabel("✓ O progresso é salvo após cada trecho concluído.")
        self.saved.setObjectName("success")
        actions = QHBoxLayout()
        self.pause = QPushButton("Pausar")
        self.cancel = QPushButton("Cancelar")
        self.cancel.setObjectName("danger")
        actions.addStretch()
        actions.addWidget(self.pause)
        actions.addWidget(self.cancel)
        layout.addWidget(title)
        layout.addSpacing(16)
        layout.addWidget(self.file)
        layout.addWidget(self.detail)
        layout.addSpacing(20)
        layout.addWidget(self.bar)
        layout.addWidget(self.progress_text)
        layout.addSpacing(18)
        layout.addWidget(card(self._latest_layout()))
        layout.addWidget(self.saved)
        layout.addStretch()
        layout.addLayout(actions)
        self.pause.clicked.connect(self.pause_requested)
        self.cancel.clicked.connect(self.cancel_requested)

    def _latest_layout(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        label = QLabel("Último trecho concluído")
        label.setObjectName("formLabel")
        layout.addWidget(label)
        layout.addWidget(self.latest)
        return layout

    def set_job(self, name: str, index: int, total: int, profile: str) -> None:
        self.file.setText(name)
        self.detail.setText(f"Arquivo {index} de {total} • {profile}")
        self.update_progress(0, "Preparando o modelo e o áudio...")

    def update_progress(self, value: float, latest: str) -> None:
        self.bar.setValue(int(value * 10))
        self.progress_text.setText(f"{value:.1f}% processado")
        self.latest.setText(latest or "Processando...")


class HistoryPage(QWidget):
    open_requested = Signal(int)
    continue_requested = Signal(int)
    export_requested = Signal(int)
    delete_requested = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 40, 48, 32)
        layout.setSpacing(24)
        header = QHBoxLayout()
        title = QLabel("Transcrições")
        title.setObjectName("title")
        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar por nome...")
        self.search.addAction(
            vector_icon("assets/icons/lucide/search.svg", "#5d5d5d", 20),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        self.search.setFixedWidth(340)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.search)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Arquivo", "Duração", "Estado", "Progresso", "Ações"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(2, 126)
        self.table.setColumnWidth(3, 108)
        self.table.setColumnWidth(4, 180)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        elevate(self.table)
        layout.addLayout(header)
        layout.addWidget(self.table)

    @staticmethod
    def progress_cell(value: float) -> QWidget:
        """Render the percentage and its visual indicator as a single compact table cell."""
        cell = QWidget()
        cell_layout = QVBoxLayout(cell)
        cell_layout.setContentsMargins(8, 9, 8, 9)
        cell_layout.setSpacing(4)
        percentage = QLabel(f"{value:.1f}%")
        percentage.setAlignment(Qt.AlignmentFlag.AlignCenter)
        percentage.setFont(interface_font(12, QFont.Weight.Medium, tabular=True))
        bar = QProgressBar()
        bar.setObjectName("tableProgress")
        bar.setRange(0, 1000)
        bar.setValue(round(value * 10))
        bar.setTextVisible(False)
        cell_layout.addWidget(percentage)
        cell_layout.addWidget(bar)
        return cell

    def populate(self, rows: list[Any]) -> None:
        self.table.setRowCount(0)
        for row in rows:
            index = self.table.rowCount()
            self.table.insertRow(index)
            audio_item = QTableWidgetItem(row["audio_name"])
            audio_item.setIcon(vector_icon("assets/icons/lucide/file-text.svg", "#1769ff", 22))
            self.table.setItem(index, 0, audio_item)
            duration_item = QTableWidgetItem(format_duration(row["duration"]))
            duration_item.setFont(interface_font(12, QFont.Weight.Medium, tabular=True))
            self.table.setItem(index, 1, duration_item)
            status = JobStatus(row["status"])
            status_item = QTableWidgetItem(STATUS_LABELS[status])
            if status == JobStatus.COMPLETED:
                status_item.setForeground(QBrush(QColor("#168a4b")))
            self.table.setItem(index, 2, status_item)
            self.table.setCellWidget(index, 3, self.progress_cell(float(row["progress"])))
            actions = QWidget()
            actions_layout = QHBoxLayout(actions)
            actions_layout.setContentsMargins(6, 6, 6, 6)
            actions_layout.setSpacing(6)
            can_continue = status in {
                JobStatus.READY,
                JobStatus.PAUSED,
                JobStatus.CANCELLED,
                JobStatus.FAILED,
            }
            open_button = QPushButton()
            export_button = QPushButton()
            delete_button = QPushButton()
            for button, label in (
                (open_button, "Continuar" if can_continue else "Abrir"),
                (export_button, "Exportar"),
                (delete_button, "Excluir"),
            ):
                button.setObjectName("iconAction")
                button.setToolTip(label)
                button.setAccessibleName(label)
            delete_button.setObjectName("dangerIcon")
            add_asset_icon(open_button, "assets/ui/action-open.png")
            add_asset_icon(export_button, "assets/ui/action-export.png")
            add_asset_icon(delete_button, "assets/ui/action-delete.png")
            if can_continue:
                open_button.clicked.connect(lambda _=False, value=row["id"]: self.continue_requested.emit(value))
            else:
                open_button.clicked.connect(lambda _=False, value=row["id"]: self.open_requested.emit(value))
            export_button.clicked.connect(lambda _=False, value=row["id"]: self.export_requested.emit(value))
            delete_button.clicked.connect(lambda _=False, value=row["id"]: self.delete_requested.emit(value))
            actions_layout.addWidget(open_button)
            actions_layout.addWidget(export_button)
            actions_layout.addWidget(delete_button)
            self.table.setCellWidget(index, 4, actions)
            self.table.setRowHeight(index, 64)


class ReviewPage(QWidget):
    back_requested = Signal()
    export_requested = Signal(int)

    def __init__(self, database: Database):
        super().__init__()
        self.database = database
        self.job_id: int | None = None
        self.rows: list[Any] = []
        self.audio_output = QAudioOutput(self)
        self.player = QMediaPlayer(self)
        self.player.setAudioOutput(self.audio_output)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 40, 48, 32)
        layout.setSpacing(20)
        header = QHBoxLayout()
        back = QPushButton("← Transcrições")
        self.title = QLabel("Revisão")
        self.title.setObjectName("title")
        export = QPushButton("Exportar")
        export.setObjectName("primary")
        header.addWidget(back)
        header.addWidget(self.title)
        header.addStretch()
        header.addWidget(export)
        player_layout = QHBoxLayout()
        self.play = QPushButton("▶ Reproduzir")
        self.position = QLabel("00:00:00")
        self.position.setObjectName("timestamp")
        self.position.setFont(interface_font(12, QFont.Weight.Medium, tabular=True))
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 0)
        player_layout.addWidget(self.play)
        player_layout.addWidget(self.position)
        player_layout.addWidget(self.slider)
        self.filter = QLineEdit()
        self.filter.setPlaceholderText("Buscar na transcrição...")
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Tempo", "Texto revisável", "Atenção", "Revisado"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setWordWrap(True)
        elevate(self.table)
        layout.addLayout(header)
        layout.addWidget(card(player_layout))
        layout.addWidget(self.filter)
        layout.addWidget(self.table)
        back.clicked.connect(self.back_requested)
        export.clicked.connect(lambda: self.export_requested.emit(self.job_id or 0))
        self.play.clicked.connect(self.toggle_play)
        self.slider.sliderMoved.connect(self.player.setPosition)
        self.player.positionChanged.connect(self.position_changed)
        self.player.durationChanged.connect(self.slider.setMaximum)
        self.table.cellDoubleClicked.connect(self.play_segment)
        self.table.itemChanged.connect(self.item_changed)
        self.filter.textChanged.connect(self.apply_filter)

    def load_job(self, job_id: int) -> None:
        self.job_id = job_id
        job = self.database.get_job(job_id)
        if job is None:
            return
        self.title.setText(job["audio_name"])
        self.player.setSource(QUrl.fromLocalFile(job["audio_path"]))
        self.rows = self.database.get_segments(job_id)
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        for row in self.rows:
            index = self.table.rowCount()
            self.table.insertRow(index)
            time_item = QTableWidgetItem(f"{format_duration(row['start'])}\n{format_duration(row['end'])}")
            time_item.setFont(interface_font(12, QFont.Weight.Medium, tabular=True))
            time_item.setData(Qt.ItemDataRole.UserRole, row["start"])
            text_item = QTableWidgetItem(row["revised_text"] or row["original_text"])
            text_item.setFont(interface_font(16, QFont.Weight.Normal))
            text_item.setData(Qt.ItemDataRole.UserRole, row["id"])
            warning = QTableWidgetItem("Verifique" if row["review_required"] else "Normal")
            reviewed = QTableWidgetItem("Sim" if row["reviewed"] else "Não")
            reviewed.setData(Qt.ItemDataRole.UserRole, row["id"])
            self.table.setItem(index, 0, time_item)
            self.table.setItem(index, 1, text_item)
            self.table.setItem(index, 2, warning)
            self.table.setItem(index, 3, reviewed)
            self.table.setRowHeight(index, 72)
        self.table.blockSignals(False)

    def toggle_play(self) -> None:
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.play.setText("▶ Reproduzir")
        else:
            self.player.play()
            self.play.setText("⏸ Pausar")

    def position_changed(self, millis: int) -> None:
        self.slider.setValue(millis)
        self.position.setText(format_duration(millis / 1000))

    def play_segment(self, row: int, _column: int) -> None:
        item = self.table.item(row, 0)
        if item is None:
            return
        self.player.setPosition(int(float(item.data(Qt.ItemDataRole.UserRole)) * 1000))
        self.player.play()
        self.play.setText("⏸ Pausar")

    def item_changed(self, item: QTableWidgetItem) -> None:
        if item.column() != 1:
            return
        segment_id = int(item.data(Qt.ItemDataRole.UserRole))
        self.database.revise_segment(segment_id, item.text())
        reviewed_item = self.table.item(item.row(), 3)
        if reviewed_item is not None:
            reviewed_item.setText("Sim")

    def apply_filter(self, text: str) -> None:
        query = text.casefold()
        for row in range(self.table.rowCount()):
            text_item = self.table.item(row, 1)
            self.table.setRowHidden(row, text_item is None or query not in text_item.text().casefold())


class ModelsPage(QWidget):
    def __init__(self, manager: ModelManager):
        super().__init__()
        self.manager = manager
        self.worker_thread: QThread | None = None
        self.worker: ModelDownloadWorker | None = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 40, 48, 32)
        layout.setSpacing(20)
        title = QLabel("Modelos")
        title.setObjectName("title")
        description = QLabel("Baixe os modelos antes de transcrever ou deixe o aplicativo baixá-los automaticamente.")
        description.setObjectName("secondaryText")
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Perfil", "Modelo", "Estado", "Ação"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 240)
        self.table.setColumnWidth(2, 220)
        self.table.setColumnWidth(3, 144)
        self.table.verticalHeader().setVisible(False)
        elevate(self.table)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(self.table)
        layout.addWidget(self.progress)
        self.refresh()

    def refresh(self) -> None:
        self.table.setRowCount(0)
        for state in self.manager.states():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(state.label))
            self.table.setItem(row, 1, QTableWidgetItem(state.model_name))
            size = f" • {state.size_bytes / 1024**3:.2f} GB" if state.size_bytes else ""
            self.table.setItem(
                row,
                2,
                QTableWidgetItem(("Instalado" if state.installed else "Não instalado") + size),
            )
            button = QPushButton("Remover" if state.installed else "Baixar")
            if state.installed:
                button.setObjectName("danger")
                add_asset_icon(button, "assets/ui/action-delete.png")
                button.clicked.connect(lambda _=False, model=state.model_name: self.remove_model(model))
            else:
                button.setObjectName("outlineAction")
                add_asset_icon(button, "assets/ui/action-export.png")
                button.clicked.connect(lambda _=False, model=state.model_name: self.download_model(model))
            button.setMinimumWidth(128)
            self.table.setCellWidget(row, 3, button)
            self.table.setRowHeight(row, 64)

    def download_model(self, model_name: str) -> None:
        if self.worker_thread is not None and self.worker_thread.isRunning():
            QMessageBox.information(self, "Download em andamento", "Aguarde o download atual terminar.")
            return
        self.progress.show()
        self.table.setEnabled(False)
        self.worker_thread = QThread(self)
        self.worker = ModelDownloadWorker(self.manager, model_name)
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.completed.connect(self.download_completed)
        self.worker.failed.connect(self.download_failed)
        self.worker.completed.connect(self.worker_thread.quit)
        self.worker.failed.connect(self.worker_thread.quit)
        self.worker_thread.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.start()

    @Slot(str)
    def download_completed(self, _model_name: str) -> None:
        self.progress.hide()
        self.table.setEnabled(True)
        self.refresh()
        QMessageBox.information(self, "Modelo pronto", "O modelo foi baixado e verificado.")

    @Slot(str)
    def download_failed(self, error: str) -> None:
        self.progress.hide()
        self.table.setEnabled(True)
        self.refresh()
        QMessageBox.critical(
            self,
            "Não foi possível baixar o modelo",
            f"Arquivos incompletos não serão usados. Tente novamente.\n\n{error}",
        )

    def remove_model(self, model_name: str) -> None:
        if (
            QMessageBox.question(
                self,
                "Remover modelo?",
                "O modelo poderá ser baixado novamente quando necessário.",
            )
            == QMessageBox.StandardButton.Yes
        ):
            self.manager.remove(model_name)
            self.refresh()


class SimplePage(QWidget):
    def __init__(self, title_text: str, html: str):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 40, 48, 32)
        layout.setSpacing(24)
        title = QLabel(title_text)
        title.setObjectName("title")
        content = QTextBrowser()
        content.setObjectName("content")
        content.setOpenExternalLinks(True)
        content.setHtml(html)
        elevate(content)
        layout.addWidget(title)
        layout.addWidget(content)


def divider() -> QFrame:
    line = QFrame()
    line.setObjectName("divider")
    return line


class HelpPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 40, 48, 32)
        layout.setSpacing(24)
        title = QLabel("Ajuda")
        title.setObjectName("title")
        layout.addWidget(title)

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(26)
        sections = (
            (
                "assets/icons/lucide/notebook-pen.svg",
                "Como usar",
                (
                    "1. Abra Nova transcrição.",
                    "2. Selecione os áudios.",
                    "3. Confirme idioma e qualidade.",
                    "4. Inicie e aguarde. O modelo será baixado na primeira utilização.",
                    "5. Revise e exporte.",
                ),
            ),
            (
                "assets/icons/lucide/sparkles.svg",
                "Como melhorar a precisão",
                ("Informe o idioma, use Alta precisão quando o computador permitir e revise os trechos marcados.",),
            ),
            (
                "assets/icons/lucide/mic.svg",
                "Privacidade",
                ("O áudio é processado localmente e não é enviado para um serviço de transcrição.",),
            ),
            (
                "assets/icons/lucide/file-text.svg",
                "Formatos",
                ("MP3, WAV, M4A, AAC, FLAC, OGG, OPUS, WMA, AIFF e WEBM.",),
            ),
        )
        for index, (icon, heading, lines) in enumerate(sections):
            row = QHBoxLayout()
            row.setSpacing(18)
            row.setAlignment(Qt.AlignmentFlag.AlignTop)
            row.addWidget(icon_badge(self, icon), alignment=Qt.AlignmentFlag.AlignTop)
            text_layout = QVBoxLayout()
            text_layout.setSpacing(10)
            section_title = QLabel(heading)
            section_title.setObjectName("cardTitle")
            text_layout.addWidget(section_title)
            for line in lines:
                body = QLabel(line)
                body.setObjectName("cardBody")
                body.setWordWrap(True)
                text_layout.addWidget(body)
            row.addLayout(text_layout, 1)
            content_layout.addLayout(row)
            if index < len(sections) - 1:
                content_layout.addWidget(divider())
        layout.addWidget(card(content_layout))


class SettingsPage(QWidget):
    def __init__(self, hardware: Any) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 40, 48, 32)
        layout.setSpacing(24)
        title = QLabel("Configurações")
        title.setObjectName("title")
        layout.addWidget(title)

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(32, 32, 32, 30)
        content_layout.setSpacing(22)
        heading = QHBoxLayout()
        heading.setSpacing(18)
        heading.addWidget(icon_badge(self, "assets/icons/lucide/sparkles.svg"))
        heading_label = QLabel("Configuração automática ativa")
        heading_label.setObjectName("cardTitle")
        heading.addWidget(heading_label)
        heading.addStretch()
        content_layout.addLayout(heading)
        rows = (
            ("Processador:", hardware.cpu),
            ("Processadores lógicos:", str(hardware.logical_cpus)),
            ("Memória:", f"{hardware.ram_gb:.1f} GB"),
            ("Aceleração:", hardware.gpu_name or "CPU"),
            ("Recomendação:", hardware.recommended_profile),
        )
        for label_text, value_text in rows:
            row = QHBoxLayout()
            row.setSpacing(18)
            label = QLabel(label_text)
            label.setObjectName("infoLabel")
            label.setFixedWidth(205)
            value = QLabel(value_text)
            value.setObjectName("recommendationValue" if label_text == "Recomendação:" else "infoValue")
            value.setWordWrap(True)
            row.addWidget(label)
            row.addWidget(value, 1)
            content_layout.addLayout(row)
        content_layout.addWidget(divider())
        privacy = QHBoxLayout()
        privacy.setSpacing(14)
        privacy.addWidget(icon_badge(self, "assets/icons/lucide/mic.svg"))
        privacy_text = QLabel("O processamento é local. Falhas de aceleração NVIDIA retornam automaticamente para CPU.")
        privacy_text.setObjectName("cardBody")
        privacy_text.setWordWrap(True)
        privacy.addWidget(privacy_text, 1)
        content_layout.addLayout(privacy)
        layout.addWidget(card(content_layout))
        layout.addStretch()


class MainWindow(QMainWindow):
    def __init__(self, paths: AppPaths, database: Database, brand_symbol_path: Path | None = None):
        super().__init__()
        self.paths = paths
        self.database = database
        self.hardware = detect_hardware()
        self.queue: list[tuple[int, AudioInfo, str]] = []
        self.queue_position = 0
        self.worker_thread: QThread | None = None
        self.worker: TranscriptionWorker | None = None
        self.controller: TranscriptionController | None = None
        self.worker_outcome: JobStatus | None = None
        self.close_when_finished = False
        self.setWindowTitle("Voxnote")
        if brand_symbol_path is not None:
            self.setWindowIcon(QIcon(str(brand_symbol_path.with_name("voxnote-app-icon.ico"))))
        self.setMinimumSize(1100, 720)
        self.resize(1280, 820)
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        main = QHBoxLayout(root)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(260)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(16, 30, 16, 20)
        side.setSpacing(8)
        brand = QWidget()
        brand.setObjectName("brandLockup")
        brand_layout = QHBoxLayout(brand)
        brand_layout.setContentsMargins(12, 0, 0, 22)
        brand_layout.setSpacing(10)
        brand_symbol = QLabel()
        brand_symbol.setFixedSize(42, 42)
        if brand_symbol_path is not None:
            pixmap = QPixmap(str(brand_symbol_path))
            if not pixmap.isNull():
                brand_symbol.setPixmap(
                    pixmap.scaled(
                        42,
                        42,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
        brand_name = QLabel("Voxnote")
        brand_name.setObjectName("brandName")
        brand_layout.addWidget(brand_symbol)
        brand_layout.addWidget(brand_name)
        brand_layout.addStretch()
        side.addWidget(brand)
        self.nav_buttons: list[QPushButton] = []
        self.nav_icon_assets: list[str] = []
        navigation = (
            ("Nova transcrição", "assets/icons/lucide/mic.svg"),
            ("Transcrições", "assets/icons/lucide/file-text.svg"),
            ("Modelos", "assets/icons/lucide/notebook-pen.svg"),
            ("Configurações", "assets/icons/lucide/sparkles.svg"),
            ("Ajuda", "assets/icons/lucide/notebook-pen.svg"),
        )
        for index, (label, icon) in enumerate(navigation):
            button = QPushButton(label)
            button.setObjectName("nav")
            button.setCheckable(True)
            add_vector_icon(button, icon, size=22)
            button.clicked.connect(lambda _=False, value=index: self.navigate(value))
            side.addWidget(button)
            self.nav_buttons.append(button)
            self.nav_icon_assets.append(icon)
        side.addStretch()
        device = self.hardware.gpu_name or "Processamento por CPU"
        hardware_card = QFrame()
        hardware_card.setObjectName("hardwareCard")
        hardware_layout = QVBoxLayout(hardware_card)
        hardware_layout.setContentsMargins(14, 14, 14, 14)
        hardware_layout.setSpacing(8)
        hardware_heading = QHBoxLayout()
        hardware_heading.setSpacing(8)
        hardware_heading.addWidget(asset_label(hardware_card, "assets/ui/hardware.png", 24))
        hardware_title = QLabel("Hardware disponível")
        hardware_title.setObjectName("formLabel")
        hardware_heading.addWidget(hardware_title)
        hardware_heading.addStretch()
        hardware_layout.addLayout(hardware_heading)
        hardware_details = QLabel(f"{device}\n{self.hardware.ram_gb:.1f} GB de RAM")
        hardware_details.setObjectName("caption")
        hardware_details.setWordWrap(True)
        hardware_layout.addWidget(hardware_details)
        elevate(hardware_card, blur_radius=20, offset_y=5, alpha=12)
        side.addWidget(hardware_card)
        self.stack = QStackedWidget()
        hardware_text = (
            f"Configuração recomendada: {self.hardware.recommended_profile}. "
            f"{self.hardware.gpu_name or f'CPU com {self.hardware.logical_cpus} processadores lógicos'} • "
            f"{self.hardware.ram_gb:.1f} GB de RAM."
        )
        self.new_page = NewPage(hardware_text, self.hardware.recommended_profile)
        self.history_page = HistoryPage()
        self.models_page = ModelsPage(ModelManager(paths.models))
        self.settings_page = SettingsPage(self.hardware)
        self.help_page = HelpPage()
        self.progress_page = ProgressPage()
        self.review_page = ReviewPage(database)
        for page in (
            self.new_page,
            self.history_page,
            self.models_page,
            self.settings_page,
            self.help_page,
            self.progress_page,
            self.review_page,
        ):
            self.stack.addWidget(page)
        main.addWidget(sidebar)
        main.addWidget(self.stack)
        self.new_page.start_requested.connect(self.start_queue)
        self.history_page.search.textChanged.connect(self.refresh_history)
        self.history_page.open_requested.connect(self.open_review)
        self.history_page.continue_requested.connect(self.resume_job)
        self.history_page.export_requested.connect(self.export_job)
        self.history_page.delete_requested.connect(self.delete_job)
        self.review_page.back_requested.connect(lambda: self.navigate(1))
        self.review_page.export_requested.connect(self.export_job)
        self.progress_page.pause_requested.connect(self.toggle_pause)
        self.progress_page.cancel_requested.connect(self.cancel_current)
        self.navigate(0)

    def navigate(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        for position, button in enumerate(self.nav_buttons):
            active = position == index
            button.setChecked(active)
            add_vector_icon(button, self.nav_icon_assets[position], "#1769ff" if active else "#2b2b2b", 22)
        if index == 1:
            self.refresh_history()

    @Slot(list, str, str, str)
    def start_queue(self, files: list[AudioInfo], language: str | None, profile: str, glossary: str) -> None:
        model = MODEL_PROFILES[profile]
        self.queue = [
            (self.database.create_job(info, language, profile, model, glossary), info, profile) for info in files
        ]
        self.queue_position = 0
        self.new_page.clear()
        self.start_next()

    def start_next(self) -> None:
        if self.queue_position >= len(self.queue):
            QMessageBox.information(self, "Transcrição concluída", "Todos os arquivos da fila foram processados.")
            self.navigate(1)
            return
        job_id, info, profile = self.queue[self.queue_position]
        self.progress_page.set_job(info.path.name, self.queue_position + 1, len(self.queue), profile)
        self.stack.setCurrentWidget(self.progress_page)
        self.controller = TranscriptionController()
        self.worker_outcome = None
        self.worker_thread = QThread(self)
        self.worker = TranscriptionWorker(self.database, job_id, self.paths.models, self.controller)
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.progress_page.update_progress)
        self.worker.completed.connect(self.current_completed)
        self.worker.cancelled.connect(self.current_cancelled)
        self.worker.failed.connect(self.current_failed)
        self.worker.completed.connect(self.worker_thread.quit)
        self.worker.cancelled.connect(self.worker_thread.quit)
        self.worker.failed.connect(self.worker_thread.quit)
        self.worker_thread.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.finished.connect(self.worker_finished)
        self.worker_thread.start()

    @Slot()
    def current_completed(self) -> None:
        self.worker_outcome = JobStatus.COMPLETED
        self.queue_position += 1

    @Slot()
    def current_cancelled(self) -> None:
        self.worker_outcome = JobStatus.CANCELLED

    @Slot(str)
    def current_failed(self, error: str) -> None:
        self.worker_outcome = JobStatus.FAILED
        QMessageBox.critical(
            self,
            "A transcrição foi interrompida",
            "O progresso concluído foi preservado.\n\n"
            f"Detalhe: {error}\n\nVocê pode tentar novamente pelas Transcrições.",
        )
        self.navigate(1)

    @Slot()
    def worker_finished(self) -> None:
        if self.close_when_finished:
            self.close_when_finished = False
            self.close()
            return
        if self.worker_outcome == JobStatus.COMPLETED:
            self.start_next()
        elif self.worker_outcome == JobStatus.CANCELLED:
            self.progress_page.cancel.setEnabled(True)
            QMessageBox.information(
                self,
                "Transcrição interrompida",
                "Os trechos concluídos foram preservados. Você pode continuar pelo histórico.",
            )
            self.navigate(1)

    def toggle_pause(self) -> None:
        if self.controller is None:
            return
        if self.controller.pause_event.is_set():
            self.controller.resume()
            self.progress_page.pause.setText("Pausar")
            self.progress_page.saved.setText("✓ Transcrição retomada. O progresso continua sendo salvo.")
        else:
            self.controller.pause()
            self.progress_page.pause.setText("Continuar")
            self.progress_page.saved.setText("Pausando com segurança após o trecho atual...")

    def cancel_current(self) -> None:
        if self.controller is None:
            return
        answer = QMessageBox.question(
            self,
            "Cancelar esta transcrição?",
            "Os trechos concluídos serão preservados e o áudio original não será alterado.",
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.controller.cancel()
            self.progress_page.cancel.setEnabled(False)
            self.progress_page.saved.setText("Cancelando com segurança após o trecho atual...")

    def refresh_history(self, query: str = "") -> None:
        self.history_page.populate(self.database.list_jobs(query))

    def resume_job(self, job_id: int) -> None:
        if self.worker_thread is not None and self.worker_thread.isRunning():
            QMessageBox.information(self, "Transcrição em andamento", "Aguarde ou cancele o trabalho atual.")
            return
        job = self.database.get_job(job_id)
        if job is None:
            return
        audio_path = Path(job["audio_path"])
        if not audio_path.is_file():
            QMessageBox.warning(
                self,
                "Arquivo original não encontrado",
                "O áudio pode ter sido movido ou removido. O progresso existente foi preservado.",
            )
            return
        info = AudioInfo(
            audio_path,
            float(job["duration"]),
            str(job["format_name"]),
            int(job["size"]),
        )
        self.queue = [(job_id, info, str(job["profile"]))]
        self.queue_position = 0
        self.start_next()

    def open_review(self, job_id: int) -> None:
        self.review_page.load_job(job_id)
        self.stack.setCurrentWidget(self.review_page)
        for button in self.nav_buttons:
            button.setChecked(False)

    def export_job(self, job_id: int) -> None:
        if not job_id:
            return
        job = self.database.get_job(job_id)
        if job is None:
            return
        path, selected = QFileDialog.getSaveFileName(
            self,
            "Exportar transcrição",
            str(self.paths.exports / f"{Path(job['audio_name']).stem}.txt"),
            "Texto (*.txt);;Legendas SRT (*.srt);;Legendas WebVTT (*.vtt);;Dados JSON (*.json)",
        )
        if not path:
            return
        kind = {
            "Texto (*.txt)": "txt",
            "Legendas SRT (*.srt)": "srt",
            "Legendas WebVTT (*.vtt)": "vtt",
            "Dados JSON (*.json)": "json",
        }.get(selected, Path(path).suffix[1:].lower())
        try:
            export_transcript(job, self.database.get_segments(job_id), Path(path), kind)
            QMessageBox.information(self, "Exportação concluída", f"Arquivo salvo em:\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "Não foi possível exportar", f"Nenhum dado foi apagado.\n\n{exc}")

    def delete_job(self, job_id: int) -> None:
        if self.database.is_job_active(job_id):
            QMessageBox.warning(
                self,
                "Transcrição em andamento",
                "Pause ou cancele esta transcrição antes de excluí-la.",
            )
            return
        if (
            QMessageBox.question(
                self,
                "Excluir transcrição?",
                "A transcrição e suas correções serão excluídas. O arquivo de áudio original não será apagado.",
            )
            == QMessageBox.StandardButton.Yes
        ):
            self.database.delete_job(job_id)
            self.refresh_history(self.history_page.search.text())

    def closeEvent(self, event: QCloseEvent) -> None:
        model_thread = self.models_page.worker_thread
        if model_thread is not None and model_thread.isRunning():
            QMessageBox.information(
                self,
                "Download em andamento",
                "Aguarde o download do modelo terminar antes de fechar o aplicativo.",
            )
            event.ignore()
            return
        if self.worker_thread is not None and self.worker_thread.isRunning():
            answer = QMessageBox.question(
                self,
                "Encerrar com segurança?",
                "O trecho atual será concluído e o progresso será salvo antes de fechar.",
            )
            if answer == QMessageBox.StandardButton.Yes:
                self.close_when_finished = True
                if self.controller is not None:
                    self.controller.cancel()
            event.ignore()
            return
        event.accept()

    def _models_html(self) -> str:
        return """
        <h2>Modelos são baixados quando necessários</h2>
        <p><b>Leve</b> — indicado para computadores com 8 GB de RAM.</p>
        <p><b>Equilibrado</b> — boa precisão e consumo moderado.</p>
        <p><b>Alta precisão</b> — melhor qualidade, maior download e processamento.</p>
        <p><b>Rápido</b> — prioriza velocidade, especialmente com GPU NVIDIA.</p>
        <p>Os arquivos ficam em <code>%LOCALAPPDATA%\\Transcritor\\models</code>.</p>
        """

    def _settings_html(self) -> str:
        return f"""
        <h2>Configuração automática ativa</h2>
        <p><b>Processador:</b> {self.hardware.cpu}</p>
        <p><b>Processadores lógicos:</b> {self.hardware.logical_cpus}</p>
        <p><b>Memória:</b> {self.hardware.ram_gb:.1f} GB</p>
        <p><b>Aceleração:</b> {self.hardware.gpu_name or "CPU"}</p>
        <p><b>Recomendação:</b> {self.hardware.recommended_profile}</p>
        <p>O processamento é local. Falhas de aceleração NVIDIA retornam automaticamente para CPU.</p>
        """

    def _help_html(self) -> str:
        return """
        <h2>Como usar</h2>
        <ol><li>Abra Nova transcrição.</li><li>Selecione os áudios.</li><li>Confirme idioma e qualidade.</li>
        <li>Inicie e aguarde. O modelo será baixado na primeira utilização.</li><li>Revise e exporte.</li></ol>
        <h2>Como melhorar a precisão</h2>
        <p>Informe o idioma, use Alta precisão quando o computador permitir e revise os trechos marcados.</p>
        <h2>Privacidade</h2><p>O áudio é processado localmente e não é enviado para um serviço de transcrição.</p>
        <h2>Formatos</h2><p>MP3, WAV, M4A, AAC, FLAC, OGG, OPUS, WMA, AIFF e WEBM.</p>
        """


def configure_logging(paths: AppPaths) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[logging.FileHandler(paths.logs / "transcritor.log", encoding="utf-8")],
    )
