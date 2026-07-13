from __future__ import annotations

import logging
from collections.abc import Sequence

import requests  # type: ignore[import-untyped]
from PySide6.QtCore import QObject, Signal, Slot

from transcritor import __version__

LOG = logging.getLogger(__name__)
LATEST_RELEASE_URL = "https://api.github.com/repos/Marcosemanuel/voxnote/releases/latest"


def version_key(value: str) -> tuple[int, ...] | None:
    """Parse stable semantic versions such as v0.1.0 without external dependencies."""
    try:
        parts: Sequence[str] = value.strip().removeprefix("v").split("-")[0].split(".")
        if not parts or any(not part.isdigit() for part in parts):
            return None
        return tuple(int(part) for part in parts)
    except (AttributeError, ValueError):
        return None


def is_newer_version(current: str, candidate: str) -> bool:
    current_key = version_key(current)
    candidate_key = version_key(candidate)
    if current_key is None or candidate_key is None:
        return False
    width = max(len(current_key), len(candidate_key))
    return current_key + (0,) * (width - len(current_key)) < candidate_key + (0,) * (width - len(candidate_key))


class UpdateCheckWorker(QObject):
    update_available = Signal(str, str)
    finished = Signal()

    @Slot()
    def run(self) -> None:
        try:
            response = requests.get(
                LATEST_RELEASE_URL,
                headers={"Accept": "application/vnd.github+json", "User-Agent": "Voxnote"},
                timeout=(2, 5),
            )
            if response.status_code != 200:
                return
            payload = response.json()
            version = str(payload.get("tag_name", ""))
            release_url = str(payload.get("html_url", ""))
            if release_url and is_newer_version(__version__, version):
                self.update_available.emit(version.removeprefix("v"), release_url)
        except (requests.RequestException, TypeError, ValueError) as exc:
            LOG.info("Update check unavailable: %s", exc)
        finally:
            self.finished.emit()
