import json
from pathlib import Path

import pytest

from vidskim.errors import VidSkimError
from vidskim.models import Segment, Transcript
from vidskim.render import render_summary, write_summary


@pytest.fixture
def transcript():
    return Transcript(
        title="省时间的方法",
        source="https://www.douyin.com/video/123",
        duration=100,
        language="zh",
        segments=[Segment(7, 65.5, 75, "先确定目标。"), Segment(9, 90, 100, "再选择方法。")],
    )


@pytest.fixture
def payload():
    return {
        "overview": "确定目标后选择方法。",
        "points": [{"text": "目标先于方法。", "segment_ids": [9, 7, 7]}],
        "body": "目标帮助我们筛选方法。\n\n执行时保留必要反馈。",
    }


def input_files(tmp_path, transcript, payload):
    transcript_path = tmp_path / "transcript.json"
    summary_input = tmp_path / "ai-summary.json"
    transcript_path.write_text(
        json.dumps(transcript.to_dict(), ensure_ascii=False), encoding="utf-8"
    )
    summary_input.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return transcript_path, summary_input


def test_summary_renders_fixed_sections_and_real_timestamps(transcript, payload):
    result = render_summary(transcript, payload)
    assert [line for line in result.splitlines() if line.startswith("## ")] == [
        "## 一句话看懂",
        "## 核心精华",
        "## 精简正文",
    ]
    assert "- 目标先于方法。（01:05、01:30）" in result
    assert "目标帮助我们筛选方法。\n\n执行时保留必要反馈。" in result


def test_long_content_can_have_one_point_without_forced_padding(transcript, payload):
    transcript.duration = 5000
    assert "目标先于方法" in render_summary(transcript, payload)


@pytest.mark.parametrize("ids", [[], [999], [7, 999], ["7"], [True], None])
def test_invalid_segment_ids_are_rejected(transcript, payload, ids):
    payload["points"][0]["segment_ids"] = ids
    with pytest.raises(VidSkimError, match="segment_ids"):
        render_summary(transcript, payload)


@pytest.mark.parametrize(
    "key,value", [("overview", ""), ("overview", 1), ("body", " "), ("body", None)]
)
def test_empty_or_wrong_type_text_is_rejected(transcript, payload, key, value):
    payload[key] = value
    with pytest.raises(VidSkimError, match="非空字符串"):
        render_summary(transcript, payload)


@pytest.mark.parametrize(
    "points", [[], None, [{"text": "空引用"}], [{"text": "", "segment_ids": [7]}]]
)
def test_invalid_points_are_rejected(transcript, payload, points):
    payload["points"] = points
    with pytest.raises(VidSkimError):
        render_summary(transcript, payload)


def test_more_than_five_points_is_rejected(transcript, payload):
    payload["points"] *= 6
    with pytest.raises(VidSkimError, match="1—5"):
        render_summary(transcript, payload)


@pytest.mark.parametrize("duration", [-1, float("nan"), float("inf"), True, "100"])
def test_invalid_duration_is_rejected(transcript, payload, duration):
    transcript.duration = duration
    with pytest.raises(VidSkimError, match="时长"):
        render_summary(transcript, payload)


@pytest.mark.parametrize(
    "segments",
    [
        [],
        [Segment(True, 0, 1, "文本")],
        [Segment(-1, 0, 1, "文本")],
        [Segment(7, 0, 1, "甲"), Segment(7, 1, 2, "乙")],
        [Segment(7, -1, 1, "文本")],
        [Segment(7, 10, 5, "文本")],
        [Segment(7, 90, 101, "文本")],
        [Segment(7, float("nan"), 1, "文本")],
        [Segment(7, 0, 1, " ")],
    ],
)
def test_invalid_transcript_segments_are_rejected(transcript, payload, segments):
    transcript.segments = segments
    with pytest.raises(VidSkimError):
        render_summary(transcript, payload)


def test_model_text_cannot_add_extra_sections_or_html(transcript, payload):
    payload["body"] = "## 额外标题\n<script>文本</script>"
    result = render_summary(transcript, payload)
    assert len([line for line in result.splitlines() if line.startswith("## ")]) == 3
    assert "<script>" not in result


