import os
from pathlib import Path

from .models import Settings


def cache_dir() -> Path:
    return Path(os.environ.get("WATCH2NOTE_CACHE_DIR", Path.home() / ".cache" / "watch2note"))


def load_settings() -> Settings:
    return Settings(
        asr_model=os.environ.get("WATCH2NOTE_ASR_MODEL", "small"),
        language=os.environ.get("WATCH2NOTE_LANGUAGE") or None,
    )
