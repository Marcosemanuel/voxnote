from pathlib import Path
from types import SimpleNamespace

from transcritor.database import Database
from transcritor.domain import AudioInfo, JobStatus, SegmentData
from transcritor.engine import TranscriptionController, transcribe_job


class FakeModel:
    last_options: dict = {}

    def __init__(self, *_args, **_kwargs):
        pass

    def transcribe(self, _path: str, **options):
        FakeModel.last_options = options
        segment = SimpleNamespace(
            start=10.0,
            end=15.0,
            text=" continuação",
            avg_logprob=-0.2,
            no_speech_prob=0.1,
            compression_ratio=1.0,
            words=[],
        )
        return iter([segment]), SimpleNamespace()


def prepare_engine(monkeypatch, models_dir: Path) -> None:
    monkeypatch.setattr("transcritor.engine.WhisperModel", FakeModel)
    monkeypatch.setattr("ctranslate2.get_supported_compute_types", lambda _device: set())
    monkeypatch.setattr("transcritor.engine.ModelManager.is_valid", lambda _manager, _name: True)
    monkeypatch.setattr("transcritor.engine.ModelManager.path_for", lambda _manager, _name: models_dir / "small")


def test_resume_starts_at_last_checkpoint(monkeypatch, tmp_path: Path) -> None:
    prepare_engine(monkeypatch, tmp_path / "models")
    database = Database(tmp_path / "test.db")
    audio = tmp_path / "audio.wav"
    audio.touch()
    job_id = database.create_job(AudioInfo(audio, 20, "wav", 1), "pt", "Leve", "small")
    database.save_segment(job_id, 0, SegmentData(0, 10, "primeira parte"), [])
    result = transcribe_job(database, job_id, tmp_path / "models", TranscriptionController(), lambda *_: None)
    assert result == JobStatus.COMPLETED
    assert FakeModel.last_options["clip_timestamps"] == "10.0,"
    segments = database.get_segments(job_id)
    assert [row["segment_index"] for row in segments] == [0, 1]


def test_cancelled_job_is_not_completed(monkeypatch, tmp_path: Path) -> None:
    prepare_engine(monkeypatch, tmp_path / "models")
    database = Database(tmp_path / "test.db")
    audio = tmp_path / "audio.wav"
    audio.touch()
    job_id = database.create_job(AudioInfo(audio, 20, "wav", 1), "pt", "Leve", "small")
    controller = TranscriptionController()
    controller.cancel()
    result = transcribe_job(database, job_id, tmp_path / "models", controller, lambda *_: None)
    assert result == JobStatus.CANCELLED
    assert database.get_job(job_id)["status"] == JobStatus.CANCELLED


def test_cuda_error_during_transcription_retries_on_cpu(monkeypatch, tmp_path: Path) -> None:
    attempts: list[str] = []

    class CudaFailureModel(FakeModel):
        def __init__(self, _source: str, *, device: str, **_kwargs):
            self.device = device
            attempts.append(device)

        def transcribe(self, _path: str, **options):
            if self.device == "cuda":
                raise RuntimeError("CUDA runtime failed")
            return super().transcribe(_path, **options)

    models_dir = tmp_path / "models"
    monkeypatch.setattr("transcritor.engine.WhisperModel", CudaFailureModel)
    monkeypatch.setattr("ctranslate2.get_supported_compute_types", lambda _device: {"float16"})
    monkeypatch.setattr("transcritor.engine.ModelManager.is_valid", lambda _manager, _name: True)
    monkeypatch.setattr("transcritor.engine.ModelManager.path_for", lambda _manager, _name: models_dir / "small")
    database = Database(tmp_path / "test.db")
    audio = tmp_path / "audio.wav"
    audio.touch()
    job_id = database.create_job(AudioInfo(audio, 20, "wav", 1), "pt", "Leve", "small")

    result = transcribe_job(database, job_id, models_dir, TranscriptionController(), lambda *_: None)

    assert result == JobStatus.COMPLETED
    assert attempts == ["cuda", "cpu"]
    assert database.get_job(job_id)["backend"] == "cpu"
