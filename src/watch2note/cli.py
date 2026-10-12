import argparse
import json
import sys
from importlib.resources import files
from pathlib import Path

from . import __version__
from .config import load_settings
from .errors import Watch2NoteError
from .skills import install_skill, skill_text


def progress(message: str) -> None:
    print(f"· {message}", file=sys.stderr, flush=True)


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(
        prog="watch2note",
        description="Watch2Note 视频拾记：给 AI 工具提取完整视频内容，用你的 AI 模型生成精华。",
        epilog="接入 Codex：watch2note setup --codex | 接入 Claude Code：watch2note setup --claude",
    )
    if argv and argv[0] == "save":
        parser.add_argument("command", choices=["save"])
        parser.add_argument("transcript", type=Path, help="Watch2Note 生成的 transcript.json")
        parser.add_argument(
            "--from", dest="summary", required=True, type=Path, help="AI 生成的总结 JSON"
        )
        parser.add_argument("-o", type=Path, metavar="FILE", help="总结 Markdown 的保存位置")
    elif argv and argv[0] == "setup":
        parser.add_argument("input", choices=["setup"])
        parser.add_argument("--codex", action="store_true", help="安装 Codex 用户 Skill")
        parser.add_argument("--claude", action="store_true", help="安装 Claude Code 用户 Skill")
    else:
        parser.add_argument(
            "input", nargs="?", help="音视频文件、抖音分享文本/链接，或 setup / demo / skill"
        )
    parser.add_argument("--version", action="version", version=f"Watch2Note {__version__}")
    args = parser.parse_args(argv)
    try:
        if argv and argv[0] == "save":
            from .render import write_summary

            target = write_summary(args.transcript, args.summary, args.o)
            print(json.dumps({"summary_md": str(target)}, ensure_ascii=False))
            progress(f"精华已保存：{target}")
        elif args.input is None:
            parser.print_help()
        elif args.input == "setup":
            from .progress import ProgressStage
            from .transcribe import prepare_model

            for agent in ("codex", "claude"):
                if getattr(args, agent):
                    target = install_skill(agent)
                    name = "Codex" if agent == "codex" else "Claude Code"
                    progress(f"已安装 {name} Skill：{target}")
            with ProgressStage(progress, "准备本地识别模型（首次需要下载，可能耗时数分钟）"):
                prepare_model(load_settings())
            progress("模型已就绪；精华总结使用调用工具的 AI 模型，无需配置另一套 API。")
            if args.codex:
                progress("在 Codex 中输入：$watch2note 抖音链接或本地文件路径")
            if args.claude:
                progress("在 Claude Code 中输入：/watch2note 抖音链接或本地文件路径")
            if args.codex or args.claude:
                progress("如未显示新 Skill，请重新打开会话或重启 AI 客户端。")
            else:
                progress("接入 AI 快捷调用：watch2note setup --codex 或 watch2note setup --claude")
        elif args.input == "skill":
            print(skill_text())
        elif args.input == "demo":
            progress("预置样例预览：没有现场转写，也没有调用模型")
            sample = files("watch2note").joinpath("data/demo.md")
            if not sample.is_file():
                sample = Path(__file__).resolve().parents[2] / "examples" / "summary.md"
            print(sample.read_text(encoding="utf-8"))
        else:
            from .pipeline import extract

            result = extract(args.input, load_settings(), progress)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Watch2NoteError as exc:
        print(f"Watch2Note：{exc}", file=sys.stderr)
        return 1
    except (EOFError, KeyboardInterrupt):
        print("\n已取消；已完成的转写将在下次运行时复用。", file=sys.stderr)
        return 130
    except OSError:
        print("Watch2Note：无法读写文件，请检查文件路径、权限和剩余空间。", file=sys.stderr)
        return 1
