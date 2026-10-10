import argparse
import json
import sys
from importlib.resources import files
from pathlib import Path

from . import __version__
from .config import load_settings
from .errors import VidSkimError


def progress(message: str) -> None:
    print(f"· {message}", file=sys.stderr, flush=True)


def skill_text() -> str:
    bundled = files("vidskim").joinpath("data/SKILL.md")
    if bundled.is_file():
        return bundled.read_text(encoding="utf-8")
    source = Path(__file__).resolve().parents[2] / "skills" / "vidskim" / "SKILL.md"
    return source.read_text(encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(
        prog="vidskim",
        description="给 AI 工具提取完整视频内容，用你的 AI 模型生成精华。",
        epilog="工作流程：vidskim skill | 准备模型：vidskim setup | 样例：vidskim demo",
    )
    if argv and argv[0] == "save":
        parser.add_argument("command", choices=["save"])
        parser.add_argument("transcript", type=Path, help="VidSkim 生成的 transcript.json")
        parser.add_argument(
            "--from", dest="summary", required=True, type=Path, help="AI 生成的总结 JSON"
        )
        parser.add_argument("-o", type=Path, metavar="FILE", help="总结 Markdown 的保存位置")
    else:
        parser.add_argument(
            "input", nargs="?", help="音视频文件、抖音分享文本/链接，或 setup / demo / skill"
        )
    parser.add_argument("--version", action="version", version=f"VidSkim {__version__}")
    args = parser.parse_args(argv)
    try:
        if argv and argv[0] == "save":
            from .render import write_summary

            target = write_summary(args.transcript, args.summary, args.o)
            print(json.dumps({"summary_md": str(target)}, ensure_ascii=False))
        elif args.input is None:
            parser.print_help()
        elif args.input == "setup":
            from .transcribe import prepare_model

            progress("准备本地识别模型（首次需要下载，可能耗时数分钟）")
            prepare_model(load_settings())
            progress("模型已就绪；精华总结使用调用工具的 AI 模型，无需配置另一套 API。")
        elif args.input == "skill":
            print(skill_text())
        elif args.input == "demo":
            progress("预置样例预览：没有现场转写，也没有调用模型")
            sample = files("vidskim").joinpath("data/demo.md")
            if not sample.is_file():
                sample = Path(__file__).resolve().parents[2] / "examples" / "summary.md"
            print(sample.read_text(encoding="utf-8"))
        else:
            from .pipeline import extract

            result = extract(args.input, load_settings(), progress)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except VidSkimError as exc:
        print(f"VidSkim：{exc}", file=sys.stderr)
        return 1
    except (EOFError, KeyboardInterrupt):
        print("\n已取消；已完成的转写将在下次运行时复用。", file=sys.stderr)
        return 130
    except OSError:
        print("VidSkim：无法读写文件，请检查文件路径、权限和剩余空间。", file=sys.stderr)
        return 1
