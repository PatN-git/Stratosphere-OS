"""BT-118: the canonical `dist/skills/` bundle — one host-agnostic tree, 26 self-contained
skills, HITL sidecars intact — replacing the per-host dist/claude-code + dist/antigravity trees.
Asserts on the committed bundle (drift-guarded by check.sh) and on build.py's fatal paths.
"""
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import REPO_ROOT

DIST_SKILLS = REPO_ROOT / "dist" / "skills"
SETUP = DIST_SKILLS / "stratosphere-setup"
EXPECTED_SKILLS = 26
EXPECTED_LIFECYCLE = 22


def _skill_dirs():
    return sorted(p for p in DIST_SKILLS.iterdir() if (p / "SKILL.md").is_file())


def _fm(path):
    m = re.match(r"^---\r?\n(.*?)\r?\n---", path.read_text(encoding="utf-8"), re.S)
    return m.group(1) if m else ""


def _load_build():
    spec = importlib.util.spec_from_file_location("build_mod", REPO_ROOT / "build" / "build.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_single_bundle_emits_exactly_26_skills():
    assert len(_skill_dirs()) == EXPECTED_SKILLS


def test_per_host_duplicate_trees_are_gone():
    assert not (REPO_ROOT / "dist" / "claude-code").exists()
    assert not (REPO_ROOT / "dist" / "antigravity" / "skills").exists()


def test_no_root_skills_dir_is_created():
    # Isolation invariant: a root skills/ would collide with OpenClaw's skillsDir.
    assert not (REPO_ROOT / "skills").exists()


def test_skill_dir_name_equals_frontmatter_name():
    for d in _skill_dirs():
        assert re.search(rf'^name:\s*"?{re.escape(d.name)}"?\s*$', _fm(d / "SKILL.md"), re.M), d.name


def test_lifecycle_skills_carry_all_hitl_sidecars():
    hitl = [d for d in _skill_dirs()
            if re.search(r"^disable-model-invocation:\s*true\s*$", _fm(d / "SKILL.md"), re.M)]
    assert len(hitl) == EXPECTED_LIFECYCLE
    for d in hitl:
        assert re.search(r'^triggers:\s*\["user"\]\s*$', _fm(d / "SKILL.md"), re.M), d.name
        sidecar = d / "agents" / "openai.yaml"
        assert sidecar.is_file(), f"{d.name}: missing agents/openai.yaml"
        assert "allow_implicit_invocation: false" in sidecar.read_text(encoding="utf-8"), d.name


def test_every_cited_reference_is_shipped_inside_the_skill():
    build = _load_build()
    for d in _skill_dirs():
        body = (d / "SKILL.md").read_text(encoding="utf-8")
        for name in build.cited_refs(body):
            assert (d / "references" / name).is_file(), f"{d.name}: references/{name} not shipped"


@pytest.fixture
def sandbox(tmp_path):
    """A throwaway copy of build/ + src/, so the real build entrypoint can be broken safely."""
    for d in ("build", "src"):
        shutil.copytree(REPO_ROOT / d, tmp_path / d, ignore=shutil.ignore_patterns("__pycache__"))
    return tmp_path


def _run_build(root):
    return subprocess.run([sys.executable, str(root / "build" / "build.py")], capture_output=True, text=True)


def test_sandbox_build_succeeds_unmodified(sandbox):
    r = _run_build(sandbox)
    assert r.returncode == 0, r.stdout + r.stderr
    assert len([p for p in (sandbox / "dist" / "skills").iterdir() if (p / "SKILL.md").is_file()]) == EXPECTED_SKILLS


def _cite(path, ref):
    path.write_text(path.read_text(encoding="utf-8") + f"\nSee references/{ref}\n", encoding="utf-8")


def test_missing_cited_reference_fails_the_build_with_status_1(sandbox):
    _cite(sandbox / "src" / "workflows" / "0a-start-session.md", "does-not-exist.md")
    r = _run_build(sandbox)
    assert r.returncode == 1, r.stdout + r.stderr
    assert "does-not-exist.md" in r.stderr


def test_missing_transitive_reference_fails_the_build_with_status_1(sandbox):
    (sandbox / "src" / "references" / "chain-a.md").write_text(
        '---\nversion: "1.0.0"\n---\nSee references/chain-missing.md\n', encoding="utf-8")
    _cite(sandbox / "src" / "workflows" / "0a-start-session.md", "chain-a.md")
    r = _run_build(sandbox)
    assert r.returncode == 1, r.stdout + r.stderr
    assert "chain-missing.md" in r.stderr


def test_execution_skill_with_missing_reference_fails_the_build_with_status_1(sandbox):
    _cite(sandbox / "src" / "skills" / "micro-tdd" / "SKILL.md", "does-not-exist.md")
    r = _run_build(sandbox)
    assert r.returncode == 1, r.stdout + r.stderr
    assert "does-not-exist.md" in r.stderr


def test_setup_skill_carries_its_own_scaffold_payload():
    # Track A/B/C installs place only skill folders, so the scaffolder payload rides inside setup.
    assert (SETUP / "scripts" / "scaffold.py").is_file()
    assert (SETUP / "assets" / "templates" / "memory").is_dir()
    manifest = json.loads((SETUP / "versions.json").read_text(encoding="utf-8"))
    assert manifest["plugin_version"]
    assert "skills/0a-start-session/SKILL.md" in manifest["artifacts"]


def test_marketplace_lists_all_26_skills_via_valid_plugins_schema():
    mk = json.loads((REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    (plugin,) = mk["plugins"]
    assert plugin["source"] == "./"
    assert plugin["strict"] is False
    assert sorted(plugin["skills"]) == sorted(f"./dist/skills/{d.name}" for d in _skill_dirs())
    assert len(plugin["skills"]) == EXPECTED_SKILLS


def test_antigravity_manifest_stays_in_its_canonical_location():
    assert (REPO_ROOT / "dist" / "antigravity" / "plugin.json").is_file()


def _sync_destination(tmp_path, host_dir):
    skills = tmp_path / host_dir / "skills"
    shutil.copytree(DIST_SKILLS, skills)
    proj = tmp_path / "proj"
    proj.mkdir(exist_ok=True)
    r = subprocess.run([sys.executable, str(skills / "stratosphere-setup" / "scripts" / "sync_skills.py"),
                        "--category", "system", "--dry-run", "--project-root", str(proj)],
                       capture_output=True, text=True, cwd=proj)
    assert r.returncode == 0, r.stdout + r.stderr
    line = next(l for l in r.stdout.splitlines() if l.startswith("Skills destination directory"))
    return Path(line.split(": ", 1)[1].rsplit(" (", 1)[0]), proj


def test_sync_skills_follows_a_claude_install_to_dot_claude_skills(tmp_path):
    """No plugin manifest travels with the bundle any more, so the host is read off the
    install location: a bundle under .claude/ syncs to <project>/.claude/skills."""
    dest, proj = _sync_destination(tmp_path, ".claude")
    assert dest == proj / ".claude" / "skills"


def test_sync_skills_defaults_to_dot_agents_skills_elsewhere(tmp_path):
    dest, proj = _sync_destination(tmp_path, ".agents")
    assert dest == proj / ".agents" / "skills"


def test_sync_skills_skill_points_at_the_setup_skill_payload():
    """sync_skills.py ships only inside stratosphere-setup/scripts/, so the skill that
    documents it must not send the agent to a retired plugin directory."""
    body = (DIST_SKILLS / "sync-skills" / "SKILL.md").read_text(encoding="utf-8")
    assert "stratosphere-setup" in body
    assert "plugins/stratosphere-os" not in body


def test_sync_skills_ignores_a_claude_worktree_checkout(tmp_path):
    """A bare `.claude` path segment is not a Claude install: worktrees live under .claude/worktrees/."""
    dest, proj = _sync_destination(tmp_path, ".claude/worktrees/feature")
    assert dest == proj / ".agents" / "skills"
