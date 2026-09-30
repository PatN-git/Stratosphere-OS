"""BT-119: legacy per-host installers are retired; nothing live may reference them.

Superseded by the canonical dist/skills bundle (BT-118) and the Antigravity bridge
(BT-120). Historical docs (research, PRD, design, archive) keep their mentions.
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SELF = Path(__file__).resolve()

LEGACY = [
    "scripts/install-claude-code.sh",
    "scripts/install-claude-code.ps1",
    "scripts/install-antigravity.sh",
    "scripts/install-antigravity.ps1",
]
LIVE_ROOTS = ["README.md", "RELEASING.md", "src", "scripts", "build", "tests", ".github", ".claude-plugin", "dist/skills"]
# `install-antigravity-bridge` is the replacement, not a legacy reference.
REF = re.compile(r"install-claude-code|install-antigravity(?!-bridge)")
TEXT_SUFFIXES = {".md", ".sh", ".ps1", ".py", ".txt", ".yml", ".yaml", ".json"}


def _live_files():
    for root in LIVE_ROOTS:
        p = REPO / root
        assert p.exists(), f"scan root missing (renamed?): {root}"
        files = [p] if p.is_file() else p.rglob("*")
        for f in files:
            if f.is_file() and f.suffix in TEXT_SUFFIXES and "__pycache__" not in f.parts and f != SELF:
                yield f


def test_legacy_installer_scripts_are_deleted():
    assert [p for p in LEGACY if (REPO / p).exists()] == []


def test_no_live_references_to_legacy_installers():
    hits = [
        f"{f.relative_to(REPO).as_posix()}:{n}"
        for f in _live_files()
        for n, line in enumerate(f.read_text(encoding="utf-8", errors="ignore").splitlines(), 1)
        if REF.search(line)
    ]
    assert hits == []
