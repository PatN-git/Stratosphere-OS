"""BT-122: suite integrity check for stratosphere-setup / stratosphere-update.

Seam: the `check_suite.py` CLI (stdout + exit code). Fixtures copy the committed
`dist/skills` bundle into tmp_path so every case starts from a known-good suite.
"""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import REPO_ROOT

SCRIPT = REPO_ROOT / "src" / "scripts" / "check_suite.py"
DIST_SKILLS = REPO_ROOT / "dist" / "skills"
REMEDIATION = "npx skills add PatN-git/Stratosphere-OS/dist/skills -a <agent> --copy -y"


def run(*args, env=None):
    e = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    e.update(env or {})
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True, env=e)


@pytest.fixture
def suite(tmp_path):
    dst = tmp_path / "skills"
    shutil.copytree(DIST_SKILLS, dst)
    return dst


def lifecycle_names():
    """Ground truth from frontmatter (never from the script under test)."""
    return sorted(
        d.name for d in DIST_SKILLS.iterdir()
        if re.search(r"^\s+stratos\.layer:\s*lifecycle\s*$", (d / "SKILL.md").read_text(encoding="utf-8"), re.M)
    )


# --- suite ---------------------------------------------------------------

def test_suite_passes_when_all_22_lifecycle_skills_present(suite):
    r = run("suite", "--skills-dir", suite)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "22/22" in r.stdout


def test_suite_ignores_execution_skills(suite):
    for name in ("load-memory", "micro-tdd", "plan-html", "concept-brainstorm"):
        shutil.rmtree(suite / name)
    r = run("suite", "--skills-dir", suite)
    assert r.returncode == 0, r.stdout + r.stderr


def test_suite_halts_listing_7_missing_with_remediation(suite):
    missing = lifecycle_names()[:7]
    for name in missing:
        shutil.rmtree(suite / name)
    r = run("suite", "--skills-dir", suite)
    assert r.returncode == 1
    assert "15/22" in r.stdout
    assert all(name in r.stdout for name in missing)
    assert REMEDIATION in r.stdout


def test_suite_detects_missing_reference_file(suite):
    refs = sorted((suite / "4a-verify-and-ship" / "references").iterdir())
    assert refs, "fixture assumption: 4a carries references/"
    refs[0].unlink()
    r = run("suite", "--skills-dir", suite)
    assert r.returncode == 1
    assert "4a-verify-and-ship" in r.stdout and refs[0].name in r.stdout


def test_suite_detects_stripped_hitl_sidecar(suite):
    (suite / "3d-implement-issue" / "agents" / "openai.yaml").unlink()
    r = run("suite", "--skills-dir", suite)
    assert r.returncode == 1
    assert "3d-implement-issue" in r.stdout and "openai.yaml" in r.stdout


def test_suite_detects_stripped_hitl_frontmatter(suite):
    md = suite / "1a-research" / "SKILL.md"
    md.write_text(md.read_text(encoding="utf-8").replace("disable-model-invocation: true", ""), encoding="utf-8")
    r = run("suite", "--skills-dir", suite)
    assert r.returncode == 1
    assert "1a-research" in r.stdout and "disable-model-invocation" in r.stdout


def test_suite_detects_name_dir_mismatch(suite):
    md = suite / "0b-stop-session" / "SKILL.md"
    md.write_text(md.read_text(encoding="utf-8").replace("name: 0b-stop-session", "name: 0B-Stop-Session"), encoding="utf-8")
    r = run("suite", "--skills-dir", suite)
    assert r.returncode == 1
    assert "0b-stop-session" in r.stdout and "name" in r.stdout


def test_hardcoded_lifecycle_list_matches_bundle_frontmatter():
    """Drift guard: adding/removing a lifecycle skill must update check_suite.LIFECYCLE_SKILLS."""
    sys.path.insert(0, str(SCRIPT.parent))
    import check_suite
    assert sorted(check_suite.LIFECYCLE_SKILLS) == lifecycle_names()
    assert len(check_suite.LIFECYCLE_SKILLS) == 22


