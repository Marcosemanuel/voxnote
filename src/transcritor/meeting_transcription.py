from __future__ import annotations

import logging
import shutil
import wave
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from faster_whisper import WhisperModel

from transcritor.database import Database
from transcritor.engine import TranscriptionController
from transcritor.models import ModelManager

LOG = logging.getLogger(__name__)

ProgressCallback = Callable[[float, str], None]


@dataclass(frozen=True, slots=True)
class AudioUnit:
    track_kind: str
    start_ms: int
    safe_end_ms: int
    path: Path
    duration_ms: int


def _review_required(avg_logprob: float | None, no_speech_prob: float | None, compression_ratio: float | None) -> bool:
    """Technical signals identify review candidates; they are not confidence percentages."""
    return bool(
        (avg_logprob is not None and avg_logprob < -0.8)
        or (compression_ratio is not None and compression_ratio > 2.4)
        or (no_speech_prob is not None and no_speech_prob > 0.6 and (avg_logprob or 0) < -1.0)
    )


def _build_units(
    cache_dir: Path,
    track_kind: str,
    blocks: list[Any],
    window_blocks: int = 5,
    overlap_blocks: int = 1,
) -> list[AudioUnit]:
    """Join only a bounded window. No full-meeting WAV is created."""
    if not blocks:
        return []
    cache_dir.mkdir(parents=True, exist_ok=True)
    stride = max(1, window_blocks - overlap_blocks)
    units: list[AudioUnit] = []
    for start in range(0, len(blocks), stride):
        selected = blocks[start : start + window_blocks]
        if not selected:
            break
        first_path = Path(str(selected[0]["path"]))
        with wave.open(str(first_path), "rb") as source:
            params = (
                source.getnchannels(),
                source.getsampwidth(),
                source.getframerate(),
                source.getcomptype(),
                source.getcompname(),
            )
        target = cache_dir / f"{track_kind}-{start:08d}.wav"
        written_frames = 0
        with wave.open(str(target), "wb") as output:
            output.setnchannels(params[0])
            output.setsampwidth(params[1])
            output.setframerate(params[2])
            output.setcomptype(params[3], params[4])
            for block in selected:
                path = Path(str(block["path"]))
                with wave.open(str(path), "rb") as source:
                    current = (
                        source.getnchannels(),
                        source.getsampwidth(),
                        source.getframerate(),
                        source.getcomptype(),
                        source.getcompname(),
                    )
                    if current != params:
                        raise RuntimeError(
                            "A configuração do dispositivo mudou durante a reunião. A trilha precisa ser revisada."
                        )
                    frames = source.readframes(source.getnframes())
                    output.writeframesraw(frames)
                    written_frames += source.getnframes()
        duration_ms = round(written_frames / params[2] * 1000)
        first_start_ms = int(selected[0]["started_ms"])
        safe_block_index = min(len(selected), stride) - 1
        safe_end_ms = int(selected[safe_block_index]["started_ms"]) + int(selected[safe_block_index]["duration_ms"])
        if start + len(selected) >= len(blocks):
            safe_end_ms = first_start_ms + duration_ms
        units.append(AudioUnit(track_kind, first_start_ms, safe_end_ms, target, duration_ms))
        if start + len(selected) >= len(blocks):
            break
    return units


def _select_backend() -> tuple[str, str]:
    try:
        import ctranslate2

        if "float16" in ctranslate2.get_supported_compute_types("cuda"):
            return "cuda", "float16"
    except Exception:
        pass
    return "cpu", "int8"


