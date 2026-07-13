from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

from faster_whisper import WhisperModel

from transcritor.database import Database
from transcritor.domain import JobStatus, SegmentData
from transcritor.models import ModelManager

LOG = logging.getLogger(__name__)

ProgressCallback = Callable[[float, str], None]


class TranscriptionController:
    def __init__(self) -> None:
        self.pause_event = threading.Event()
        self.cancel_event = threading.Event()

    def pause(self) -> None:
        self.pause_event.set()

    def resume(self) -> None:
        self.pause_event.clear()

    def cancel(self) -> None:
        self.cancel_event.set()


def transcribe_job(
    database: Database, job_id: int, models_dir: Path, controller: TranscriptionController, callback: ProgressCallback
) -> JobStatus:
    job = database.get_job(job_id)
    if job is None:
        raise ValueError("Transcrição não encontrada.")
    backend = "cpu"
    compute_type = "int8"
    try:
        import ctranslate2

        if "float16" in ctranslate2.get_supported_compute_types("cuda"):
            backend, compute_type = "cuda", "float16"
    except Exception:
        backend, compute_type = "cpu", "int8"
    manager = ModelManager(models_dir)
    model_source = (
        str(manager.path_for(str(job["model_name"])))
        if manager.is_valid(str(job["model_name"]))
        else str(manager.download(str(job["model_name"])))
    )

    def run_with(device: str, selected_compute_type: str) -> JobStatus:
        database.update_job(job_id, JobStatus.TRANSCRIBING, backend=device)
        model = WhisperModel(
            model_source,
            device=device,
            compute_type=selected_compute_type,
            download_root=str(models_dir),
            cpu_threads=max(2, min(8, __import__("os").cpu_count() or 2)),
        )
        glossary = str(job["glossary"] or "") or None
        next_index, resume_at = database.resume_point(job_id)
        segments, _info = model.transcribe(
            str(job["audio_path"]),
            language=job["language"] or None,
            task="transcribe",
            beam_size=5,
            temperature=0.0,
            vad_filter=True,
            word_timestamps=True,
            condition_on_previous_text=False,
            hotwords=glossary,
            clip_timestamps=f"{resume_at}," if resume_at > 0 else "0",
        )
        for offset, item in enumerate(segments):
            index = next_index + offset
            if controller.cancel_event.is_set():
                database.update_job(job_id, JobStatus.CANCELLED)
                return JobStatus.CANCELLED
            while controller.pause_event.is_set():
                database.update_job(job_id, JobStatus.PAUSED)
                if controller.cancel_event.wait(0.2):
                    database.update_job(job_id, JobStatus.CANCELLED)
                    return JobStatus.CANCELLED
            database.update_job(job_id, JobStatus.TRANSCRIBING)
            data = SegmentData(
                item.start, item.end, item.text.strip(), item.avg_logprob, item.no_speech_prob, item.compression_ratio
            )
            words: list[dict[str, Any]] = [
                {"start": word.start, "end": word.end, "word": word.word, "probability": word.probability}
                for word in (item.words or [])
            ]
            database.save_segment(job_id, index, data, words)
            progress = min(100.0, item.end / float(job["duration"]) * 100)
            database.update_job(job_id, JobStatus.TRANSCRIBING, progress=progress)
            callback(progress, data.text)
        database.update_job(job_id, JobStatus.COMPLETED, progress=100.0)
        return JobStatus.COMPLETED

    try:
        return run_with(backend, compute_type)
    except Exception as exc:
        if backend != "cuda":
            raise
        LOG.warning("CUDA transcription failed for job %s; retrying on CPU: %s", job_id, exc)
        database.update_job(job_id, JobStatus.TRANSCRIBING, backend="cpu", error=f"Fallback CUDA→CPU: {exc}")
        return run_with("cpu", "int8")