# --- visibility ----------------------------------------------------------

SYSTEM_PACK = ["code-simplifier", "skill-creator"]


@pytest.fixture
def proj(tmp_path):
    project, home = tmp_path / "proj", tmp_path / "home"
    project.mkdir()
    home.mkdir()
    return project, home


def install(root: Path, names=SYSTEM_PACK):
    for n in names:
        (root / n).mkdir(parents=True, exist_ok=True)
        (root / n / "SKILL.md").write_text(f"---\nname: {n}\n---\n", encoding="utf-8")


def visibility(project, home, host, **kw):
    return run("visibility", "--project", project, "--home", home, "--host", host, **kw)


def test_claude_host_halts_when_system_pack_only_in_agents_skills(proj):
    project, home = proj
    install(project / ".agents" / "skills")
    r = visibility(project, home, "claude")
    assert r.returncode == 1
    assert all(n in r.stdout for n in SYSTEM_PACK)
    assert ".claude" in r.stdout and "skills" in r.stdout
    assert "Copy-Item" in r.stdout and "cp -r" in r.stdout  # copy remediation for both shells


def test_claude_host_passes_with_project_claude_skills(proj):
    project, home = proj
    install(project / ".claude" / "skills")
    assert visibility(project, home, "claude").returncode == 0


def test_claude_host_passes_with_global_claude_skills(proj):
    project, home = proj
    install(home / ".claude" / "skills")
    assert visibility(project, home, "claude").returncode == 0


def test_agents_host_passes_with_project_agents_skills(proj):
    project, home = proj
    install(project / ".agents" / "skills")
    assert visibility(project, home, "agents").returncode == 0


def test_agents_host_passes_with_global_locations(proj):
    project, home = proj
    install(home / ".agents" / "skills", ["code-simplifier"])
    install(home / ".gemini" / "config" / "skills", ["skill-creator"])
    r = visibility(project, home, "agents")
    assert r.returncode == 0, r.stdout


def test_agents_host_does_not_count_claude_dir(proj):
    project, home = proj
    install(project / ".claude" / "skills")
    assert visibility(project, home, "agents").returncode == 1


def test_absent_everywhere_points_to_sync_skills(proj):
    project, home = proj
    r = visibility(project, home, "claude")
    assert r.returncode == 1
    assert "/sync-skills" in r.stdout


def test_partial_pack_lists_only_the_invisible_skill(proj):
    project, home = proj
    install(project / ".claude" / "skills", ["skill-creator"])
    r = visibility(project, home, "claude")
    assert r.returncode == 1
    assert "code-simplifier" in r.stdout and "skill-creator" not in r.stdout


def test_host_auto_detects_claude_code_from_environment(proj):
    project, home = proj
    install(project / ".agents" / "skills")
    on_claude = run("visibility", "--project", project, "--home", home, env={"CLAUDECODE": "1"})
    elsewhere = run("visibility", "--project", project, "--home", home)
    assert on_claude.returncode == 1 and elsewhere.returncode == 0


# --- legacy --------------------------------------------------------------

def legacy(project, home, *extra):
    return run("legacy", "--project", project, "--home", home, *extra)


