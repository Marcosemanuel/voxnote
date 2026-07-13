from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AppPaths:
    root: Path
    data: Path
    models: Path
    logs: Path
    cache: Path
    exports: Path

    @classmethod
    def resolve(cls, override: Path | None = None) -> AppPaths:
        root = override or Path(os.environ.get("LOCALAPPDATA", Path.home())) / "Transcritor"
        value = cls(
            root=root,
            data=root / "data",
            models=root / "models",
            logs=root / "logs",
            cache=root / "cache",
            exports=Path.home() / "Documents" / "Transcrições",
        )
        for folder in (value.root, value.data, value.models, value.logs, value.cache, value.exports):
            folder.mkdir(parents=True, exist_ok=True)
        return value
