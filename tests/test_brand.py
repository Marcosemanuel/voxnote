from pathlib import Path

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


def test_installer_uses_a_versioned_official_icon_for_program_and_desktop_shortcuts() -> None:
    installer = Path("installer/TranscritorLocal.iss").read_text(encoding="utf-8")
    assert 'DestName: "voxnote-app-icon-{#MyAppVersion}.ico"' in installer
    icon_reference = 'IconFilename: "{app}\\assets\\branding\\voxnote-app-icon-{#MyAppVersion}.ico"; IconIndex: 0'
    assert installer.count(icon_reference) == 2


def test_installer_refreshes_an_existing_desktop_shortcut_after_update() -> None:
    installer = Path("installer/TranscritorLocal.iss").read_text(encoding="utf-8")
    assert "procedure RefreshDesktopShortcutIcon();" in installer
    assert "if not FileExists(shortcutPath) then" in installer
    assert "DeleteFile(shortcutPath);" in installer
    assert "CreateShellLink(shortcutPath" in installer
    assert "if CurStep = ssPostInstall then" in installer


def test_voxnote_palette_is_applied_to_the_interface() -> None:
    for color in ("#111111", "#2b2b2b", "#d9d9d6", "#f5f5f3", "#3b82f6"):
        assert color in STYLE
