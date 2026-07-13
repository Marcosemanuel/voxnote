from __future__ import annotations

import audioop
import hashlib
import json
import os
import queue
import threading
import time
import wave
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


class CaptureError(RuntimeError):
    """A capture failure that can be shown to the user without a traceback."""


@dataclass(frozen=True, slots=True)
class AudioDevice:
    index: int
    name: str
    channels: int
    sample_rate: int
    is_loopback: bool
    is_default: bool = False


@dataclass(frozen=True, slots=True)
class CaptureBlock:
    kind: str
    sequence: int
    path: Path
    started_ms: int
    duration_ms: int
    size_bytes: int
    sha256: str


def _pyaudio() -> Any:
    try:
        import pyaudiowpatch as pyaudio
    except ImportError as exc:  # pragma: no cover - guarded by package dependency.
        raise CaptureError("O componente de captura WASAPI não está disponível neste pacote.") from exc
    return pyaudio


def _wasapi_devices() -> tuple[list[AudioDevice], list[AudioDevice]]:
    pyaudio = _pyaudio()
    with pyaudio.PyAudio() as audio:
        default_loopback: int | None = None
        try:
            default_loopback = int(audio.get_default_wasapi_loopback()["index"])
        except (OSError, KeyError, TypeError, ValueError):
            default_loopback = None
        loopbacks = [
            AudioDevice(
                index=int(info["index"]),
                name=str(info["name"]),
                channels=max(1, int(info["maxInputChannels"])),
                sample_rate=max(8000, int(float(info["defaultSampleRate"]))),
                is_loopback=True,
                is_default=int(info["index"]) == default_loopback,
            )
            for info in audio.get_loopback_device_info_generator()
        ]
        microphones = [
            AudioDevice(
                index=int(info["index"]),
                name=str(info["name"]),
                channels=max(1, int(info["maxInputChannels"])),
                sample_rate=max(8000, int(float(info["defaultSampleRate"]))),
                is_loopback=False,
            )
            for info in audio.get_device_info_generator()
            if int(info.get("maxInputChannels", 0)) > 0
            and not bool(info.get("isLoopbackDevice", False))
            and str(info.get("name", "")) != "Mapeador de som da Microsoft - Input"
        ]
    return loopbacks, microphones


def list_capture_devices() -> tuple[list[AudioDevice], list[AudioDevice]]:
    """Return WASAPI output loopbacks and input microphones available now."""
    loopbacks, microphones = _wasapi_devices()
    if not loopbacks:
        raise CaptureError("Nenhuma saída de áudio WASAPI foi encontrada neste computador.")
    return loopbacks, microphones


def measure_signal(device: AudioDevice, seconds: float = 1.5) -> float:
    """Measure one device without writing a file. It is called from a worker thread."""
    pyaudio = _pyaudio()
    frames_per_buffer = 1024
    frame_count = max(frames_per_buffer, int(device.sample_rate * seconds))
    values: list[int] = []
    with pyaudio.PyAudio() as audio:
        try:
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=device.channels,
                rate=device.sample_rate,
                input=True,
                input_device_index=device.index,
                frames_per_buffer=frames_per_buffer,
            )
        except OSError as exc:
            raise CaptureError(f"Não foi possível abrir {device.name} para teste.") from exc
        try:
            remaining = frame_count
            while remaining > 0:
                frames = min(frames_per_buffer, remaining)
                data = stream.read(frames, exception_on_overflow=False)
                values.append(audioop.rms(data, 2))
                remaining -= frames
        except OSError as exc:
            raise CaptureError(f"O teste de sinal de {device.name} falhou.") from exc
        finally:
            stream.stop_stream()
            stream.close()
    return float(max(values, default=0)) / 32768.0


