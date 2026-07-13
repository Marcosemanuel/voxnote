from __future__ import annotations

from pathlib import Path

import av

from transcritor.domain import SUPPORTED_EXTENSIONS, AudioInfo


class AudioValidationError(ValueError):
    pass


def inspect_audio(path: Path) -> AudioInfo:
    if not path.is_file():
        raise AudioValidationError("O arquivo não foi encontrado. Localize-o e tente novamente.")
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise AudioValidationError("Este formato não é compatível com o aplicativo.")
    try:
        with av.open(str(path)) as container:
            streams = [stream for stream in container.streams if stream.type == "audio"]
            if not streams:
                raise AudioValidationError("O arquivo não contém uma faixa de áudio reconhecível.")
            stream = streams[0]
            duration = 0.0
            if stream.duration is not None and stream.time_base is not None:
                duration = float(stream.duration * stream.time_base)
            elif container.duration is not None:
                duration = float(container.duration / av.time_base)
            if duration <= 0:
                raise AudioValidationError("Não foi possível determinar a duração do áudio.")
            iterator = container.decode(stream)
            next(iterator, None)
            return AudioInfo(path, duration, container.format.name or path.suffix[1:], path.stat().st_size)
    except AudioValidationError:
        raise
    except (OSError, ValueError) as exc:
        raise AudioValidationError(
            "Não foi possível ler este áudio. O arquivo pode estar incompleto ou corrompido."
        ) from exc
    raise AudioValidationError("Não foi possível validar o áudio.")
