#!/usr/bin/env python3
"""BT-144 guards: 2z-write-spec is a thin user-invoked orchestrator over 2a -> 2b -> 2c (no copied bodies), registered everywhere skill counts are pinned."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"


def _read(rel: str) -> str:
    return (SRC / rel).read_text(encoding="utf-8")


def _phase(text: str, start: str, end: str) -> str:
    return text.split(start)[1].split(end)[0]


def test_2z_is_a_user_invoked_lifecycle_skill_like_1c():
    fm = re.match(r"^---\n(.*?)\n---", _read("workflows/2z-write-spec.md"), re.S).group(1)
    assert re.search(r"^name: 2z-write-spec$", fm, re.M)
    assert "disable-model-invocation: true" in fm
    assert 'triggers: ["user"]' in fm
    assert "stratos.layer: lifecycle" in fm and "stratos.mode: HITL" in fm
    assert "never autonomously" in fm


def test_2z_names_the_three_units_and_copies_no_bodies():
    text = _read("workflows/2z-write-spec.md")
    for unit in ("2a-write-prd", "2b-interface-design", "2c-reconcile-specs"):
        assert unit in text, unit
    for unit_only in ("ATOMIC MINTING RULE", "Greenfield Bootstrap Deltas", "### Scan Matrix", "Context Isolation Rule:**"):
        assert unit_only not in text, unit_only


def test_2z_phases_run_the_units_in_order():
    text = _read("workflows/2z-write-spec.md")
    order = [text.index(h) for h in ("## Phase 0", "## Phase 1", "## Phase 2", "## Phase 3", "## Phase 4")]
    assert order == sorted(order)
    assert "/2a-write-prd" in _phase(text, "## Phase 1", "## Phase 2")
    assert "/2b-interface-design" in _phase(text, "## Phase 2", "## Phase 3")
    assert "/2c-reconcile-specs" in _phase(text, "## Phase 3", "## Phase 4")


def test_2z_phase_0_loads_memory_once_and_detects_resume():
    p0 = _phase(_read("workflows/2z-write-spec.md"), "## Phase 0", "## Phase 1")
    assert "load-memory" in p0 and "once" in p0
    assert "docs/prds/BT-<padded>-*.md" in p0
    assert "status: stable" in p0
    assert ".tmp/2z-BT-<padded>-decisions.md" in p0 and ".tmp/2z-<slug>-decisions.md" in p0


def test_2z_phase_0_resume_reads_the_log_and_owns_the_rename():
    p0 = _phase(_read("workflows/2z-write-spec.md"), "## Phase 0", "## Phase 1")
    assert "last 5 lines" in p0
    assert "BT-LOCAL-<slug>" in p0
    assert "renames" in p0 and "both names" in p0


def test_2z_phase_3_passes_a_2c_skip_through_to_hand_off():
    p3 = _phase(_read("workflows/2z-write-spec.md"), "## Phase 3", "## Phase 4")
    assert "[SKIP]" in p3 and "Phase 4" in p3


def test_2z_phase_4_offers_an_optional_user_owned_commit_one_liner():
    p4 = _read("workflows/2z-write-spec.md").split("## Phase 4")[1]
    assert "git add docs/prds docs/design docs/research" in p4 and "reconcile specs" in p4
    assert "ptional" in p4


def test_2z_load_memory_is_worded_as_the_units_cached_status():
    p0 = _phase(_read("workflows/2z-write-spec.md"), "## Phase 0", "## Phase 1")
    assert "`cached`" in p0 and "skip it" not in p0


def test_2z_phase_2_honours_skip_path_and_path_a_pause():
    p2 = _phase(_read("workflows/2z-write-spec.md"), "## Phase 2", "## Phase 3")
    assert "skip" in p2.lower() and "Path A" in p2
    assert "/2z-write-spec BT-<n>" in p2 and "resum" in p2.lower()


def test_2z_phase_3_runs_2c_in_main_thread_and_keeps_edits_uncommitted():
    p3 = _phase(_read("workflows/2z-write-spec.md"), "## Phase 3", "## Phase 4")
    assert "main thread" in p3
    assert "Do **not** wrap" in p3
    assert "uncommitted" in p3


def test_2z_phase_4_routes_like_2b_and_states_the_depth_budget():
    text = _read("workflows/2z-write-spec.md")
    p4 = text.split("## Phase 4")[1]
    assert "/3a-version-planning" in p4 and "/3b-create-issue" in p4
    assert "at most 2 levels" in text


def test_2a_handoff_offers_the_chain():
    p5 = _phase(_read("workflows/2a-write-prd.md"), "## Phase 5", "## Label Registry")
    assert "/2z-write-spec BT-<padded>" in p5


def test_3z_authority_names_2z_as_user_invoked_spec_orchestrator():
    assert "`2z` is the user-invoked spec orchestrator" in _read("workflows/3z-afk-loop.md")


def test_2z_registered_in_check_suite_and_readme():
    assert '"2z-write-spec"' in _read("scripts/check_suite.py")
    assert "| `/2z-write-spec` |" in (ROOT / "README.md").read_text(encoding="utf-8")
