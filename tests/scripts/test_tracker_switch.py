"""BT-197: `tracker_switch.py` moves a local-tracker project to GitHub and records `tracker: github`.

Seams: `write_tracker` (the frontmatter record, shared with scaffold.py) and `main(argv)` against the
gh shim (`tests/lifecycle-harness/shims/gh_shim.py`, a JSON-store `gh`), with `reconcile._gh_run` pointed at it.
"""
import json
import shutil
import subprocess
import sys

import pytest

from conftest import REPO_ROOT

SCRIPTS = REPO_ROOT / "src" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import reconcile
import tracker_switch as ts


# --- write_tracker: the `tracker:` frontmatter key --------------------------------------------------

def test_write_tracker_inserts_the_key_before_the_closing_fence(tmp_path):
    p = tmp_path / "ARCHITECTURE.md"
    p.write_text("---\ntype: architecture\nversion: \"1.0.0\"\n---\n# Body\ntracker: not frontmatter\n", encoding="utf-8")
    assert ts.write_tracker(p, "github") is True
    assert p.read_text(encoding="utf-8") == (
        "---\ntype: architecture\nversion: \"1.0.0\"\ntracker: github\n---\n# Body\ntracker: not frontmatter\n")


def test_write_tracker_replaces_an_existing_value_and_reports_no_change_when_equal(tmp_path):
    p = tmp_path / "ARCHITECTURE.md"
    p.write_text("---\ntracker: local\ntype: architecture\n---\n", encoding="utf-8")
    assert ts.write_tracker(p, "github") is True
    assert p.read_text(encoding="utf-8") == "---\ntracker: github\ntype: architecture\n---\n"
    assert ts.write_tracker(p, "github") is False


def test_write_tracker_keeps_crlf_line_endings(tmp_path):
    p = tmp_path / "ARCHITECTURE.md"
    p.write_bytes(b"---\r\ntype: architecture\r\n---\r\n# Body\r\n")
    ts.write_tracker(p, "github")
    assert p.read_bytes() == b"---\r\ntype: architecture\r\ntracker: github\r\n---\r\n# Body\r\n"


def test_write_tracker_refuses_a_file_without_frontmatter(tmp_path):
    p = tmp_path / "ARCHITECTURE.md"
    p.write_text("# Body only\n", encoding="utf-8")
    with pytest.raises(ValueError):
        ts.write_tracker(p, "github")
    assert p.read_text(encoding="utf-8") == "# Body only\n"


# --- main(): the switch, against the gh shim --------------------------------------------------------

SHIM = REPO_ROOT / "tests" / "lifecycle-harness" / "shims" / "gh_shim.py"
ROWS = (
    "| BT-LOCAL-auth | Auth epic | in progress | type:feature, tier:epic | — | — | — | ICE: - | — |\n"
    "| BT-LOCAL-db | DB setup | done | type:feature, mode:AFK, tier:slice, size:small | — | BT-LOCAL-auth | — | ICE: - | — |\n"
    "| BT-LOCAL-login | Login page | planned | type:feature, mode:HITL, tier:slice, size:small | v1.0.1 | BT-LOCAL-auth | BT-LOCAL-db | ICE: 0.27 (I: 2.0, C: 80%) | [[L-001]], [[A-002]] |\n"
    "| BT-003 | Existing issue | planned | type:bug, mode:AFK, tier:slice, size:small | — | — | — | ICE: 0.50 (I: 1.0, C: 50%) | [[L-002]] |\n"
)
MAP = (
    "---\ntype: backlog\n---\n# BACKLOG MAP\n\n## Label Registry\n- **Area (`area:xxx`)**: `area:FE-login`\n\n## Backlog\n"
    "| ID | Title | Status | Labels | Milestone | Parent | Blocked by | ICE | Ref |\n"
    "|:---|:---|:---|:---|:---|:---|:---|:---|:---|\n" + ROWS
)


@pytest.fixture
def project(tmp_path, monkeypatch):
    """A local-tracker project plus a gh shim store holding issues #1-#3 (BT-003 is the real one)."""
    store = tmp_path / "gh-store.json"
    monkeypatch.setenv("L3_GH_STORE", str(store))
    for var in ("GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN"):
        monkeypatch.delenv(var, raising=False)

    def shim(args):
        r = subprocess.run([sys.executable, str(SHIM), *args], capture_output=True, text=True, encoding="utf-8")
        return r.returncode, r.stdout, r.stderr
    monkeypatch.setattr(reconcile, "_gh_run", shim)

    root = tmp_path / "proj"
    (root / ".memory").mkdir(parents=True)
    (root / "docs" / "prds").mkdir(parents=True)
    (root / "src").mkdir()
    (root / ".memory" / "ARCHITECTURE.md").write_text("---\ntype: architecture\ntracker: local\n---\n# ARCHITECTURE\n", encoding="utf-8")
    (root / ".memory" / "BACKLOG_MAP.md").write_text(MAP, encoding="utf-8")
    (root / "docs" / "prds" / "auth.md").write_text("Build BT-LOCAL-login after BT-LOCAL-db; epic BT-LOCAL-auth.\n", encoding="utf-8")
    (root / "src" / "app.py").write_text("# see BT-LOCAL-db\n", encoding="utf-8")
    (root / ".memory" / "LEARNINGS.md").write_text("Lesson from BT-LOCAL-auth.\n", encoding="utf-8")
    for n in (1, 2, 3):
        shim(["issue", "create", "--title", f"filler {n}", "--body", f"body {n}"])
    monkeypatch.chdir(root)
    return root, store


def gh_state(store):
    return json.loads(store.read_text(encoding="utf-8"))


