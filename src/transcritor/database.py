from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from transcritor.domain import AudioInfo, JobStatus, SegmentData

SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_migrations(version INTEGER PRIMARY KEY);
CREATE TABLE IF NOT EXISTS jobs(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audio_path TEXT NOT NULL,
    audio_name TEXT NOT NULL,
    duration REAL NOT NULL,
    format_name TEXT NOT NULL,
    size INTEGER NOT NULL,
    status TEXT NOT NULL,
    language TEXT,
    profile TEXT NOT NULL,
    model_name TEXT NOT NULL,
    glossary TEXT,
    backend TEXT NOT NULL DEFAULT 'cpu',
    progress REAL NOT NULL DEFAULT 0,
    error_message TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS segments(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    segment_index INTEGER NOT NULL,
    start REAL NOT NULL,
    end REAL NOT NULL,
    original_text TEXT NOT NULL,
    revised_text TEXT,
    avg_logprob REAL,
    no_speech_prob REAL,
    compression_ratio REAL,
    review_required INTEGER NOT NULL DEFAULT 0,
    reviewed INTEGER NOT NULL DEFAULT 0,
    words_json TEXT,
    UNIQUE(job_id, segment_index)
);
CREATE INDEX IF NOT EXISTS idx_segments_job ON segments(job_id, segment_index);
"""


class Database:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = NORMAL")
        connection.execute("PRAGMA busy_timeout = 5000")
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(SCHEMA)
            columns = {str(row["name"]) for row in connection.execute("PRAGMA table_info(jobs)")}
            if "glossary" not in columns:
                connection.execute("ALTER TABLE jobs ADD COLUMN glossary TEXT")
            connection.execute("INSERT OR IGNORE INTO schema_migrations(version) VALUES (1)")
            connection.execute("INSERT OR IGNORE INTO schema_migrations(version) VALUES (2)")
            connection.execute(
                """UPDATE jobs SET status=?, updated_at=CURRENT_TIMESTAMP
                   WHERE status IN (?, ?, ?)""",
                (
                    JobStatus.PAUSED,
                    JobStatus.TRANSCRIBING,
                    JobStatus.PAUSING,
                    JobStatus.CANCELLING,
                ),
            )

    def create_job(self, audio: AudioInfo, language: str | None, profile: str, model: str, glossary: str = "") -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                """INSERT INTO jobs(
                   audio_path,audio_name,duration,format_name,size,status,
                   language,profile,model_name,glossary)
                   VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (
                    str(audio.path),
                    audio.path.name,
                    audio.duration,
                    audio.format_name,
                    audio.size,
                    JobStatus.READY,
                    language,
                    profile,
                    model,
                    glossary,
                ),
            )
            if cursor.lastrowid is None:
                raise RuntimeError("Não foi possível criar a transcrição.")
            return int(cursor.lastrowid)

    def update_job(
        self,
        job_id: int,
        status: JobStatus,
        progress: float | None = None,
        backend: str | None = None,
        error: str | None = None,
    ) -> None:
        fields: list[str] = ["status=?", "updated_at=CURRENT_TIMESTAMP"]
        values: list[Any] = [status]
        if progress is not None:
            fields.append("progress=?")
            values.append(progress)
        if backend is not None:
            fields.append("backend=?")
            values.append(backend)
        if error is not None:
            fields.append("error_message=?")
            values.append(error)
        values.append(job_id)
        with self.connect() as connection:
            connection.execute(f"UPDATE jobs SET {', '.join(fields)} WHERE id=?", values)

    def save_segment(self, job_id: int, index: int, segment: SegmentData, words: list[dict[str, Any]]) -> None:
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO segments(
                   job_id,segment_index,start,end,original_text,revised_text,avg_logprob,
                   no_speech_prob,compression_ratio,review_required,words_json)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(job_id, segment_index) DO UPDATE SET
                     start=excluded.start,
                     end=excluded.end,
                     original_text=excluded.original_text,
                     revised_text=CASE WHEN segments.reviewed=1
                       THEN segments.revised_text ELSE excluded.original_text END,
                     avg_logprob=excluded.avg_logprob,
                     no_speech_prob=excluded.no_speech_prob,
                     compression_ratio=excluded.compression_ratio,
                     review_required=excluded.review_required,
                     words_json=excluded.words_json""",
                (
                    job_id,
                    index,
                    segment.start,
                    segment.end,
                    segment.text,
                    segment.text,
                    segment.avg_logprob,
                    segment.no_speech_prob,
                    segment.compression_ratio,
                    int(segment.review_required),
                    json.dumps(words, ensure_ascii=False),
                ),
            )

    def list_jobs(self, query: str = "") -> list[sqlite3.Row]:
        with self.connect() as connection:
            return list(
                connection.execute(
                    "SELECT * FROM jobs WHERE audio_name LIKE ? ORDER BY updated_at DESC, id DESC", (f"%{query}%",)
                )
            )

    def get_job(self, job_id: int) -> sqlite3.Row | None:
        with self.connect() as connection:
            row: sqlite3.Row | None = connection.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
            return row

    def get_segments(self, job_id: int) -> list[sqlite3.Row]:
        with self.connect() as connection:
            return list(connection.execute("SELECT * FROM segments WHERE job_id=? ORDER BY segment_index", (job_id,)))

    def resume_point(self, job_id: int) -> tuple[int, float]:
        with self.connect() as connection:
            row = connection.execute(
                """SELECT COALESCE(MAX(segment_index), -1) AS last_index,
                          COALESCE(MAX(end), 0) AS last_end
                   FROM segments WHERE job_id=?""",
                (job_id,),
            ).fetchone()
            if row is None:
                return 0, 0.0
            return int(row["last_index"]) + 1, float(row["last_end"])

    def is_job_active(self, job_id: int) -> bool:
        job = self.get_job(job_id)
        return bool(
            job is not None and job["status"] in {JobStatus.TRANSCRIBING, JobStatus.PAUSING, JobStatus.CANCELLING}
        )

    def revise_segment(self, segment_id: int, text: str, reviewed: bool = True) -> None:
        with self.connect() as connection:
            connection.execute(
                "UPDATE segments SET revised_text=?, reviewed=? WHERE id=?", (text, int(reviewed), segment_id)
            )

    def delete_job(self, job_id: int) -> None:
        with self.connect() as connection:
            connection.execute("DELETE FROM jobs WHERE id=?", (job_id,))
