import json
from pathlib import Path
from types import SimpleNamespace

import faster_whisper
import faster_whisper.utils
import pytest
from faster_whisper.feature_extractor import FeatureExtractor
from huggingface_hub.errors import LocalEntryNotFoundError

from watch2note.errors import Watch2NoteError
from watch2note.models import Settings
from watch2note.transcribe import prepare_model


@pytest.fixture
def model_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("WATCH2NOTE_CACHE_DIR", str(tmp_path / "cache"))
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    for filename in ("model.bin", "config.json", "tokenizer.json", "vocabulary.txt"):
        (snapshot / filename).write_bytes(b"model data")
    loaded = []
    model = SimpleNamespace(
        model=SimpleNamespace(n_mels=80),
        feature_extractor=SimpleNamespace(mel_filters=SimpleNamespace(shape=(80, 201))),
    )

    def load(path, **kwargs):
        loaded.append((path, kwargs))
        return model

    monkeypatch.setattr(faster_whisper, "WhisperModel", load)
    return snapshot, loaded, model


@pytest.mark.parametrize("vocabulary", ["vocabulary.txt", "vocabulary.json"])
def test_complete_cache_is_loaded_without_network(model_cache, monkeypatch, vocabulary):
    snapshot, loaded, model = model_cache
    (snapshot / "vocabulary.txt").rename(snapshot / vocabulary)
    requests = []

    def download(name, **kwargs):
        requests.append((name, kwargs))
        assert kwargs["local_files_only"] is True
        return str(snapshot)

    monkeypatch.setattr(faster_whisper.utils, "download_model", download)
    assert prepare_model(Settings()) is model
    assert len(requests) == 1
    assert loaded[0][0] == str(snapshot)
    assert loaded[0][1]["device"] == "cpu"
    assert loaded[0][1]["compute_type"] == "int8"
    assert loaded[0][1]["cpu_threads"] <= 8


def test_absent_cache_downloads_model_once(model_cache, monkeypatch):
    snapshot, loaded, model = model_cache
    requests = []

    def download(name, **kwargs):
        requests.append(kwargs["local_files_only"])
        if kwargs["local_files_only"]:
            raise LocalEntryNotFoundError("no cached snapshot")
        return str(snapshot)

    monkeypatch.setattr(faster_whisper.utils, "download_model", download)
    assert prepare_model(Settings()) is model
    assert requests == [True, False]
    assert loaded[0][0] == str(snapshot)


@pytest.mark.parametrize(
    "missing", ["model.bin", "config.json", "tokenizer.json", "vocabulary.txt"]
)
def test_partial_cache_is_completed_before_loading(model_cache, monkeypatch, missing):
    snapshot, loaded, model = model_cache
    (snapshot / missing).unlink()
    requests = []

    def download(name, **kwargs):
        requests.append(kwargs["local_files_only"])
        if not kwargs["local_files_only"]:
            (snapshot / missing).write_bytes(b"downloaded data")
        return str(snapshot)

    monkeypatch.setattr(faster_whisper.utils, "download_model", download)
    assert prepare_model(Settings()) is model
    assert requests == [True, False]
    assert Path(loaded[0][0], missing).is_file()


def test_empty_model_file_requires_download(model_cache, monkeypatch):
    snapshot, _, model = model_cache
    (snapshot / "model.bin").write_bytes(b"")
    requests = []

    def download(name, **kwargs):
        requests.append(kwargs["local_files_only"])
        if not kwargs["local_files_only"]:
            (snapshot / "model.bin").write_bytes(b"downloaded model")
        return str(snapshot)

    monkeypatch.setattr(faster_whisper.utils, "download_model", download)
    assert prepare_model(Settings()) is model
    assert requests == [True, False]


def test_user_model_directory_keeps_existing_load_behavior(model_cache, monkeypatch):
    snapshot, loaded, model = model_cache

    def unexpected_download(*args, **kwargs):
        pytest.fail("user model directory must not resolve a Hub model")

    monkeypatch.setattr(faster_whisper.utils, "download_model", unexpected_download)
    assert prepare_model(Settings(asr_model=str(snapshot))) is model
    assert loaded[0][0] == str(snapshot)


def test_download_failure_remains_actionable(model_cache, monkeypatch):
    def download(name, **kwargs):
        if kwargs["local_files_only"]:
            raise LocalEntryNotFoundError("no cached snapshot")
        raise OSError("network unavailable")

    monkeypatch.setattr(faster_whisper.utils, "download_model", download)
    with pytest.raises(Watch2NoteError, match="识别模型准备失败"):
        prepare_model(Settings())


@pytest.mark.parametrize("name", ["large-v3", "large-v3-turbo", "example/custom-whisper"])
def test_missing_required_preprocessor_is_downloaded(model_cache, monkeypatch, name):
    snapshot, _, _ = model_cache
    requests, loaded = [], []

    def download(model_name, **kwargs):
        assert model_name == name
        requests.append(kwargs["local_files_only"])
        if not kwargs["local_files_only"]:
            (snapshot / "preprocessor_config.json").write_text('{"feature_size": 128}')
        return str(snapshot)

    def load(path, **kwargs):
        config = Path(path, "preprocessor_config.json")
        features = json.loads(config.read_text()) if config.is_file() else {}
        model = SimpleNamespace(
            model=SimpleNamespace(n_mels=128),
            feature_extractor=FeatureExtractor(**features),
        )
        loaded.append(model.feature_extractor.mel_filters.shape[0])
        return model

    monkeypatch.setattr(faster_whisper.utils, "download_model", download)
    monkeypatch.setattr(faster_whisper, "WhisperModel", load)
    model = prepare_model(Settings(asr_model=name))
    assert requests == [True, False]
    assert loaded == [80, 128]
    assert model.model.n_mels == model.feature_extractor.mel_filters.shape[0]


def test_complete_128_mel_model_does_not_download(model_cache, monkeypatch):
    snapshot, _, model = model_cache
    (snapshot / "preprocessor_config.json").write_text('{"feature_size": 128}')
    model.model.n_mels = 128
    model.feature_extractor = FeatureExtractor(feature_size=128)

    def download(name, **kwargs):
        assert kwargs["local_files_only"] is True
        return str(snapshot)

    monkeypatch.setattr(faster_whisper.utils, "download_model", download)
    assert prepare_model(Settings(asr_model="example/custom-whisper")) is model


def test_unrepairable_preprocessor_mismatch_is_reported(model_cache, monkeypatch):
    snapshot, _, model = model_cache
    model.model.n_mels = 128
    requests = []

    def download(name, **kwargs):
        requests.append(kwargs["local_files_only"])
        return str(snapshot)

    monkeypatch.setattr(faster_whisper.utils, "download_model", download)
    with pytest.raises(Watch2NoteError, match="识别模型准备失败"):
        prepare_model(Settings(asr_model="example/custom-whisper"))
    assert requests == [True, False]
