#!/usr/bin/env python3
"""@google/design.md toolchain pin and lint invocation (BT-135).

The pin documents the version consumers get from unpinned `npx`; the bare
`npx @google/design.md lint` form yields empty output on Windows, so every doc
must use the `-p ... designmd` alias form.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "src"
PIN = "0.4.0"


def test_bt135_design_md_pin_tracks_upstream():
    pkg = json.loads((SRC / "scripts" / "design" / "package.json").read_text(encoding="utf-8"))
    assert pkg["dependencies"]["@google/design.md"] == PIN


def test_bt135_no_bare_npx_design_md_invocation_in_src():
    bare = re.compile(r"npx\s+(?:--yes\s+)?@google/design\.md")
    offenders = [
        str(p.relative_to(REPO_ROOT))
        for p in SRC.rglob("*")
        if p.is_file() and p.suffix in {".md", ".json", ".py", ".sh"}
        and bare.search(p.read_text(encoding="utf-8", errors="ignore"))
    ]
    assert offenders == []
