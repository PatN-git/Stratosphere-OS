"""BT-118: the canonical `dist/skills/` bundle — one host-agnostic tree, 27 self-contained
skills, HITL sidecars intact — replacing the per-host dist/claude-code + dist/antigravity trees.
Asserts on the committed bundle (drift-guarded by check.sh) and on build.py's fatal paths.
"""
import importlib.util
import os
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
EXPECTED_SKILLS = 27
EXPECTED_LIFECYCLE = 23


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


def test_single_bundle_emits_exactly_27_skills():
    assert len(_skill_dirs()) == EXPECTED_SKILLS


def test_per_host_duplicate_trees_are_gone():
    assert not (REPO_ROOT / "dist" / "claude-code").exists()
    assert not (REPO_ROOT / "dist" / "antigravity").exists()


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


def test_marketplace_lists_all_27_skills_via_valid_plugins_schema():
    mk = json.loads((REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    (plugin,) = mk["plugins"]
    assert plugin["source"] == "./"
    assert plugin["strict"] is False
    assert sorted(plugin["skills"]) == sorted(f"./dist/skills/{d.name}" for d in _skill_dirs())
    assert len(plugin["skills"]) == EXPECTED_SKILLS


def test_marketplace_describes_itself_and_no_longer_advertises_an_installer():
    """`claude plugin validate` warns when the marketplace has no description; the plugin
    text must not sell the per-host installers that BT-119 deleted."""
    mk = json.loads((REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    assert mk["metadata"]["description"].strip()
    assert "installer" not in mk["plugins"][0]["description"].lower()


def test_plugin_manifest_is_the_dist_root():
    """BT-150: dist/ is itself the plugin root (`agy plugin install dist`): the manifest sits beside
    dist/skills and no per-host directory stands next to them."""
    dist = REPO_ROOT / "dist"
    assert sorted(p.name for p in dist.iterdir()) == ["plugin.json", "skills"]
    manifest = json.loads((dist / "plugin.json").read_text(encoding="utf-8"))
    assert manifest["name"] == "stratosphere-os"
    assert manifest["version"] == _load_build().VERSION
    assert len(_skill_dirs()) == EXPECTED_SKILLS, "agy reports one processed skill per dist/skills directory"


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


def _sync_global_destination(tmp_path, host_dir):
    skills = tmp_path / host_dir / "skills"
    shutil.copytree(DIST_SKILLS, skills)
    home, proj = tmp_path / "home", tmp_path / "proj"
    home.mkdir(), proj.mkdir()
    env = {**os.environ, "HOME": str(home), "USERPROFILE": str(home)}
    r = subprocess.run([sys.executable, str(skills / "stratosphere-setup" / "scripts" / "sync_skills.py"),
                        "--category", "system", "--dry-run", "--global", "--project-root", str(proj)],
                       capture_output=True, text=True, cwd=proj, env=env)
    assert r.returncode == 0, r.stdout + r.stderr
    line = next(l for l in r.stdout.splitlines() if l.startswith("Skills destination directory"))
    return Path(line.split(": ", 1)[1].rsplit(" (", 1)[0]), home


def test_sync_skills_global_from_a_claude_install_targets_home_dot_claude_skills(tmp_path):
    dest, home = _sync_global_destination(tmp_path, ".claude")
    assert dest == home / ".claude" / "skills"


def test_sync_skills_global_elsewhere_targets_a_directory_the_host_reads(tmp_path):
    """The retired ~/.gemini/config/plugins/stratosphere-os/skills is read by nothing, so the pack
    would land invisible; the destination must be one of check_suite's visible global dirs."""
    dest, home = _sync_global_destination(tmp_path, ".agents")
    assert dest == home / ".gemini" / "config" / "skills"


@pytest.mark.parametrize("host_dir,scope_root,label", [
    (".claude/skills", "proj", "local Claude Code"),
    (".claude/skills", "home", "global Claude Code"),
    (".agents/skills", "proj", "local skills"),
    (".agents/skills", "home", "global skills"),
    (".gemini/config/skills", "home", "global Antigravity"),
])
def test_scaffold_labels_a_skills_dir_install_instead_of_custom_path(tmp_path, host_dir, scope_root, label):
    """The scope label compared against retired plugins/stratosphere-os paths, so every
    skill-directory install printed '(custom path)'."""
    home, proj = tmp_path / "home", tmp_path / "proj"
    home.mkdir(), proj.mkdir()
    skills = (proj if scope_root == "proj" else home) / host_dir
    shutil.copytree(DIST_SKILLS, skills)
    env = {**os.environ, "HOME": str(home), "USERPROFILE": str(home)}
    r = subprocess.run([sys.executable, str(skills / "stratosphere-setup" / "scripts" / "scaffold.py"), "--dry-run"],
                       capture_output=True, text=True, cwd=proj, env=env)
    line = next(l for l in r.stdout.splitlines() if l.startswith("Resolved plugin root"))
    assert f"({label})" in line, r.stdout + r.stderr
