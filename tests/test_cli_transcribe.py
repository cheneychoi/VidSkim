import io
import json
from contextlib import nullcontext, redirect_stderr, redirect_stdout
from types import SimpleNamespace

import av
import pytest

from watch2note import __version__, cli, pipeline, transcribe
from watch2note.errors import Watch2NoteError
from watch2note.models import Settings


def test_cli_displays_new_name_in_version_and_help(capsys):
    with pytest.raises(SystemExit) as result:
        cli.main(["--version"])
    assert result.value.code == 0
    assert capsys.readouterr().out.strip() == f"Watch2Note {__version__}"

    with pytest.raises(SystemExit) as result:
        cli.main(["--help"])
    assert result.value.code == 0
    help_text = capsys.readouterr().out
    assert "usage: watch2note" in help_text
    assert "watch2note setup --codex" in help_text
    assert "watch2note setup --claude" in help_text


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
        raise Watch2NoteError("语音识别失败")

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
    with pytest.raises(Watch2NoteError, match="未识别到语音"):
        transcribe.transcribe(tmp_path / "video.mp4", "title", "source", Settings(), lambda _: None)


def test_short_transcription_reports_stages_and_first_segment(monkeypatch, tmp_path):
    monkeypatch.setattr(
        av, "open", lambda _: nullcontext(SimpleNamespace(duration=20 * av.time_base))
    )
    messages = []

    def segments():
        yield SimpleNamespace(start=0.0, end=5.0, text="第一段")
        assert any("00:05 / 00:20" in message for message in messages)
        yield SimpleNamespace(start=5.0, end=18.0, text="最后一段")

    model = SimpleNamespace(
        transcribe=lambda *args, **kwargs: (
            segments(), SimpleNamespace(duration=20.0, language="zh")
        )
    )
    monkeypatch.setattr(transcribe, "prepare_model", lambda _: model)
    transcribe.transcribe(tmp_path / "video.mp4", "title", "source", Settings(), messages.append)
    expected = ["媒体时长", "加载语音模型", "模型已就绪", "解码音频", "开始转写", "转写完成"]
    positions = [next(i for i, text in enumerate(messages) if label in text) for label in expected]
    assert positions == sorted(positions)
    assert any("25%" in text and "已耗时" in text for text in messages)
    assert any("2 段" in text and "转写完成" in text for text in messages)


def test_transcription_failure_does_not_report_completion(monkeypatch, tmp_path):
    monkeypatch.setattr(
        av, "open", lambda _: nullcontext(SimpleNamespace(duration=20 * av.time_base))
    )

    def segments():
        yield SimpleNamespace(start=0.0, end=5.0, text="第一段")
        raise RuntimeError("decoder failed")

    model = SimpleNamespace(
        transcribe=lambda *args, **kwargs: (
            segments(), SimpleNamespace(duration=20.0, language="zh")
        )
    )
    monkeypatch.setattr(transcribe, "prepare_model", lambda _: model)
    messages = []
    with pytest.raises(Watch2NoteError, match="音视频识别失败"):
        transcribe.transcribe(
            tmp_path / "video.mp4", "title", "source", Settings(), messages.append
        )
    assert any("00:05 / 00:20" in text for text in messages)
    assert not any("转写完成" in text for text in messages)
