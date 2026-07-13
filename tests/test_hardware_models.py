from pathlib import Path

from transcritor.hardware import detect_hardware
from transcritor.models import ModelManager


def test_gpu_with_insufficient_vram_is_not_recommended_for_large(monkeypatch) -> None:
    monkeypatch.setattr("transcritor.hardware._nvidia_info", lambda: ("GPU pequena", 4.0))
    monkeypatch.setattr("transcritor.hardware._cuda_compatible", lambda: True)
    monkeypatch.setattr("transcritor.hardware.psutil.virtual_memory", lambda: type("M", (), {"total": 16 * 1024**3})())
    profile = detect_hardware()
    assert profile.gpu_vram_gb == 4.0
    assert profile.recommended_profile == "Equilibrada"


def test_model_manager_download_validates_and_removes(monkeypatch, tmp_path: Path) -> None:
    def fake_download(_name: str, output_dir: str) -> None:
        destination = Path(output_dir)
        destination.mkdir(parents=True)
        (destination / "model.bin").write_bytes(b"model")
        (destination / "config.json").write_text("{}", encoding="utf-8")

    monkeypatch.setattr("transcritor.models.download_model", fake_download)
    manager = ModelManager(tmp_path)
    manager.download("small")
    assert manager.is_valid("small")
    assert manager.resolve("small") == str(tmp_path / "small")
    manager.remove("small")
    assert not manager.path_for("small").exists()


def test_model_manager_rejects_tampered_file(monkeypatch, tmp_path: Path) -> None:
    def fake_download(_name: str, output_dir: str) -> None:
        destination = Path(output_dir)
        destination.mkdir(parents=True)
        (destination / "model.bin").write_bytes(b"model")
        (destination / "config.json").write_text("{}", encoding="utf-8")

    monkeypatch.setattr("transcritor.models.download_model", fake_download)
    manager = ModelManager(tmp_path)
    path = manager.download("small")

    (path / "model.bin").write_bytes(b"tampered")

    assert not manager.is_valid("small")
