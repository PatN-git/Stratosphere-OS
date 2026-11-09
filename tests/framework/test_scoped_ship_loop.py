# md-crosscheck: build and ship loop (3b, 3d, 3z, 4a, pr-body-and-ship, ci-gate) vs tracker-verbs.md and reconcile.py
"""BT-199: in `tracker: github` mode the build and ship loop asks GitHub for one issue at a time and 4a's ship gate is
one combined `reconcile.py` call. BT-221: the local backend is the issues.py store; no loop file names the old map.
"""
import importlib.util
import re

import pytest

from conftest import SRC, assert_argv_accepted, combined_gate_argv, combined_gate_calls, read_src, write_architecture

LOOP = ["workflows/3b-create-issue.md", "workflows/3d-implement-issue.md", "workflows/3z-afk-loop.md",
        "workflows/4a-verify-and-ship.md", "references/pr-body-and-ship.md", "references/ci-gate.md"]

_spec = importlib.util.spec_from_file_location("reconcile_ship_loop", SRC / "scripts" / "reconcile.py")
rec = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rec)


@pytest.mark.parametrize("rel", LOOP)
def test_no_loop_file_names_the_retired_map(rel):
    offenders = [l.strip()[:120] for l in read_src(rel).splitlines() if re.search(r"BACKLOG|map row|map cell", l)]
    assert offenders == [], f"{rel} still reads or writes the retired map: {offenders}"


def test_3b_mints_the_draft_as_the_body_and_deletes_drafts_only_after_the_post_condition():
    text = read_src("workflows/3b-create-issue.md")
    assert re.search(r"`create`[^\n]*`\.tmp/3b-issue-body\.md`", text), "3b must mint with the body file"
    assert "issues.py check" in text, "3b's local post-condition is `issues.py check`"
    cleanup = next(l for l in text.splitlines() if "Scratch cleanup" in l)
    assert "`check`" in cleanup, "the drafts are deleted only after the gate or the local `check` passes"


def test_3d_claims_the_slice_and_halts_on_a_claimed_one():
    text = read_src("workflows/3d-implement-issue.md")
    assert re.search(r"`claim` the slice[^\n]*\[CLAIMED", text), "3d must `claim` the slice and halt on [CLAIMED]"


def test_3z_local_queue_comes_from_ready():
    assert "python .agents/scripts/issues.py ready" in read_src("workflows/3z-afk-loop.md")


def test_4a_auditor_reads_acceptance_criteria_with_get():
    line = next(l for l in read_src("workflows/4a-verify-and-ship.md").splitlines() if "Business-Logic Auditor" in l)
    assert re.search(r"Acceptance Criteria[^\n]*`get`", line), "the auditor reads the AC with the `get` read"


def test_4a_ship_pushes_the_tracker_branch_after_the_terminal_gate():
    ship = read_src("workflows/4a-verify-and-ship.md")
    push = next(l for l in ship.splitlines() if "git push origin" in l and "issues.py branch" in l)
    assert ship.index("Terminal sync gate") < ship.index(push) < ship.index("**Cleanup:**"), "tracker push follows the gate"


@pytest.mark.parametrize("rel", ["workflows/3d-implement-issue.md", "workflows/3z-afk-loop.md", "workflows/4a-verify-and-ship.md"])
def test_status_writes_are_verbs(rel):
    assert "`set_status`" in read_src(rel), f"{rel} writes status without naming the verb"


def test_3d_reads_milestone_and_parent_from_the_single_issue():
    text = read_src("workflows/3d-implement-issue.md")
    assert "gh issue view <n> --json milestone,parent" in text


def test_3z_builds_its_queue_with_a_scoped_query():
    text = read_src("workflows/3z-afk-loop.md")
    assert "gh issue view <n> --json number,state,labels,milestone,parent" in text
    assert re.search(r"gh issue list --state open --milestone <[^>]+> --json number,title,labels,milestone,parent", text)


