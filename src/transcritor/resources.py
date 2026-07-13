from __future__ import annotations

import sys
from pathlib import Path


def bundled_path(relative_path: str) -> Path:
    """Resolve a project asset in development and in the PyInstaller bundle."""
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root is not None:
        return Path(str(bundle_root)) / relative_path
    return Path(__file__).resolve().parents[2] / relative_path
