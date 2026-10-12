from pathlib import Path

from watch2note import config


def test_default_cache_uses_watch2note_directory(tmp_path, monkeypatch):
    monkeypatch.delenv("WATCH2NOTE_CACHE_DIR", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    assert config.cache_dir() == tmp_path / ".cache" / "watch2note"


def test_watch2note_environment_configures_cache_and_transcription(tmp_path, monkeypatch):
    monkeypatch.setenv("WATCH2NOTE_CACHE_DIR", str(tmp_path / "custom-cache"))
    monkeypatch.setenv("WATCH2NOTE_ASR_MODEL", "base")
    monkeypatch.setenv("WATCH2NOTE_LANGUAGE", "zh")
    assert config.cache_dir() == tmp_path / "custom-cache"
    settings = config.load_settings()
    assert settings.asr_model == "base"
    assert settings.language == "zh"