class _TrackRecorder(threading.Thread):
    def __init__(
        self,
        session: MeetingCaptureService,
        kind: str,
        device: AudioDevice,
        directory: Path,
        stop_event: threading.Event,
    ) -> None:
        super().__init__(name=f"voxnote-capture-{kind}", daemon=True)
        self.session = session
        self.kind = kind
        self.device = device
        self.directory = directory
        self.stop_event = stop_event
        self.sequence = 0
        self.last_level = 0.0

    def run(self) -> None:  # noqa: C901 - the resource lifetime must stay linear.
        pyaudio = _pyaudio()
        frames_per_buffer = 1024
        frames_per_block = self.device.sample_rate * self.session.block_seconds
        self.directory.mkdir(parents=True, exist_ok=True)
        try:
            with pyaudio.PyAudio() as audio:
                stream = audio.open(
                    format=pyaudio.paInt16,
                    channels=self.device.channels,
                    rate=self.device.sample_rate,
                    input=True,
                    input_device_index=self.device.index,
                    frames_per_buffer=frames_per_buffer,
                )
                try:
                    while not self.stop_event.is_set():
                        self._record_one_block(stream, frames_per_block, frames_per_buffer)
                finally:
                    stream.stop_stream()
                    stream.close()
        except Exception as exc:
            self.session.emit(
                "capture_degraded" if self.kind == "microphone" else "fatal_error",
                kind=self.kind,
                message=f"A captura de {self._label} foi interrompida: {exc}",
            )
            if self.kind == "system":
                self.stop_event.set()

    @property
    def _label(self) -> str:
        return "sua voz" if self.kind == "microphone" else "áudio da reunião"

    def _record_one_block(self, stream: Any, frames_per_block: int, frames_per_buffer: int) -> None:
        self.sequence += 1
        started_ms = int((time.perf_counter_ns() - self.session.started_qpc_ns) / 1_000_000)
        final_path = self.directory / f"{self.sequence:08d}.wav"
        temporary_path = final_path.with_suffix(".wav.partial")
        frames_written = 0
        rms_peak = 0
        with wave.open(str(temporary_path), "wb") as output:
            output.setnchannels(self.device.channels)
            output.setsampwidth(2)
            output.setframerate(self.device.sample_rate)
            while frames_written < frames_per_block and not self.stop_event.is_set():
                frames_to_read = min(frames_per_buffer, frames_per_block - frames_written)
                try:
                    data = stream.read(frames_to_read, exception_on_overflow=False)
                except OSError as exc:
                    raise CaptureError("O dispositivo de áudio foi removido ou deixou de responder.") from exc
                output.writeframesraw(data)
                frames_read = len(data) // (self.device.channels * 2)
                frames_written += frames_read
                rms_peak = max(rms_peak, audioop.rms(data, 2))
        if frames_written == 0:
            temporary_path.unlink(missing_ok=True)
            return
        self._flush_file(temporary_path)
        os.replace(temporary_path, final_path)
        duration_ms = round(frames_written / self.device.sample_rate * 1000)
        block = CaptureBlock(
            kind=self.kind,
            sequence=self.sequence,
            path=final_path,
            started_ms=started_ms,
            duration_ms=duration_ms,
            size_bytes=final_path.stat().st_size,
            sha256=self._sha256(final_path),
        )
        self.last_level = rms_peak / 32768.0
        self.session.commit(block, self.device, self.last_level)

    @staticmethod
    def _flush_file(path: Path) -> None:
        # Windows rejects fsync on a read-only descriptor (WinError/EBADF).
        descriptor = os.open(path, os.O_RDWR)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()


