#!/usr/bin/env python3
"""BT-142 guards: 0d is a drift-only advisor with scripted indices, sampling and a decisions record."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEXT = (ROOT / "src" / "workflows" / "0d-nightly-consolidation.md").read_text(encoding="utf-8")


def _phase(start: str, end: str) -> str:
    return TEXT.split(start)[1].split(end)[0]


def test_calls_the_scripts_instead_of_reasoning():
    assert "python .agents/scripts/reconcile.py --all-open" in TEXT
    assert "python .agents/scripts/okf_view.py --rebuild-indices" in TEXT
    assert "verbatim" in _phase("Backlog Drift Check", "## Phase 4")


def test_planning_advisor_is_gone_but_the_no_lifecycle_guard_stays():
    assert "Recommendation (evaluate in this order" not in TEXT
    assert "also pending" not in TEXT
    assert "/3a-version-planning" not in TEXT and "ROADMAP" not in TEXT
    assert "Planning-State Advisor" not in TEXT
    assert "Backlog Drift Check" in TEXT
    assert "This phase invokes no lifecycle skill." in TEXT


def test_description_says_backlog_drift():
    head = TEXT.split("---")[1]
    assert "check backlog drift" in head and "roadmap health" not in head


def test_phase1_ladder_sampling_and_lean_report():
    phase1 = _phase("## Phase 1", "## Phase 2")
    assert "references/environment-fix-ladder.md" in phase1
    assert "~15" in phase1 and "inspect the failing calls of the 5 with the most errors" in phase1
    assert "state the sample in the report" in phase1
    assert "roster" in phase1 and "positive observations" in phase1  # named so they stay out of the report


def test_watermark_state_schema_is_owned_by_nightly_state_script():
    assert "sessions_reviewed" not in TEXT
    phase2 = _phase("## Phase 2", "## Phase 3: Crystallize")
    assert "python .agents/scripts/nightly_state.py stamp" in phase2
    assert "never hand-write" in phase2
    assert '{"last_run": ' not in TEXT  # no hand-written JSON


def test_phase1_reads_slug_names_only_and_escalates_recurrence():
    phase1 = _phase("## Phase 1", "## Phase 2")
    assert "python .agents/scripts/nightly_state.py slugs" in phase1
    assert "read no prior report text" in phase1
    record = next(l for l in phase1.splitlines() if "nightly_state.py findings --slugs" in l)
    route = next(l for l in phase1.splitlines() if "references/environment-fix-ladder.md" in l)
    assert "reusing a listed slug" in record and "(skip when there are none)" in record
    assert phase1.index(record) < phase1.index(route)  # slug + nights come before routing
    assert "`nights ≥ 2`" in route and "rung 1 or 4" in route and "rung 3" not in route


def test_recurring_law_finding_uses_nights_and_ladder_rungs():
    rule = next(l for l in TEXT.split("## Phase 4")[1].splitlines() if "existing law" in l)
    assert "unless it recurs" in rule
    assert "law not reaching agents" in rule


def test_retention_prunes_reports_only_by_filename_date():
    retention = next(l for l in _phase("## Phase 2", "## Phase 3: Crystallize").splitlines() if "**Retention:**" in l)
    assert "`docs/nightly/nightly-*.md`" in retention and "filename date" in retention
    assert "Keep `.last-run.json` and `index.md`" in retention
    assert "docs/nightly/*" not in TEXT


def test_phase3_promotes_assumed_cited_twice_before_the_supersede_row():
    phase3 = _phase("## Phase 3: Crystallize", "## Phase 3.5")
    promote = "| `[ASSUMED]` cited by ≥2 distinct tasks | Promote to `[PATTERN]`? |"
    assert promote in phase3
    assert phase3.index(promote) < phase3.index("Supersede with")
    assert "collapse into one status line in the report" in phase3


def test_phase4_stubs_pending_decisions_before_the_halt_and_rewrites_them():
    phase4 = TEXT.split("## Phase 4")[1]
    stub = next(l for l in phase4.splitlines() if l.startswith("3. "))
    assert "## Decisions" in stub and "R-n · <action> · pending" in stub and "<kind> D-a..D-b BT-x" in stub
    assert phase4.index(stub) < phase4.index("4. Halt.")
    final = phase4.split("After the user answers")[1]
    for status in ("accepted · applied", "accepted · deferred", "declined"):
        assert status in final, status
    assert "`none` → every line `declined`" in final and "keeping its BT·kind" in final
    assert "never append a second one" in final
    # a carried pending line is closed at stub time in its original report, so it cannot multiply
    assert "`carried → nightly-<date> R-m`" in stub and "original report" in stub
    assert "also gets that status" not in final


def test_phase4_orders_forced_items_when_they_exceed_the_cap():
    step2 = next(l for l in TEXT.split("## Phase 4")[1].splitlines() if l.startswith("2. "))
    assert "exceed 5" in step2
    assert step2.index("carried `pending`") < step2.index("`[CHRONIC]`") < step2.index("drift heals")
    assert "overflow as a one-line count" in step2


def test_phase2_carries_pending_decisions_as_forced_binaries():
    phase2 = _phase("## Phase 2", "## Phase 3: Crystallize")
    assert "`pending`" in phase2 and "carried forward" in phase2
    assert "pending" in TEXT.split("## Phase 4")[1].split("3. Write")[0] and "binary" in TEXT.split("## Phase 4")[1]


def test_drift_runs_summary_mode_records_keys_and_forces_chronic_recommendations():
    drift = _phase("Backlog Drift Check", "## Phase 4")
    assert "reconcile.py --all-open --summary --out .tmp/nightly-drift.txt --keys-out .tmp/nightly-drift-keys.txt" in drift
    assert "new items verbatim" in drift and "never paste `.tmp/nightly-drift.txt`" in drift
    assert "nightly_state.py drift --keys-file .tmp/nightly-drift-keys.txt" in drift and "`[local-only`" in drift
    assert "[CHRONIC n]" in drift and "heal-or-decline" in drift
    assert "`declined` Decisions line for that BT·kind" in drift and "last 7 reports" in drift
    group = next(l for l in TEXT.split("## Phase 4")[1].splitlines() if l.strip().startswith("- Drift:"))
    assert "every kind in the summary" in group and "stale_blocker" in group and "`D-n` range" in group


def test_decisions_record_is_read_in_phase2_stubbed_and_rewritten_in_phase4():
    phase2 = _phase("## Phase 2", "## Phase 3: Crystallize")
    assert "## Decisions" in phase2 and "declined" in phase2
    assert "`## Decisions`" in phase2 and "30 lines" in phase2 and "last 7" in phase2  # bounded read, not whole reports
    phase4 = TEXT.split("## Phase 4")[1]
    assert "## Decisions" in phase4 and "accepted" in phase4 and "declined" in phase4


def test_assumed_entries_aged_by_inline_date_and_superseded_not_deleted():
    phase3 = _phase("## Phase 3: Crystallize", "## Phase 3.5")
    assert "7 days" in phase3 and "[YYYY-MM-DD]" in phase3
    assert "5 sessions" not in phase3
    assert "Delete?" not in phase3
    assert "Supersede with" in phase3 and "[REMOVED]" in phase3


def test_drift_lines_are_numbered_proposal_items_with_a_heal_route():
    drift = _phase("Backlog Drift Check", "## Phase 4")
    assert "python .agents/scripts/reconcile.py --all-open" in drift and "verbatim" in drift
    assert "`D-1`" in drift and "`D-2`" in drift
    assert "references/terminal-sync-invariant.md" in TEXT.split("## Phase 4")[1]


def test_decisions_cover_drift_items():
    phase4 = TEXT.split("## Phase 4")[1]
    assert "`D-n`" in phase4
    assert "BT-x" in phase4


def test_chat_is_a_ranked_brief_not_a_report_copy():
    drift = _phase("Backlog Drift Check", "## Phase 4")
    assert "never to chat" in drift and "Print its findings" not in drift
    phase4 = TEXT.split("## Phase 4")[1]
    assert "`## Recommendations` at the top of the report" in phase4 and "## Recommendations" not in _phase("## Phase 2", "## Phase 3: Crystallize")
    assert "Never restate report sections" in phase4
    assert "≤5 recommendations" in phase4 and "`R-n`" in phase4
    assert "**Quick fix**" in phase4 and "**New issue**" in phase4  # route split: this session vs backlog
    assert "`/3b-create-issue`" in phase4 and "0d never creates it" in phase4
    # StratOS skill defects are a forwardable notice, never a project issue or an outward action
    assert "StratOS framework change" not in phase4
    assert "## Framework feedback" in phase4 and "per the ladder" in phase4
    assert "law not reaching agents" in phase4  # existing-law findings escalate only on recurrence


def test_constraint_is_scoped_to_the_workflows_own_writes():
    constraint = _phase("## Constraint", "## Phase 1")
    assert "Do not modify files without user approval" in constraint
    for write in ("report", ".last-run.json", "indices", "approved heals"):
        assert write in constraint, write
    assert "`## Decisions` line of an earlier report (that line only)" in constraint


def test_decisions_read_is_host_neutral_and_cannot_hang_without_reports():
    """`grep ... $(ls docs/nightly/nightly-*.md | tail -7)` reads stdin when no report exists (hangs an unattended run) and is bash-only."""
    phase2 = _phase("## Phase 2", "## Phase 3: Crystallize")
    assert "$(ls" not in TEXT and "grep" not in phase2 and "tail -7" not in TEXT
    assert "docs/nightly/nightly-*.md" in phase2
    assert "none yet" in phase2 and "skip" in phase2


def test_phase1_runs_the_scan_before_any_transcript_and_opens_one_only_for_a_failing_call():
    phase1 = _phase("## Phase 1", "## Phase 2")
    scan = next(l for l in phase1.splitlines() if "nightly_scan.py" in l)
    assert "`python .agents/scripts/nightly_scan.py`" in scan and "--since=" not in scan  # the script owns the default
    assert "`since`" in scan and "last-run.json" not in phase1  # no hand-read of the watermark
    log = next(l for l in phase1.splitlines() if "git log --all" in l)
    assert "not transcripts" in log and "open one only to inspect a failing call" in log
    assert phase1.index("nightly_scan.py") < phase1.index("git log")
    assert "Review session transcripts" not in phase1  # the scan replaces the by-hand transcript review
    assert "More than ~15 sessions" in phase1
    redundant = next(l for l in phase1.splitlines() if l.startswith("3. "))
    assert "`repeats` in the scan" in redundant


def test_drift_heal_uses_reconcile_heal_and_runs_github_commands_only_after_approval():
    drift = _phase("Backlog Drift Check", "## Phase 4")
    final = TEXT.split("## Phase 4")[1].split("After the user answers")[1]
    assert "reconcile.py --heal --kind" in final and "--source gh" in final and "never writes GitHub" in final
    assert "`--source map` prints the `gh`/GraphQL commands" in final
    assert "run them only after the user approves that R-n" in final
    assert "(stale_blocker, closed, pr_link, absent, not_found, other)" in final
    assert "`reconcile.py --ids <healed> --fields <kind>` once; no loop" in final
