#!/usr/bin/env python3
"""BT-171 guards: PRD §7 Boundaries (2a, 3b), the shared design red-flags reference (2b), usage-first Path C contracts and per-feature UI patterns-to-reject (design-doc template)."""
import re

from conftest import read_src as _read

FLAGS = ["Shallow module", "Information leakage", "Temporal decomposition", "Pass-through method",
         "Split ownership", "Two ways to do one task", "Importable internals", "Hand-synced list"]
REF = "references/design-red-flags.md"


def _between(text, start, end=None):
    i = text.index(start)
    j = text.index(end, i + len(start)) if end else len(text)
    return text[i:j]


def _template_block(label):
    """One path block of the design-doc template, from its heading to the next `### [Path`."""
    text = _read("references/design-doc-template.md")
    i = text.index(f"### [{label}")
    m = re.search(r"^### \[Path", text[i + 5:], re.M)
    return text[i:i + 5 + m.start()] if m else text[i:]


def test_prd_template_section7_has_three_tier_boundaries():
    s7 = _between(_read("references/PRD-template.md"), "## 7.", "## 8.")
    assert "**Boundaries:**" in s7
    for tier in ("**Always:**", "**Ask first:**", "**Never:**"):
        assert tier in s7, tier
    assert "no paths" in s7 and "not repeated" in s7


def test_2a_phase4_checks_boundaries_mechanically_and_phase3_stays_path_free():
    text = _read("workflows/2a-write-prd.md")
    item = next(l for l in _between(text, "## Phase 4: Validate", "## Phase 5").splitlines() if "Boundaries" in l)
    assert "three tier lines" in item and "`none — <reason>`" in item
    rule = next(l for l in _between(text, "## Phase 3: Draft", "## Phase 4").splitlines() if "Boundaries" in l)
    assert "path-free" in rule


def test_red_flags_reference_names_all_eight_and_credits_pstack():
    text = _read(REF)
    assert [h for h in re.findall(r"^## (.+)$", text, re.M) if h in FLAGS] == FLAGS
    assert "pstack" in text and "Lauren Tan" in text and "MIT" in text
    assert "revise or reject" in text


def test_red_flags_reference_is_delta_only_and_points_at_existing_definitions():
    text = _read(REF)
    shallow = _between(text, "## Shallow module", "## Information leakage")
    passthrough = _between(text, "## Pass-through method", "## Split ownership")
    assert "ARCHITECTURE.md" in shallow and "Deletion Test" in shallow
    assert "code-smell-baseline.md" in passthrough and "Middle Man" in passthrough
    assert len(shallow) < 450 and len(passthrough) < 450, "overlapping flags are pointers, not restated definitions"
    assert len(text.encode("utf-8")) < 2600


def test_2b_phase_2_5_and_path_c_cite_red_flags():
    text = _read("workflows/2b-interface-design.md")
    assert REF in _between(text, "## Phase 2.5", "## Phase 3")
    step1 = next(l for l in _between(text, "### Path C (Non-UI", "### UX / System").splitlines() if l.startswith("1. "))
    assert REF in step1 and "deep vs. shallow" not in step1
    assert step1.index("usage") < step1.index("signatures"), "caller usage is written before types/signatures"
    assert "name the flags that apply" in _between(text, "## Phase 2.5", "## Phase 3")


def test_path_c_template_orders_usage_before_signature_and_has_scrap_and_errors_rows():
    block = _template_block("Path C")
    assert block.index("Caller Usage") < block.index("Interface/API Signature")
    assert "Compatibility & Errors" in block and "additive" in block and "one error shape" in block
    scrap = _between(block, "Scrap Signals")
    assert "## Deviations" in scrap and "/2c-reconcile-specs" in scrap


def test_path_ab_blocks_have_patterns_to_reject_and_states_line_has_permission_and_na():
    for label in ("Path A", "Path B"):
        block = _template_block(label)
        assert "Patterns to Reject" in block and "[[DR-001]]" in block, label
    text = _read("references/design-doc-template.md")
    states = next(l for l in text.splitlines() if l.startswith("- **UI (Path A/B):**"))
    assert "permission" in states and "n/a" in states
    b2 = _read("workflows/2b-interface-design.md")
    assert "Patterns to Reject" in _between(b2, "### Path A", "### Path C")


def test_3b_copies_ask_first_never_into_slice_body_with_halt_semantics():
    drafting = _between(_read("workflows/3b-create-issue.md"), "Contracts/invariants", "Verifiable AC")
    line = next(l for l in drafting.splitlines() if "Boundaries" in l)
    assert "§7" in line and "Ask first" in line and "Never" in line
    assert "HITL" in line and "stuck" in line
