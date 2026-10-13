#!/usr/bin/env python3
"""BT-165 guards: deterministic artifact links. The discovery brief is located by `linked-prd:` (briefs are slug-only), PRD frontmatter carries `discovery:`/`research:`, and spec paths for a slice are keyed to its parent. Later slices extend this file."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"


def _read(rel: str) -> str:
    return (SRC / rel).read_text(encoding="utf-8")


def test_no_workflow_locates_a_brief_by_bt_id():
    # Briefs are slug-only; a BT-<padded>-* filename pattern never matches one.
    for f in sorted((SRC / "workflows").glob("*.md")):
        assert "docs/discovery/BT-" not in f.read_text(encoding="utf-8"), f.name


LOCATOR = ("whose frontmatter has `linked-prd: BT-<padded>`; "
           "if none, 2a's slug fuzzy-match (2a Phase 1 step 5)")


def test_2c_and_2z_share_one_brief_locator():
    # One rule, worded identically, so the two readers cannot drift apart.
    for rel in ("workflows/2c-reconcile-specs.md", "workflows/2z-write-spec.md"):
        assert LOCATOR in _read(rel), rel


def test_2a_fills_the_prd_links():
    assert "`discovery:` / `research:`" in _read("workflows/2a-write-prd.md")


def test_prd_template_frontmatter_links_brief_and_research():
    fm = _read("references/PRD-template.md").split("## Artifact frontmatter")[1].split("## Artifact body")[0]
    assert "\ndiscovery:" in fm and "\nresearch:" in fm


def test_slice_workflows_key_spec_paths_to_the_parent():
    for rel in ("workflows/3d-implement-issue.md", "workflows/4a-verify-and-ship.md", "workflows/3z-afk-loop.md"):
        text = _read(rel)
        for stale in ("docs/prds/BT-<padded>", "docs/design/BT-<padded>"):
            assert stale not in text, (rel, stale)
        assert "BT-<parentPadded>" in text, rel
        assert "standalone slice has no" in text, rel


# --- BT-164: the brief's sections have a home downstream ---------------------

# Read by other mechanisms or not carried into the PRD (RAT Carry-Over reads Riskiest Assumption too).
NOT_INGESTED = {"Ask", "Prior Art", "Riskiest Assumption", "Recommended Next Step"}


def _brief_sections() -> list[str]:
    body = _read("references/discovery_brief_template.md").split("## Artifact body")[1]
    names = []
    for line in body.splitlines():
        m = re.match(r"^## (.+?)(?: \(.*\))?$", line)
        if m:
            names.append(m.group(1))
    return names


def test_brief_template_headings_parse():
    assert {"Problem", "Established Facts", "Success State", "Decoupled Follow-ups",
            "Constraints & Settled Decisions"} <= set(_brief_sections())


def test_every_brief_section_is_ingested_by_2a_or_exempt():
    lines = [l for l in _read("workflows/2a-write-prd.md").splitlines()
             if l.startswith("**Discovery-brief ingestion")]
    assert len(lines) == 1
    for name in _brief_sections():
        assert name in lines[0] or name in NOT_INGESTED, name


def test_cheapest_test_offers_brownfield_options():
    line = next(l for l in _read("references/discovery_brief_template.md").splitlines()
                if "cheapest_test" in l)
    for opt in ("offline sample benchmark", "read-only production probe", "simulation harness"):
        assert opt in line, opt


NEW_GATES = ("Established Facts", "Success State", "Decoupled Follow-ups")


def test_1b_phase6_gate_checks_the_new_sections():
    gate = _read("workflows/1b-concept-framing.md").split("## Phase 6")[1].split("## Phase 7")[0]
    for s in NEW_GATES:
        assert s in gate, s


def test_1c_self_review_checks_the_new_sections():
    gate = _read("workflows/1c-concept-map.md").split("4. **Self-Review")[1].split("5. **Crystallize")[0]
    for s in NEW_GATES:
        assert s in gate, s


def test_1b_hand_off_points_to_2a_and_repeats_no_section_list():
    line = next(l for l in _read("workflows/1b-concept-framing.md").splitlines()
                if l.startswith("**Hand-off contract:**"))
    assert "Discovery-brief ingestion" in line and "2a" in line
    assert "§" not in line


def test_brief_links_to_concept_map_and_names_both_writers():
    tpl = _read("references/discovery_brief_template.md")
    assert "\nconcept-map:" in tpl
    assert "1b-concept-framing | 1c-concept-map" in tpl
    assert "generated.by: 1c-concept-map" in _read("workflows/1c-concept-map.md")
    assert "`concept-map:`" in _read("workflows/2c-reconcile-specs.md")


def test_3b_reads_the_brief_and_flags_gaps():
    text = _read("workflows/3b-create-issue.md")
    assert "`discovery:`" in text and "[BRIEF-GAP]" in text and "Established Facts" in text


def test_rat_status_values_route_to_sections():
    assert "`untested | running | failed` → §10" in _read("workflows/2a-write-prd.md")


def test_design_template_hands_off_to_3d():
    text = _read("references/design-doc-template.md")
    assert "## Handoff Notes for 3d/4a" in text and "that 3c must" not in text
