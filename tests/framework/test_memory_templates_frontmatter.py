"""Memory templates mint in-scope .memory/ documents, so they carry OKF v0.2 `generated:`.

`timestamp:` is retired inside the bundle scope (okf-protocol §1-§2). The templates
are copied byte-for-byte by scaffold.py, so whatever frontmatter they ship is what
every new project starts with.
"""
import re
import sys

import pytest

from conftest import REPO_ROOT

TEMPLATES = sorted((REPO_ROOT / "src" / "memory-templates").glob("*.md"))
# DESIGN.md follows Google's DESIGN.md spec and is exempt from OKF stamping (okf-protocol §5).
MINTING = [t for t in TEMPLATES if t.name != "DESIGN.md"]

sys.path.insert(0, str(REPO_ROOT / "src" / "scripts"))
import _versioning  # noqa: E402


def frontmatter(path):
    m = re.match(r"^---\r?\n(.*?)\r?\n---", path.read_text(encoding="utf-8"), re.S)
    assert m, f"{path.name} has no frontmatter"
    return m.group(1)


@pytest.mark.parametrize("tpl", MINTING, ids=lambda p: p.name)
def test_template_carries_generated_not_timestamp(tpl):
    fm = frontmatter(tpl)
    assert not re.search(r"^timestamp:", fm, re.M), f"{tpl.name} still ships retired timestamp:"
    assert re.search(r"^generated:\s*\n[ \t]+by:\s*\S+\s*\n[ \t]+at:\s*\S+", fm, re.M), \
        f"{tpl.name} must carry generated: {{by, at}}"


def test_version_reader_falls_back_to_generated_at():
    text = '---\ntype: x\ngenerated:\n  by: stratosphere-setup\n  at: 2026-09-29\nversion: "1.0.0"\n---\nbody\n'
    assert _versioning.read_version(text, "x.md") == ("1.0.0", "2026-09-29")


def test_version_reader_still_reads_legacy_timestamp():
    text = '---\ntype: x\ntimestamp: 2026-07-08\nversion: "1.0.0"\n---\nbody\n'
    assert _versioning.read_version(text, "x.md") == ("1.0.0", "2026-07-08")
