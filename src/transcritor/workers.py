from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from transcritor.database import Database
from transcritor.domain import JobStatus
from transcritor.engine import TranscriptionController, transcribe_job
from transcritor.exporters import export_transcript
from transcritor.models import ModelManager

LOG = logging.getLogger(__name__)


class TranscriptionWorker(QObject):
    progress = Signal(float, str)
    completed = Signal()
    cancelled = Signal()
    failed = Signal(str)

    def __init__(self, database: Database, job_id: int, models_dir: Path, controller: TranscriptionController):
        super().__init__()
        self.database = database
        self.job_id = job_id
        self.models_dir = models_dir
        self.controller = controller

    @Slot()
    def run(self) -> None:
        try:
            result = transcribe_job(
                self.database,
                self.job_id,
                self.models_dir,
                self.controller,
                lambda value, text: self.progress.emit(value, text),
            )
            if result == JobStatus.CANCELLED:
                self.cancelled.emit()
            else:
                self.completed.emit()
        except Exception as exc:
            LOG.exception("Transcription failed")
            self.database.update_job(self.job_id, JobStatus.FAILED, error=str(exc))
            self.failed.emit(str(exc))


class ModelDownloadWorker(QObject):
    completed = Signal(str)
    failed = Signal(str)

    def __init__(self, manager: ModelManager, model_name: str):
        super().__init__()
        self.manager = manager
        self.model_name = model_name

    @Slot()
    def run(self) -> None:
        try:
            self.manager.download(self.model_name)
            self.completed.emit(self.model_name)
        except Exception as exc:
            LOG.exception("Model download failed")
            self.failed.emit(str(exc))


class ExportWorker(QObject):
    completed = Signal(str)
    failed = Signal(str)

    def __init__(self, database: Database, job_id: int, destination: Path, kind: str):
        super().__init__()
        self.database = database
        self.job_id = job_id
        self.destination = destination
        self.kind = kind

    @Slot()
    def run(self) -> None:
        try:
            job = self.database.get_job(self.job_id)
            if job is None:
                raise ValueError("Transcrição não encontrada.")
            export_transcript(job, self.database.get_segments(self.job_id), self.destination, self.kind)
            self.completed.emit(str(self.destination))
        except Exception as exc:
            LOG.exception("Export failed")
            self.failed.emit(str(exc))
