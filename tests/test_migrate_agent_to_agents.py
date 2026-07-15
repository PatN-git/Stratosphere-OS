#!/usr/bin/env python3
"""Tests for scripts/migrations/migrate_agent_to_agents.py (AGENT.md -> AGENTS.md)."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "migrations" / "migrate_agent_to_agents.py"

VISION = "# STRATOSPHEREOS ARCHITECT\n\n## Vision\nMy bespoke project vision — must survive migration.\n"


def run(project: Path, *extra):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--project", str(project), *extra],
        capture_output=True, text=True,
    )


def _seed(project: Path, *, with_agent=True, with_agents=False):
    """Create a minimal instantiated-project layout."""
    if with_agent:
        (project / "AGENT.md").write_text(VISION, encoding="utf-8")
    if with_agents:
        (project / "AGENTS.md").write_text(VISION, encoding="utf-8")
    (project / "CLAUDE.md").write_text(
        "Follow the full constitution in AGENT.md. Check .agents/skills.\n", encoding="utf-8")
    (project / "GEMINI.md").write_text(
        "Follow the full constitution in AGENT.md. Check .agents/skills.\n", encoding="utf-8")
    agents_dir = project / ".agents"
    agents_dir.mkdir(exist_ok=True)
    (agents_dir / ".stratosphere-lock.json").write_text(json.dumps({
        "installed_plugin_version": "1.1.1",
        "artifacts": {"AGENT.md": {"version": "1.0.3", "sha256": "x"},
                      "CLAUDE.md": {"version": "1.0.1", "sha256": "y"}},
    }, indent=2), encoding="utf-8")


def test_basic_migration():
    print("--- test_basic_migration ---")
    with tempfile.TemporaryDirectory() as d:
        proj = Path(d)
        _seed(proj)
        res = run(proj)
        print(res.stdout, res.stderr)
        assert res.returncode == 0, "expected exit 0"
        assert (proj / "AGENTS.md").exists(), "AGENTS.md should exist"
        assert not (proj / "AGENT.md").exists(), "AGENT.md should be gone"
        assert (proj / "AGENTS.md").read_text(encoding="utf-8") == VISION, "content must be preserved"
        for name in ("CLAUDE.md", "GEMINI.md"):
            txt = (proj / name).read_text(encoding="utf-8")
            assert "AGENT.md" not in txt and "AGENTS.md" in txt, f"{name} should repoint to AGENTS.md"
        lock = json.loads((proj / ".agents" / ".stratosphere-lock.json").read_text(encoding="utf-8"))
        assert "AGENTS.md" in lock["artifacts"] and "AGENT.md" not in lock["artifacts"], "lock key renamed"
        assert lock["artifacts"]["AGENTS.md"]["version"] == "1.0.3", "lock value preserved"
    print("PASS")
    return True


def test_idempotent():
    print("--- test_idempotent ---")
    with tempfile.TemporaryDirectory() as d:
        proj = Path(d)
        _seed(proj)
        assert run(proj).returncode == 0
        snap = {p.name: p.read_text(encoding="utf-8")
                for p in proj.iterdir() if p.is_file()}
        res2 = run(proj)  # second run
        print(res2.stdout, res2.stderr)
        assert res2.returncode == 0, "re-run should exit 0"
        after = {p.name: p.read_text(encoding="utf-8")
                 for p in proj.iterdir() if p.is_file()}
        assert snap == after, "second run must not change anything"
    print("PASS")
    return True


def test_dry_run():
    print("--- test_dry_run ---")
    with tempfile.TemporaryDirectory() as d:
        proj = Path(d)
        _seed(proj)
        res = run(proj, "--dry-run")
        print(res.stdout, res.stderr)
        assert res.returncode == 0
        assert "DRY-RUN" in res.stdout
        assert (proj / "AGENT.md").exists(), "dry-run must not rename"
        assert not (proj / "AGENTS.md").exists(), "dry-run must not create AGENTS.md"
    print("PASS")
    return True


def test_conflict_refuses():
    print("--- test_conflict_refuses ---")
    with tempfile.TemporaryDirectory() as d:
        proj = Path(d)
        _seed(proj, with_agent=True, with_agents=True)  # both present
        res = run(proj)
        print(res.stdout, res.stderr)
        assert res.returncode == 2, "conflict must exit non-zero"
        assert (proj / "AGENT.md").exists() and (proj / "AGENTS.md").exists(), "no clobber on conflict"
    print("PASS")
    return True


if __name__ == "__main__":
    ok = True
    for t in (test_basic_migration, test_idempotent, test_dry_run, test_conflict_refuses):
        try:
            ok = t() and ok
        except AssertionError as e:
            print(f"FAIL: {t.__name__}: {e}")
            ok = False
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
    sys.exit(0 if ok else 1)
