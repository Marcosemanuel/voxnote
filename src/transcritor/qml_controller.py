from __future__ import annotations

import json
import logging
import queue
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from PySide6.QtCore import Property, QObject, QThread, QTimer, QUrl, Signal, Slot

from transcritor.audio import AudioValidationError, inspect_audio
from transcritor.database import Database
from transcritor.domain import MODEL_PROFILES, STATUS_LABELS, AudioInfo, HardwareProfile, JobStatus, format_duration
from transcritor.engine import TranscriptionController
from transcritor.hardware import detect_hardware
from transcritor.meeting import AudioDevice, CaptureError, MeetingCaptureService, list_capture_devices, measure_signal
from transcritor.models import ModelManager
from transcritor.paths import AppPaths
from transcritor.resources import bundled_path
from transcritor.updates import UpdateCheckWorker
from transcritor.workers import (
    ExportWorker,
    MeetingExportWorker,
    MeetingTranscriptionWorker,
    ModelDownloadWorker,
    TranscriptionWorker,
)

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
    meetingChanged = Signal()
    meetingReviewChanged = Signal()
    meetingStopFinished = Signal(bool, str)
    meetingSignalFinished = Signal(float, float, str)
    noticeRequested = Signal(str, str, str)
    confirmationRequested = Signal(str, str, str)
    updateChanged = Signal()

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
        self._export_worker: ExportWorker | MeetingExportWorker | None = None
        self._pending_confirmation: tuple[str, int | str | None] | None = None
        self._update_thread: QThread | None = None
        self._update_worker: UpdateCheckWorker | None = None
        self._update_available = False
        self._update_version = ""
        self._update_url = ""
        self._meeting_system_devices: list[AudioDevice] = []
        self._meeting_microphone_devices: list[AudioDevice] = []
        self._meeting_service: MeetingCaptureService | None = None
        self._meeting_session_id = 0
        self._meeting_track_ids: dict[str, int] = {}
        self._meeting_state = "idle"
        self._meeting_duration_ms = 0
        self._meeting_last_saved_ms = 0
        self._meeting_system_level = 0.0
        self._meeting_microphone_level = 0.0
        self._meeting_progress = 0.0
        self._meeting_message = "Selecione os dispositivos e teste o sinal antes de iniciar."
        self._meeting_tested = False
        self._meeting_test_message = ""
        self._meeting_timer = QTimer(self)
        self._meeting_timer.setInterval(200)
        self._meeting_timer.timeout.connect(self._poll_meeting_events)
        self._meeting_thread: QThread | None = None
        self._meeting_worker: MeetingTranscriptionWorker | None = None
        self._meeting_controller: TranscriptionController | None = None
        self._meeting_review_session = 0
        self._meeting_review_run = 0
        self._meeting_review_title = "Revisão da reunião"
        self._meeting_review_segments: list[dict[str, Any]] = []
        self._meeting_sessions: list[dict[str, Any]] = []
        self.meetingStopFinished.connect(self._finish_meeting_stop)
        self.meetingSignalFinished.connect(self._finish_meeting_signal_test)
        self._recover_meeting_sessions()
        self.refresh_jobs()
        self.refresh_models()
        self.refresh_meeting_sessions()

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
        return (self._worker_thread is not None and self._worker_thread.isRunning()) or (
            self._meeting_thread is not None and self._meeting_thread.isRunning()
        )

    @Property(bool, notify=modelDownloadActiveChanged)
    def modelDownloadActive(self) -> bool:
        return self._model_thread is not None and self._model_thread.isRunning()

    @Property(bool, notify=exportActiveChanged)
    def exportActive(self) -> bool:
        return self._export_thread is not None and self._export_thread.isRunning()

    @Property(bool, notify=updateChanged)
    def updateAvailable(self) -> bool:
        return self._update_available

    @Property(str, notify=updateChanged)
    def updateVersion(self) -> str:
        return self._update_version

    @Property(str, notify=updateChanged)
    def updateUrl(self) -> str:
        return self._update_url

    @Property(str, constant=True)
    def assetRoot(self) -> str:
        return QUrl.fromLocalFile(str(bundled_path("assets"))).toString()

    @Slot(int, result=str)
    def default_export_path(self, job_id: int) -> str:
        job = self.database.get_job(job_id)
        if job is None:
            return QUrl.fromLocalFile(str(self.paths.exports / "transcricao.txt")).toString()
        return QUrl.fromLocalFile(str(self.paths.exports / f"{Path(job['audio_name']).stem}.txt")).toString()

    @Slot(int, result=str)
    def default_meeting_export_path(self, session_id: int) -> str:
        session = self.database.get_meeting_session(session_id)
        title = str(session["title"]) if session is not None else "reuniao"
        safe_name = "".join(
            character if character.isalnum() or character in "-_ " else "" for character in title
        ).strip()
        return QUrl.fromLocalFile(str(self.paths.exports / f"{safe_name or 'reuniao'}.txt")).toString()

    @Property(list, notify=meetingChanged)
    def meetingSystemDevices(self) -> list[dict[str, Any]]:
        return [self._device_payload(device) for device in self._meeting_system_devices]

    @Property(list, notify=meetingChanged)
    def meetingMicrophoneDevices(self) -> list[dict[str, Any]]:
        return [self._device_payload(device) for device in self._meeting_microphone_devices]

    @Property(str, notify=meetingChanged)
    def meetingState(self) -> str:
        return self._meeting_state

    @Property(str, notify=meetingChanged)
    def meetingMessage(self) -> str:
        return self._meeting_message

    @Property(float, notify=meetingChanged)
    def meetingProgress(self) -> float:
        return self._meeting_progress

    @Property(str, notify=meetingChanged)
    def meetingDuration(self) -> str:
        return format_duration(self._meeting_duration_ms / 1000)

    @Property(str, notify=meetingChanged)
    def meetingLastSaved(self) -> str:
        return format_duration(self._meeting_last_saved_ms / 1000)

    @Property(float, notify=meetingChanged)
    def meetingSystemLevel(self) -> float:
        return min(1.0, self._meeting_system_level * 4)

    @Property(float, notify=meetingChanged)
    def meetingMicrophoneLevel(self) -> float:
        return min(1.0, self._meeting_microphone_level * 4)

    @Property(bool, notify=meetingChanged)
    def meetingTested(self) -> bool:
        return self._meeting_tested

    @Property(str, notify=meetingChanged)
    def meetingTestMessage(self) -> str:
        return self._meeting_test_message

    @Property(int, notify=meetingChanged)
    def meetingSessionId(self) -> int:
        return self._meeting_session_id

    @Property(str, notify=meetingReviewChanged)
    def meetingReviewTitle(self) -> str:
        return self._meeting_review_title

    @Property(list, notify=meetingReviewChanged)
    def meetingReviewSegments(self) -> list[dict[str, Any]]:
        return self._meeting_review_segments

    @Property(int, notify=meetingReviewChanged)
    def meetingReviewSessionId(self) -> int:
        return self._meeting_review_session

    @Property(int, notify=meetingReviewChanged)
    def meetingReviewRunId(self) -> int:
        return self._meeting_review_run

    @Property(list, notify=meetingChanged)
    def meetingSessions(self) -> list[dict[str, Any]]:
        return self._meeting_sessions

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

    @staticmethod
    def _device_payload(device: AudioDevice) -> dict[str, Any]:
        return {
            "index": device.index,
            "name": device.name,
            "channels": device.channels,
            "sampleRate": device.sample_rate,
            "default": device.is_default,
        }

    @Slot()
    def refresh_meeting_devices(self) -> None:
        if self._meeting_state in {"capturing", "stopping", "transcribing"}:
            return
        try:
            self._meeting_system_devices, self._meeting_microphone_devices = list_capture_devices()
            self._meeting_message = "Dispositivos atualizados. Execute o teste de sinal antes de iniciar."
        except CaptureError as exc:
            self._meeting_system_devices = []
            self._meeting_microphone_devices = []
            self._meeting_message = str(exc)
        self._meeting_tested = False
        self._meeting_test_message = ""
        self.meetingChanged.emit()

    def _recover_meeting_sessions(self) -> None:
        """Import finalized journal blocks left by an interrupted capture before exposing sessions."""
        # A failed capture/transcription may still have fsync-confirmed journal blocks.
        # Importing them makes the preserved audio available for a safe retry.
        recoverable = {"preparing", "capturing", "stopping", "failed"}
        for session in self.database.list_meeting_sessions():
            if str(session["status"]) not in recoverable:
                continue
            capture_root = Path(str(session["capture_path"]))
            capture_tracks = self.database.list_capture_tracks(int(session["id"]))
            tracks = {str(track["kind"]): int(track["id"]) for track in capture_tracks}
            journal = capture_root / "capture.journal.ndjson"
            maximum_end = 0
            if journal.is_file():
                for raw_event in journal.read_text(encoding="utf-8").splitlines():
                    try:
                        event = json.loads(raw_event)
                    except json.JSONDecodeError:
                        continue
                    if event.get("event") != "block_committed":
                        continue
                    kind = str(event.get("kind", ""))
                    block_path = Path(str(event.get("path", "")))
                    if kind not in tracks or not block_path.is_file():
                        continue
                    self.database.save_capture_block(
                        tracks[kind],
                        int(event["sequence"]),
                        block_path,
                        int(event["started_ms"]),
                        int(event["duration_ms"]),
                        int(event["bytes"]),
                        str(event["sha256"]),
                    )
                    maximum_end = max(maximum_end, int(event["started_ms"]) + int(event["duration_ms"]))
            if maximum_end:
                self.database.update_meeting_session(int(session["id"]), "captured", duration_ms=maximum_end)
            else:
                self.database.update_meeting_session(
                    int(session["id"]),
                    "failed",
                    error="A captura foi interrompida antes de concluir um bloco recuperável.",
                )

    def refresh_meeting_sessions(self) -> None:
        labels = {
            "preparing": "Preparando",
            "capturing": "Captura interrompida",
            "captured": "Pronta para transcrever",
            "transcribing": "Transcrevendo",
            "completed": "Concluída",
            "failed": "Requer atenção",
        }
        self._meeting_sessions = [
            {
                "id": int(row["id"]),
                "title": str(row["title"]),
                "duration": format_duration(int(row["duration_ms"]) / 1000),
                "status": labels.get(str(row["status"]), str(row["status"])),
                "canReview": self.database.get_latest_transcription_run(int(row["id"])) is not None,
                "canTranscribe": self.database.capture_block_count(int(row["id"])) > 0
                and str(row["status"]) not in {"capturing", "stopping", "transcribing"},
            }
            for row in self.database.list_meeting_sessions()
        ]
        self.meetingChanged.emit()

    @Slot(int, bool, int)
    def test_meeting_signal(self, system_row: int, include_microphone: bool, microphone_row: int) -> None:
        try:
            system = self._meeting_system_devices[system_row]
            microphone = self._meeting_microphone_devices[microphone_row] if include_microphone else None
        except IndexError:
            self.noticeRequested.emit(
                "warning", "Selecione os dispositivos", "Escolha uma saída de áudio válida antes do teste."
            )
            return
        self._meeting_tested = False
        self._meeting_test_message = "Testando áudio. Fale e deixe o som da reunião tocar..."
        self.meetingChanged.emit()

        def measure() -> None:
            try:
                output = measure_signal(system)
                voice = measure_signal(microphone) if microphone is not None else 0.0
                self.meetingSignalFinished.emit(output, voice, "")
            except CaptureError as exc:
                self.meetingSignalFinished.emit(0.0, 0.0, str(exc))

        threading.Thread(target=measure, name="voxnote-signal-test", daemon=True).start()

    @Slot(float, float, str)
    def _finish_meeting_signal_test(self, output: float, voice: float, error: str) -> None:
        if error:
            self._meeting_tested = False
            self._meeting_test_message = error
        else:
            self._meeting_system_level = output
            self._meeting_microphone_level = voice
            self._meeting_tested = output > 0.002
            if self._meeting_tested:
                self._meeting_test_message = "Sinal da saída confirmado. Você pode iniciar a captura."
            else:
                self._meeting_test_message = (
                    "Nenhum áudio foi detectado. Confirme a saída do Windows e execute o teste novamente."
                )
        self.meetingChanged.emit()

    @Slot(bool, int, bool, int, str, str, str)
    def start_meeting_capture(
        self,
        consent: bool,
        system_row: int,
        include_microphone: bool,
        microphone_row: int,
        language: str,
        profile: str,
        glossary: str,
    ) -> None:
        if self._meeting_state not in {"idle", "completed", "failed"}:
            return
        if not consent:
            self.noticeRequested.emit(
                "warning", "Confirmação necessária", "Confirme que você está autorizado a gravar a reunião."
            )
            return
        if not self._meeting_tested:
            self.noticeRequested.emit(
                "warning", "Teste de sinal pendente", "Teste a saída de áudio antes de iniciar a captura."
            )
            return
        try:
            system = self._meeting_system_devices[system_row]
            microphone = self._meeting_microphone_devices[microphone_row] if include_microphone else None
        except IndexError:
            self.noticeRequested.emit(
                "warning", "Dispositivo indisponível", "Atualize a lista de dispositivos e tente novamente."
            )
            return
        if profile not in MODEL_PROFILES:
            self.noticeRequested.emit("warning", "Qualidade inválida", "Selecione um perfil de transcrição disponível.")
            return
        capture_root = self.paths.captures / datetime.now().strftime("%Y%m%d-%H%M%S")
        language_value = None if language == "auto" else language
        glossary_value = ", ".join(line.strip() for line in glossary.splitlines() if line.strip())
        session_id = self.database.create_meeting_session(
            f"Reunião {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            language_value,
            profile,
            MODEL_PROFILES[profile],
            glossary_value,
            "final-first",
            capture_root,
        )
        self._meeting_track_ids = {
            "system": self.database.create_capture_track(
                session_id, "system", system.index, system.name, system.sample_rate, system.channels
            )
        }
        if microphone is not None:
            self._meeting_track_ids["microphone"] = self.database.create_capture_track(
                session_id, "microphone", microphone.index, microphone.name, microphone.sample_rate, microphone.channels
            )
        try:
            service = MeetingCaptureService(capture_root, system, microphone)
            service.start()
        except CaptureError as exc:
            self.database.update_meeting_session(session_id, "failed", error=str(exc))
            self.noticeRequested.emit("error", "Não foi possível iniciar a captura", str(exc))
            return
        self._meeting_service = service
        self._meeting_session_id = session_id
        self._meeting_state = "capturing"
        self._meeting_duration_ms = 0
        self._meeting_last_saved_ms = 0
        self._meeting_progress = 0
        self._meeting_message = "Capturando localmente. O áudio permanece nesta máquina."
        self.database.update_meeting_session(session_id, "capturing")
        self._meeting_timer.start()
        self.meetingChanged.emit()

    @Slot()
    def stop_meeting_capture(self) -> None:
        if self._meeting_service is None or self._meeting_state != "capturing":
            return
        self._meeting_state = "stopping"
        self._meeting_message = "Finalizando os blocos em disco com segurança..."
        self.meetingChanged.emit()
        service = self._meeting_service

        def stop() -> None:
            try:
                service.stop()
                self.meetingStopFinished.emit(True, "")
            except CaptureError as exc:
                self.meetingStopFinished.emit(False, str(exc))

        threading.Thread(target=stop, name="voxnote-stop-capture", daemon=True).start()

    @Slot(bool, str)
    def _finish_meeting_stop(self, stopped: bool, error: str) -> None:
        self._meeting_timer.stop()
        service = self._meeting_service
        if not stopped or service is None:
            self._meeting_state = "failed"
            self._meeting_message = error or "A captura não pôde ser finalizada com segurança."
            if self._meeting_session_id:
                self.database.update_meeting_session(self._meeting_session_id, "failed", error=self._meeting_message)
            self.meetingChanged.emit()
            return
        self._poll_meeting_events()
        self._meeting_duration_ms = service.duration_ms
        self.database.update_meeting_session(
            self._meeting_session_id, "captured", duration_ms=self._meeting_duration_ms
        )
        self._meeting_state = "transcribing"
        self._meeting_message = "Preparando a transcrição final em blocos. A interface continua disponível."
        self.meetingChanged.emit()
        self._start_meeting_transcription(self._meeting_session_id)

    @Slot()
    def _poll_meeting_events(self) -> None:
        service = self._meeting_service
        if service is None:
            return
        self._meeting_duration_ms = service.duration_ms
        while True:
            try:
                event = service.events.get_nowait()
            except queue.Empty:
                break
            event_name = str(event["event"])
            if event_name == "block_committed":
                track_id = self._meeting_track_ids.get(str(event["kind"]))
                if track_id is not None:
                    self.database.save_capture_block(
                        track_id,
                        int(event["sequence"]),
                        Path(str(event["path"])),
                        int(event["started_ms"]),
                        int(event["duration_ms"]),
                        int(event["bytes"]),
                        str(event["sha256"]),
                    )
                    self._meeting_last_saved_ms = max(
                        self._meeting_last_saved_ms, int(event["started_ms"]) + int(event["duration_ms"])
                    )
                if event["kind"] == "system":
                    self._meeting_system_level = float(event["level"])
                else:
                    self._meeting_microphone_level = float(event["level"])
            elif event_name == "capture_degraded":
                self._meeting_message = str(event["message"])
            elif event_name == "track_synchronization":
                # Block timestamps already use the same QPC origin. This records measured drift
                # without combining or changing either source track.
                if abs(int(event["drift_ms"])) > 250:
                    self._meeting_message = (
                        f"Sincronização das trilhas variou {abs(int(event['drift_ms']))} ms. "
                        "Revise os trechos antes de exportar."
                    )
            elif event_name == "fatal_error":
                self._meeting_state = "failed"
                self._meeting_message = str(event["message"])
                self.database.update_meeting_session(self._meeting_session_id, "failed", error=self._meeting_message)
                self._meeting_timer.stop()
                self.noticeRequested.emit("error", "Captura interrompida", self._meeting_message)
        self.meetingChanged.emit()

    def _start_meeting_transcription(self, session_id: int) -> None:
        self._meeting_controller = TranscriptionController()
        self._meeting_thread = QThread(self)
        self._meeting_worker = MeetingTranscriptionWorker(
            self.database, session_id, self.paths.models, self.paths.cache / "meeting-windows", self._meeting_controller
        )
        self._meeting_worker.moveToThread(self._meeting_thread)
        self._meeting_thread.started.connect(self._meeting_worker.run)
        self._meeting_worker.progress.connect(self._update_meeting_progress)
        self._meeting_worker.completed.connect(self._meeting_completed)
        self._meeting_worker.cancelled.connect(self._meeting_cancelled)
        self._meeting_worker.failed.connect(self._meeting_failed)
        self._meeting_worker.completed.connect(self._meeting_thread.quit)
        self._meeting_worker.cancelled.connect(self._meeting_thread.quit)
        self._meeting_worker.failed.connect(self._meeting_thread.quit)
        self._meeting_thread.finished.connect(self._meeting_worker.deleteLater)
        self._meeting_thread.finished.connect(self._meeting_thread.deleteLater)
        self._meeting_thread.finished.connect(self.transcriptionActiveChanged)
        self._meeting_thread.finished.connect(self._meeting_worker_finished)
        self._meeting_thread.start()
        self.transcriptionActiveChanged.emit()

    @Slot(int)
    def resume_meeting_transcription(self, session_id: int) -> None:
        """Start a new immutable final run from persisted capture blocks."""
        if self.transcriptionActive or self._meeting_state in {"capturing", "stopping", "transcribing"}:
            return
        session = self.database.get_meeting_session(session_id)
        if session is None or self.database.capture_block_count(session_id) == 0:
            self.noticeRequested.emit(
                "warning",
                "Blocos indisponíveis",
                "Não há blocos de áudio confirmados para transcrever. O trabalho existente foi preservado.",
            )
            return
        self._meeting_service = None
        self._meeting_session_id = session_id
        self._meeting_track_ids = {}
        self._meeting_state = "transcribing"
        self._meeting_progress = 0
        self._meeting_duration_ms = int(session["duration_ms"])
        self._meeting_last_saved_ms = int(session["duration_ms"])
        self._meeting_message = "Retomando a transcrição final dos blocos preservados."
        self.database.update_meeting_session(session_id, "transcribing")
        self.meetingChanged.emit()
        self._start_meeting_transcription(session_id)

    @Slot(float, str)
    def _update_meeting_progress(self, value: float, message: str) -> None:
        self._meeting_progress = value
        self._meeting_message = message
        self.meetingChanged.emit()

    @Slot(int)
    def _meeting_completed(self, run_id: int) -> None:
        self._meeting_state = "completed"
        self._meeting_progress = 100
        self._meeting_message = "Transcrição final concluída. Revise e exporte quando estiver pronto."
        self._meeting_review_run = run_id
        self.refresh_meeting_sessions()
        self.meetingChanged.emit()
        self.noticeRequested.emit("success", "Reunião transcrita", "A transcrição final está pronta para revisão.")

    @Slot(int)
    def _meeting_cancelled(self, _run_id: int) -> None:
        self._meeting_state = "completed"
        self._meeting_message = "Processamento interrompido. Os blocos capturados foram preservados."
        self.refresh_meeting_sessions()
        self.meetingChanged.emit()

    @Slot(str)
    def _meeting_failed(self, error: str) -> None:
        self._meeting_state = "failed"
        self._meeting_message = f"Os blocos capturados foram preservados. {error}"
        self.refresh_meeting_sessions()
        self.meetingChanged.emit()
        self.noticeRequested.emit("error", "Transcrição da reunião interrompida", self._meeting_message)

    @Slot()
    def _meeting_worker_finished(self) -> None:
        if self._pending_confirmation is not None and self._pending_confirmation[0] == "close":
            self.closeRequested.emit()

    @Slot(int)
    def open_meeting_review(self, session_id: int) -> None:
        session = self.database.get_meeting_session(session_id)
        run = self.database.get_latest_transcription_run(session_id)
        if session is None or run is None:
            self.noticeRequested.emit(
                "info", "Ainda não há transcrição", "Finalize a captura e aguarde a transcrição final."
            )
            return
        self._meeting_review_session = session_id
        self._meeting_review_run = int(run["id"])
        self._meeting_review_title = str(session["title"])
        self._meeting_review_segments = [
            {
                "id": int(row["id"]),
                "time": (
                    f"{format_duration(int(row['start_ms']) / 1000)} – {format_duration(int(row['end_ms']) / 1000)}"
                ),
                "track": "Sistema" if row["track_kind"] == "system" else "Microfone",
                "text": str(row["revised_text"] or row["original_text"]),
                "attention": bool(row["review_required"]),
            }
            for row in self.database.list_run_segments(self._meeting_review_run)
        ]
        self.meetingReviewChanged.emit()
        self.navigate(8)

    @Slot(int, str)
    def revise_meeting_segment(self, segment_id: int, text: str) -> None:
        self.database.revise_run_segment(segment_id, text)

    @Slot(int, int, str, str)
    def export_meeting_run(self, session_id: int, run_id: int, destination_url: str, selected: str) -> None:
        if self.exportActive or not destination_url:
            return
        destination = Path(QUrl(destination_url).toLocalFile() or destination_url)
        kind = {
            "Texto (*.txt)": "txt",
            "Legendas SRT (*.srt)": "srt",
            "Legendas WebVTT (*.vtt)": "vtt",
            "Dados JSON (*.json)": "json",
        }.get(selected, destination.suffix[1:].lower())
        self._export_thread = QThread(self)
        self._export_worker = MeetingExportWorker(self.database, session_id, run_id, destination, kind)
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

    @Slot()
    def start_update_check(self) -> None:
        if self._update_thread is not None:
            return
        self._update_thread = QThread(self)
        self._update_worker = UpdateCheckWorker()
        self._update_worker.moveToThread(self._update_thread)
        self._update_thread.started.connect(self._update_worker.run)
        self._update_worker.update_available.connect(self._set_update_available)
        self._update_worker.finished.connect(self._update_thread.quit)
        self._update_thread.finished.connect(self._update_worker.deleteLater)
        self._update_thread.finished.connect(self._update_thread.deleteLater)
        self._update_thread.start()

    @Slot(str, str)
    def _set_update_available(self, version: str, url: str) -> None:
        self._update_available = True
        self._update_version = version
        self._update_url = url
        self.updateChanged.emit()

    @Slot(int)
    def navigate(self, page: int) -> None:
        if page == 1:
            self.refresh_jobs()
        elif page == 2:
            self.refresh_models()
        elif page == 7:
            self.refresh_meeting_devices()
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
        if self._meeting_state in {"capturing", "stopping"}:
            self.noticeRequested.emit(
                "info",
                "Captura em andamento",
                "Encerre a captura para confirmar os blocos antes de fechar o aplicativo.",
            )
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
        elif action == "close":
            self._pending_confirmation = ("close", None)
            if self._controller is not None:
                self._controller.cancel()
                self._progress_latest = "Cancelando com segurança antes de fechar..."
                self.progressChanged.emit()
            elif self._meeting_controller is not None:
                self._meeting_controller.cancel()
                self._meeting_message = "Cancelando a transcrição final com os blocos preservados antes de fechar..."
                self.meetingChanged.emit()
        elif action == "delete" and isinstance(value, int):
            self.database.delete_job(value)
            self.refresh_jobs()
        elif action == "remove_model" and isinstance(value, str):
            self.model_manager.remove(value)
            self.refresh_models()

    @Slot()
    def reject_confirmation(self) -> None:
        self._pending_confirmation = None
