from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from PySide6.QtCore import Property, QObject, QThread, QUrl, Signal, Slot

from transcritor.audio import AudioValidationError, inspect_audio
from transcritor.database import Database
from transcritor.domain import MODEL_PROFILES, STATUS_LABELS, AudioInfo, HardwareProfile, JobStatus, format_duration
from transcritor.engine import TranscriptionController
from transcritor.hardware import detect_hardware
from transcritor.models import ModelManager
from transcritor.paths import AppPaths
from transcritor.resources import bundled_path
from transcritor.workers import ExportWorker, ModelDownloadWorker, TranscriptionWorker

LOG = logging.getLogger(__name__)


class QmlController(QObject):
    """Small presentation bridge between the QML shell and the existing application services."""

    pageChanged = Signal()
    filesChanged = Signal()
    jobsChanged = Signal()
    modelsChanged = Signal()
    progressChanged = Signal()
    reviewChanged = Signal()
    transcriptionActiveChanged = Signal()
    closeRequested = Signal()
    modelDownloadActiveChanged = Signal()
    exportActiveChanged = Signal()
    noticeRequested = Signal(str, str, str)
    confirmationRequested = Signal(str, str, str)

    def __init__(self, paths: AppPaths, database: Database) -> None:
        super().__init__()
        self.paths = paths
        self.database = database
        self.hardware: HardwareProfile = detect_hardware()
        self.model_manager = ModelManager(paths.models)
        self._page = 0
        self._files: list[AudioInfo] = []
        self._jobs: list[dict[str, Any]] = []
        self._models: list[dict[str, Any]] = []
        self._review_segments: list[dict[str, Any]] = []
        self._review_title = "Revisão"
        self._review_audio_url = ""
        self._current_review_job = 0
        self._progress_value = 0.0
        self._progress_title = "Preparando..."
        self._progress_detail = ""
        self._progress_latest = "Preparando o modelo e o áudio..."
        self._queue: list[tuple[int, AudioInfo, str]] = []
        self._queue_position = 0
        self._worker_thread: QThread | None = None
        self._worker: TranscriptionWorker | None = None
        self._controller: TranscriptionController | None = None
        self._worker_outcome: JobStatus | None = None
        self._model_thread: QThread | None = None
        self._model_worker: ModelDownloadWorker | None = None
        self._export_thread: QThread | None = None
        self._export_worker: ExportWorker | None = None
        self._pending_confirmation: tuple[str, int | str | None] | None = None
        self.refresh_jobs()
        self.refresh_models()

    @Property(int, notify=pageChanged)
    def page(self) -> int:
        return self._page

    @Property(list, notify=filesChanged)
    def files(self) -> list[dict[str, Any]]:
        return [
            {
                "name": item.path.name,
                "path": str(item.path),
                "duration": format_duration(item.duration),
                "format": item.format_name.upper(),
                "size": f"{item.size / 1024**2:.1f} MB",
            }
            for item in self._files
        ]

    @Property(list, notify=jobsChanged)
    def jobs(self) -> list[dict[str, Any]]:
        return self._jobs

    @Property(list, notify=modelsChanged)
    def models(self) -> list[dict[str, Any]]:
        return self._models

    @Property(list, notify=reviewChanged)
    def reviewSegments(self) -> list[dict[str, Any]]:
        return self._review_segments

    @Property(str, notify=reviewChanged)
    def reviewTitle(self) -> str:
        return self._review_title

    @Property(str, notify=reviewChanged)
    def reviewAudioUrl(self) -> str:
        return self._review_audio_url

    @Property(int, notify=reviewChanged)
    def reviewJobId(self) -> int:
        return self._current_review_job

    @Property(float, notify=progressChanged)
    def progressValue(self) -> float:
        return self._progress_value

    @Property(str, notify=progressChanged)
    def progressTitle(self) -> str:
        return self._progress_title

    @Property(str, notify=progressChanged)
    def progressDetail(self) -> str:
        return self._progress_detail

    @Property(str, notify=progressChanged)
    def progressLatest(self) -> str:
        return self._progress_latest

    @Property(bool, notify=transcriptionActiveChanged)
    def transcriptionActive(self) -> bool:
        return self._worker_thread is not None and self._worker_thread.isRunning()

    @Property(bool, notify=modelDownloadActiveChanged)
    def modelDownloadActive(self) -> bool:
        return self._model_thread is not None and self._model_thread.isRunning()

    @Property(bool, notify=exportActiveChanged)
    def exportActive(self) -> bool:
        return self._export_thread is not None and self._export_thread.isRunning()

    @Property(str, constant=True)
    def assetRoot(self) -> str:
        return QUrl.fromLocalFile(str(bundled_path("assets"))).toString()

    @Slot(int, result=str)
    def default_export_path(self, job_id: int) -> str:
        job = self.database.get_job(job_id)
        if job is None:
            return QUrl.fromLocalFile(str(self.paths.exports / "transcricao.txt")).toString()
        return QUrl.fromLocalFile(str(self.paths.exports / f"{Path(job['audio_name']).stem}.txt")).toString()

    @Property(str, constant=True)
    def recommendedProfile(self) -> str:
        return self.hardware.recommended_profile

    @Property(str, constant=True)
    def hardwareSummary(self) -> str:
        device = self.hardware.gpu_name or f"CPU com {self.hardware.logical_cpus} processadores lógicos"
        return f"{device}\n{self.hardware.ram_gb:.1f} GB de RAM"

    @Property(str, constant=True)
    def hardwareRecommendation(self) -> str:
        device = self.hardware.gpu_name or f"CPU com {self.hardware.logical_cpus} processadores lógicos"
        return (
            f"Configuração recomendada: {self.hardware.recommended_profile}. "
            f"{device} • {self.hardware.ram_gb:.1f} GB de RAM."
        )

    @Property(str, constant=True)
    def processor(self) -> str:
        return self.hardware.cpu

    @Property(str, constant=True)
    def logicalProcessors(self) -> str:
        return str(self.hardware.logical_cpus)

    @Property(str, constant=True)
    def memory(self) -> str:
        return f"{self.hardware.ram_gb:.1f} GB"

    @Property(str, constant=True)
    def acceleration(self) -> str:
        return self.hardware.gpu_name or "Processamento por CPU"

    @Slot(int)
    def navigate(self, page: int) -> None:
        if page == 1:
            self.refresh_jobs()
        elif page == 2:
            self.refresh_models()
        self._page = page
        self.pageChanged.emit()

    @Slot("QVariantList")
    def add_files(self, values: list[Any]) -> None:
        errors: list[str] = []
        known = {item.path.resolve() for item in self._files}
        for value in values:
            url = QUrl(str(value))
            path = Path(url.toLocalFile() if url.isLocalFile() else str(value))
            try:
                info = inspect_audio(path)
                if info.path.resolve() not in known:
                    self._files.append(info)
                    known.add(info.path.resolve())
            except AudioValidationError as exc:
                errors.append(f"{path.name}: {exc}")
        self.filesChanged.emit()
        if errors:
            self.noticeRequested.emit("warning", "Alguns arquivos não foram adicionados", "\n\n".join(errors))

    @Slot(int)
    def remove_file(self, index: int) -> None:
        if 0 <= index < len(self._files):
            self._files.pop(index)
            self.filesChanged.emit()

    @Slot(str, str, str)
    def start_queue(self, language: str, profile: str, glossary: str) -> None:
        if not self._files or profile not in MODEL_PROFILES:
            return
        language_value = None if language == "auto" else language
        glossary_value = ", ".join(line.strip() for line in glossary.splitlines() if line.strip())
        model = MODEL_PROFILES[profile]
        self._queue = [
            (
                self.database.create_job(info, language_value, profile, model, glossary_value),
                info,
                profile,
            )
            for info in self._files
        ]
        self._files.clear()
        self.filesChanged.emit()
        self._queue_position = 0
        self._start_next()

    def _start_next(self) -> None:
        if self._queue_position >= len(self._queue):
            self.noticeRequested.emit(
                "success", "Transcrição concluída", "Todos os arquivos da fila foram processados."
            )
            self.navigate(1)
            return
        job_id, info, profile = self._queue[self._queue_position]
        self._progress_value = 0.0
        self._progress_title = info.path.name
        self._progress_detail = f"Arquivo {self._queue_position + 1} de {len(self._queue)} • {profile}"
        self._progress_latest = "Preparando o modelo e o áudio..."
        self.progressChanged.emit()
        self.navigate(5)
        self._controller = TranscriptionController()
        self._worker_outcome = None
        self._worker_thread = QThread(self)
        self._worker = TranscriptionWorker(self.database, job_id, self.paths.models, self._controller)
        self._worker.moveToThread(self._worker_thread)
        self._worker_thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._update_progress)
        self._worker.completed.connect(self._current_completed)
        self._worker.cancelled.connect(self._current_cancelled)
        self._worker.failed.connect(self._current_failed)
        self._worker.completed.connect(self._worker_thread.quit)
        self._worker.cancelled.connect(self._worker_thread.quit)
        self._worker.failed.connect(self._worker_thread.quit)
        self._worker_thread.finished.connect(self._worker.deleteLater)
        self._worker_thread.finished.connect(self._worker_thread.deleteLater)
        self._worker_thread.finished.connect(self._worker_finished)
        self._worker_thread.start()
        self.transcriptionActiveChanged.emit()

    @Slot(float, str)
    def _update_progress(self, value: float, text: str) -> None:
        self._progress_value = value
        self._progress_latest = text or "Processando..."
        self.progressChanged.emit()

    @Slot()
    def _current_completed(self) -> None:
        self._worker_outcome = JobStatus.COMPLETED
        self._queue_position += 1

    @Slot()
    def _current_cancelled(self) -> None:
        self._worker_outcome = JobStatus.CANCELLED

    @Slot(str)
    def _current_failed(self, error: str) -> None:
        self._worker_outcome = JobStatus.FAILED
        self.noticeRequested.emit(
            "error",
            "A transcrição foi interrompida",
            f"O progresso concluído foi preservado.\n\nDetalhe: {error}\n\nTente novamente por Transcrições.",
        )
        self.navigate(1)

    @Slot()
    def _worker_finished(self) -> None:
        self.transcriptionActiveChanged.emit()
        close_after_worker = self._pending_confirmation is not None and self._pending_confirmation[0] == "close"
        if self._worker_outcome == JobStatus.COMPLETED:
            self._start_next()
        elif self._worker_outcome == JobStatus.CANCELLED:
            if not close_after_worker:
                self.noticeRequested.emit(
                    "info",
                    "Transcrição interrompida",
                    "Os trechos concluídos foram preservados. Você pode continuar por Transcrições.",
                )
            self.navigate(1)
        if close_after_worker:
            self.closeRequested.emit()

    @Slot()
    def toggle_pause(self) -> None:
        if self._controller is None:
            return
        if self._controller.pause_event.is_set():
            self._controller.resume()
            self._progress_latest = "Transcrição retomada. O progresso continua sendo salvo."
        else:
            self._controller.pause()
            self._progress_latest = "Pausando com segurança após o trecho atual..."
        self.progressChanged.emit()

    @Slot()
    def request_cancel_current(self) -> None:
        if self._controller is None:
            return
        self._pending_confirmation = ("cancel", None)
        self.confirmationRequested.emit(
            "cancel",
            "Cancelar esta transcrição?",
            "Os trechos concluídos serão preservados e o áudio original não será alterado.",
        )

    @Slot(str)
    def search_jobs(self, query: str) -> None:
        self.refresh_jobs(query)

    def refresh_jobs(self, query: str = "") -> None:
        self._jobs = []
        for row in self.database.list_jobs(query):
            status = JobStatus(row["status"])
            self._jobs.append(
                {
                    "id": int(row["id"]),
                    "name": str(row["audio_name"]),
                    "duration": format_duration(float(row["duration"])),
                    "status": STATUS_LABELS[status],
                    "statusKey": status.value,
                    "progress": float(row["progress"]),
                    "canContinue": status in {JobStatus.READY, JobStatus.PAUSED, JobStatus.CANCELLED, JobStatus.FAILED},
                }
            )
        self.jobsChanged.emit()

    @Slot(int)
    def open_job(self, job_id: int) -> None:
        job = self.database.get_job(job_id)
        if job is None:
            return
        self._current_review_job = job_id
        self._review_title = str(job["audio_name"])
        self._review_audio_url = QUrl.fromLocalFile(str(job["audio_path"])).toString()
        self._review_segments = [
            {
                "id": int(row["id"]),
                "time": f"{format_duration(float(row['start']))} – {format_duration(float(row['end']))}",
                "text": str(row["revised_text"] or row["original_text"]),
                "attention": bool(row["review_required"]),
                "reviewed": bool(row["reviewed"]),
            }
            for row in self.database.get_segments(job_id)
        ]
        self.reviewChanged.emit()
        self.navigate(6)

    @Slot(int, str)
    def revise_segment(self, segment_id: int, text: str) -> None:
        self.database.revise_segment(segment_id, text)

    @Slot(int)
    def resume_job(self, job_id: int) -> None:
        if self.transcriptionActive:
            self.noticeRequested.emit("info", "Transcrição em andamento", "Aguarde ou cancele o trabalho atual.")
            return
        job = self.database.get_job(job_id)
        if job is None:
            return
        path = Path(job["audio_path"])
        if not path.is_file():
            self.noticeRequested.emit(
                "warning",
                "Arquivo original não encontrado",
                "O áudio pode ter sido movido. O progresso existente foi preservado.",
            )
            return
        info = AudioInfo(path, float(job["duration"]), str(job["format_name"]), int(job["size"]))
        self._queue = [(job_id, info, str(job["profile"]))]
        self._queue_position = 0
        self._start_next()

    @Slot(int, str, str)
    def export_job(self, job_id: int, destination_url: str, selected: str) -> None:
        if self.exportActive:
            self.noticeRequested.emit("info", "Exportação em andamento", "Aguarde a exportação atual terminar.")
            return
        if not destination_url:
            return
        destination = Path(QUrl(destination_url).toLocalFile() or destination_url)
        kind = {
            "Texto (*.txt)": "txt",
            "Legendas SRT (*.srt)": "srt",
            "Legendas WebVTT (*.vtt)": "vtt",
            "Dados JSON (*.json)": "json",
        }.get(selected, destination.suffix[1:].lower())
        self._export_thread = QThread(self)
        self._export_worker = ExportWorker(self.database, job_id, destination, kind)
        self._export_worker.moveToThread(self._export_thread)
        self._export_thread.started.connect(self._export_worker.run)
        self._export_worker.completed.connect(self._export_completed)
        self._export_worker.failed.connect(self._export_failed)
        self._export_worker.completed.connect(self._export_thread.quit)
        self._export_worker.failed.connect(self._export_thread.quit)
        self._export_thread.finished.connect(self._export_worker.deleteLater)
        self._export_thread.finished.connect(self._export_thread.deleteLater)
        self._export_thread.finished.connect(self.exportActiveChanged)
        self._export_thread.start()
        self.exportActiveChanged.emit()

    @Slot(str)
    def _export_completed(self, path: str) -> None:
        self.noticeRequested.emit("success", "Exportação concluída", f"Arquivo salvo em:\n{path}")

    @Slot(str)
    def _export_failed(self, error: str) -> None:
        self.noticeRequested.emit("error", "Não foi possível exportar", f"Nenhum dado foi apagado.\n\n{error}")

    @Slot(int)
    def request_delete_job(self, job_id: int) -> None:
        if self.database.is_job_active(job_id):
            self.noticeRequested.emit("warning", "Transcrição em andamento", "Pause ou cancele antes de excluir.")
            return
        self._pending_confirmation = ("delete", job_id)
        self.confirmationRequested.emit(
            "delete",
            "Excluir transcrição?",
            "A transcrição será excluída. O arquivo de áudio original não será apagado.",
        )

    def refresh_models(self) -> None:
        self._models = [
            {
                "label": state.label,
                "name": state.model_name,
                "installed": state.installed,
                "status": "Instalado" if state.installed else "Não instalado",
                "size": f"{state.size_bytes / 1024**3:.2f} GB" if state.size_bytes else "",
            }
            for state in self.model_manager.states()
        ]
        self.modelsChanged.emit()

    @Slot(str, bool)
    def request_model_action(self, model_name: str, installed: bool) -> None:
        if installed:
            self._pending_confirmation = ("remove_model", model_name)
            self.confirmationRequested.emit(
                "remove_model", "Remover modelo?", "O modelo poderá ser baixado novamente quando necessário."
            )
            return
        self._download_model(model_name)

    def _download_model(self, model_name: str) -> None:
        if self.modelDownloadActive:
            self.noticeRequested.emit("info", "Download em andamento", "Aguarde o download atual terminar.")
            return
        self._model_thread = QThread(self)
        self._model_worker = ModelDownloadWorker(self.model_manager, model_name)
        self._model_worker.moveToThread(self._model_thread)
        self._model_thread.started.connect(self._model_worker.run)
        self._model_worker.completed.connect(self._model_downloaded)
        self._model_worker.failed.connect(self._model_failed)
        self._model_worker.completed.connect(self._model_thread.quit)
        self._model_worker.failed.connect(self._model_thread.quit)
        self._model_thread.finished.connect(self._model_worker.deleteLater)
        self._model_thread.finished.connect(self._model_thread.deleteLater)
        self._model_thread.finished.connect(self.modelDownloadActiveChanged)
        self._model_thread.start()
        self.modelDownloadActiveChanged.emit()

    @Slot(str)
    def _model_downloaded(self, _model_name: str) -> None:
        self.refresh_models()
        self.noticeRequested.emit("success", "Modelo pronto", "O modelo foi baixado e verificado.")

    @Slot(str)
    def _model_failed(self, error: str) -> None:
        self.refresh_models()
        self.noticeRequested.emit(
            "error",
            "Não foi possível baixar o modelo",
            f"Arquivos incompletos não serão usados. Tente novamente.\n\n{error}",
        )

    @Slot()
    def request_close(self) -> None:
        if self.modelDownloadActive:
            self.noticeRequested.emit("info", "Download em andamento", "Aguarde o download terminar antes de fechar.")
            return
        if self.transcriptionActive:
            self._pending_confirmation = ("close", None)
            self.confirmationRequested.emit(
                "close",
                "Encerrar com segurança?",
                "O progresso concluído será preservado. Deseja cancelar o trabalho e fechar quando possível?",
            )
            return
        self.closeRequested.emit()

    @Slot(str)
    def confirm(self, action: str) -> None:
        if self._pending_confirmation is None or self._pending_confirmation[0] != action:
            return
        _, value = self._pending_confirmation
        self._pending_confirmation = None
        if action == "cancel" and self._controller is not None:
            self._controller.cancel()
            self._progress_latest = "Cancelando com segurança após o trecho atual..."
            self.progressChanged.emit()
        elif action == "close" and self._controller is not None:
            self._pending_confirmation = ("close", None)
            self._controller.cancel()
            self._progress_latest = "Cancelando com segurança antes de fechar..."
            self.progressChanged.emit()
        elif action == "delete" and isinstance(value, int):
            self.database.delete_job(value)
            self.refresh_jobs()
        elif action == "remove_model" and isinstance(value, str):
            self.model_manager.remove(value)
            self.refresh_models()

    @Slot()
    def reject_confirmation(self) -> None:
        self._pending_confirmation = None
