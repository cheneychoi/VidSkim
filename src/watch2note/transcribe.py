import os
from pathlib import Path
from typing import Callable

from .config import cache_dir
from .errors import Watch2NoteError
from .models import Segment, Settings, Transcript, timestamp
from .progress import ProgressStage


def prepare_model(settings: Settings):
    from faster_whisper import WhisperModel
    from faster_whisper.utils import download_model
    from huggingface_hub.errors import LocalEntryNotFoundError

    try:
        model_path = settings.asr_model
        download_root = str(cache_dir() / "models")
        local_directory = Path(model_path).is_dir()
        if not local_directory:
            try:
                model_path = download_model(
                    settings.asr_model, local_files_only=True, cache_dir=download_root
                )
                snapshot = Path(model_path)
                required = [
                    snapshot / name for name in ("model.bin", "config.json", "tokenizer.json")
                ]
                vocabulary = [snapshot / name for name in ("vocabulary.txt", "vocabulary.json")]
                if not (
                    all(path.is_file() and path.stat().st_size for path in required)
                    and any(path.is_file() and path.stat().st_size for path in vocabulary)
                ):
                    raise LocalEntryNotFoundError("Model cache is incomplete")
            except LocalEntryNotFoundError:
                model_path = download_model(
                    settings.asr_model, local_files_only=False, cache_dir=download_root
                )
        for attempt in range(2):
            model = WhisperModel(
                model_path,
                device="cpu",
                compute_type="int8",
                cpu_threads=min(8, os.cpu_count() or 1),
                download_root=download_root,
            )
            if (
                local_directory
                or model.model.n_mels == model.feature_extractor.mel_filters.shape[0]
            ):
                return model
            if attempt:
                raise ValueError("Audio preprocessor configuration does not match the model")
            # Some snapshots require a preprocessor config; 80-mel models may omit it.
            del model
            model_path = download_model(
                settings.asr_model, local_files_only=False, cache_dir=download_root
            )
    except Exception as exc:
        raise Watch2NoteError(
            "识别模型准备失败。首次运行需要下载模型；"
            "请检查网络或把 WATCH2NOTE_ASR_MODEL 指向本地模型目录。"
        ) from exc


def transcribe(
    path: Path,
    title: str,
    source: str,
    settings: Settings,
    progress: Callable[[str], None],
) -> Transcript:
    import av

    try:
        with ProgressStage(progress, "读取音频信息"):
            with av.open(str(path)) as container:
                media_duration = (container.duration or 0) / av.time_base
        if media_duration:
            progress(f"媒体已读取，媒体时长 {timestamp(media_duration)}")
    except Exception as exc:
        raise Watch2NoteError("无法读取音视频信息，请确认文件完整且可播放。") from exc
    with ProgressStage(progress, "加载语音模型（首次使用需要下载）") as stage:
        model = prepare_model(settings)
    progress(f"模型已就绪（耗时 {stage.elapsed:.1f} 秒）")
    try:
        with ProgressStage(progress, "解码音频并检测语音") as stage:
            segments, info = model.transcribe(
                str(path),
                language=settings.language,
                vad_filter=True,
                condition_on_previous_text=False,
            )
        result = []
        audio_duration = float(info.duration)
        duration = max(audio_duration, media_duration)
        progress(
            f"音频准备完成，音频时长 {timestamp(audio_duration)}，语言 {info.language}"
            f"（耗时 {stage.elapsed:.1f} 秒）"
        )
        with ProgressStage(
            progress, f"开始转写，音频 00:00 / {timestamp(audio_duration)}"
        ) as stage:
            first_segment = True
            for segment in segments:
                text = segment.text.strip()
                if text:
                    start = min(float(segment.start), duration)
                    end = min(float(segment.end), duration)
                    result.append(Segment(len(result), start, end, text))
                position = max(0, min(float(segment.end), audio_duration))
                percentage = position / audio_duration * 100 if audio_duration else 0
                stage.update(
                    f"已转写音频 {timestamp(position)} / {timestamp(audio_duration)}"
                    f"（{percentage:.0f}%）",
                    force=first_segment,
                )
                first_segment = False
            if not result:
                raise Watch2NoteError("未识别到语音；没有生成精华总结。")
    except Watch2NoteError:
        raise
    except Exception as exc:
        raise Watch2NoteError("音视频识别失败。请确认文件有可播放的语音轨道，且文件完整。") from exc
    progress(f"转写完成，共 {len(result)} 段（转写耗时 {stage.elapsed:.1f} 秒）")
    return Transcript(title, source, duration, info.language, result)