def touch(path: Path, text="x"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_legacy_reports_dist_claude_code_without_deleting(proj):
    project, home = proj
    touch(project / "dist" / "claude-code" / "plugin.json")
    r = legacy(project, home)
    assert r.returncode == 1
    assert "dist" in r.stdout and "claude-code" in r.stdout
    assert (project / "dist" / "claude-code").exists()


def test_legacy_apply_deletes_and_second_run_is_clean(proj):
    project, home = proj
    touch(project / "dist" / "claude-code" / "plugin.json")
    r = legacy(project, home, "--apply")
    assert r.returncode == 0
    assert not (project / "dist" / "claude-code").exists()
    assert legacy(project, home).returncode == 0


def test_legacy_clean_project_passes(proj):
    project, home = proj
    r = legacy(project, home)
    assert r.returncode == 0 and "[LEGACY OK]" in r.stdout


def test_legacy_spares_current_antigravity_manifest_dir(proj):
    project, home = proj
    touch(project / "dist" / "antigravity" / "plugin.json")
    assert legacy(project, home).returncode == 0


def test_legacy_flags_antigravity_dir_carrying_a_skills_payload(proj):
    project, home = proj
    touch(project / "dist" / "antigravity" / "plugin.json")
    touch(project / "dist" / "antigravity" / "skills" / "0a-start-session" / "SKILL.md")
    r = legacy(project, home, "--apply")
    assert r.returncode == 0
    assert not (project / "dist" / "antigravity").exists()


def test_legacy_commands_dir_only_stratos_files_are_removed(proj):
    project, home = proj
    touch(project / "commands" / "0a_start-session.md")   # legacy underscore spelling
    touch(project / "commands" / "3d-implement-issue.md")
    touch(project / "commands" / "deploy.md")             # user-authored, must survive
    r = legacy(project, home, "--apply")
    assert r.returncode == 0
    assert sorted(p.name for p in (project / "commands").iterdir()) == ["deploy.md"]


def test_legacy_commands_dir_removed_when_it_becomes_empty(proj):
    project, home = proj
    touch(project / "commands" / "4a-verify-and-ship.md")
    legacy(project, home, "--apply")
    assert not (project / "commands").exists()


def test_legacy_ignores_user_commands_dir(proj):
    project, home = proj
    touch(project / "commands" / "deploy.md")
    assert legacy(project, home).returncode == 0


def test_legacy_scans_old_plugin_install_roots(proj):
    project, home = proj
    stale = [
        project / ".agents" / "plugins" / "stratosphere-os" / "commands" / "0b-stop-session.md",
        home / ".claude" / "plugins" / "stratosphere-os" / "dist" / "claude-code" / "plugin.json",
    ]
    for f in stale:
        touch(f)
    r = legacy(project, home)
    assert r.returncode == 1
    assert "0b-stop-session.md" in r.stdout or "commands" in r.stdout
    assert legacy(project, home, "--apply").returncode == 0
    assert not any(f.exists() for f in stale)
    # the plugin roots themselves are never removed
    assert (home / ".claude" / "plugins" / "stratosphere-os").is_dir()


# --- wiring: who calls the checks (and who must not) ----------------------

SRC = REPO_ROOT / "src"


def _read(rel):
    return (SRC / rel).read_text(encoding="utf-8")


def test_setup_runs_suite_check_before_scaffolding_and_visibility_after_pack_sync():
    text = _read("commands/stratosphere-setup/SKILL.md")
    suite = text.index("check_suite.py suite")
    assert suite < text.index("python <plugin>/scripts/scaffold.py")
    assert text.index("check_suite.py visibility") > text.index("## Checkpoint 9")


def test_update_runs_suite_and_legacy_checks_before_scope_and_visibility_after_sync():
    text = _read("commands/stratosphere-update/SKILL.md")
    scope = text.index("## Phase 1: Compute Update Scope")
    assert text.index("check_suite.py suite") < scope
    assert text.index("check_suite.py legacy") < scope
    assert "--apply" in text
    assert text.index("check_suite.py visibility") > text.index("## Phase 6")


def test_start_session_has_zero_suite_validation():
    text = _read("workflows/0a-start-session.md")
    assert "check_suite" not in text and "integrity" not in text.lower()


def test_constitution_states_skill_locations_and_disk_resolution_rule():
    text = _read("constitution/AGENTS.md")
    assert ".claude/skills" in text and "does **not** read `.agents/skills/`" in text
    assert "code-simplifier" in text
    assert "read `<skills-dir>/<name>/SKILL.md` on disk before calling it unavailable" in text
