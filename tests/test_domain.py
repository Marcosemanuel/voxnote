from transcritor.domain import SegmentData, format_duration


def test_format_duration() -> None:
    assert format_duration(3661.9) == "01:01:01"


def test_segment_requires_review_for_low_log_probability() -> None:
    assert SegmentData(0, 2, "texto", avg_logprob=-1.0).review_required
    assert not SegmentData(0, 2, "texto", avg_logprob=-0.2).review_required
