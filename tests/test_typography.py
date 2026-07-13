from PySide6.QtGui import QFont, QFontDatabase

from transcritor.app import bundled_path, register_manrope
from transcritor.ui import STYLE, interface_font


def test_bundled_manrope_registers_for_qt(qtbot) -> None:
    font_path = bundled_path("assets/fonts/Manrope-Variable.ttf")
    assert font_path.is_file()
    assert register_manrope() == "Manrope"
    assert "Manrope" in QFontDatabase.families()


def test_style_uses_only_manrope_and_supported_weights() -> None:
    assert "Manrope" in STYLE
    assert "Segoe UI" not in STYLE
    assert "Georgia" not in STYLE
    assert "font-weight: 300" not in STYLE
    assert "font-weight: 800" not in STYLE
    assert "font-weight: 650" not in STYLE


def test_timestamp_font_enables_tabular_numbers() -> None:
    font = interface_font(12, QFont.Weight.Medium, tabular=True)
    tag = font.Tag.fromString("tnum")
    assert font.featureValue(tag) == 1
