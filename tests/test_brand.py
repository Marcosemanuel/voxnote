from PySide6.QtGui import QPixmap

from transcritor.app import bundled_path
from transcritor.ui import STYLE


def test_voxnote_brand_assets_are_present_and_renderable(qtbot) -> None:
    symbol_path = bundled_path("assets/branding/voxnote-symbol.png")
    icon_path = bundled_path("assets/branding/voxnote-app-icon.ico")
    assert symbol_path.is_file()
    assert icon_path.is_file()
    assert not QPixmap(str(symbol_path)).isNull()


def test_voxnote_palette_is_applied_to_the_interface() -> None:
    for color in ("#111111", "#2b2b2b", "#d9d9d6", "#f5f5f3", "#3b82f6"):
        assert color in STYLE
