import json
import os
import time
from pathlib import Path

import pytest

from vidskim import pipeline
from vidskim.errors import VidSkimError
from vidskim.models import Segment, Settings, Transcript


@pytest.fixture
def environment(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("VIDSKIM_CACHE_DIR", str(tmp_path / "cache"))
    video = tmp_path / "video.mp4"
    video.write_bytes(b"original video bytes")
    calls = []

    def fake_transcribe(path, title, source, settings, progress):
        calls.append((path, settings.asr_model))
        return Transcript(
            title,
            source,
            1800,
            "zh",
            [Segment(0, 0, 10, "开头观点"), Segment(1, 1790, 1800, "后半段的关键例外")],
        )

    monkeypatch.setattr(pipeline, "transcribe", fake_transcribe)
    return tmp_path, video, calls


def test_extraction_preserves_complete_material_and_reuses_cache(environment):
    _, video, calls = environment
    first = pipeline.extract(str(video), Settings(), lambda _: None)
    material = Path(first["transcript_json"])
    data = json.loads(material.read_text(encoding="utf-8"))
    assert data["segments"][-1]["text"] == "后半段的关键例外"
    assert first["segment_count"] == 2
    assert not Path(first["summary_output"]).exists()
    assert material.is_absolute()
    assert "29:50" in Path(first["transcript_md"]).read_text(encoding="utf-8")
    second = pipeline.extract(str(video), Settings(), lambda _: None)
    assert second == first
    assert len(calls) == 1


def test_changed_media_and_model_invalidate_cache(environment):
    _, video, calls = environment
    first = pipeline.extract(str(video), Settings(), lambda _: None)
    video.write_bytes(b"different video bytes")
    second = pipeline.extract(str(video), Settings(), lambda _: None)
    third = pipeline.extract(str(video), Settings(asr_model="tiny"), lambda _: None)
    assert len(calls) == 3
    assert len({first["transcript_json"], second["transcript_json"], third["transcript_json"]}) == 3


def test_broken_cache_is_rebuilt(environment):
    root, video, calls = environment
    pipeline.extract(str(video), Settings(), lambda _: None)
    cached = next((root / "cache" / "jobs").glob("*/transcript.json"))
    cached.write_text("{broken", encoding="utf-8")
    pipeline.extract(str(video), Settings(), lambda _: None)
    assert len(calls) == 2


@pytest.mark.parametrize("damage", ["empty", "invalid-time", "wrong-source"])
def test_invalid_cached_transcript_is_rebuilt(environment, damage):
    root, video, calls = environment
    pipeline.extract(str(video), Settings(), lambda _: None)
    cached = next((root / "cache" / "jobs").glob("*/transcript.json"))
    data = json.loads(cached.read_text(encoding="utf-8"))
    if damage == "empty":
        data["segments"] = []
    elif damage == "invalid-time":
        data["segments"][0]["start"] = "broken-time"
    else:
        data["source"] = "another.mp4"
    cached.write_text(json.dumps(data), encoding="utf-8")
    result = pipeline.extract(str(video), Settings(), lambda _: None)
    assert len(calls) == 2
    assert result["segment_count"] == 2


def test_missing_file_is_actionable(environment):
    with pytest.raises(VidSkimError, match="不存在"):
        pipeline.extract("missing.mp4", Settings(), lambda _: None)


def test_long_share_text_does_not_attempt_to_stat_a_filename(environment, monkeypatch):
    from vidskim import douyin

    def resolve(value):
        raise VidSkimError("解析已执行")

    monkeypatch.setattr(douyin, "resolve_input", resolve)
    with pytest.raises(VidSkimError, match="解析已执行"):
        pipeline.extract(
            "很长的分享文案" * 100 + " https://v.douyin.com/example/", Settings(), lambda _: None
        )


def test_cache_retention_is_bounded(tmp_path):
    active = tmp_path / "active"
    active.mkdir()
    for index in range(25):
        entry = tmp_path / str(index)
        entry.mkdir()
        os.utime(entry, (time.time() - index, time.time() - index))
    expired = tmp_path / "expired"
    expired.mkdir()
    os.utime(expired, (0, 0))
    pipeline.prune_cache(tmp_path, active)
    assert active.exists()
    assert not expired.exists()
    assert len(list(tmp_path.iterdir())) == 20