def test_4a_ship_gate_is_one_combined_call():
    calls = combined_gate_calls()
    assert len(calls) == 1, f"want exactly one combined `--with-edges dependents` call in 4a, found {len(calls)}"
    args = calls[0]
    for flag in ("--ids", "--pr-id", "--expect"):
        assert flag in args, f"4a's combined call lacks {flag}"
    assert "BT-<slice>:status=done" in args


def test_4a_combined_call_parses_under_the_real_argparse(tmp_path, monkeypatch):
    write_architecture(tmp_path / "ARCHITECTURE.md", "github")
    monkeypatch.setattr(rec, "fetch_nodes", lambda nums, comments=False, edges=False: {n: None for n in nums})
    assert_argv_accepted(rec.main, combined_gate_argv("BT-001", "BT-002") +
                         ["--arch", str(tmp_path / "ARCHITECTURE.md"), "--backlog", str(tmp_path / "BACKLOG_MAP.md")])


def test_4a_clears_dependents_through_the_verb_and_rechecks_once():
    text = read_src("workflows/4a-verify-and-ship.md")
    assert "`clear_blocker`" in text and "--edges dependents" in text
    assert re.search(r"re-run[^\n]*--edges dependents[^\n]*no `\[CLEAR\]`", text), \
        "4a must re-run `--edges dependents` once and require no [CLEAR] left"


# --- BT-194 live-test round 2: pins for the FAA, 4a audit-only, 3d globs, micro-tdd and shell-free cleanup ---

def test_faa_is_handed_the_confidence_scale_and_has_one_scope_and_a_watch_home():
    faa = read_src("references/feature-acceptance-audit.md")
    assert "confidence-scale.md" in faa, "the FAA auditor must be handed the scale, as 4a hands it to slice auditors"
    assert "already mapped PASS" not in faa, "a per-slice ship-only dispatch holds no shipped slices' coverage maps"
    output = next(l for l in faa.splitlines() if l.startswith("- **Output:**"))
    assert "Watch" in output and "40-59" in output, "the FAA output needs a home for Watch and the withheld footnote"


def test_4a_audit_only_stops_before_the_hitl_halt_and_defines_its_verdict():
    gate = next(l for l in read_src("workflows/4a-verify-and-ship.md").splitlines() if "Named gate" in l)
    assert re.search(r"Phases 1[-\u2013]3", gate) and "Phase 4" in gate, "audit-only ends before the Phase 4 HITL halt"
    assert all(v in gate for v in ("[PASS]", "[UNCOVERED]", "[SKIP]")), "audit-only must define its three verdicts"


def test_audit_only_return_contract_names_the_3z_json_with_verdict_and_coverage_map():
    line = next(l for l in read_src("references/pr-body-and-ship.md").splitlines() if "`audit-only` returns" in l)
    assert "Step 2B" in line, "the audit-only return is the 3z Step 2B JSON, verdict and coverage_map included"


def test_3d_finds_an_active_branch_through_any_globs_entry():
    text = read_src("workflows/3d-implement-issue.md")
    assert "first `globs` entry" not in text, "a release-unit branch matches only the second glob"
    assert "any `globs` entry" in text


def test_micro_tdd_carve_out_covers_a_guard_the_code_already_satisfies():
    carve = next(l for l in read_src("skills/micro-tdd/SKILL.md").splitlines() if "Characterization Carve-out" in l)
    assert "guard" in carve and "mutation" in carve, "a guard that passes on arrival records a mutation as its RED"
    assert "ImportError" in read_src("skills/micro-tdd/SKILL.md"), "a missing-module ImportError is a valid RED"


def test_faa_verdict_is_the_word_clean_or_gaps_with_no_bracket_token():
    verdict = read_src("references/feature-acceptance-audit.md").split("## Verdict", 1)[1]
    assert "no bracket token" in verdict, "the FAA verdict is prose; without this an agent invents `[FEATURE-PASS]`"


