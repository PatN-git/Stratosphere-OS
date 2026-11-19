import json
import os
import subprocess
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DIST_SETUP = REPO_ROOT / "dist" / "skills" / "stratosphere-setup"
SCAFFOLD_SCRIPT = DIST_SETUP / "scripts" / "scaffold.py"
DELIVERY_SCRIPT = REPO_ROOT / "src" / "scripts" / "delivery.py"


def run_scaffold(cwd, *args):
    return subprocess.run(
        [sys.executable, str(SCAFFOLD_SCRIPT), *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


def test_scaffold_delivery_plugin_clean(tmp_path):
    r = run_scaffold(tmp_path, "--delivery", "plugin")
    assert r.returncode == 0, r.stdout + r.stderr

    lock_file = tmp_path / ".agents" / ".stratosphere-lock.json"
    assert lock_file.exists()
    lock_data = json.loads(lock_file.read_text(encoding="utf-8"))
    assert lock_data.get("plugin_id") == "stratosphere-os"
    assert lock_data.get("skill_delivery") == "plugin"

    # .gitkeep must be tracked/created
    gitkeep = tmp_path / ".agents" / "skills" / ".gitkeep"
    assert gitkeep.exists()

    # Bundled skills must not be in .agents/skills
    assert not (tmp_path / ".agents" / "skills" / "0a-start-session").exists()
    assert not (tmp_path / ".agents" / "skills" / "3d-implement-issue").exists()

    # Scripts and rules must be present
    assert (tmp_path / ".agents" / "scripts" / "delivery.py").exists()
    assert (tmp_path / ".agents" / "rules").exists()


def test_scaffold_delivery_in_repo(tmp_path):
    r = run_scaffold(tmp_path, "--delivery", "in-repo")
    assert r.returncode == 0, r.stdout + r.stderr

    lock_file = tmp_path / ".agents" / ".stratosphere-lock.json"
    assert lock_file.exists()
    lock_data = json.loads(lock_file.read_text(encoding="utf-8"))
    assert lock_data.get("skill_delivery") == "in-repo"

    # Bundled skills must be placed
    assert (tmp_path / ".agents" / "skills" / "0a-start-session" / "SKILL.md").exists()
    assert (tmp_path / ".agents" / "skills" / "3d-implement-issue" / "SKILL.md").exists()


def test_migration_quarantines_modified_skill(tmp_path):
    # Step 1: scaffold in-repo
    r = run_scaffold(tmp_path, "--delivery", "in-repo")
    assert r.returncode == 0

    # Step 2: modify a bundled skill
    modified_skill_file = tmp_path / ".agents" / "skills" / "0a-start-session" / "SKILL.md"
    assert modified_skill_file.exists()
    original_text = modified_skill_file.read_text(encoding="utf-8")
    modified_skill_file.write_text(original_text + "\n# Custom user edit\n", encoding="utf-8")

    # Step 3: migrate to plugin delivery mode
    r = run_scaffold(tmp_path, "--update", "--delivery", "plugin")
    assert r.returncode == 0, r.stdout + r.stderr

    # Pristine skill removed
    assert not (tmp_path / ".agents" / "skills" / "3d-implement-issue").exists()

    # Modified skill quarantined to .agents/custom-skills
    quarantined = tmp_path / ".agents" / "custom-skills" / "0a-start-session" / "SKILL.md"
    assert quarantined.exists()
    assert "# Custom user edit" in quarantined.read_text(encoding="utf-8")
    assert not (tmp_path / ".agents" / "skills" / "0a-start-session").exists()

    # Lockfile updated
    lock_data = json.loads((tmp_path / ".agents" / ".stratosphere-lock.json").read_text(encoding="utf-8"))
    assert lock_data.get("skill_delivery") == "plugin"
    assert not any(k.startswith(".agents/skills/3d-implement-issue") for k in lock_data.get("artifacts", {}))


def test_delivery_cli_status_and_switch(tmp_path):
    r = run_scaffold(tmp_path, "--delivery", "plugin")
    assert r.returncode == 0

    delivery_script = tmp_path / ".agents" / "scripts" / "delivery.py"
    assert delivery_script.exists()

    env = dict(os.environ, STRATOSPHERE_SCAFFOLD_SCRIPT=str(SCAFFOLD_SCRIPT))

    # Test --status
    r_status = subprocess.run([sys.executable, str(delivery_script), "--status"], cwd=str(tmp_path), capture_output=True, text=True, env=env)
    assert r_status.returncode == 0
    assert "plugin" in r_status.stdout

    # Test --restore-skills
    r_restore = subprocess.run([sys.executable, str(delivery_script), "--restore-skills"], cwd=str(tmp_path), capture_output=True, text=True, env=env)
    assert r_restore.returncode == 0, r_restore.stdout + r_restore.stderr
    assert (tmp_path / ".agents" / "skills" / "0a-start-session" / "SKILL.md").exists()

    # Check status again
    r_status2 = subprocess.run([sys.executable, str(delivery_script), "--status"], cwd=str(tmp_path), capture_output=True, text=True, env=env)
    assert "in-repo" in r_status2.stdout


def _isolated_delivery(tmp_path, monkeypatch):
    sys.path.insert(0, str(DELIVERY_SCRIPT.parent))
    import delivery
    proj = tmp_path / "proj"
    home = tmp_path / "home"
    proj.mkdir(parents=True, exist_ok=True)
    home.mkdir(parents=True, exist_ok=True)
    monkeypatch.chdir(proj)
    monkeypatch.delenv("STRATOSPHERE_SCAFFOLD_SCRIPT", raising=False)
    monkeypatch.delenv("STRATOSPHERE_PLUGIN_SKILLS", raising=False)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    return delivery, proj, home


def _touch_scaffold(skills_dir: Path) -> Path:
    p = skills_dir / "stratosphere-setup" / "scripts" / "scaffold.py"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("# scaffold\n", encoding="utf-8")
    return p


def test_locate_scaffolder_resolves_env_and_gemini_plugins(tmp_path, monkeypatch):
    delivery, proj, home = _isolated_delivery(tmp_path, monkeypatch)

    env_skills = tmp_path / "env_skills"
    env_scaffold = _touch_scaffold(env_skills)
    monkeypatch.setenv("STRATOSPHERE_PLUGIN_SKILLS", str(env_skills))
    assert delivery.locate_scaffolder(proj) == env_scaffold

    monkeypatch.delenv("STRATOSPHERE_PLUGIN_SKILLS", raising=False)
    older = _touch_scaffold(home / ".gemini" / "config" / "plugins" / "100" / "skills")
    newer = _touch_scaffold(home / ".gemini" / "config" / "plugins" / "200" / "skills")
    assert older.is_file()
    assert delivery.locate_scaffolder(proj) == newer


def test_locate_scaffolder_resolves_antigravity_fallback_and_sorted_claude_cache(tmp_path, monkeypatch):
    delivery, proj, home = _isolated_delivery(tmp_path, monkeypatch)

    ag_scaffold = _touch_scaffold(home / ".gemini" / "antigravity" / "plugins" / "stratosphere-os" / "skills")
    assert delivery.locate_scaffolder(proj) == ag_scaffold

    delivery2, proj2, home2 = _isolated_delivery(tmp_path / "sub", monkeypatch)
    mkt = home2 / ".claude" / "plugins" / "cache" / "stratosphere-marketplace" / "stratosphere-os"
    s_521 = _touch_scaffold(mkt / "5.2.1" / "dist" / "skills")
    s_530 = _touch_scaffold(mkt / "5.3.0" / "dist" / "skills")
    assert s_521.is_file()
    assert delivery2.locate_scaffolder(proj2) == s_530

    s_1_9 = _touch_scaffold(mkt / "1.9.0" / "dist" / "skills")
    s_1_10 = _touch_scaffold(mkt / "1.10.0" / "dist" / "skills")
    s_521.unlink()
    s_530.unlink()
    monkeypatch.setattr(delivery.glob, "glob", lambda *a, **k: [str(s_1_9), str(s_1_10)])
    assert delivery2.locate_scaffolder(proj2) == s_1_10