def test_default_save_preserves_inputs_and_links_original(tmp_path, transcript, payload):
    transcript_path, summary_input = input_files(tmp_path, transcript, payload)
    original = tmp_path / "transcript.md"
    original.write_text("识别原稿", encoding="utf-8")
    before = {path: path.read_bytes() for path in (transcript_path, summary_input, original)}

    target = write_summary(transcript_path, summary_input)

    assert target == tmp_path / "summary.md"
    text = target.read_text(encoding="utf-8")
    assert text.startswith("# 省时间的方法\n")
    assert "(transcript.md)" in text
    assert all(path.read_bytes() == content for path, content in before.items())


def test_explicit_output_directory_links_back_to_json_if_no_original(tmp_path, transcript, payload):
    transcript_path, summary_input = input_files(tmp_path, transcript, payload)
    output = tmp_path / "notes" / "精华.md"
    assert write_summary(transcript_path, summary_input, output) == output
    assert "(../transcript.json)" in output.read_text(encoding="utf-8")


def test_cross_drive_output_uses_absolute_original_link(monkeypatch, tmp_path, transcript, payload):
    transcript_path, summary_input = input_files(tmp_path, transcript, payload)
    original = tmp_path / "transcript.md"
    original.write_text("识别原稿", encoding="utf-8")

    def different_drives(path, start):
        raise ValueError("path is on a different drive")

    monkeypatch.setattr("vidskim.render.os.path.relpath", different_drives)
    output = tmp_path / "notes" / "精华.md"
    assert write_summary(transcript_path, summary_input, output) == output
    assert f"({original.as_uri()})" in output.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "filename", ["transcript.json", "ai-summary.json", "transcript.md", "another.json"]
)
def test_save_refuses_to_overwrite_materials(tmp_path, transcript, payload, filename):
    transcript_path, summary_input = input_files(tmp_path, transcript, payload)
    output = tmp_path / filename
    if not output.exists():
        output.write_text("原始内容", encoding="utf-8")
    before = output.read_bytes()
    with pytest.raises(VidSkimError, match="不能覆盖"):
        write_summary(transcript_path, summary_input, output)
    assert output.read_bytes() == before


def test_save_refuses_local_source_collision(tmp_path, transcript, payload):
    source = tmp_path / "source.md"
    source.write_text("本地源内容", encoding="utf-8")
    transcript.source = str(source)
    transcript_path, summary_input = input_files(tmp_path, transcript, payload)
    with pytest.raises(VidSkimError, match="不能覆盖"):
        write_summary(transcript_path, summary_input, source)
    assert source.read_text(encoding="utf-8") == "本地源内容"


def test_symlink_to_original_is_protected(tmp_path, transcript, payload):
    transcript_path, summary_input = input_files(tmp_path, transcript, payload)
    original = tmp_path / "transcript.md"
    original.write_text("原稿", encoding="utf-8")
    alias = tmp_path / "alias.md"
    alias.symlink_to(original)
    with pytest.raises(VidSkimError, match="不能覆盖"):
        write_summary(transcript_path, summary_input, alias)
    assert original.read_text(encoding="utf-8") == "原稿"


def test_atomic_replace_failure_preserves_existing_summary(
    monkeypatch, tmp_path, transcript, payload
):
    transcript_path, summary_input = input_files(tmp_path, transcript, payload)
    target = tmp_path / "summary.md"
    target.write_text("已有精华", encoding="utf-8")

    def fail_replace(self, destination):
        raise OSError("磁盘写入失败")

    monkeypatch.setattr(Path, "replace", fail_replace)
    with pytest.raises(VidSkimError, match="无法保存"):
        write_summary(transcript_path, summary_input)
    assert target.read_text(encoding="utf-8") == "已有精华"
    assert list(tmp_path.glob(".summary.md.*")) == []


def test_bad_json_is_a_friendly_error(tmp_path, transcript, payload):
    transcript_path, summary_input = input_files(tmp_path, transcript, payload)
    summary_input.write_text("not JSON", encoding="utf-8")
    with pytest.raises(VidSkimError, match="有效的 UTF-8 JSON"):
        write_summary(transcript_path, summary_input)
    assert not (tmp_path / "summary.md").exists()


def test_bad_transcript_schema_is_a_friendly_error(tmp_path, transcript, payload):
    transcript_path, summary_input = input_files(tmp_path, transcript, payload)
    transcript_path.write_text('{"segments": []}', encoding="utf-8")
    with pytest.raises(VidSkimError, match="字段不完整"):
        write_summary(transcript_path, summary_input)