def test_3z_ci_gate_runs_inside_ship_only_after_the_audit_and_the_dispatch_does_not_order_it():
    line = next(l for l in read_src("workflows/3z-afk-loop.md").splitlines() if l.lstrip().startswith("- **CI gate**"))
    assert "Phase 5 step 8" in line and "after the Feature Acceptance Audit" in line, "ship-only runs the gate; the dispatch must not order it"


@pytest.mark.parametrize("rel", sorted(str(p.relative_to(SRC)).replace("\\", "/") for p in SRC.rglob("*.md")))
def test_no_artifact_hands_the_agent_a_posix_only_rm_f(rel):
    assert "rm -f" not in read_src(rel), f"{rel}: `rm -f` fails on Windows PowerShell 5.1; say 'delete <files> (ignore absent)'"


def test_0b_fetches_origin_non_fatally_before_the_local_merged_close():
    line = _line("workflows/0b-stop-session.md", "merged --close", "Local backend")
    fetch, close = line.index("git fetch -q origin"), line.index("issues.py merged --close")
    assert fetch < close, "the fetch runs before the check"
    assert re.search(r"non-fatal|ignore a failure", line[fetch:], re.I), "a failed fetch (offline, no origin) must not stop the sync"


# --- BT-194 live-test round 3: the no-PR ship path, audit-only gaps and rounds wording ---

def _line(rel, *needles):
    line = next((l for l in read_src(rel).splitlines() if all(n in l for n in needles)), None)
    assert line, f"{rel}: no line with {needles}"
    return line


def _ship_step(n):
    ship = read_src("workflows/4a-verify-and-ship.md").partition("## Phase 5")[2]
    m = re.search(rf"^{n}\. .*?(?=^{n + 1}\. |\Z)", ship, re.M | re.S)
    assert m, f"4a Phase 5 has no step {n}"
    return m.group(0)


def test_4a_with_no_pr_skips_the_ci_gate_instead_of_halting_on_it():
    step8 = _ship_step(8)
    assert re.search(r"no PR[^\n]*skip[^\n]*CI gate", step8), "a ship that made no PR must skip the CI gate (exit 2 on `--pr 0` is not a verdict)"
    scope = _line("references/ci-gate.md", "no PR (`gh` not connected, none made)")  # the §1 scope line
    ci_sec1 = read_src("references/ci-gate.md").split("## 2.")[0]
    assert "## 1. Scope" in ci_sec1, "ci-gate.md §1 has exact ## 1. Scope heading"
    assert scope in ci_sec1, "the scope line belongs to ci-gate.md §1"
    assert "skip and say so, never fail, never `status --pr 0`" in scope, "ci-gate.md §1 states the same scope: skip, say so, never `--pr 0`"
    assert re.search(r"no PR[^\n]*skip", _ship_step(7)), "the standalone CI-gate twin (step 7) skips with no PR too"
    assert "standalone issue or no PR" in _ship_step(9), "the draft rule skips with no PR"
    assert "draft statement" in step8, "a ship with no PR makes no draft claim"


def test_4a_pushes_only_when_gh_is_connected_and_says_so_otherwise():
    """AGENTS.md section 4 (Git Protocol 4): a push needs `gh` connected, an `origin` alone is not enough."""
    assert re.search(r"`gh` is connected[^\n]*stay local", _ship_step(4)), "step 4 pushes the unit branch only when `gh` is connected"
    tracker = _line("workflows/4a-verify-and-ship.md", "issues.py branch", "git push")
    assert re.search(r"`gh` is connected[^\n]*no PR", tracker), "the tracker-branch push is conditional on `gh` too (otherwise no PR)"
    assert "`origin` remote exists" not in read_src("workflows/4a-verify-and-ship.md"), "no push is gated on a bare origin remote"


def test_4a_ship_line_has_a_no_pr_form():
    step11 = _ship_step(11)
    assert re.search(r"No PR: `\[SHIPPED\][^`]*<sha>", step11), "a no-PR ship needs its own `[SHIPPED]` line"


