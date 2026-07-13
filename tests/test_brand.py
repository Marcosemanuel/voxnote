from PySide6.QtGui import QPixmap

from transcritor.app import bundled_path
from transcritor.ui import STYLE


def test_voxnote_brand_assets_are_present_and_renderable(qtbot) -> None:
    symbol_path = bundled_path("assets/branding/voxnote-symbol.png")
    icon_path = bundled_path("assets/branding/voxnote-app-icon.ico")
    assert symbol_path.is_file()
    assert icon_path.is_file()
    assert not QPixmap(str(symbol_path)).isNull()


def test_voxnote_windows_icon_contains_standard_multiresolution_frames() -> None:
    icon_path = bundled_path("assets/branding/voxnote-app-icon.ico")
    content = icon_path.read_bytes()
    frame_count = int.from_bytes(content[4:6], "little")
    sizes = []
    for index in range(frame_count):
        width = content[6 + index * 16] or 256
        height = content[7 + index * 16] or 256
        sizes.append((width, height))

    assert sizes == [(16, 16), (20, 20), (24, 24), (32, 32), (40, 40), (48, 48), (64, 64), (128, 128), (256, 256)]


def test_voxnote_palette_is_applied_to_the_interface() -> None:
    for color in ("#111111", "#2b2b2b", "#d9d9d6", "#f5f5f3", "#3b82f6"):
        assert color in STYLE
