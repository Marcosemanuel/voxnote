from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontDatabase, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtWidgets import QApplication

from transcritor.database import Database
from transcritor.paths import AppPaths
from transcritor.resources import bundled_path
from transcritor.ui import STYLE, MainWindow, configure_logging


def register_manrope() -> str:
    """Register the bundled Manrope variable font for the current Qt process."""
    font_path = bundled_path("assets/fonts/Manrope-Variable.ttf")
    font_id = QFontDatabase.addApplicationFont(str(font_path))
    if font_id < 0:
        raise RuntimeError(f"Não foi possível carregar a fonte da interface: {font_path}")
    families = QFontDatabase.applicationFontFamilies(font_id)
    if "Manrope" not in families:
        raise RuntimeError("A fonte embutida não expôs a família Manrope.")
    return "Manrope"


def main() -> int:
    paths = AppPaths.resolve()
    configure_logging(paths)
    app = QApplication(sys.argv)
    app.setApplicationName("Voxnote")
    app.setOrganizationName("Voxnote")
    app_font = QFont(register_manrope())
    app_font.setPixelSize(16)
    app_font.setWeight(QFont.Weight.Normal)
    app.setFont(app_font)
    app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
    app.setWindowIcon(QIcon(str(bundled_path("assets/branding/voxnote-app-icon.ico"))))

    if os.environ.get("VOXNOTE_LEGACY_UI") == "1":
        app.setStyle("Fusion")
        app.setStyleSheet(STYLE)
        window = MainWindow(
            paths,
            Database(paths.data / "transcritor.db"),
            bundled_path("assets/branding/voxnote-symbol.png"),
        )
        window.show()
        return app.exec()

    from transcritor.qml_controller import QmlController

    qml_root = (
        bundled_path("qml") if getattr(sys, "_MEIPASS", None) is not None else Path(__file__).resolve().parent / "qml"
    )
    QQuickStyle.setStyle("Basic")
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_root))
    controller = QmlController(paths, Database(paths.data / "transcritor.db"))
    engine.rootContext().setContextProperty("backend", controller)
    engine.load(str(qml_root / "Main.qml"))
    if not engine.rootObjects():
        return 1
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
