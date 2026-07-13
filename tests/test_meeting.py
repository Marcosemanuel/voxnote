from __future__ import annotations

import hashlib
import json
import wave
from pathlib import Path

from transcritor.database import Database
from transcritor.domain import HardwareProfile
from transcritor.exporters import export_meeting_transcript
from transcritor.meeting import AudioDevice, CaptureBlock, MeetingCaptureService
from transcritor.meeting_transcription import _build_units
from transcritor.models import MODEL_PROFILES
from transcritor.paths import AppPaths
from transcritor.qml_controller import QmlController


def _block(path: Path, frames: int = 8_000) -> None:
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(8_000)
        output.writeframes(b"\x00\x00" * frames)


def test_meeting_run_preserves_human_revision_and_exports(tmp_path: Path) -> None:
    database = Database(tmp_path / "meeting.db")
    session_id = database.create_meeting_session(
        "Reunião de teste", "pt", "Leve", "small", "Voxnote", "final-first", tmp_path / "capture"
    )
    track_id = database.create_capture_track(session_id, "system", 10, "Saída", 8_000, 1)
    captured = tmp_path / "capture.wav"
    _block(captured)
    database.save_capture_block(track_id, 1, captured, 0, 1_000, captured.stat().st_size, "checksum")
    run_id = database.create_transcription_run(session_id, "final", "small", "cpu", {"beam_size": 5})
    database.save_run_segment(run_id, 0, "system", 0, 900, "texto reconhecido", {}, True)
    segment = database.list_run_segments(run_id)[0]
    database.revise_run_segment(int(segment["id"]), "texto revisado")
    database.save_run_segment(run_id, 0, "system", 0, 950, "novo reconhecimento", {}, False)
    preserved = database.list_run_segments(run_id)[0]
    assert preserved["original_text"] == "novo reconhecimento"
    assert preserved["revised_text"] == "texto revisado"
    assert preserved["reviewed"] == 1

    destination = tmp_path / "reuniao.json"
    session = database.get_meeting_session(session_id)
    run = database.get_latest_transcription_run(session_id)
    assert session is not None and run is not None
    export_meeting_transcript(session, run, database.list_run_segments(run_id), destination, "json")
    assert '"original": "novo reconhecimento"' in destination.read_text(encoding="utf-8")
    assert '"revised": "texto revisado"' in destination.read_text(encoding="utf-8")


def test_build_units_uses_bounded_windows_and_keeps_final_partial_block(tmp_path: Path) -> None:
    blocks: list[dict[str, object]] = []
    for index in range(6):
        path = tmp_path / f"{index}.wav"
        _block(path)
        blocks.append({"path": str(path), "started_ms": index * 1_000, "duration_ms": 1_000})

    units = _build_units(tmp_path / "cache", "system", blocks, window_blocks=3, overlap_blocks=1)
    assert len(units) == 3
    assert units[0].duration_ms == 3_000
    assert units[0].safe_end_ms == 2_000
    assert units[-1].safe_end_ms == 6_000
    assert all(unit.path.is_file() for unit in units)


def _hardware_fixture() -> HardwareProfile:
    return HardwareProfile(
        cpu="CPU de teste",
        logical_cpus=8,
        ram_gb=16.0,
        gpu_name=None,
        gpu_vram_gb=None,
        cuda_compatible=False,
        recommended_profile="Equilibrada",
    )


def test_failed_session_recovers_journal_blocks_and_can_restart(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("transcritor.qml_controller.detect_hardware", _hardware_fixture)
    paths = AppPaths.resolve(tmp_path / "app")
    database = Database(paths.data / "test.db")
    capture_root = paths.captures / "interrupted"
    system_directory = capture_root / "system"
    system_directory.mkdir(parents=True)
    block_path = system_directory / "00000001.wav"
    _block(block_path)
    checksum = hashlib.sha256(block_path.read_bytes()).hexdigest()
    session_id = database.create_meeting_session(
        "Reunião interrompida", "pt", "Leve", "small", "", "final-first", capture_root
    )
    database.create_capture_track(session_id, "system", 1, "Saída", 8_000, 1)
    database.update_meeting_session(session_id, "failed", error="Dispositivo removido")
    (capture_root / "capture.journal.ndjson").write_text(
        json.dumps(
            {
                "event": "block_committed",
                "kind": "system",
                "sequence": 1,
                "path": str(block_path),
                "started_ms": 0,
                "duration_ms": 1_000,
                "bytes": block_path.stat().st_size,
                "sha256": checksum,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    controller = QmlController(paths, database)

    recovered = database.get_meeting_session(session_id)
    assert recovered is not None
    assert recovered["status"] == "captured"
    assert database.capture_block_count(session_id) == 1
    assert controller.meetingSessions[0]["canTranscribe"] is True


def test_resume_meeting_transcription_uses_preserved_blocks(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("transcritor.qml_controller.detect_hardware", _hardware_fixture)
    paths = AppPaths.resolve(tmp_path / "app")
    database = Database(paths.data / "test.db")
    session_id = database.create_meeting_session(
        "Reunião para repetir", "pt", "Alta precisão", "large-v3", "", "final-first", paths.captures / "retry"
    )
    track_id = database.create_capture_track(session_id, "system", 1, "Saída", 8_000, 1)
    block_path = tmp_path / "retry.wav"
    _block(block_path)
    database.save_capture_block(track_id, 1, block_path, 0, 1_000, block_path.stat().st_size, "checksum")
    database.update_meeting_session(session_id, "failed", error="Falha transitória")
    controller = QmlController(paths, database)
    started: list[int] = []
    monkeypatch.setattr(controller, "_start_meeting_transcription", lambda value: started.append(value))

    controller.resume_meeting_transcription(session_id)

    session = database.get_meeting_session(session_id)
    assert started == [session_id]
    assert session is not None and session["status"] == "transcribing"
    assert controller.meetingState == "transcribing"


def test_track_synchronization_reports_drift_without_merging_audio(tmp_path: Path) -> None:
    device = AudioDevice(1, "Dispositivo", 1, 8_000, True)
    service = MeetingCaptureService(tmp_path, device, device)
    block_path = tmp_path / "block.wav"
    _block(block_path)
    for kind, sequence, started_ms in [
        ("system", 1, 0),
        ("microphone", 1, 100),
        ("system", 2, 1_000),
        ("microphone", 2, 1_400),
    ]:
        service.commit(
            CaptureBlock(kind, sequence, block_path, started_ms, 1_000, block_path.stat().st_size, "checksum"),
            device,
            0.0,
        )

    events = []
    while not service.events.empty():
        events.append(service.events.get_nowait())
    synchronization = [event for event in events if event["event"] == "track_synchronization"]
    warnings = [event for event in events if event["event"] == "capture_degraded"]
    assert [event["drift_ms"] for event in synchronization] == [0, 300]
    assert len(warnings) == 1
    assert service._track_starts["system"][2] == 1_000
    assert service._track_starts["microphone"][2] == 1_400


def test_meeting_quality_labels_match_backend_profiles() -> None:
    source = (Path(__file__).parents[1] / "src" / "transcritor" / "qml" / "Main.qml").read_text(encoding="utf-8")
    labels = ["Leve", "Equilibrada", "Alta precisão", "Rápida"]

    assert all(label in MODEL_PROFILES for label in labels)
    assert 'model: ["Leve", "Equilibrada", "Alta precisão", "Rápida"]' in source
