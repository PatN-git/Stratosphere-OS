# md-crosscheck: the S6 contract (BT-200, BT-221): deleted map-diff / heal / drift prose and code, and the retired BACKLOG_MAP store, vs src/ and the always-loaded rules
"""BT-200: no mirror write, map diff or heal remains. The patterns are narrow on purpose: `--summary` is a real
`pr_body.py build` flag and "mirror" is legitimate in PRD/roadmap prose."""
import re

import pytest

from conftest import REPO_ROOT, SRC, read_src

DEAD = [r"reconcile\.py[^`\n]*--(heal|summary|require-gh)", r"nightly_state\.py drift", r"MIRROR-UNVERIFIED",
        r"faithful mirror", r"Backlog Drift", r"\[CHRONIC", r"stale_blocker", r"\bmap=", r"map_only="]
MEMORY_PROTOCOL_CHARS_BEFORE = 6749  # characters (not bytes) of src/rules/memory-protocol.md before BT-200
SHRINK = 600
MAP_MIGRATORS = {"commands/stratosphere-update/SKILL.md", "scripts/tracker_switch.py", "scripts/issues.py"}


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


def test_the_map_store_is_retired_and_named_only_by_its_migration():
    """BT-221: the local store is one file per issue on the `<repo>/issues` branch. `BACKLOG_MAP.md` survives only
    where a v5 map is migrated (`issues.py migrate`, run by stratosphere-update) or switched (`tracker_switch.py`)."""
    assert not (SRC / "memory-templates" / "BACKLOG_MAP.md").exists()
    hits = [f"{p.relative_to(SRC).as_posix()}:{i}" for p in _sources() if p.relative_to(SRC).as_posix() not in MAP_MIGRATORS
            for i, l in enumerate(p.read_text(encoding="utf-8").splitlines(), 1) if "BACKLOG_MAP" in l]
    assert hits == [], f"BACKLOG_MAP outside its migration: {hits}"


def test_no_local_tracker_store_is_left_in_memory_or_a_map_file():
    """The concept-map `## Tickets` table and the map registry are gone: concept tickets are issues too."""
    hits = [f"{p.relative_to(SRC).as_posix()}:{i}" for p in _sources()
            for i, l in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
            if re.search(r"## Tickets|map's Label Registry|Backlog table", l)]
    assert hits == [], hits


def test_the_local_backend_has_one_id_rule_everywhere():
    """tracker-verbs `create`: the local id is `BT-LOCAL-<slug>`; GitHub mode binds `BT-<padded>` from `gh issue create`."""
    for rel in ("workflows/3b-create-issue.md", "references/tracker-verbs.md", "commands/stratosphere-setup/SKILL.md",
                "rules/memory-protocol.md"):
        assert "BT-LOCAL-<n>" not in read_src(rel), rel
    create = next(l for l in read_src("references/tracker-verbs.md").splitlines() if l.startswith("| `create`"))
    assert "`BT-LOCAL-<slug>`" in create and "-2" in create, create
    assert "BT-LOCAL-<slug>" in read_src("rules/memory-protocol.md")
    assert "MUST emit BT ids in zero-padded" not in read_src("commands/stratosphere-setup/SKILL.md")
    stale = [f"{p.relative_to(SRC)}:{i}" for p in _sources()
             for i, l in enumerate(p.read_text(encoding="utf-8").splitlines(), 1) if "BT-LOCAL-<n>" in l]
    assert stale == [], f"local ids are `BT-LOCAL-<slug>`: {stale}"


def test_the_breaking_v5_release_is_documented_for_consumers():
    notes = (REPO_ROOT / "RELEASING.md").read_text(encoding="utf-8")
    section = notes.split("## v5.0.0 — breaking release", 1)[1]
    for needle in ("tracker_switch.py", "--apply", "tracker: github", "BACKLOG_MAP", "--heal", "needs_review_constitution"):
        assert needle in section, needle
