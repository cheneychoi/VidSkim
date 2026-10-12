import hashlib
import json
import os
import re
import time
from pathlib import Path
from typing import Callable

from .config import cache_dir
from .errors import Watch2NoteError
from .models import Settings, Transcript, timestamp
from .progress import ProgressStage
from .transcribe import transcribe


def prune_cache(jobs: Path, active: Path) -> None:
    import shutil

    entries = sorted(
        (
            entry
            for entry in jobs.iterdir()
            if entry.is_dir() and not entry.is_symlink() and entry != active
        ),
        key=lambda entry: entry.stat().st_mtime,
        reverse=True,
    )
    cutoff = time.time() - 7 * 24 * 3600
    for index, entry in enumerate(entries):
        if index >= 19 or entry.stat().st_mtime < cutoff:
            shutil.rmtree(entry)


def local_key(path: Path, settings: Settings) -> str:
    digest = hashlib.sha256()
    digest.update(str(path.resolve()).encode())
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    digest.update(f"{settings.asr_model}\0{settings.language}".encode())
    return digest.hexdigest()[:16]


def write_atomic(path: Path, text: str) -> None:
    temporary = path.with_name(path.name + ".tmp")
    try:
        temporary.write_text(text, encoding="utf-8")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def transcript_markdown(transcript: Transcript) -> str:
    lines = [f"# {transcript.title} · 识别原稿", "", f"来源：{transcript.source}", ""]
    for segment in transcript.segments:
        lines.extend([f"[{timestamp(segment.start)}–{timestamp(segment.end)}] {segment.text}", ""])
    return "\n".join(lines) + "\n"


def output_path(transcript: Transcript, key: str) -> Path:
    title = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "-", transcript.title).strip(". ")[:70] or "视频"
    return (Path("digests") / f"{title}-{key[:8]}" / "summary.md").resolve()


def extract(value: str, settings: Settings, progress: Callable[[str], None]) -> dict:
    path = Path(value).expanduser()
    remote_input = re.search(r"https?://", value, flags=re.IGNORECASE) is not None
    if not remote_input and path.is_file():
        path = path.resolve()
        title, source = path.stem, str(path)
        with ProgressStage(progress, "读取本地音视频") as stage:
            key = local_key(path, settings)
        progress(
            f"本地媒体已就绪（{path.stat().st_size / 1024**2:.2f} MB，"
            f"耗时 {stage.elapsed:.1f} 秒）"
        )
        remote = False
    else:
        from .douyin import resolve_input

        if not remote_input:
            raise Watch2NoteError("输入文件不存在，请提供本地音视频文件或抖音分享链接。")
        with ProgressStage(progress, "解析抖音分享链接") as stage:
            source = resolve_input(value)
        progress(f"抖音链接解析成功（耗时 {stage.elapsed:.1f} 秒）")
        key = hashlib.sha256(
            f"{source}\0{settings.asr_model}\0{settings.language}".encode()
        ).hexdigest()[:16]
        remote = True
    jobs = cache_dir() / "jobs"
    job = jobs / key
    job.mkdir(parents=True, exist_ok=True)
    prune_cache(jobs, job)
    cached = job / "transcript.json"
    transcript = None
    if cached.exists():
        try:
            transcript = Transcript.from_dict(json.loads(cached.read_text(encoding="utf-8")))
            if transcript.source != source:
                raise ValueError("cache source mismatch")
        except (ValueError, TypeError, KeyError, Watch2NoteError):
            transcript = None
            progress("转写缓存不完整，重新识别")
    if transcript is None:
        if remote:
            from .douyin import download_video

            with ProgressStage(progress, "获取视频") as stage:
                path, title = download_video(source, job)
            progress(
                f"视频已取得（{path.stat().st_size / 1024**2:.2f} MB，"
                f"耗时 {stage.elapsed:.1f} 秒）"
            )
        transcript = transcribe(path, title, source, settings, progress)
        transcript.validate()
        write_atomic(cached, json.dumps(transcript.to_dict(), ensure_ascii=False))
    else:
        progress("复用已完成的语音识别")
    os.utime(job, None)
    target = output_path(transcript, key)
    target.parent.mkdir(parents=True, exist_ok=True)
    original = target.parent / "transcript.md"
    material = target.parent / "transcript.json"
    with ProgressStage(progress, "保存完整转写原稿"):
        write_atomic(original, transcript_markdown(transcript))
        write_atomic(
            material, json.dumps(transcript.to_dict(), ensure_ascii=False, indent=2) + "\n"
        )
    progress(f"原稿已保存：{material.parent}；接下来由当前 AI 阅读原稿并生成精华")
    return {
        "title": transcript.title,
        "source": transcript.source,
        "duration_seconds": transcript.duration,
        "language": transcript.language,
        "segment_count": len(transcript.segments),
        "transcript_json": str(material),
        "transcript_md": str(original),
        "summary_output": str(target),
        "next_step": (
            "读取完整 transcript_json，用当前 AI 模型生成精华；"
            "运行 watch2note skill 查看结构与保存命令。"
        ),
    }
