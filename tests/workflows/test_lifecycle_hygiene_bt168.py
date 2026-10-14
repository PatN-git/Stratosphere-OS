#!/usr/bin/env python3
"""BT-168 guards: ephemeral directions.html (H3), 3a epic inputs (H1) and 3a release close (H1). Wording pins only --
the `gh api` milestone close cannot run offline."""
import re

from conftest import SRC, read_src as _read

A3 = _read("workflows/3a-version-planning.md")


def _phase4(text: str) -> str:
    return text.split("## Phase 4: Commit & Sync")[1].split("## Re-run Notes")[0]


# --- H3: directions.html is ephemeral -----------------------------------------

def test_2b_renders_directions_under_tmp_render():
    assert ".tmp/render/docs/design/BT-<padded>-directions.html" in _read("workflows/2b-interface-design.md")


def test_no_src_file_puts_directions_html_under_docs():
    for f in sorted(SRC.rglob("*")):
        if f.suffix in {".md", ".py"}:
            hits = re.findall(r"(?<!\.tmp/render/)docs/design/\S*directions\.html", f.read_text(encoding="utf-8"))
            assert not hits, (f.name, hits)


# --- H1: 3a epic inputs ---------------------------------------------------------

def test_3a_reads_complexity_not_a_size_column():
    assert "complexity (§12)" in A3
    assert "scope, size" not in A3


def test_3a_proposes_new_deps_at_the_halt_and_writes_them_amend_only():
    assert "`[NEW-DEP] BT-<padded> ← BT-<prereq>`" in A3
    assert "it is proposed at the Phase 2.5 halt" in A3
    step = next(l for l in _phase4(A3).splitlines() if l.startswith("4. **Record confirmed dependencies"))
    for part in ("`addBlockedBy` mutation per `references/github-issue-relations.md`", "`Blocked by` column in `BACKLOG_MAP.md`",
                 "explicit confirmation", "Never remove a `Blocked by` entry in 3a", "`2a` remains the birth writer"):
        assert part in step, part


def test_3a_reconcile_gate_checks_milestone_and_blocked_by():
    assert "--fields milestone,blocked_by" in A3
    assert "--fields milestone`" not in A3


def test_2a_still_mints_epics_with_empty_blocked_by():
    assert "`Blocked by = —`" in _read("workflows/2a-write-prd.md")


# --- H1: 3a closes shipped releases ----------------------------------------------

def test_3a_scale_gate_has_a_closable_release_condition():
    gate = A3.split("**Scale-gate:**")[1].split("Else skip:")[0]
    assert "it has ≥ 1 parent epic, all `done`" in gate
    assert "every open `vX.Y.*` milestone reports `open_issues == 0`" in gate


def test_3a_close_is_all_or_nothing_per_release():
    phase1 = A3.split("## Phase 1")[1].split("## Phase 2:")[0]
    assert "Any `open_issues > 0` → the release is not closable; surface it instead" in phase1
    close = next(l for l in _phase4(A3).splitlines() if l.startswith("1. **Release close"))
    assert "All-or-nothing per release" in close and "close none of them and surface those milestones" in close


def test_3a_close_out_only_path_hands_off():
    assert "*\"Release vX.Y closed.\"*" in A3


def test_3b_defaults_only_onto_open_milestones():
    text = _read("workflows/3b-create-issue.md")
    assert "milestones?state=open" in text and "milestones?state=all" not in text
    assert "never mint onto a closed release" in text


def test_2b_handoff_names_both_promotion_phases():
    assert "`needs_spec → planned` (Phase 1 or 5)" in _read("workflows/2b-interface-design.md")


def test_milestone_close_is_behind_the_halt_and_precedes_shipped_tag():
    p4 = _phase4(A3)
    close = next(l for l in p4.splitlines() if l.startswith("1. **Release close"))
    assert "gh api -X PATCH repos/{owner}/{repo}/milestones/<n> -f state=closed" in close
    assert "never auto-run" in close and "confirmed at the Phase 2.5 halt" in close
    roadmap = next(l for l in p4.splitlines() if l.startswith("2. **Write `docs/ROADMAP.md`"))
    assert "`[SHIPPED <date>]` only for a release whose milestones step 1 closed" in roadmap
    halt = A3.split("3. **Present and Halt:**")[1].split("\n")[0]
    assert "each release proposed for close" in halt and "milestone close" in halt


def test_only_3a_closes_milestones():
    for f in sorted((SRC / "workflows").glob("*.md")):
        if f.stem != "3a-version-planning":
            assert "-f state=closed" not in f.read_text(encoding="utf-8"), f.name


def test_0b_hints_at_3a_when_a_release_is_done():
    text = _read("workflows/0b-stop-session.md")
    assert "When every epic in a `vX.Y.0` release is then `done`, suggest `/3a-version-planning`" in text


def test_roadmap_template_says_3a_closes_the_milestones_before_shipped():
    assert "`/3a-version-planning` closes them once every epic is `done`, then writes this tag" in _read(
        "references/ROADMAP-template.md")
