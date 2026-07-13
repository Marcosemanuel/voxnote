from pathlib import Path

from transcritor.database import Database
from transcritor.domain import AudioInfo, HardwareProfile, JobStatus
from transcritor.engine import TranscriptionController
from transcritor.paths import AppPaths
from transcritor.qml_controller import QmlController


def hardware_fixture() -> HardwareProfile:
    return HardwareProfile(
        cpu="CPU de teste",
        logical_cpus=8,
        ram_gb=16.0,
        gpu_name=None,
        gpu_vram_gb=None,
        cuda_compatible=False,
        recommended_profile="Equilibrada",
    )


def test_qml_controller_exposes_history(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("transcritor.qml_controller.detect_hardware", hardware_fixture)
    paths = AppPaths.resolve(tmp_path / "app")
    database = Database(paths.data / "test.db")
    database.create_job(AudioInfo(tmp_path / "audio.wav", 12.0, "wav", 100), "pt", "Leve", "small")

    controller = QmlController(paths, database)
    controller.navigate(1)

    assert controller.page == 1
    assert controller.jobs[0]["name"] == "audio.wav"
    assert controller.jobs[0]["duration"] == "00:00:12"


def test_qml_shell_and_components_are_versioned() -> None:
    qml_root = Path(__file__).parents[1] / "src" / "transcritor" / "qml"
    assert (qml_root / "Main.qml").is_file()
    assert (qml_root / "Theme.qml").is_file()
    assert (qml_root / "components" / "NavItem.qml").is_file()
    for component in ("VxCheckBox.qml", "VxProgressBar.qml", "VxTextArea.qml"):
        assert (qml_root / "components" / component).is_file()
    combo_box = (qml_root / "components" / "VxComboBox.qml").read_text(encoding="utf-8")
    assert "highlightedIndex =" not in combo_box
    main_qml = (qml_root / "Main.qml").read_text(encoding="utf-8")
    assert "VxCheckBox {\n                                    id: captureConsent" in main_qml
    assert "VxProgressBar {" in main_qml
    assert "VxTextArea {\n                                    id: meetingEdit" in main_qml


def test_qml_controller_closes_after_cancelled_worker(qtbot, monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("transcritor.qml_controller.detect_hardware", hardware_fixture)
    paths = AppPaths.resolve(tmp_path / "app")
    controller = QmlController(paths, Database(paths.data / "test.db"))
    controller._worker_thread = type("Thread", (), {"isRunning": lambda _self: True})()
    controller._controller = TranscriptionController()

    with qtbot.waitSignal(controller.confirmationRequested, timeout=1000) as confirmation:
        controller.request_close()
    assert confirmation.args[0] == "close"

    controller.confirm("close")
    controller._worker_outcome = JobStatus.CANCELLED
    with qtbot.waitSignal(controller.closeRequested, timeout=1000):
        controller._worker_finished()
    assert controller._controller.cancel_event.is_set()


def test_qml_controller_exposes_newer_release(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("transcritor.qml_controller.detect_hardware", hardware_fixture)
    paths = AppPaths.resolve(tmp_path / "app")
    controller = QmlController(paths, Database(paths.data / "test.db"))

    controller._set_update_available("0.1.1", "https://github.com/Marcosemanuel/voxnote/releases/tag/v0.1.1")

    assert controller.updateAvailable is True
    assert controller.updateVersion == "0.1.1"
    assert controller.updateUrl.endswith("v0.1.1")
