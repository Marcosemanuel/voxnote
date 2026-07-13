from __future__ import annotations

import hashlib
import json
import os
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path

from faster_whisper.utils import download_model

from transcritor.domain import MODEL_PROFILES


@dataclass(frozen=True, slots=True)
class ModelState:
    label: str
    model_name: str
    installed: bool
    size_bytes: int


class ModelManager:
    integrity_filename = ".voxnote-integrity.json"

    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def path_for(self, model_name: str) -> Path:
        return self.root / model_name

    def is_valid(self, model_name: str) -> bool:
        folder = self.path_for(model_name)
        manifest_path = folder / self.integrity_filename
        if (
            not (folder / "model.bin").is_file()
            or not (folder / "config.json").is_file()
            or not manifest_path.is_file()
        ):
            return False
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            files = manifest["files"]
            return (
                isinstance(files, dict)
                and bool(files)
                and all(
                    self._sha256(folder / relative_path) == expected_hash
                    for relative_path, expected_hash in files.items()
                )
            )
        except (KeyError, OSError, TypeError, ValueError):
            return False

    def resolve(self, model_name: str) -> str:
        path = self.path_for(model_name)
        return str(path) if self.is_valid(model_name) else model_name

    def download(self, model_name: str) -> Path:
        destination = self.path_for(model_name)
        if self.is_valid(model_name):
            return destination
        temporary = self.root / f".{model_name}.downloading-{uuid.uuid4().hex}"
        try:
            download_model(model_name, output_dir=str(temporary))
            self._write_manifest(temporary)
            if destination.exists():
                shutil.rmtree(destination)
            os.replace(temporary, destination)
            if not self.is_valid(model_name):
                raise RuntimeError("O modelo baixado não passou na verificação de integridade.")
            return destination
        finally:
            if temporary.exists():
                shutil.rmtree(temporary, ignore_errors=True)

    def _write_manifest(self, folder: Path) -> None:
        required = (folder / "model.bin", folder / "config.json")
        if not all(path.is_file() for path in required):
            raise RuntimeError("O download do modelo está incompleto.")
        files = {
            str(path.relative_to(folder)).replace("\\", "/"): self._sha256(path)
            for path in folder.rglob("*")
            if path.is_file() and path.name != self.integrity_filename
        }
        (folder / self.integrity_filename).write_text(
            json.dumps({"version": 1, "files": files}, indent=2, sort_keys=True), encoding="utf-8"
        )

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def remove(self, model_name: str) -> None:
        path = self.path_for(model_name)
        if path.exists():
            shutil.rmtree(path)

    def states(self) -> list[ModelState]:
        values: list[ModelState] = []
        for label, model_name in MODEL_PROFILES.items():
            folder = self.path_for(model_name)
            size = sum(file.stat().st_size for file in folder.rglob("*") if file.is_file()) if folder.exists() else 0
            values.append(ModelState(label, model_name, self.is_valid(model_name), size))
        return values
