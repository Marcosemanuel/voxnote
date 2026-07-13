from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from transcritor.database import Database
from transcritor.domain import JobStatus
from transcritor.engine import TranscriptionController, transcribe_job
from transcritor.exporters import export_meeting_transcript, export_transcript
from transcritor.meeting_transcription import transcribe_meeting
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


class MeetingTranscriptionWorker(QObject):
    progress = Signal(float, str)
    completed = Signal(int)
    cancelled = Signal(int)
    failed = Signal(str)

    def __init__(
        self,
        database: Database,
        session_id: int,
        models_dir: Path,
        cache_dir: Path,
        controller: TranscriptionController,
    ):
        super().__init__()
        self.database = database
        self.session_id = session_id
        self.models_dir = models_dir
        self.cache_dir = cache_dir
        self.controller = controller

    @Slot()
    def run(self) -> None:
        try:
            run_id = transcribe_meeting(
                self.database,
                self.session_id,
                self.models_dir,
                self.cache_dir,
                self.controller,
                lambda value, text: self.progress.emit(value, text),
            )
            if self.controller.cancel_event.is_set():
                self.cancelled.emit(run_id)
            else:
                self.completed.emit(run_id)
        except Exception as exc:
            LOG.exception("Meeting transcription failed")
            self.failed.emit(str(exc))


class MeetingExportWorker(QObject):
    completed = Signal(str)
    failed = Signal(str)

    def __init__(self, database: Database, session_id: int, run_id: int, destination: Path, kind: str):
        super().__init__()
        self.database = database
        self.session_id = session_id
        self.run_id = run_id
        self.destination = destination
        self.kind = kind

    @Slot()
    def run(self) -> None:
        try:
            session = self.database.get_meeting_session(self.session_id)
            run = self.database.get_latest_transcription_run(self.session_id)
            if session is None or run is None or int(run["id"]) != self.run_id:
                raise ValueError("Transcrição da reunião não encontrada.")
            segments = self.database.list_run_segments(self.run_id)
            export_meeting_transcript(session, run, segments, self.destination, self.kind)
            self.completed.emit(str(self.destination))
        except Exception as exc:
            LOG.exception("Meeting export failed")
            self.failed.emit(str(exc))