def test_faa_has_an_input_for_an_epic_with_no_prd_and_no_source_line():
    run = read_src("references/feature-acceptance-audit.md").split("## Run", 1)[1].split("## Verdict", 1)[0]
    assert re.search(r"no PRD[^\n]*no `Source:`", run, re.I), "an epic with neither a PRD nor a `Source:` line needs an input rule"


def test_0b_names_the_confirmation_for_a_probably_merged_squash():
    line = _line("workflows/0b-stop-session.md", "merged --close", "Local backend")
    assert re.search(r"PROBABLY-MERGED[^\n]*confirm[^\n]*issues\.py close", line), "0b must say how a `[PROBABLY-MERGED]` squash is confirmed and closed"


def test_3z_step_2b_return_carries_the_gaps_and_their_bars_the_retry_passes():
    text = read_src("workflows/3z-afk-loop.md")
    ret = _line("workflows/3z-afk-loop.md", "Return JSON:", "verdict")
    assert re.search(r'\\"gaps\\"', ret) and "`{ac, confidence, bar}`" in ret, "the retry passes each gap's stated bar; the audit return must carry it"
    assert "`Gaps` entries" not in text, "no `Gaps` entries exist in the return contract"
    keep = _line("workflows/3z-afk-loop.md", "Findings (every Step 2B return)")
    assert "`coverage_map`" in keep and "`gaps`" in keep, "2C keeps what the delta re-audit is handed"
    ship_4a = read_src("workflows/4a-verify-and-ship.md")
    table = ship_4a.split("### 1.", 1)[1].split("### 2.", 1)[0]
    assert "| Gap / Security Risk / Bar |" in table, "the Phase 3 Spec table header names the Bar column"
    assert "**bar** = the fix that would close it" in table, "the Spec table row defines the bar the delta rule freezes"
    assert "confidence ≥ 80" in ship_4a, "4a defines the confidence >= 80 rule"


def test_3z_audit_rounds_counts_audits_not_attempts_and_the_delta_needs_a_prior_audit():
    text = read_src("workflows/3z-afk-loop.md")
    line = _line("workflows/3z-afk-loop.md", "`--audit-rounds`")
    assert re.search(r"Step 2B", line) and "final `attempt`" not in line, "`--audit-rounds` = audits run, not the attempt counter"
    assert "On attempt > 1 also pass" not in text, "an attempt that skipped 2B leaves no earlier audit to delta against"


def test_pr_body_closing_link_recheck_waits_for_github_to_catch_up():
    """Found live (smoke repo, twice): `closingIssuesReferences` read right after a body edit omits the new `Closes`."""
    line = _line("references/pr-body-and-ship.md", "NO-AUTOCLOSE")
    assert "re-check **once**, after ~5 s" in line, "an instant re-check reads the stale link and falsely reports NO-AUTOCLOSE"


def test_ci_fix_commits_before_the_suite_record_and_none_means_no_checks_without_expect():
    """Found live (smoke repo): `record --suite` refuses a dirty tree; `--expect-checks` with no checks is `pending`, not `none`."""
    text = read_src("references/ci-gate.md")
    fix = text.split("## 3. Fix", 1)[1].split("## 4.", 1)[0]
    assert fix.index("2. commit") < fix.index("3. `test_gate.py record --suite"), "the suite record needs the clean HEAD the commit makes"
    line = _line("references/ci-gate.md", "`none` = ")
    assert "without `--expect-checks`" in line and "`pending`" in line, "with --expect-checks, no checks after the grace is pending"


def test_4a_defines_severity_bar_once():
    ship_4a = read_src("workflows/4a-verify-and-ship.md")
    table = ship_4a.split("### 1.", 1)[1].split("### 2.", 1)[0]
    assert "| Gap / Security Risk / Bar |" in table, "the Phase 3 Spec table header names the Bar column"
    assert "**bar** = the fix that would close it" in table, "the Spec table row defines the bar the delta rule freezes"
    assert "confidence ≥ 80" in ship_4a, "4a defines the confidence >= 80 rule"


