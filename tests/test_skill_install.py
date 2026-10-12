import errno
from pathlib import Path

import pytest

from watch2note import cli, skills, transcribe
from watch2note.errors import Watch2NoteError


@pytest.fixture
def skill_home(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    return tmp_path


def test_setup_installs_both_native_skills_and_prepares_model(skill_home, monkeypatch, capsys):
    prepared = []
    monkeypatch.setattr(transcribe, "prepare_model", lambda settings: prepared.append(settings))
    assert cli.main(["setup", "--codex", "--claude"]) == 0
    for folder in (".agents", ".claude"):
        installed = skill_home / folder / "skills" / "watch2note" / "SKILL.md"
        assert installed.read_text(encoding="utf-8") == skills.skill_text()
        assert "name: watch2note\n" in installed.read_text(encoding="utf-8")
    assert len(prepared) == 1
    output = capsys.readouterr()
    assert "$watch2note" in output.err and "/watch2note" in output.err


def test_setup_without_target_only_prepares_model(skill_home, monkeypatch):
    monkeypatch.setattr(transcribe, "prepare_model", lambda settings: None)
    assert cli.main(["setup"]) == 0
    assert not list(skill_home.iterdir())


def test_reinstall_updates_only_an_unmodified_managed_skill(skill_home, monkeypatch):
    target = skills.install_skill("codex")
    assert skills.install_skill("codex") == target
    updated = skills.skill_text() + "\nNew workflow instruction.\n"
    monkeypatch.setattr(skills, "skill_text", lambda: updated)
    assert skills.install_skill("codex") == target
    assert target.read_text(encoding="utf-8") == updated


@pytest.mark.parametrize("managed", [False, True])
def test_install_preserves_existing_custom_instructions(skill_home, managed):
    target = skill_home / ".agents" / "skills" / "watch2note" / "SKILL.md"
    if managed:
        skills.install_skill("codex")
    else:
        target.parent.mkdir(parents=True)
    target.write_text("My custom instructions", encoding="utf-8")
    with pytest.raises(Watch2NoteError, match="未覆盖"):
        skills.install_skill("codex")
    assert target.read_text(encoding="utf-8") == "My custom instructions"


def test_setup_conflict_does_not_start_model_download(skill_home, monkeypatch, capsys):
    target = skill_home / ".claude" / "skills" / "watch2note" / "SKILL.md"
    target.parent.mkdir(parents=True)
    target.write_text("My skill", encoding="utf-8")
    monkeypatch.setattr(transcribe, "prepare_model", lambda _: pytest.fail("No model download"))
    assert cli.main(["setup", "--claude"]) == 1
    assert "未覆盖" in capsys.readouterr().err
    assert target.read_text(encoding="utf-8") == "My skill"


def test_install_does_not_write_through_a_linked_skill(skill_home):
    source = skill_home / "source"
    source.mkdir()
    (source / "SKILL.md").write_text("Shared skill", encoding="utf-8")
    target = skill_home / ".agents" / "skills" / "watch2note"
    target.parent.mkdir(parents=True)
    try:
        target.symlink_to(source, target_is_directory=True)
    except OSError:
        pytest.skip("Creating symlinks is not allowed on this platform")
    with pytest.raises(Watch2NoteError, match="符号链接"):
        skills.install_skill("codex")
    assert (source / "SKILL.md").read_text(encoding="utf-8") == "Shared skill"


def test_install_flags_require_setup():
    with pytest.raises(SystemExit) as error:
        cli.main(["video.mp4", "--codex"])
    assert error.value.code == 2


def test_failed_upgrade_preserves_working_skill_and_can_retry(skill_home, monkeypatch):
    target = skills.install_skill("codex")
    original = target.read_bytes()
    updated = skills.skill_text() + "\nUpdated workflow.\n"
    monkeypatch.setattr(skills, "skill_text", lambda: updated)
    write_bytes = Path.write_bytes

    def incomplete_write(path, content):
        write_bytes(path, content[:20])
        raise OSError(errno.ENOSPC, "No space left on device")

    with monkeypatch.context() as patch:
        patch.setattr(Path, "write_bytes", incomplete_write)
        with pytest.raises(OSError):
            skills.install_skill("codex")
    assert target.read_bytes() == original
    assert not list(target.parent.glob("*.tmp"))
    skills.install_skill("codex")
    assert target.read_text(encoding="utf-8") == updated