def transcribe_meeting(
    database: Database,
    session_id: int,
    models_dir: Path,
    cache_dir: Path,
    controller: TranscriptionController,
    callback: ProgressCallback,
) -> int:
    session = database.get_meeting_session(session_id)
    if session is None:
        raise ValueError("Sessão de reunião não encontrada.")
    tracks = database.list_capture_tracks(session_id)
    if not tracks:
        raise RuntimeError("Nenhuma trilha confirmada foi encontrada para esta reunião.")
    backend, compute_type = _select_backend()
    parameters = {
        "beam_size": 5,
        "temperature": 0.0,
        "vad_filter": True,
        "vad_parameters": {"min_silence_duration_ms": 700, "speech_pad_ms": 350, "max_speech_duration_s": 28},
        "word_timestamps": True,
        "condition_on_previous_text": False,
    }
    run_id = database.create_transcription_run(session_id, "final", str(session["model_name"]), backend, parameters)
    manager = ModelManager(models_dir)
    model_source = (
        str(manager.path_for(str(session["model_name"])))
        if manager.is_valid(str(session["model_name"]))
        else str(manager.download(str(session["model_name"])))
    )
    units: list[AudioUnit] = []
    for track in tracks:
        blocks = database.list_capture_blocks(int(track["id"]))
        units.extend(_build_units(cache_dir / str(session_id) / str(track["kind"]), str(track["kind"]), blocks))
    if not units:
        raise RuntimeError("A reunião não contém blocos de áudio concluídos.")
    total_ms = sum(unit.duration_ms for unit in units)
    processed_ms = 0
    next_index = 0

    def transcribe_unit(active_model: WhisperModel, unit: AudioUnit) -> Any:
        segments, _ = active_model.transcribe(
            str(unit.path),
            language=str(session["language"] or "pt"),
            task="transcribe",
            beam_size=5,
            temperature=0.0,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 700, "speech_pad_ms": 350, "max_speech_duration_s": 28},
            word_timestamps=True,
            condition_on_previous_text=False,
            hotwords=str(session["glossary"] or "") or None,
        )
        return segments

    try:
        try:
            model = WhisperModel(
                model_source,
                device=backend,
                compute_type=compute_type,
                download_root=str(models_dir),
                cpu_threads=max(1, (__import__("os").cpu_count() or 2) - 2),
            )
        except Exception:
            if backend != "cuda":
                raise
            LOG.warning("CUDA is unavailable for meeting transcription; using CPU", exc_info=True)
            backend, compute_type = "cpu", "int8"
            database.update_transcription_run(run_id, "preparing", backend=backend)
            model = WhisperModel(
                model_source,
                device=backend,
                compute_type=compute_type,
                download_root=str(models_dir),
                cpu_threads=max(1, (__import__("os").cpu_count() or 2) - 2),
            )
        for unit in units:
            if controller.cancel_event.is_set():
                database.update_transcription_run(run_id, "cancelled", processed_ms / total_ms * 100)
                database.update_meeting_session(session_id, "captured")
                return run_id
            while controller.pause_event.is_set():
                database.update_transcription_run(run_id, "paused", processed_ms / total_ms * 100)
                if controller.cancel_event.wait(0.2):
                    database.update_transcription_run(run_id, "cancelled", processed_ms / total_ms * 100)
                    database.update_meeting_session(session_id, "captured")
                    return run_id
            database.update_transcription_run(run_id, "transcribing", processed_ms / total_ms * 100)
            try:
                segments = transcribe_unit(model, unit)
            except Exception:
                if backend != "cuda":
                    raise
                LOG.warning(
                    "CUDA inference failed for meeting transcription; retrying this block on CPU", exc_info=True
                )
                backend, compute_type = "cpu", "int8"
                database.update_transcription_run(run_id, "transcribing", backend=backend)
                model = WhisperModel(
                    model_source,
                    device=backend,
                    compute_type=compute_type,
                    download_root=str(models_dir),
                    cpu_threads=max(1, (__import__("os").cpu_count() or 2) - 2),
                )
                callback(processed_ms / total_ms * 100, "A aceleração falhou. Este bloco será retomado com CPU.")
                segments = transcribe_unit(model, unit)
            for item in segments:
                start_ms = unit.start_ms + round(item.start * 1000)
                end_ms = unit.start_ms + round(item.end * 1000)
                if end_ms > unit.safe_end_ms + 10:
                    continue
                metrics = {
                    "avg_logprob": item.avg_logprob,
                    "no_speech_prob": item.no_speech_prob,
                    "compression_ratio": item.compression_ratio,
                    "words": [
                        {
                            "start_ms": start_ms + round(word.start * 1000),
                            "end_ms": start_ms + round(word.end * 1000),
                            "text": word.word,
                        }
                        for word in (item.words or [])
                    ],
                }
                database.save_run_segment(
                    run_id,
                    next_index,
                    unit.track_kind,
                    start_ms,
                    end_ms,
                    item.text.strip(),
                    metrics,
                    _review_required(item.avg_logprob, item.no_speech_prob, item.compression_ratio),
                )
                next_index += 1
            processed_ms += unit.duration_ms
            progress = min(99.9, processed_ms / total_ms * 100)
            database.update_transcription_run(run_id, "transcribing", progress)
            callback(progress, "Gerando transcrição final com checkpoints salvos.")
        database.update_transcription_run(run_id, "completed", 100)
        database.update_meeting_session(session_id, "completed", duration_ms=int(session["duration_ms"]))
        callback(100, "Transcrição final pronta para revisão.")
        return run_id
    except Exception as exc:
        database.update_transcription_run(run_id, "failed", error=str(exc))
        database.update_meeting_session(session_id, "failed", error=str(exc))
        raise
    finally:
        shutil.rmtree(cache_dir / str(session_id), ignore_errors=True)
