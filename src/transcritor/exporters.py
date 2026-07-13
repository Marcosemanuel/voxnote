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
