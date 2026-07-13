from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

SUPPORTED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus", ".wma", ".aiff", ".aif", ".webm"}


class JobStatus(StrEnum):
    PENDING = "pending"
    VALIDATING = "validating"
    READY = "ready"
    TRANSCRIBING = "transcribing"
    PAUSING = "pausing"
    PAUSED = "paused"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    FAILED = "failed"


STATUS_LABELS = {
    JobStatus.PENDING: "Aguardando",
    JobStatus.VALIDATING: "Verificando arquivo",
    JobStatus.READY: "Pronta",
    JobStatus.TRANSCRIBING: "Em andamento",
    JobStatus.PAUSING: "Pausando",
    JobStatus.PAUSED: "Pausada",
    JobStatus.CANCELLING: "Cancelando",
    JobStatus.CANCELLED: "Interrompida",
    JobStatus.COMPLETED: "Concluída",
    JobStatus.FAILED: "Não concluída",
}


@dataclass(frozen=True, slots=True)
class AudioInfo:
    path: Path
    duration: float
    format_name: str
    size: int


@dataclass(frozen=True, slots=True)
class SegmentData:
    start: float
    end: float
    text: str
    avg_logprob: float | None = None
    no_speech_prob: float | None = None
    compression_ratio: float | None = None

    @property
    def review_required(self) -> bool:
        return bool(
            (self.avg_logprob is not None and self.avg_logprob < -0.8)
            or (self.no_speech_prob is not None and self.no_speech_prob > 0.6)
            or (self.compression_ratio is not None and self.compression_ratio > 2.4)
        )


@dataclass(frozen=True, slots=True)
class HardwareProfile:
    cpu: str
    logical_cpus: int
    ram_gb: float
    gpu_name: str | None
    gpu_vram_gb: float | None
    cuda_compatible: bool
    recommended_profile: str


MODEL_PROFILES = {
    "Leve": "small",
    "Equilibrada": "medium",
    "Alta precisão": "large-v3",
    "Rápida": "turbo",
}


def format_duration(seconds: float) -> str:
    total = max(0, int(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"
