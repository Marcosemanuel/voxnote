from __future__ import annotations

import platform
import subprocess

import psutil

from transcritor.domain import HardwareProfile


def _nvidia_info() -> tuple[str | None, float | None]:
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=4,
            check=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        first_line = result.stdout.strip().splitlines()[0]
        name, memory = (part.strip() for part in first_line.rsplit(",", 1))
        return name or None, float(memory) / 1024
    except (OSError, subprocess.SubprocessError, IndexError, ValueError):
        return None, None


def _cuda_compatible() -> bool:
    try:
        import ctranslate2

        return bool(ctranslate2.get_supported_compute_types("cuda"))
    except Exception:
        return False


def detect_hardware() -> HardwareProfile:
    ram_gb = psutil.virtual_memory().total / (1024**3)
    gpu, vram_gb = _nvidia_info()
    cuda_compatible = bool(gpu and _cuda_compatible())
    if cuda_compatible and vram_gb is not None and vram_gb >= 6 and ram_gb >= 12:
        recommendation = "Alta precisão"
    elif ram_gb >= 16:
        recommendation = "Equilibrada"
    else:
        recommendation = "Leve"
    return HardwareProfile(
        cpu=platform.processor() or "Processador x64",
        logical_cpus=psutil.cpu_count(logical=True) or 1,
        ram_gb=ram_gb,
        gpu_name=gpu,
        gpu_vram_gb=vram_gb,
        cuda_compatible=cuda_compatible,
        recommended_profile=recommendation,
    )