def test_ci_gate_reference_keeps_fix_loop_capped_and_scoped():
    ci_ref = read_src("references/ci-gate.md")
    sec1 = ci_ref.split("## 2.")[0]
    assert "## 1. Scope" in sec1, "ci-gate.md has ## 1. Scope heading"
    assert "skip and say so, never fail, never `status --pr 0`" in sec1, "ci-gate.md §1 skips when no PR"
    assert "--wait" in ci_ref and "pending" in ci_ref, "ci-gate.md covers --wait and pending"
    assert "without `--expect-checks`" in sec1 or "without `--expect-checks`" in ci_ref, "ci-gate.md covers expect-checks"


def test_0d_commit_rule_empty_findings_and_cross_file_promotion():
    text = read_src("workflows/0d-nightly-consolidation.md")
    # (a) D1 Commit Rule
    assert re.search(r"default branch[^\n]*chore\(nightly\): consolidate <YYYY-MM-DD>", text), \
        "0d commits locally on default branch with chore(nightly) message"
    assert re.search(r"accepted · applied <sha>", text), \
        "0d appends <sha> on default branch commit"
    assert re.search(r"feature branch[^\n]*uncommitted[^\n]*accepted · applied", text), \
        "0d leaves changes uncommitted on feature branch without <sha>"
    # (b) Empty-findings path
    assert re.search(r"(?:0 `R-n`|empty findings)[^\n]*(?:omit|No recommendations)[^\n]*skip[^\n]*halt", text, re.I), \
        "0d skips Phase 4 decision halt when 0 findings"
    # (c) Cross-file promotion
    assert re.search(r"\[PATTERN\][^\n]*\[LAW\][^\n]*cross-file supersession", text), \
        "0d specifies cross-file supersession for PATTERN -> LAW"
    assert "[SUPERSEDED BY [[A-yyy]]]" in text or "[SUPERSEDED BY [[A-" in text, \
        "0d specifies target tombstone tag for cross-file supersession"


def test_4a_and_pr_body_local_close_partial_cleanup_and_unified_gh_wording():
    ship = read_src("workflows/4a-verify-and-ship.md")
    pr_body_ref = read_src("references/pr-body-and-ship.md")
    # (a) --close with local backend adds no Closes lines
    assert re.search(r"tracker: local[^\n]*adds no `Closes` lines", pr_body_ref, re.I) or \
           re.search(r"local backend[^\n]*adds no `Closes` lines", ship, re.I), \
        "local backend adds no Closes lines on --close"
    # (b) PARTIAL definition in status vocabulary
    assert re.search(r"PARTIAL[^\n]*PRD §8[^\n]*later open slice", ship), \
        "4a defines PARTIAL as a PRD §8 item owned by a later open slice"
    # (c) .tmp/4a-pr-body-* cleanup on every outcome including no PR
    assert re.search(r"\.tmp/4a-pr-body[^\n]*every outcome[^\n]*no PR", ship, re.I), \
        "4a deletes .tmp/4a-pr-body on every outcome including no PR"
    # (d) Unified when gh is connected wording
    assert "when `gh` is connected (otherwise stay local with no PR)" in ship, \
        "4a standardizes when gh is connected wording"
    # (e) -m integration checklist line
    assert re.search(r"-m integration[^\n]*harness/shim", ship), \
        "4a mentions running -m integration when integration tests are touched or in harness/shim ship gate"


def test_3z_step_2b_template_includes_std_tier_phase1_input():
    ret = _line("workflows/3z-afk-loop.md", "Return JSON:", "verdict")
    assert r'\"phase1\"' in ret and r'\"std_tier\"' in ret and r'\"input\"' in ret, \
        "3z Step 2B Return JSON template must include phase1, std_tier, and input"

