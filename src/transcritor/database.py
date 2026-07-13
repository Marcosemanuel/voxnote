from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, cast

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
CREATE TABLE IF NOT EXISTS meeting_sessions(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    language TEXT,
    profile TEXT NOT NULL,
    model_name TEXT NOT NULL,
    glossary TEXT NOT NULL DEFAULT '',
    mode TEXT NOT NULL,
    consent_at TEXT NOT NULL,
    capture_path TEXT NOT NULL,
    status TEXT NOT NULL,
    duration_ms INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS capture_tracks(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES meeting_sessions(id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    device_index INTEGER NOT NULL,
    device_name TEXT NOT NULL,
    sample_rate INTEGER NOT NULL,
    channels INTEGER NOT NULL,
    started_at_ms INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active',
    UNIQUE(session_id, kind)
);
CREATE TABLE IF NOT EXISTS capture_blocks(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    track_id INTEGER NOT NULL REFERENCES capture_tracks(id) ON DELETE CASCADE,
    sequence INTEGER NOT NULL,
    path TEXT NOT NULL,
    started_ms INTEGER NOT NULL,
    duration_ms INTEGER NOT NULL,
    bytes INTEGER NOT NULL,
    sha256 TEXT NOT NULL,
    committed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(track_id, sequence)
);
CREATE INDEX IF NOT EXISTS idx_capture_blocks_track ON capture_blocks(track_id, sequence);
CREATE TABLE IF NOT EXISTS transcription_runs(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES meeting_sessions(id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    model_name TEXT NOT NULL,
    backend TEXT NOT NULL,
    parameters_json TEXT NOT NULL,
    status TEXT NOT NULL,
    progress REAL NOT NULL DEFAULT 0,
    error_message TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS run_segments(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES transcription_runs(id) ON DELETE CASCADE,
    track_kind TEXT NOT NULL,
    segment_index INTEGER NOT NULL,
    start_ms INTEGER NOT NULL,
    end_ms INTEGER NOT NULL,
    original_text TEXT NOT NULL,
    revised_text TEXT,
    metrics_json TEXT NOT NULL DEFAULT '{}',
    review_required INTEGER NOT NULL DEFAULT 0,
    reviewed INTEGER NOT NULL DEFAULT 0,
    UNIQUE(run_id, segment_index)
);
CREATE INDEX IF NOT EXISTS idx_run_segments_run ON run_segments(run_id, segment_index);
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
            connection.execute("INSERT OR IGNORE INTO schema_migrations(version) VALUES (3)")
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

    def create_meeting_session(
        self,
        title: str,
        language: str | None,
        profile: str,
        model_name: str,
        glossary: str,
        mode: str,
        capture_path: Path,
    ) -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                """INSERT INTO meeting_sessions(
                   title,language,profile,model_name,glossary,mode,consent_at,capture_path,status)
                   VALUES(?,?,?,?,?,?,CURRENT_TIMESTAMP,?,?)""",
                (title, language, profile, model_name, glossary, mode, str(capture_path), "preparing"),
            )
            if cursor.lastrowid is None:
                raise RuntimeError("Não foi possível criar a sessão de captura.")
            return int(cursor.lastrowid)

    def update_meeting_session(
        self,
        session_id: int,
        status: str,
        duration_ms: int | None = None,
        error: str | None = None,
    ) -> None:
        fields = ["status=?", "updated_at=CURRENT_TIMESTAMP"]
        values: list[Any] = [status]
        if duration_ms is not None:
            fields.append("duration_ms=?")
            values.append(duration_ms)
        if error is not None:
            fields.append("error_message=?")
            values.append(error)
        values.append(session_id)
        with self.connect() as connection:
            connection.execute(f"UPDATE meeting_sessions SET {', '.join(fields)} WHERE id=?", values)

    def get_meeting_session(self, session_id: int) -> sqlite3.Row | None:
        with self.connect() as connection:
            return cast(
                sqlite3.Row | None,
                connection.execute("SELECT * FROM meeting_sessions WHERE id=?", (session_id,)).fetchone(),
            )

    def list_meeting_sessions(self, query: str = "") -> list[sqlite3.Row]:
        with self.connect() as connection:
            return list(
                connection.execute(
                    "SELECT * FROM meeting_sessions WHERE title LIKE ? ORDER BY updated_at DESC, id DESC",
                    (f"%{query}%",),
                )
            )

    def create_capture_track(
        self,
        session_id: int,
        kind: str,
        device_index: int,
        device_name: str,
        sample_rate: int,
        channels: int,
    ) -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                """INSERT INTO capture_tracks(session_id,kind,device_index,device_name,sample_rate,channels)
                   VALUES(?,?,?,?,?,?)""",
                (session_id, kind, device_index, device_name, sample_rate, channels),
            )
            if cursor.lastrowid is None:
                raise RuntimeError("Não foi possível registrar a trilha de captura.")
            return int(cursor.lastrowid)

    def list_capture_tracks(self, session_id: int) -> list[sqlite3.Row]:
        with self.connect() as connection:
            query = "SELECT * FROM capture_tracks WHERE session_id=? ORDER BY id"
            return list(connection.execute(query, (session_id,)))

    def save_capture_block(
        self,
        track_id: int,
        sequence: int,
        path: Path,
        started_ms: int,
        duration_ms: int,
        size_bytes: int,
        sha256: str,
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """INSERT OR REPLACE INTO capture_blocks(
                   track_id,sequence,path,started_ms,duration_ms,bytes,sha256)
                   VALUES(?,?,?,?,?,?,?)""",
                (track_id, sequence, str(path), started_ms, duration_ms, size_bytes, sha256),
            )

    def list_capture_blocks(self, track_id: int) -> list[sqlite3.Row]:
        with self.connect() as connection:
            return list(
                connection.execute("SELECT * FROM capture_blocks WHERE track_id=? ORDER BY sequence", (track_id,))
            )

    def capture_block_count(self, session_id: int) -> int:
        """Return only persisted blocks; a session may be retried only from these files."""
        with self.connect() as connection:
            row = connection.execute(
                """SELECT COUNT(*) AS total
                   FROM capture_blocks blocks
                   JOIN capture_tracks tracks ON tracks.id=blocks.track_id
                   WHERE tracks.session_id=?""",
                (session_id,),
            ).fetchone()
            return int(row["total"] if row is not None else 0)

    def create_transcription_run(
        self, session_id: int, kind: str, model_name: str, backend: str, parameters: dict[str, Any]
    ) -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                """INSERT INTO transcription_runs(session_id,kind,model_name,backend,parameters_json,status)
                   VALUES(?,?,?,?,?,?)""",
                (session_id, kind, model_name, backend, json.dumps(parameters, ensure_ascii=False), "transcribing"),
            )
            if cursor.lastrowid is None:
                raise RuntimeError("Não foi possível iniciar o reconhecimento final.")
            return int(cursor.lastrowid)

    def update_transcription_run(
        self,
        run_id: int,
        status: str,
        progress: float | None = None,
        error: str | None = None,
        backend: str | None = None,
    ) -> None:
        fields = ["status=?", "updated_at=CURRENT_TIMESTAMP"]
        values: list[Any] = [status]
        if progress is not None:
            fields.append("progress=?")
            values.append(progress)
        if error is not None:
            fields.append("error_message=?")
            values.append(error)
        if backend is not None:
            fields.append("backend=?")
            values.append(backend)
        values.append(run_id)
        with self.connect() as connection:
            connection.execute(f"UPDATE transcription_runs SET {', '.join(fields)} WHERE id=?", values)

    def get_latest_transcription_run(self, session_id: int) -> sqlite3.Row | None:
        with self.connect() as connection:
            return cast(
                sqlite3.Row | None,
                connection.execute(
                    "SELECT * FROM transcription_runs WHERE session_id=? ORDER BY id DESC LIMIT 1", (session_id,)
                ).fetchone(),
            )

    def save_run_segment(
        self,
        run_id: int,
        index: int,
        track_kind: str,
        start_ms: int,
        end_ms: int,
        text: str,
        metrics: dict[str, Any],
        review_required: bool,
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO run_segments(
                   run_id,track_kind,segment_index,start_ms,end_ms,original_text,revised_text,
                   metrics_json,review_required)
                   VALUES(?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(run_id, segment_index) DO UPDATE SET
                     track_kind=excluded.track_kind,start_ms=excluded.start_ms,end_ms=excluded.end_ms,
                     original_text=excluded.original_text,
                     revised_text=CASE WHEN run_segments.reviewed=1
                       THEN run_segments.revised_text ELSE excluded.original_text END,
                     metrics_json=excluded.metrics_json,review_required=excluded.review_required""",
                (
                    run_id,
                    track_kind,
                    index,
                    start_ms,
                    end_ms,
                    text,
                    text,
                    json.dumps(metrics, ensure_ascii=False),
                    int(review_required),
                ),
            )

    def list_run_segments(self, run_id: int) -> list[sqlite3.Row]:
        with self.connect() as connection:
            return list(
                connection.execute(
                    "SELECT * FROM run_segments WHERE run_id=? ORDER BY start_ms, end_ms, segment_index", (run_id,)
                )
            )

    def revise_run_segment(self, segment_id: int, text: str, reviewed: bool = True) -> None:
        with self.connect() as connection:
            connection.execute(
                "UPDATE run_segments SET revised_text=?, reviewed=? WHERE id=?", (text, int(reviewed), segment_id)
            )
