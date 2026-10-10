import io
import json
from contextlib import nullcontext, redirect_stderr, redirect_stdout
from types import SimpleNamespace

import av
import pytest

from vidskim import cli, pipeline, transcribe
from vidskim.errors import VidSkimError
from vidskim.models import Settings


def test_cli_metadata_stdout_and_progress_stderr(monkeypatch, capsys):
    def extract(value, settings, progress):
        progress("阶段进度")
        return {"transcript_json": "/tmp/transcript.json", "duration_seconds": 30}

    monkeypatch.setattr(pipeline, "extract", extract)
    assert cli.main(["video.mp4"]) == 0
    output = capsys.readouterr()
    assert json.loads(output.out)["duration_seconds"] == 30
    assert "阶段进度" in output.err


def test_cli_uses_utf8_for_redirected_chinese_output(monkeypatch):
    def extract(value, settings, progress):
        progress("阶段进度")
        return {"transcript_json": "中文目录/transcript.json"}

    monkeypatch.setattr(pipeline, "extract", extract)
    out, err = io.BytesIO(), io.BytesIO()
    stdout = io.TextIOWrapper(out, encoding="cp1252")
    stderr = io.TextIOWrapper(err, encoding="cp1252")
    with redirect_stdout(stdout), redirect_stderr(stderr):
        assert cli.main(["video.mp4"]) == 0
    stdout.flush()
    stderr.flush()
    result = json.loads(out.getvalue().decode("utf-8"))
    assert result["transcript_json"] == "中文目录/transcript.json"
    assert "阶段进度" in err.getvalue().decode("utf-8")


def test_cli_failed_extraction_returns_no_success_json(monkeypatch, capsys):
    def extract(*args):
        raise VidSkimError("语音识别失败")

    monkeypatch.setattr(pipeline, "extract", extract)
    assert cli.main(["video.mp4"]) == 1
    output = capsys.readouterr()
    assert not output.out
    assert "语音识别失败" in output.err


def test_transcription_consumes_lazy_segments(monkeypatch, tmp_path):
    monkeypatch.setattr(
        av, "open", lambda _: nullcontext(SimpleNamespace(duration=65 * av.time_base))
    )
    seen = []

    def segments():
        seen.append("started")
        yield SimpleNamespace(start=0.1, end=1.2, text=" 第一段 ")
        yield SimpleNamespace(start=62.0, end=64.2, text=" 最后一段 ")
        seen.append("finished")

    model = SimpleNamespace(
        transcribe=lambda *args, **kwargs: (
            segments(),
            SimpleNamespace(duration=65.0, language="zh"),
        )
    )
    monkeypatch.setattr(transcribe, "prepare_model", lambda _: model)
    result = transcribe.transcribe(
        tmp_path / "video.mp4", "title", "source", Settings(), lambda _: None
    )
    assert seen == ["started", "finished"]
    assert [item.id for item in result.segments] == [0, 1]
    assert result.segments[-1].end == 64.2
    assert result.segments[0].text == "第一段"


def test_transcription_rejects_silence(monkeypatch, tmp_path):
    monkeypatch.setattr(
        av, "open", lambda _: nullcontext(SimpleNamespace(duration=20 * av.time_base))
    )
    model = SimpleNamespace(
        transcribe=lambda *args, **kwargs: (iter([]), SimpleNamespace(duration=20.0, language="zh"))
    )
    monkeypatch.setattr(transcribe, "prepare_model", lambda _: model)
    with pytest.raises(VidSkimError, match="未识别到语音"):
        transcribe.transcribe(tmp_path / "video.mp4", "title", "source", Settings(), lambda _: None)
