"""Claude Code installers must replace shipped entries, not merge over them.

A merge-copy (`cp -rf dist/* dest/`) never deletes, so a file removed upstream
(e.g. plan-html templates dropped in 9406151) survives every reinstall and keeps
shipping stale, broken copies. Foreign entries in the shared ~/.claude/skills and
~/.claude/commands dirs must survive.
"""
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
TEMPLATES = Path("skills/plan-html/assets/templates")


def _plant(claude_dir: Path):
    orphans = [
        claude_dir / "plugins/stratosphere-os" / TEMPLATES / "annotated-flowchart.html",
        claude_dir / TEMPLATES / "implementation-plan.html",
        claude_dir / "plugins/stratosphere-os/commands/0b_stop-session.md",  # retired v3 dir
    ]
    foreign = [
        claude_dir / "skills/my-own-skill/SKILL.md",
        claude_dir / "commands/my-own-command.md",
        claude_dir / "plugins/stratosphere-os/skills/external-pack/SKILL.md",
    ]
    for f in orphans + foreign:
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("planted", encoding="utf-8")
    return orphans, foreign


def _assert_overlay(claude_dir: Path, orphans, foreign):
    assert not orphans[0].exists(), "stale file inside a shipped plugin skill survived"
    assert not orphans[1].exists(), "stale file inside a shipped skill survived"
    for f in foreign:
        assert f.exists(), f"foreign entry was deleted: {f}"
    assert (claude_dir / "plugins/stratosphere-os" / TEMPLATES / "plan-document.html").exists()
    assert (claude_dir / TEMPLATES / "plan-document.html").exists()
    assert (claude_dir / "skills/0b-stop-session/SKILL.md").exists()
    assert (claude_dir / "plugins/stratosphere-os/.claude-plugin/plugin.json").exists(), "dot-dirs must be staged"
    assert not (claude_dir / "plugins/stratosphere-os/commands").exists(), "retired v3 dir must stay removed"


def _require_build():
    if not (REPO / "dist/claude-code/skills/plan-html").is_dir():
        pytest.skip("dist/claude-code not built")


def test_bash_installer_replaces_shipped_entries(tmp_path):
    _require_build()
    bash = shutil.which("bash")
    if not bash:
        pytest.skip("bash not available")
    orphans, foreign = _plant(tmp_path / ".claude")
    target = tmp_path.as_posix()
    if ":" in target:  # Git Bash on Windows: C:/x -> /c/x
        target = "/" + target[0].lower() + target[2:]
    subprocess.run([bash, (REPO / "scripts/install-claude-code.sh").as_posix(), "--local", "--target", target],
                   check=True, capture_output=True)
    _assert_overlay(tmp_path / ".claude", orphans, foreign)


def test_powershell_installer_replaces_shipped_entries(tmp_path):
    _require_build()
    ps = shutil.which("pwsh") or shutil.which("powershell")
    if not ps:
        pytest.skip("PowerShell not available")
    orphans, foreign = _plant(tmp_path / ".claude")
    subprocess.run([ps, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                    str(REPO / "scripts/install-claude-code.ps1"), "--local", "--target", str(tmp_path)],
                   check=True, capture_output=True)
    _assert_overlay(tmp_path / ".claude", orphans, foreign)
