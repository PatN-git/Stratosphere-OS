#!/usr/bin/env python3
"""BT-166 (3b side) guards: sibling read, explicit PRD scope, design link on the Build slice, `[MED]`, migration items, slice milestone."""
import importlib.util
import re

from conftest import SRC, read_src as _read

spec = importlib.util.spec_from_file_location("reconcile", SRC / "scripts" / "reconcile.py")
rec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rec)


def _3b() -> str:
    return _read("workflows/3b-create-issue.md")


def test_3b_reads_existing_siblings_and_credits_them_in_the_breadth_map():
    text = _3b()
    assert "--json subIssues" in text and "Parent = BT-<parent>" in text
    assert "existing sibling cited by `BT-<n>`" in text


def test_3b_scope_is_explicit_and_blocking_questions_become_spikes_before_drafting():
    text = _3b()
    scope = text[text.index("3. **Scope:**"):text.index("4. **Siblings")]  # lead + nested bullets
    for s in ("§1", "§6", "§7", "§8", "§10"):
        assert s in scope, s
    line = next(l for l in text.splitlines() if l.startswith("   - **§10:**"))
    assert "→ a Spike" in line and "before any drafting" in line


def test_hand_off_lines_of_2a_and_3b_name_the_same_sections():
    sections = ("§1", "§6", "§7", "§8", "§10")
    two_a = next(l for l in _read("workflows/2a-write-prd.md").splitlines() if l.startswith("**Hand-off contract:**"))
    three_b = next(l for l in _3b().splitlines() if l.startswith("**Hand-off contract:**"))
    for s in sections:
        assert s in two_a and s in three_b, s


def test_confidence_map_uses_med_and_accepts_medium_as_legacy():
    text = _3b()
    assert "`[MED]` → `80%`" in text and "`[MEDIUM]` accepted as legacy" in text


def test_build_template_carries_a_design_line_and_spike_does_not():
    tpl = _read("references/issue-templates.md")
    spike, build = tpl.split("## BUILD SLICE (Template B)")
    assert "- **Design:**" in build.split("### Dependencies")[1].split("### Notes")[0]
    assert "**Design:**" not in spike


def test_3b_drafts_fill_the_design_line_and_3d_keys_its_read_on_it():
    assert "`- **Design:**` line" in _3b()
    three_d = _read("workflows/3d-implement-issue.md")
    assert "`Design:` line" in three_d
    assert "design reference in issue/BACKLOG_MAP Ref" not in three_d
    assert "BT-<parentPadded>-interface.md" in three_d and "no PRD/design doc at that path (standalone slice)" in three_d


def test_2c_tags_migrations_and_3b_mints_them_as_slice_1():
    two_c = _read("workflows/2c-reconcile-specs.md")
    assert "`migration:` item" in two_c and "pre-Slice-1 migration for `3b`" not in two_c
    line = next(l for l in _3b().splitlines() if l.startswith("   - **§10:**"))
    assert "`migration:`-tagged item" in line and "Slices 1..k" in line


# A6: confirmed. A slice minted without --milestone has no GitHub milestone, while 3b step 5 writes vX.Y.0
# to its BACKLOG row, so the step-6 gate (all fields) reports drift.
def test_a_slice_without_a_github_milestone_drifts_from_its_backlog_row():
    row = {"status": "planned", "labels": set(), "milestone": "v1.0.0", "parent": "—", "blocked_by": set()}
    gh = {"labels": [{"name": "status:planned"}], "milestone": None}
    assert any("milestone" in d for d in rec.compare(row, gh, set(rec.ALL_FIELDS), False))
    gh["milestone"] = {"title": "v1.0.0"}
    assert not any("milestone" in d for d in rec.compare(row, gh, set(rec.ALL_FIELDS), False))


def test_3b_passes_the_milestone_on_slice_mint_and_step_5_mirrors_it():
    text = _3b()
    assert re.search(r"pass `--milestone \"<vX\.Y\.0>\"` on every slice mint", text)
    assert "milestones?state=open' --jq" in text and "Only for those defaults" in text  # open-milestone check, defaults only
    assert "step-4 Milestone value" in text
