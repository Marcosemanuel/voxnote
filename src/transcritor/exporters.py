from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from transcritor.domain import format_duration


def _timestamp(seconds: float, separator: str = ",") -> str:
    millis = int(round(seconds * 1000))
    hours, remainder = divmod(millis, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, ms = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{separator}{ms:03d}"


def export_meeting_transcript(
    session: sqlite3.Row, run: sqlite3.Row, segments: list[sqlite3.Row], destination: Path, kind: str
) -> None:
    """Export a final meeting run without changing captured audio or original recognition."""

    def text(row: sqlite3.Row) -> str:
        return str(row["revised_text"] or row["original_text"]).strip()

    def seconds(row: sqlite3.Row, column: str) -> float:
        return int(row[column]) / 1000

    if kind == "txt":
        text_payload = "\n\n".join(f"[{format_duration(seconds(row, 'start_ms'))}] {text(row)}" for row in segments)
        destination.write_text(text_payload, encoding="utf-8")
    elif kind == "srt":
        blocks = [
            f"{index}\n{_timestamp(seconds(row, 'start_ms'))} --> {_timestamp(seconds(row, 'end_ms'))}\n{text(row)}"
            for index, row in enumerate(segments, 1)
        ]
        destination.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")
    elif kind == "vtt":
        blocks = [
            f"{_timestamp(seconds(row, 'start_ms'), '.')} --> {_timestamp(seconds(row, 'end_ms'), '.')}\n{text(row)}"
            for row in segments
        ]
        destination.write_text("WEBVTT\n\n" + "\n\n".join(blocks) + "\n", encoding="utf-8")
    elif kind == "json":
        payload = {
            "meeting_session_id": int(session["id"]),
            "title": session["title"],
            "duration_ms": session["duration_ms"],
            "model": run["model_name"],
            "backend": run["backend"],
            "language": session["language"],
            "segments": [
                {
                    "track": row["track_kind"],
                    "start_ms": row["start_ms"],
                    "end_ms": row["end_ms"],
                    "original": row["original_text"],
                    "revised": row["revised_text"],
                    "reviewed": bool(row["reviewed"]),
                    "review_required": bool(row["review_required"]),
                    "metrics": json.loads(row["metrics_json"]),
                }
                for row in segments
            ],
        }
        destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        raise ValueError(f"Invalid export format: {kind}")


def export_transcript(job: sqlite3.Row, segments: list[sqlite3.Row], destination: Path, kind: str) -> None:
    def text(row: sqlite3.Row) -> str:
        return str(row["revised_text"] or row["original_text"]).strip()

    if kind == "txt":
        destination.write_text("\n\n".join(text(row) for row in segments), encoding="utf-8")
    elif kind == "srt":
        blocks = [
            f"{index}\n{_timestamp(row['start'])} --> {_timestamp(row['end'])}\n{text(row)}"
            for index, row in enumerate(segments, 1)
        ]
        destination.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")
    elif kind == "vtt":
        blocks = [f"{_timestamp(row['start'], '.')} --> {_timestamp(row['end'], '.')}\n{text(row)}" for row in segments]
        destination.write_text("WEBVTT\n\n" + "\n\n".join(blocks) + "\n", encoding="utf-8")
    elif kind == "json":
        payload = {
            "audio": job["audio_name"],
            "duration": job["duration"],
            "duration_display": format_duration(job["duration"]),
            "model": job["model_name"],
            "language": job["language"],
            "segments": [
                {
                    "start": row["start"],
                    "end": row["end"],
                    "original": row["original_text"],
                    "revised": row["revised_text"],
                    "reviewed": bool(row["reviewed"]),
                }
                for row in segments
            ],
        }
        destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        raise ValueError(f"Formato de exportação inválido: {kind}")
