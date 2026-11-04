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
    line = next(l for l in read_src("workflows/0b-stop-session.md").splitlines() if "merged --close" in l and "Local backend" in l)
    fetch, close = line.index("git fetch -q origin"), line.index("issues.py merged --close")
    assert fetch < close, "the fetch runs before the check"
    assert re.search(r"non-fatal|ignore a failure", line[fetch:], re.I), "a failed fetch (offline, no origin) must not stop the sync"


# --- BT-194 live-test round 3: the no-PR ship path, audit-only gaps and rounds wording ---

def _ship_step(n):
    ship = read_src("workflows/4a-verify-and-ship.md").split("## Phase 5", 1)[1]
    return re.search(rf"^{n}\. .*?(?=^{n + 1}\. |\Z)", ship, re.M | re.S).group(0)


def test_4a_with_no_pr_skips_the_ci_gate_instead_of_halting_on_it():
    step8 = _ship_step(8)
    assert re.search(r"no PR[^\n]*skip[^\n]*CI gate", step8), "a ship that made no PR must skip the CI gate (exit 2 on `--pr 0` is not a verdict)"
    assert re.search(r"no PR[^\n]*skip", read_src("references/ci-gate.md").split("## 2.")[0]), "ci-gate.md §1 states the same scope"


def test_4a_pushes_only_with_an_origin_remote_and_says_so_otherwise():
    assert re.search(r"origin[^\n]*stay local", _ship_step(4)), "step 4 pushes the unit branch only when an `origin` remote exists"
    tracker = next(l for l in read_src("workflows/4a-verify-and-ship.md").splitlines() if "issues.py branch" in l and "git push" in l)
    assert re.search(r"origin[^\n]*stay local|stay local[^\n]*origin", tracker), "the tracker-branch push is conditional on an origin too"


def test_4a_ship_line_has_a_no_pr_form():
    step11 = _ship_step(11)
    assert re.search(r"no PR", step11) and "<sha>" in step11, "a no-PR ship needs its own `[SHIPPED]` line"


def test_faa_has_an_input_for_an_epic_with_no_prd_and_no_source_line():
    run = read_src("references/feature-acceptance-audit.md").split("## Run", 1)[1].split("## Verdict", 1)[0]
    assert re.search(r"no PRD[^\n]*no `Source:`|neither", run, re.I),"an epic with neither a PRD nor a `Source:` line needs an input rule"


def test_0b_names_the_confirmation_for_a_probably_merged_squash():
    line = next(l for l in read_src("workflows/0b-stop-session.md").splitlines() if "merged --close" in l and "Local backend" in l)
    assert re.search(r"PROBABLY-MERGED[^\n]*confirm[^\n]*issues\.py close", line), "0b must say how a `[PROBABLY-MERGED]` squash is confirmed and closed"


def test_3z_step_2b_return_carries_the_gaps_and_their_bars_the_retry_passes():
    text = read_src("workflows/3z-afk-loop.md")
    ret = next(l for l in text.splitlines() if "Return JSON:" in l and "verdict" in l)
    assert re.search(r'\\"gaps\\"', ret) and "bar" in ret,"the retry passes each gap's stated bar; the audit return must carry it"
    assert "`Gaps` entries" not in text, "no `Gaps` entries exist in the return contract"


def test_3z_audit_rounds_counts_audits_not_attempts_and_the_delta_needs_a_prior_audit():
    text = read_src("workflows/3z-afk-loop.md")
    line = next(l for l in text.splitlines() if "`--audit-rounds`" in l)
    assert re.search(r"Step 2B", line) and "final `attempt`" not in line, "`--audit-rounds` = audits run, not the attempt counter"
    assert "On attempt > 1 also pass" not in text, "an attempt that skipped 2B leaves no earlier audit to delta against"
