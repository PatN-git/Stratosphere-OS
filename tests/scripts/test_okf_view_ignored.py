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
