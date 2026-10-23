"""BT-146: docs/okf-view.html is generated from gitignored `.memory/` text, so this public repo must not track it."""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_generated_okf_view_is_gitignored():
    lines = [ln.strip() for ln in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()]
    assert "docs/okf-view.html" in lines


def test_generated_okf_view_is_not_tracked():
    """BT-157: .gitignore does not untrack a committed file; the view must also be out of the index."""
    tracked = subprocess.run(["git", "ls-files", "docs/okf-view.html"], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout.strip()
    assert not tracked, "docs/okf-view.html is tracked: git rm --cached docs/okf-view.html"


def test_okf_view_indexes_a_github_mode_project_without_a_backlog_map(tmp_path):
    """BT-198: `tracker: github` has no BACKLOG_MAP.md; the visualizer still scans the memory layer and keeps `[[BT-n]]` links as written."""
    import sys
    sys.path.insert(0, str(ROOT / "src" / "scripts"))
    import okf_view
    mem = tmp_path / ".memory"
    mem.mkdir()
    (mem / "LEARNINGS.md").write_text("- **[[L-001]] [ASSUMED]** a lesson. Source: BT-007.\n", encoding="utf-8")
    defs = okf_view.scan_definitions(tmp_path)
    assert defs == {"L-001": ".memory/LEARNINGS.md"}
    assert okf_view.rewrite_content("See [[BT-007]] and [[L-001]]", ".memory/ARCHITECTURE.md", defs) == "See [[BT-007]] and [L-001](LEARNINGS.md)"
