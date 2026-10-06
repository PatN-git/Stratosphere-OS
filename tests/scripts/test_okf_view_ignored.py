"""BT-146: docs/okf-view.html is generated from gitignored `.memory/` text, so this public repo must not track it."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_generated_okf_view_is_gitignored():
    lines = [ln.strip() for ln in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()]
    assert "docs/okf-view.html" in lines
