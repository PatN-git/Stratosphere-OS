# md-crosscheck: the S6 contract (BT-200): deleted map-diff / heal / drift prose and code vs src/, the BACKLOG_MAP template, the always-loaded rules
"""BT-200: no mirror write, map diff or heal remains. The patterns are narrow on purpose: `--summary` is a real
`pr_body.py build` flag and "mirror" is legitimate in PRD/roadmap prose."""
import re

import pytest

from conftest import SRC, read_src

DEAD = [r"reconcile\.py[^`\n]*--(heal|summary|require-gh)", r"nightly_state\.py drift", r"MIRROR-UNVERIFIED",
        r"faithful mirror", r"Backlog Drift", r"\[CHRONIC", r"stale_blocker", r"\bmap=", r"map_only="]
MEMORY_PROTOCOL_CHARS_BEFORE = 6749  # characters (not bytes) of src/rules/memory-protocol.md before BT-200
SHRINK = 600


def _sources():
    return [p for p in SRC.rglob("*") if p.suffix in (".md", ".py") and "__pycache__" not in p.parts
            and p.parts[len(SRC.parts)] != "experimental"]


@pytest.mark.parametrize("pattern", DEAD)
def test_no_deleted_mirror_heal_or_drift_text_remains_in_src(pattern):
    hits = [f"{p.relative_to(SRC)}:{i}" for p in _sources() for i, l in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
            if re.search(pattern, l)]
    assert hits == [], f"{pattern}: {hits[:6]}"


def test_terminal_sync_invariant_is_the_github_gate_only():
    text = read_src("references/terminal-sync-invariant.md")
    assert 'version: "2.0.0"' in text
    assert "--expect" in text and "--with-edges" in text and "--pr-id" in text
    assert "## Heal" not in text and "BACKLOG_MAP" not in text
    assert "mirror" not in re.sub(r"\[MIRROR-[A-Z]+", "", text).lower()  # the gate's output tokens keep their names
    assert len(text) < 3000, len(text)


def test_0d_has_no_backlog_drift_phase():
    text = read_src("workflows/0d-nightly-consolidation.md")
    assert "reconcile.py" not in text and "nightly_state.py drift" not in text
    assert "Phase 3.6" not in text and "heal" not in text.lower()


def test_the_always_loaded_memory_protocol_shrinks_by_at_least_600_characters():
    assert len(read_src("rules/memory-protocol.md")) <= MEMORY_PROTOCOL_CHARS_BEFORE - SHRINK


def test_memory_protocol_points_to_the_tracker_verbs_and_keeps_the_minting_anchor():
    text = read_src("rules/memory-protocol.md")
    assert "## 8. Backlog ID Minting (Late Binding)" in text  # 3b links this anchor
    assert "references/tracker-verbs.md" in text
    assert "BACKLOG_MAP" not in text


def test_the_local_template_cites_the_taxonomy_and_carries_no_github_sync_rules():
    text = read_src("memory-templates/BACKLOG_MAP.md")
    assert "references/label-taxonomy.md" in text
    assert "Label source of truth" not in text and "mirror" not in text.lower()
    for block in ("backlog-rules", "label-canonical", "backlog-header"):  # existing installs carry these ids
        assert f"SOS:BLOCK id={block}" in text, block


def test_update_corroboration_counts_bt_ids_in_backlog_rows_only(tmp_path):
    import sys
    sys.path.insert(0, str(SRC / "scripts"))
    import scaffold
    rows = "## Backlog\n| ID | Title |\n|:---|:---|\n| BT-012 | real |\n"
    with_rules = "## Rules\n- e.g. BT-007 is padded\n\n" + rows
    without_rules = "## Rules\n- padded ids\n\n" + rows
    scaffold.check_cheap_corroborations(tmp_path / "BACKLOG_MAP.md", with_rules, without_rules)
    with pytest.raises(ValueError, match="BT-id set changed"):
        scaffold.check_cheap_corroborations(tmp_path / "BACKLOG_MAP.md", with_rules,
                                            without_rules.replace("BT-012", "BT-013"))
