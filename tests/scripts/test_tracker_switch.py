"""BT-197: `tracker_switch.py` moves a local-tracker project to GitHub and records `tracker: github`.

Seams: `write_tracker` (the frontmatter record, shared with scaffold.py) and `main(argv)` against the
gh shim (`tests/lifecycle-harness/shims/gh_shim.py`, a JSON-store `gh`), with `reconcile._gh_run` pointed at it.
"""
import json
import re
import shutil
import subprocess
import sys

import pytest

from conftest import REPO_ROOT

SCRIPTS = REPO_ROOT / "src" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import issues
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
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
    for k, v in (("user.email", "t@example.com"), ("user.name", "T")):
        subprocess.run(["git", "-C", str(root), "config", k, v], check=True)
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
    monkeypatch.setattr(issues, "today", lambda: "2026-10-27")
    assert issues.main(["migrate"], out=lambda s: None) == 0
    issues.main(["comment", "BT-LOCAL-login", "--body", "Design agreed"], out=lambda s: None)
    assert issues.main(["check"], out=lambda s: None) == 0, "the migrated fixture passes issues.py check"
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
    local_bodies = {r["title"]: r["body"] for r in ts.read_rows()}
    assert ts.main(["--apply"]) == 0
    out = capsys.readouterr().out
    for i in new_issues(store):  # each body byte for byte, plus only the switch marker
        bt = re.search(r"<!-- tracker-switch: (\S+) -->", i["body"]).group(1)
        assert i["body"] == local_bodies[i["title"]] + f"\n\n<!-- tracker-switch: {bt} -->\n"
    issues = {i["title"]: i for i in new_issues(store)}
    assert set(issues) == {"Auth epic", "DB setup", "Login page"}  # the real row BT-003 is not re-created
    auth, db, login = issues["Auth epic"], issues["DB setup"], issues["Login page"]
    assert {l["name"] for l in login["labels"]} == {"type:feature", "mode:HITL", "tier:slice", "size:small", "status:planned"}
    assert login["milestone"] == {"title": "v1.0.1"}
    assert "<!-- tracker-switch: BT-LOCAL-login -->" in login["body"]
    assert login["body"].startswith("Migrated from `.memory/BACKLOG_MAP.md`.\n\n- **Impact:** 2.0\n- **Confidence:** 80%")
    assert "Refs: [[L-001]], [[A-002]]" in login["body"]
    assert [c["body"] for c in login["comments"]] == [
        "Comments from the local tracker:\n\n- 2026-10-27: Design agreed\n\n<!-- tracker-switch-comments: BT-LOCAL-login -->\n"]
    assert db["state"] == "CLOSED" and login["state"] == "OPEN"
    assert login["parent"]["number"] == auth["number"] and db["parent"]["number"] == auth["number"]
    assert [b["number"] for b in login["blockedBy"]] == [db["number"]]
    # existing issue #3 gains its Refs and ICE lines, nothing else changes
    body3 = gh_state(store)["issues"]["3"]["body"]
    assert body3.startswith("body 3") and "Refs: [[L-002]]" in body3 and "- **Confidence:** 50%" in body3
    # ids rewritten under docs/ and .memory/, other files reported and untouched
    num = {k: f"BT-{v['number']:03d}" for k, v in (("login", login), ("db", db), ("auth", auth))}
    assert (root / "docs" / "prds" / "auth.md").read_text(encoding="utf-8") == (
        f"Build {num['login']} after {num['db']}; epic {num['auth']}.\n")
    assert (root / ".memory" / "LEARNINGS.md").read_text(encoding="utf-8") == f"Lesson from {num['auth']}.\n"
    assert (root / "src" / "app.py").read_text(encoding="utf-8") == "# see BT-LOCAL-db\n"
    assert "src" in out and "BT-LOCAL-db" in out and "not edited" in out
    # the migration archived the map; the switch keeps the tracker branch and flips the key last
    assert (root / ".memory" / "archive" / "BACKLOG_MAP.2026-10-27.md").read_text(encoding="utf-8") == MAP
    assert "branch proj/issues kept as the archive" in out
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
    """The key still says local (a crash before the last step): a re-run finds the issues by their marker and
    adds no second copy, comment or Refs line."""
    root, store = project
    ts.main(["--apply"])
    snapshot = gh_state(store)["issues"]
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
    assert (root / "docs" / "prds" / "auth.md").read_text(encoding="utf-8").startswith("Build BT-LOCAL-login")
    assert reconcile.read_tracker(root / ".memory" / "ARCHITECTURE.md") == "local"


def test_gh_unavailable_halts_without_touching_anything(project, monkeypatch, capsys):
    root, _ = project
    monkeypatch.setattr(reconcile, "_gh_run", lambda a: (1, "", "not logged in"))
    assert ts.main(["--apply"]) == 2
    assert "gh" in capsys.readouterr().out.lower()
    assert reconcile.read_tracker(root / ".memory" / "ARCHITECTURE.md") == "local"


