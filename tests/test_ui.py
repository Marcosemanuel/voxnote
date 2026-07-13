from pathlib import Path

from PySide6.QtWidgets import QLabel, QPushButton, QTextBrowser

from transcritor.database import Database
from transcritor.domain import AudioInfo, JobStatus
from transcritor.engine import TranscriptionController
from transcritor.paths import AppPaths
from transcritor.ui import HelpPage, HistoryPage, MainWindow, NewPage, SettingsPage, SimplePage
from transcritor.workers import TranscriptionWorker


def test_main_window_opens(qtbot, tmp_path: Path) -> None:
    paths = AppPaths.resolve(tmp_path / "app")
    window = MainWindow(paths, Database(paths.data / "test.db"))
    qtbot.addWidget(window)
    window.show()
    assert window.windowTitle() == "Voxnote"
    assert window.new_page.start.isEnabled() is False
    assert isinstance(window.help_page, HelpPage)
    assert isinstance(window.settings_page, SettingsPage)
    assert all(not button.icon().isNull() for button in window.nav_buttons)


def test_history_offers_continue_for_cancelled_job(qtbot, tmp_path: Path) -> None:
    database = Database(tmp_path / "test.db")
    job_id = database.create_job(AudioInfo(tmp_path / "audio.wav", 10, "wav", 1), "pt", "Leve", "small")
    database.update_job(job_id, JobStatus.CANCELLED)
    page = HistoryPage()
    qtbot.addWidget(page)
    page.populate(database.list_jobs())
    with qtbot.waitSignal(page.continue_requested, timeout=1000) as blocker:
        actions = page.table.cellWidget(0, 4)
        button = actions.findChildren(QPushButton)[0]
        button.click()
    assert blocker.args == [job_id]


def test_worker_emits_cancelled_instead_of_completed(qtbot, monkeypatch, tmp_path: Path) -> None:
    database = Database(tmp_path / "test.db")
    job_id = database.create_job(AudioInfo(tmp_path / "audio.wav", 10, "wav", 1), "pt", "Leve", "small")
    monkeypatch.setattr("transcritor.workers.transcribe_job", lambda *_args: JobStatus.CANCELLED)
    worker = TranscriptionWorker(database, job_id, tmp_path, TranscriptionController())
    with qtbot.waitSignal(worker.cancelled, timeout=1000):
        worker.run()


def test_simple_page_uses_styled_content_surface(qtbot) -> None:
    page = SimplePage("Ajuda", "<p>Conteúdo</p>")
    qtbot.addWidget(page)
    assert page.findChild(QTextBrowser, "content") is not None


def test_new_page_hides_empty_file_list(qtbot) -> None:
    page = NewPage("Configuração recomendada", "Leve")
    qtbot.addWidget(page)
    page.show()
    assert page.file_list.isHidden()


def test_new_page_keeps_configuration_as_a_clear_form_section(qtbot) -> None:
    page = NewPage("Configuração recomendada", "Leve")
    qtbot.addWidget(page)
    assert page.upload_panel.graphicsEffect() is not None
    assert any(label.text() == "Configurações" for label in page.findChildren(QLabel))


def test_history_actions_column_keeps_icon_actions_visible(qtbot) -> None:
    page = HistoryPage()
    qtbot.addWidget(page)
    assert page.table.columnWidth(4) == 180
