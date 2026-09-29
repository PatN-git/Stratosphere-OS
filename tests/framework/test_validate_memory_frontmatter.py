"""validate_memory.py flags v0.1 frontmatter drift in docs/ (okf-protocol §2).

`timestamp:` is retired inside the bundle scope (replaced by `generated:`) and
`status:` is exactly `draft | stable | deprecated` (discovery briefs keep their
routing vocab). Both are WARNINGS (exit 2), never errors, so a consumer project with
legacy v0.1 docs is nudged rather than blocked. Applies to docs/ and .memory/ (the
memory templates now ship `generated:`, so nothing legitimate still carries timestamp:).
"""
import subprocess
import sys

from conftest import REPO_ROOT

SCRIPT = REPO_ROOT / "src" / "scripts" / "validate_memory.py"

GOOD = "---\ntype: prd\ntitle: t\ngenerated:\n  by: 2a-write-prd\n  at: 2026-09-29\nstatus: stable\nversion: \"4.1.0\"\n---\n# t\n"


def doc(root, rel, frontmatter):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(f"---\n{frontmatter}\n---\n# body\n", encoding="utf-8")


def run(root):
    r = subprocess.run([sys.executable, str(SCRIPT), "--path", ".memory"], cwd=root,
                       capture_output=True)
    return r.returncode, r.stdout.decode("utf-8", errors="replace")


def test_flags_timestamp_and_bad_status_as_warnings(tmp_path):
    doc(tmp_path, "docs/prds/ts.md", "type: prd\ntimestamp: 2026-09-28\ngenerated:\n  by: x\n  at: 2026-09-28")
    doc(tmp_path, "docs/prds/bad-status.md", "type: prd\ngenerated:\n  by: x\n  at: 2026-09-28\nstatus: approved")
    (tmp_path / "docs/prds/good.md").write_text(GOOD, encoding="utf-8")
    doc(tmp_path, "docs/discovery/brief.md", "type: discovery-brief\ngenerated:\n  by: x\n  at: 2026-09-28\nstatus: ready-for-prd")
    doc(tmp_path, "docs/plans/comment.md", "type: plan\ngenerated:\n  by: x\n  at: 2026-09-28\nstatus: deprecated  # was: COMPLETE")
    doc(tmp_path, "docs/plans/quoted.md", "type: plan\ngenerated:\n  by: x\n  at: 2026-09-28\nstatus: \"stable\"")
    doc(tmp_path, "docs/plans/archive/old.md", "type: plan\ntimestamp: 2026-01-01\nstatus: approved")
    doc(tmp_path, ".memory/STATUS.md", "type: status\ntimestamp: 2026-07-17")

    rc, out = run(tmp_path)
    warnings = [l for l in out.splitlines() if "[WARNING]" in l]

    assert rc == 2, out
    assert not any("[ERROR]" in l for l in out.splitlines()), out
    assert any("ts.md" in w and "timestamp" in w for w in warnings), warnings
    assert any("bad-status.md" in w and "approved" in w for w in warnings), warnings
    flagged = " ".join(warnings)
    assert any("STATUS.md" in w and "timestamp" in w for w in warnings), warnings
    for clean in ("good.md", "brief.md", "comment.md", "quoted.md", "old.md"):
        assert clean not in flagged, f"{clean} should not be flagged: {warnings}"


def test_clean_docs_stay_clean(tmp_path):
    (tmp_path / "docs/prds").mkdir(parents=True)
    (tmp_path / "docs/prds/good.md").write_text(GOOD, encoding="utf-8")
    rc, out = run(tmp_path)
    assert rc == 0, out
