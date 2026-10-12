import hashlib
import tempfile
from importlib.resources import files
from pathlib import Path

from .errors import Watch2NoteError


def _write_atomic(path: Path, content: bytes) -> None:
    with tempfile.NamedTemporaryFile(dir=path.parent, suffix=".tmp", delete=False) as file:
        temporary = Path(file.name)
    try:
        temporary.write_bytes(content)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def skill_text() -> str:
    bundled = files("watch2note").joinpath("data/SKILL.md")
    if bundled.is_file():
        return bundled.read_text(encoding="utf-8")
    source = Path(__file__).resolve().parents[2] / "skills" / "watch2note" / "SKILL.md"
    return source.read_text(encoding="utf-8")


def install_skill(agent: str) -> Path:
    directory = Path.home() / {"codex": ".agents", "claude": ".claude"}[agent]
    directory = directory / "skills" / "watch2note"
    target = directory / "SKILL.md"
    marker = directory / ".watch2note-sha256"
    content = skill_text().encode("utf-8")
    if directory.is_symlink() or target.is_symlink() or marker.is_symlink():
        raise Watch2NoteError(
            f"Skill 路径是符号链接，未覆盖：{directory}。请使用现有 Skill 或移走后重试。"
        )
    if target.exists():
        current = target.read_bytes()
        managed_hash = marker.read_text(encoding="utf-8").strip() if marker.is_file() else ""
        if current != content and hashlib.sha256(current).hexdigest() != managed_hash:
            raise Watch2NoteError(
                f"已有不同或自行修改的 Skill，未覆盖：{target}。请移走该文件后重新安装。"
            )
    directory.mkdir(parents=True, exist_ok=True)
    _write_atomic(target, content)
    _write_atomic(marker, (hashlib.sha256(content).hexdigest() + "\n").encode("utf-8"))
    return target