def test_an_unmigrated_map_halts_before_gh(project, capsys):
    root, _ = project
    subprocess.run(["git", "branch", "-D", "proj/issues"], cwd=root, check=True, capture_output=True)
    (root / ".memory" / "BACKLOG_MAP.md").write_text(MAP, encoding="utf-8")
    assert ts.main(["--apply"]) == 2
    assert "[MIGRATE-FIRST]" in capsys.readouterr().out


def recording_gh(monkeypatch):
    """Every gh call from here on, in order, as an argv list."""
    calls, real = [], reconcile._gh_run
    monkeypatch.setattr(reconcile, "_gh_run", lambda a: (calls.append(list(a)), real(a))[1])
    return calls


def test_milestones_are_ensured_before_any_issue_is_created(project, monkeypatch):
    root, store = project
    calls = recording_gh(monkeypatch)
    assert ts.main(["--apply"]) == 0
    made = [i for i, a in enumerate(calls) if a[:1] == ["api"] and "title=v1.0.1" in a]
    assert len(made) == 1 and made[0] < min(i for i, a in enumerate(calls) if a[:2] == ["issue", "create"])
    assert any(m["title"] == "v1.0.1" for m in gh_state(store)["milestones"])
    ts.write_tracker(root / ".memory" / "ARCHITECTURE.md", "local")
    assert ts.main(["--apply"]) == 0
    assert len([a for a in calls if a[:1] == ["api"] and "title=v1.0.1" in a]) == 1, "an existing milestone is not created again"


def test_created_issues_hold_the_new_ids_a_claim_is_an_assignee_and_a_rerun_edits_nothing(project, monkeypatch, capsys):
    root, store = project
    (root / ".tmp").mkdir(exist_ok=True)
    text = root / ".tmp" / "login.md"
    text.write_text("Parent: BT-LOCAL-auth\nBlocked by: BT-LOCAL-db\n", encoding="utf-8")
    quiet = lambda s: None
    assert issues.main(["set", "BT-LOCAL-login", "--body-file", str(text)], out=quiet) == 0
    assert issues.main(["comment", "BT-LOCAL-login", "--body", "after BT-LOCAL-db"], out=quiet) == 0
    assert issues.main(["claim", "BT-LOCAL-login", "--by", "feat/login"], out=quiet) == 0
    before = rewrite_roots(root)
    assert ts.main(["--apply"]) == 0
    out = capsys.readouterr().out
    by_title = {i["title"]: i for i in new_issues(store)}
    auth, db, login = by_title["Auth epic"], by_title["DB setup"], by_title["Login page"]
    assert login["body"] == (f"Parent: BT-{auth['number']:03d}\nBlocked by: BT-{db['number']:03d}\n\n"
                             "<!-- tracker-switch: BT-LOCAL-login -->\n")
    comment = login["comments"][0]["body"]
    assert f"after BT-{db['number']:03d}" in comment and "BT-LOCAL-db" not in comment
    assert "<!-- tracker-switch-comments: BT-LOCAL-login -->" in comment
    for i in new_issues(store):
        assert "BT-LOCAL-" not in re.sub(r"<!-- tracker-switch: \S+ -->", "", i["body"]), i["title"]
    assert login["assignees"] == ["@me"] and db["assignees"] == [] and auth["assignees"] == []
    # the count names the files that really changed
    after = rewrite_roots(root)
    assert f"{len([p for p in after if before[p] != after[p]])} file(s) rewritten" in out
    arch = root / ".memory" / "ARCHITECTURE.md"
    # a re-run edits no body, posts no comment and adds no assignee
    ts.write_tracker(arch, "local")
    calls = recording_gh(monkeypatch)
    assert ts.main(["--apply"]) == 0
    assert [a for a in calls if a[:2] in (["issue", "edit"], ["issue", "comment"], ["issue", "create"])] == []
    assert gh_state(store)["issues"][str(login["number"])]["assignees"] == ["@me"]


def rewrite_roots(root):
    """{path: bytes} of the files the switch may rewrite (.memory/ minus the archive and the key's file, docs/)."""
    return {p: p.read_bytes() for top in (".memory", "docs") for p in (root / top).rglob("*")
            if p.is_file() and "archive" not in p.parts and p.name != "ARCHITECTURE.md"}


def test_a_failing_gh_with_no_message_still_names_a_reason(project, monkeypatch, capsys):
    real = reconcile._gh_run
    monkeypatch.setattr(reconcile, "_gh_run",
                        lambda a: (7, "", "") if a[:2] == ["issue", "create"] and "Login page" in a else real(a))
    assert ts.main(["--apply"]) == 1
    assert "[SWITCH-FAIL: gh issue create: exit 7;" in capsys.readouterr().out
