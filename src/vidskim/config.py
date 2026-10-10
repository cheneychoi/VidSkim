import os
from pathlib import Path

from .models import Settings


def cache_dir() -> Path:
    return Path(os.environ.get("VIDSKIM_CACHE_DIR", Path.home() / ".cache" / "vidskim"))


def load_settings() -> Settings:
    return Settings(
        asr_model=os.environ.get("VIDSKIM_ASR_MODEL", "small"),
        language=os.environ.get("VIDSKIM_LANGUAGE") or None,
    )
