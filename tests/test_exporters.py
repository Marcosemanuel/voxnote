from pathlib import Path

from transcritor.database import Database
from transcritor.domain import AudioInfo, SegmentData
from transcritor.exporters import export_transcript


def test_exports_all_formats(tmp_path: Path) -> None:
    database = Database(tmp_path / "test.db")
    job_id = database.create_job(AudioInfo(tmp_path / "a.wav", 5, "wav", 1), "pt", "Leve", "small")
    database.save_segment(job_id, 0, SegmentData(0, 2.5, "Olá mundo"), [])
    job = database.get_job(job_id)
    segments = database.get_segments(job_id)
    assert job is not None
    for kind in ("txt", "srt", "vtt", "json"):
        output = tmp_path / f"result.{kind}"
        export_transcript(job, segments, output, kind)
        assert output.exists()
        assert "Olá mundo" in output.read_text(encoding="utf-8")
