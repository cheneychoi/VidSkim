import os
from pathlib import Path
from typing import Callable

from .config import cache_dir
from .errors import VidSkimError
from .models import Segment, Settings, Transcript


def prepare_model(settings: Settings):
    from faster_whisper import WhisperModel

    try:
        return WhisperModel(
            settings.asr_model,
            device="cpu",
            compute_type="int8",
            cpu_threads=min(8, os.cpu_count() or 1),
            download_root=str(cache_dir() / "models"),
        )
    except Exception as exc:
        raise VidSkimError(
            "识别模型准备失败。首次运行需要下载模型；"
            "请检查网络或把 VIDSKIM_ASR_MODEL 指向本地模型目录。"
        ) from exc


def transcribe(
    path: Path,
    title: str,
    source: str,
    settings: Settings,
    progress: Callable[[str], None],
) -> Transcript:
    import av

    model = prepare_model(settings)
    try:
        with av.open(str(path)) as container:
            media_duration = (container.duration or 0) / av.time_base
        segments, info = model.transcribe(
            str(path),
            language=settings.language,
            vad_filter=True,
            condition_on_previous_text=False,
        )
        result = []
        duration = max(float(info.duration), media_duration)
        next_notice = 60.0
        for segment in segments:
            text = segment.text.strip()
            if text:
                start = min(float(segment.start), duration)
                end = min(float(segment.end), duration)
                result.append(Segment(len(result), start, end, text))
            if segment.end >= next_notice:
                progress(
                    f"已识别到 {int(segment.end // 60)} 分钟 / 共 {int(info.duration // 60)} 分钟"
                )
                next_notice = segment.end + 60
    except Exception as exc:
        raise VidSkimError("音视频识别失败。请确认文件有可播放的语音轨道，且文件完整。") from exc
    if not result:
        raise VidSkimError("未识别到语音；没有生成精华总结。")
    return Transcript(title, source, duration, info.language, result)