class MeetingCaptureService:
    """Capture separate WASAPI tracks as independently recoverable WAV blocks."""

    def __init__(
        self,
        root: Path,
        system_device: AudioDevice,
        microphone_device: AudioDevice | None = None,
        block_seconds: int = 5,
    ) -> None:
        self.root = root
        self.system_device = system_device
        self.microphone_device = microphone_device
        self.block_seconds = block_seconds
        self.events: queue.Queue[dict[str, Any]] = queue.Queue()
        self.stop_event = threading.Event()
        self.started_qpc_ns = 0
        self._journal_lock = threading.Lock()
        self._recorders: list[_TrackRecorder] = []
        self._track_starts: dict[str, dict[int, int]] = {"system": {}, "microphone": {}}
        self._sync_baseline_ms: int | None = None
        self._sync_warning_emitted = False

    def start(self) -> None:
        if self._recorders:
            raise CaptureError("A captura já está em andamento.")
        self.root.mkdir(parents=True, exist_ok=True)
        self.started_qpc_ns = time.perf_counter_ns()
        self._write_session_file("capturing")
        self._recorders = [
            _TrackRecorder(self, "system", self.system_device, self.root / "system", self.stop_event),
        ]
        if self.microphone_device is not None:
            self._recorders.append(
                _TrackRecorder(self, "microphone", self.microphone_device, self.root / "microphone", self.stop_event)
            )
        for recorder in self._recorders:
            recorder.start()
        self.emit("session_started", tracks=[recorder.kind for recorder in self._recorders])

    def stop(self, timeout_seconds: float = 12) -> None:
        self.stop_event.set()
        for recorder in self._recorders:
            recorder.join(timeout_seconds)
        still_running = [recorder.kind for recorder in self._recorders if recorder.is_alive()]
        if still_running:
            raise CaptureError("A captura não finalizou todos os blocos com segurança.")
        self._write_session_file("stopped")
        self.emit("session_stopped", duration_ms=self.duration_ms)

    @property
    def duration_ms(self) -> int:
        if self.started_qpc_ns == 0:
            return 0
        return int((time.perf_counter_ns() - self.started_qpc_ns) / 1_000_000)

    def commit(self, block: CaptureBlock, device: AudioDevice, level: float) -> None:
        payload = {
            "event": "block_committed",
            "kind": block.kind,
            "sequence": block.sequence,
            "path": str(block.path),
            "started_ms": block.started_ms,
            "duration_ms": block.duration_ms,
            "bytes": block.size_bytes,
            "sha256": block.sha256,
            "device": asdict(device),
            "level": level,
            "qpc_ns": time.perf_counter_ns(),
        }
        with self._journal_lock:
            with (self.root / "capture.journal.ndjson").open("a", encoding="utf-8") as journal:
                journal.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
                journal.flush()
                os.fsync(journal.fileno())
        self.events.put(payload)
        self._observe_track_synchronization(block)

    def _observe_track_synchronization(self, block: CaptureBlock) -> None:
        """Compare tracks against the common QPC timeline without mixing either audio stream."""
        if self.microphone_device is None:
            return
        starts = self._track_starts[block.kind]
        starts[block.sequence] = block.started_ms
        system_start = self._track_starts["system"].get(block.sequence)
        microphone_start = self._track_starts["microphone"].get(block.sequence)
        if system_start is None or microphone_start is None:
            return
        offset_ms = microphone_start - system_start
        if self._sync_baseline_ms is None:
            self._sync_baseline_ms = offset_ms
        drift_ms = offset_ms - self._sync_baseline_ms
        self.emit(
            "track_synchronization",
            sequence=block.sequence,
            microphone_offset_ms=offset_ms,
            drift_ms=drift_ms,
        )
        if abs(drift_ms) > 250 and not self._sync_warning_emitted:
            self._sync_warning_emitted = True
            self.emit(
                "capture_degraded",
                kind="synchronization",
                message=(
                    "As trilhas variaram mais de 250 ms. Elas foram preservadas separadamente; "
                    "revise os timestamps desta reunião antes de exportar."
                ),
            )

    def emit(self, event: str, **payload: Any) -> None:
        self.events.put({"event": event, **payload})

    def _write_session_file(self, status: str) -> None:
        data = {
            "version": 1,
            "status": status,
            "started_qpc_ns": self.started_qpc_ns,
            "system_device": asdict(self.system_device),
            "microphone_device": asdict(self.microphone_device) if self.microphone_device else None,
            "block_seconds": self.block_seconds,
            "duration_ms": self.duration_ms,
            "synchronization": {
                "timeline": "qpc",
                "microphone_offset_baseline_ms": self._sync_baseline_ms,
                "drift_warning_emitted": self._sync_warning_emitted,
            },
        }
        temporary = self.root / "manifest.json.partial"
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(temporary, self.root / "manifest.json")
