from pathlib import Path

ICON_NAMES = (
    "audio-lines",
    "file-text",
    "notebook-pen",
    "sparkles",
    "mic",
    "menu",
    "search",
)


def test_lucide_icon_assets_are_valid_svg_files() -> None:
    icon_directory = Path(__file__).resolve().parents[1] / "assets" / "icons" / "lucide"
    assert (icon_directory / "LICENSE").is_file()
    for icon_name in ICON_NAMES:
        content = (icon_directory / f"{icon_name}.svg").read_text(encoding="utf-8")
        assert "<svg" in content
        assert 'stroke-width="2"' in content
        assert 'stroke-linecap="round"' in content
        assert 'stroke-linejoin="round"' in content
