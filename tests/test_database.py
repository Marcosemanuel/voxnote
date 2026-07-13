import sqlite3
from pathlib import Path

from transcritor.database import Database
from transcritor.domain import AudioInfo, SegmentData


def test_job_checkpoint_and_revision(tmp_path: Path) -> None:
    database = Database(tmp_path / "test.db")
    audio = AudioInfo(tmp_path / "audio.wav", 60.0, "wav", 123)
    job_id = database.create_job(audio, "pt", "Leve", "small")
    database.save_segment(job_id, 0, SegmentData(0, 3, "original", -0.2, 0.1, 1.0), [])
    segment = database.get_segments(job_id)[0]
    database.revise_segment(segment["id"], "revisado")
    revised = database.get_segments(job_id)[0]
    assert revised["original_text"] == "original"
    assert revised["revised_text"] == "revisado"
    assert revised["reviewed"] == 1


def test_migrates_database_without_glossary(tmp_path: Path) -> None:
    path = tmp_path / "old.db"
    connection = sqlite3.connect(path)
    connection.execute(
        """CREATE TABLE jobs(
        id INTEGER PRIMARY KEY AUTOINCREMENT, audio_path TEXT NOT NULL,
        audio_name TEXT NOT NULL, duration REAL NOT NULL, format_name TEXT NOT NULL,
        size INTEGER NOT NULL, status TEXT NOT NULL, language TEXT, profile TEXT NOT NULL,
        model_name TEXT NOT NULL, backend TEXT NOT NULL DEFAULT 'cpu',
        progress REAL NOT NULL DEFAULT 0, error_message TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"""
    )
    connection.close()
    database = Database(path)
    job_id = database.create_job(AudioInfo(tmp_path / "audio.wav", 10, "wav", 1), "pt", "Leve", "small", "termo")
    assert database.get_job(job_id)["glossary"] == "termo"


def test_checkpoint_upsert_preserves_human_revision(tmp_path: Path) -> None:
    database = Database(tmp_path / "test.db")
    job_id = database.create_job(AudioInfo(tmp_path / "audio.wav", 60, "wav", 1), "pt", "Leve", "small")
    database.save_segment(job_id, 0, SegmentData(0, 3, "original"), [])
    segment = database.get_segments(job_id)[0]
    database.revise_segment(segment["id"], "correção humana")
    database.save_segment(job_id, 0, SegmentData(0, 3.1, "novo reconhecimento"), [])
    result = database.get_segments(job_id)[0]
    assert result["original_text"] == "novo reconhecimento"
    assert result["revised_text"] == "correção humana"
    assert result["reviewed"] == 1
