#!/usr/bin/env python3
"""BT-177 guards: 3z `[NO-RED]` gate, 4a Dismissed list, 4b red-flags + intent check, 4c deltas and metric honesty."""
import json
import re

from conftest import read_src as _read

RF = ".agents/skills/4b-audit-architecture-drift/references/design-red-flags.md"


def _between(text, start, end=None):
    i = text.index(start)
    j = text.index(end, i + len(start)) if end else len(text)
    return text[i:j]


def test_3z_decision_gate_rejects_tests_without_observed_red():
    gate = _between(_read("workflows/3z-afk-loop.md"), "### Step 2C", "_Loop done when")
    line = next(l for l in gate.splitlines() if "[NO-RED]" in l)
    assert "tests_added" in line and "red_confirmed" in line
    assert "[UNCOVERED]" in line, "same retry/blocked path as an uncovered AC"


def test_4a_standards_auditor_returns_dismissed_and_phase3_and_pass_print_it():
    text = _read("workflows/4a-verify-and-ship.md")
    auditor = next(l for l in text.splitlines() if l.lstrip().startswith("2. **Standards Auditor**"))
    assert "Dismissed" in auditor and "cap 3" in auditor
    assert "Dismissed" in _between(text, "### 2. Standards", "## Phase 4")
    assert "Dismissed" in _between(text, "### Clean Exit Rule", "## Phase 3")


def test_4b_phase2_cites_red_flags_by_absolute_path_and_matrix_names_the_flag():
    text = _read("workflows/4b-audit-architecture-drift.md")
    assert RF in _between(text, "## Phase 2", "## Deep Scan Matrix")
    assert "name the flag" in _between(text, "## Deep Scan Matrix", "## Confidence scale")


def test_4b_intent_check_gates_80_and_needs_a_stated_reason_that_still_applies():
    rule = _between(_read("workflows/4b-audit-architecture-drift.md"), "## Confidence scale", "## Clean Exit Rule")
    assert "git log" in rule and "80" in rule
    assert "states the reason" in rule and "still applies" in rule
    assert "Dismissed (deliberate)" in rule


def test_4c_reads_previous_last_run_before_it_is_overwritten():
    text = _read("workflows/4c-codebase-health-audit.md")
    read_at = text.index("previous `.last-run.json`")
    assert read_at < text.index("### 4.2 Update Last-Run"), "baseline is read before 4.2 overwrites it"


def test_4c_regression_flag_is_deterministic_counts_only_with_no_delta_fallback():
    text = _read("workflows/4c-codebase-health-audit.md")
    block = _between(text, "### 3.6", "## Phase 4")
    assert "[REGRESSION]" in block and "[NO-DELTA]" in block
    assert "cves_high_plus" in block and "skipped_tests" in block
    for differs in ("scan_targets", "matrix_version"):
        assert differs in block
    assert "advisory" in block


def _schema():
    t = _read("references/health-audit-report-template.md")
    return json.loads(re.search(r"```json\n(.*?)```", _between(t, "## `.last-run.json` Schema"), re.S).group(1))


def test_last_run_schema_parses_with_per_pass_counts_and_deterministic_fields():
    s = _schema()
    assert set(s["by_pass"]) == {"security", "dependency", "reliability", "correctness", "maintainability", "performance"}
    for key in ("skipped_tests", "cves_high_plus", "matrix_version", "passes_inconclusive"):
        assert key in s, key


def test_4c_clean_exit_writes_full_schema_and_healthy_needs_no_inconclusive_pass():
    clean = _between(_read("workflows/4c-codebase-health-audit.md"), "## Clean Exit")
    assert "full schema" in clean
    assert "inconclusive" in clean and "[HEALTHY]" in clean


def test_scan_matrix_c2_numbers_only_from_a_command_and_no_confidence_cap():
    c2 = _between(_read("references/health-audit-scan-matrix.md"), "### C2")
    assert "not measured" in c2 and "command" in c2
    assert "cap" not in c2.lower()


def test_scan_matrix_a2_inconclusive_on_failed_command_and_na_when_input_absent():
    a2 = _between(_read("references/health-audit-scan-matrix.md"), "### A2", "## Subagent B")
    assert "inconclusive" in a2 and "n/a" in a2


def test_scan_matrix_a1_destructive_ops_need_resolved_allowlisted_root_and_skip_sql():
    a1 = _between(_read("references/health-audit-scan-matrix.md"), "### A1", "### A2")
    row = next(l for l in a1.splitlines() if "Destructive" in l)
    assert "allowlisted root" in row and "symlink" in row
    assert "DROP" not in row and "TRUNCATE" not in row