def new_issues(store):
    return [i for n, i in sorted(gh_state(store)["issues"].items(), key=lambda kv: int(kv[0])) if int(n) > 3]


def test_dry_run_writes_nothing(project, capsys):
    root, store = project
    before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
    calls_before = len(gh_state(store)["invocations"])
    assert ts.main([]) == 0
    out = capsys.readouterr().out
    for bt in ("BT-LOCAL-auth", "BT-LOCAL-db", "BT-LOCAL-login"):
        assert bt in out
    assert "dry run" in out.lower()
    assert before == {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
    assert len(gh_state(store)["issues"]) == 3
    seen = gh_state(store)["invocations"][calls_before:]
    assert [a for a in seen if a[:2] in (["issue", "create"], ["issue", "edit"], ["issue", "close"])] == []
    assert [a for a in seen if a[:2] == ["api", "graphql"] and "mutation" in " ".join(a)] == []


def test_apply_creates_issues_rewrites_ids_archives_map_sets_key(project, capsys):
    root, store = project
    assert ts.main(["--apply"]) == 0
    out = capsys.readouterr().out
    issues = {i["title"]: i for i in new_issues(store)}
    assert set(issues) == {"Auth epic", "DB setup", "Login page"}  # the real row BT-003 is not re-created
    auth, db, login = issues["Auth epic"], issues["DB setup"], issues["Login page"]
    assert {l["name"] for l in login["labels"]} == {"type:feature", "mode:HITL", "tier:slice", "size:small", "status:planned"}
    assert login["milestone"] == {"title": "v1.0.1"}
    assert "<!-- tracker-switch: BT-LOCAL-login -->" in login["body"]
    assert "ICE: 0.27 (I: 2.0, C: 80%)" in login["body"] and "Refs: [[L-001]], [[A-002]]" in login["body"]
    assert db["state"] == "CLOSED" and login["state"] == "OPEN"
    assert login["parent"]["number"] == auth["number"] and db["parent"]["number"] == auth["number"]
    assert [b["number"] for b in login["blockedBy"]] == [db["number"]]
    # existing issue #3 gains its Refs and ICE lines, nothing else changes
    body3 = gh_state(store)["issues"]["3"]["body"]
    assert body3.startswith("body 3") and "Refs: [[L-002]]" in body3 and "ICE: 0.50 (I: 1.0, C: 50%)" in body3
    # ids rewritten under docs/ and .memory/, other files reported and untouched
    num = {k: f"BT-{v['number']:03d}" for k, v in (("login", login), ("db", db), ("auth", auth))}
    assert (root / "docs" / "prds" / "auth.md").read_text(encoding="utf-8") == (
        f"Build {num['login']} after {num['db']}; epic {num['auth']}.\n")
    assert (root / ".memory" / "LEARNINGS.md").read_text(encoding="utf-8") == f"Lesson from {num['auth']}.\n"
    assert (root / "src" / "app.py").read_text(encoding="utf-8") == "# see BT-LOCAL-db\n"
    assert "src" in out and "BT-LOCAL-db" in out and "not edited" in out
    # the map is archived whole, the key flips last
    assert not (root / ".memory" / "BACKLOG_MAP.md").exists()
    assert (root / ".memory" / "archive" / "BACKLOG_MAP.md").read_text(encoding="utf-8") == MAP
    assert reconcile.read_tracker(root / ".memory" / "ARCHITECTURE.md") == "github"


def test_rerun_is_idempotent(project, capsys):
    root, store = project
    ts.main(["--apply"])
    snapshot = gh_state(store)["issues"]
    capsys.readouterr()
    assert ts.main(["--apply"]) == 0
    assert "already" in capsys.readouterr().out.lower()
    assert gh_state(store)["issues"] == snapshot


def test_resume_after_an_interrupted_run_creates_nothing_twice(project):
    """The map is still there and the key still says local (a crash before the last steps): a re-run finds the
    issues by their marker, adds no second copy, and appends no second Refs line."""
    root, store = project
    ts.main(["--apply"])
    snapshot = gh_state(store)["issues"]
    shutil.copy(root / ".memory" / "archive" / "BACKLOG_MAP.md", root / ".memory" / "BACKLOG_MAP.md")
    ts.write_tracker(root / ".memory" / "ARCHITECTURE.md", "local")
    assert ts.main(["--apply"]) == 0
    assert gh_state(store)["issues"] == snapshot
    assert reconcile.read_tracker(root / ".memory" / "ARCHITECTURE.md") == "github"


def test_a_failed_create_stops_the_run_before_any_rewrite(project, monkeypatch, capsys):
    root, store = project
    real = reconcile._gh_run
    monkeypatch.setattr(reconcile, "_gh_run",
                        lambda a: (1, "", "milestone not found") if a[:2] == ["issue", "create"] and "Login page" in a else real(a))
    assert ts.main(["--apply"]) == 1
    assert "BT-LOCAL-login" in capsys.readouterr().out
    assert (root / ".memory" / "BACKLOG_MAP.md").exists()
    assert (root / "docs" / "prds" / "auth.md").read_text(encoding="utf-8").startswith("Build BT-LOCAL-login")
    assert reconcile.read_tracker(root / ".memory" / "ARCHITECTURE.md") == "local"


def test_gh_unavailable_halts_without_touching_anything(project, monkeypatch, capsys):
    root, _ = project
    monkeypatch.setattr(reconcile, "_gh_run", lambda a: (1, "", "not logged in"))
    assert ts.main(["--apply"]) == 2
    assert "gh" in capsys.readouterr().out.lower()
    assert (root / ".memory" / "BACKLOG_MAP.md").exists()
