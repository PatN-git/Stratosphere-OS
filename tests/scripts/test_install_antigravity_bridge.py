"""BT-120: Antigravity fallback bridge copies dist/skills/ into ~/.gemini/config/skills/.

Physical copy only (no symlinks), per-skill replace so stale files inside a shipped
skill are dropped while foreign skills survive, and an actionable error when the
bundle has not been built. `--target` overrides the destination for testing.
"""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "dist/skills"
SH = REPO / "scripts/install-antigravity-bridge.sh"
PS1 = REPO / "scripts/install-antigravity-bridge.ps1"


def _bash_path(p: Path) -> str:
    s = p.as_posix()
    if ":" in s:  # Git Bash on Windows: C:/x -> /c/x
        s = "/" + s[0].lower() + s[2:]
    return s


def _env(home: Path):
    """Sandbox the default target too: a run that ignores --target must not touch the real ~/.gemini."""
    return {**os.environ, "HOME": str(home), "USERPROFILE": str(home)}


def _run_bash(script: Path, *args, home: Path):
    bash = shutil.which("bash")
    if not bash:
        pytest.skip("bash not available")
    return subprocess.run([bash, _bash_path(script), *map(str, args)], capture_output=True, text=True, env=_env(home))


def _run_ps(script: Path, *args, home: Path):
    ps = shutil.which("pwsh") or shutil.which("powershell")
    if not ps:
        pytest.skip("PowerShell not available")
    return subprocess.run([ps, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), *map(str, args)],
                          capture_output=True, text=True, env=_env(home))


RUNNERS = pytest.mark.parametrize(
    "run,script", [(_run_bash, SH), (_run_ps, PS1)], ids=["bash", "powershell"]
)


def _bundle_skills():
    if not BUNDLE.is_dir():
        pytest.skip("dist/skills not built")
    return sorted(p.name for p in BUNDLE.iterdir() if p.is_dir())


def _is_reparse(p: Path) -> bool:
    """Windows reparse point (symlink/junction); st_file_attributes is absent elsewhere."""
    return bool(getattr(p.lstat(), "st_file_attributes", 0) & 0x400)


def _symlinks(root: Path):
    return [p for p in root.rglob("*") if p.is_symlink() or _is_reparse(p)]


@RUNNERS
def test_copies_every_skill_with_references(tmp_path, run, script):
    """BT-120 AC1/AC2: all bundled skills land in the target, references/ included."""
    skills = _bundle_skills()
    dest = tmp_path / "skills"
    r = run(script, "--target", dest, home=tmp_path / "home")
    assert r.returncode == 0, r.stderr
    assert sorted(p.name for p in dest.iterdir()) == skills
    for name in skills:
        assert (dest / name / "SKILL.md").is_file()
    src_refs = sorted(p.relative_to(BUNDLE).as_posix() for p in BUNDLE.rglob("references/*") if p.is_file())
    assert src_refs, "bundle should carry references/ files"
    for rel in src_refs:
        assert (dest / rel).is_file(), f"missing {rel}"


@RUNNERS
def test_creates_no_symlinks(tmp_path, run, script):
    """BT-120 AC4: physical copy only."""
    _bundle_skills()
    dest = tmp_path / "skills"
    assert run(script, "--target", dest, home=tmp_path / "home").returncode == 0
    assert _symlinks(dest) == []


@RUNNERS
def test_replaces_shipped_skills_and_keeps_foreign(tmp_path, run, script):
    """Per-skill replace: stale files inside a shipped skill go, foreign skills stay."""
    skills = _bundle_skills()
    dest = tmp_path / "skills"
    stale = dest / skills[0] / "stale-orphan.md"
    foreign = dest / "my-own-skill" / "SKILL.md"
    for f in (stale, foreign):
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("planted", encoding="utf-8")
    assert run(script, "--target", dest, home=tmp_path / "home").returncode == 0
    assert not stale.exists(), "stale file inside a shipped skill survived"
    assert foreign.exists(), "foreign skill was deleted"
    assert (dest / skills[0] / "SKILL.md").is_file()


@RUNNERS
def test_missing_bundle_fails_with_actionable_error(tmp_path, run, script):
    """BT-120 stress case: no dist/skills -> non-zero exit, message says how to fix it."""
    fake_repo = tmp_path / "repo"
    (fake_repo / "scripts").mkdir(parents=True)
    shutil.copy(script, fake_repo / "scripts" / script.name)
    dest = tmp_path / "skills"
    r = run(fake_repo / "scripts" / script.name, "--target", dest, home=tmp_path / "home")
    assert r.returncode != 0
    assert "dist/skills" in r.stderr
    assert "build.py" in r.stderr
    assert not dest.exists(), "nothing should be written on failure"


@RUNNERS
def test_default_target_is_gemini_config_skills(tmp_path, run, script):
    """BT-120 AC1/AC2: with no --target the skills land in <home>/.gemini/config/skills."""
    skills = _bundle_skills()
    home = tmp_path / "home"
    r = run(script, home=home)
    assert r.returncode == 0, r.stderr
    default = home / ".gemini" / "config" / "skills"
    assert sorted(p.name for p in default.iterdir()) == skills
    assert (default / skills[0] / "SKILL.md").is_file()


@RUNNERS
def test_target_without_value_fails_fast(tmp_path, run, script):
    """A dangling --target must error, never silently fall back to the real config dir."""
    _bundle_skills()
    home = tmp_path / "home"
    r = run(script, "--target", home=home)
    assert r.returncode != 0
    assert "--target" in r.stderr
    assert not (home / ".gemini").exists(), "nothing should be written on a usage error"
