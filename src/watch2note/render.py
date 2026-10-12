import json
import os
import re
import tempfile
from pathlib import Path
from urllib.parse import quote, urlparse

from .errors import Watch2NoteError
from .models import Transcript, timestamp


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _markdown(text: str) -> str:
    return re.sub(r"([\\`*_{}\[\]<>#!])", r"\\\1", text)


def render_summary(transcript: Transcript, payload: dict) -> str:
    if not isinstance(transcript, Transcript):
        raise Watch2NoteError("转写 JSON 的格式无效，请重新转写。")
    transcript.validate()
    if not isinstance(payload, dict) or not all(
        _text(payload.get(key)) for key in ("overview", "body")
    ):
        raise Watch2NoteError("摘要 JSON 需要非空字符串 overview 和 body。")
    points = payload.get("points")
    if not isinstance(points, list) or not 1 <= len(points) <= 5:
        raise Watch2NoteError("摘要 JSON 的 points 需要 1—5 条核心要点。")
    starts = {segment.id: segment.start for segment in transcript.segments}
    lines = []
    for point in points:
        if not isinstance(point, dict) or not _text(point.get("text")):
            raise Watch2NoteError("摘要的每条核心要点需要非空 text。")
        ids = point.get("segment_ids")
        if (
            not isinstance(ids, list)
            or not ids
            or any(type(segment_id) is not int or segment_id not in starts for segment_id in ids)
        ):
            raise Watch2NoteError("摘要的 segment_ids 必须是原文中存在的整数段落编号，且不能为空。")
        times = "、".join(
            timestamp(start) for start in sorted({starts[segment_id] for segment_id in ids})
        )
        text = _markdown(" ".join(point["text"].split()))
        lines.append(f"- {text}（{times}）")
    overview = _markdown(" ".join(payload["overview"].split()))
    body = _markdown(payload["body"].strip())
    return (
        f"## 一句话看懂\n\n{overview}\n\n## 核心精华\n\n"
        + "\n".join(lines)
        + f"\n\n## 精简正文\n\n{body}\n"
    )


def _read_json(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError:
        raise Watch2NoteError(f"无法读取{label}，请检查文件路径和权限。") from None
    except ValueError:
        raise Watch2NoteError(f"{label}必须是有效的 UTF-8 JSON。") from None
    if not isinstance(value, dict):
        raise Watch2NoteError(f"{label}必须是 JSON 对象。")
    return value


def write_summary(transcript_path: Path, summary_input: Path, output: Path | None = None) -> Path:
    transcript_path = transcript_path.expanduser().resolve()
    summary_input = summary_input.expanduser().resolve()
    data = _read_json(transcript_path, "转写文件")
    try:
        transcript = Transcript.from_dict(data)
    except (KeyError, TypeError, ValueError):
        raise Watch2NoteError("转写 JSON 的字段不完整或格式无效，请重新转写。") from None
    body = render_summary(transcript, _read_json(summary_input, "摘要文件"))
    target = (output or transcript_path.with_name("summary.md")).expanduser().resolve()
    original = transcript_path.with_name("transcript.md")
    protected = {transcript_path, summary_input, original.resolve()}
    if urlparse(transcript.source).scheme not in {"http", "https"}:
        source = Path(transcript.source).expanduser()
        protected.add(source.resolve())
        protected.add((transcript_path.parent / source).resolve())
    if target in protected or target.suffix.lower() != ".md":
        raise Watch2NoteError("摘要应保存为 .md 文件，且不能覆盖音视频、识别原稿或输入 JSON。")
    original = original if original.is_file() else transcript_path
    try:
        original_link = quote(Path(os.path.relpath(original, target.parent)).as_posix(), safe="/")
    except ValueError:
        original_link = original.resolve().as_uri()
    title = _markdown(" ".join(transcript.title.split()))
    source_text = _markdown(" ".join(transcript.source.split()))
    result = (
        f"# {title}\n\n来源：{source_text}\n\n原视频时长：{timestamp(transcript.duration)}\n\n"
        f"{body}\n---\n\n[查看带时间戳的识别原稿]({original_link})\n"
    )
    temporary = None
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=target.parent, prefix=f".{target.name}.", delete=False
        ) as file:
            temporary = Path(file.name)
            file.write(result)
        temporary.replace(target)
    except OSError:
        raise Watch2NoteError("无法保存摘要，请检查输出路径、权限和剩余空间。") from None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return target
