#!/usr/bin/env python3
"""BT-128 guards: workflow wording must agree with what the gates and repo hygiene require.

1. 4a step 6's slice comment must satisfy reconcile.py's PR-link predicate (no second comment).
2. Workflow `--body-file` scratch files live under `.tmp/` and are removed once consumed.

BT-137 guards (bottom of file): 4a clean-tree guard, `stratos-pr` body, risk label, draft rule.
"""
import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WF = ROOT / "src" / "workflows"
spec = importlib.util.spec_from_file_location("reconcile", ROOT / "src" / "scripts" / "reconcile.py")
rec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rec)

SAMPLE_URL = "https://github.com/o/r/pull/9"
BODY_FILE = re.compile(r"--body-file\s+(\S+)")


def test_4a_step6_comment_satisfies_reconcile_pr_link():
    text = (WF / "4a-verify-and-ship.md").read_text(encoding="utf-8")
    m = re.search(r'gh issue comment <n> --body "([^"]+)"', text)
    assert m, "4a step 6 has no `gh issue comment <n> --body \"...\"` literal"
    body = m.group(1).replace("<pr-url>", SAMPLE_URL).replace("<pr>", "9")
    drift = rec.compare({}, {"comments": [{"body": body}]}, set(), True)
    assert drift == [], f"step 6 comment {body!r} fails the reconcile PR-link check: {drift}"


def test_4a_documents_pr_body_file_under_tmp():
    text = (WF / "4a-verify-and-ship.md").read_text(encoding="utf-8")
    assert BODY_FILE.search(text), "4a step 5 must pass the PR body via `--body-file`"


def test_body_files_live_in_tmp_and_are_removed():
    for name in ("4a-verify-and-ship.md", "3b-create-issue.md"):
        text = (WF / name).read_text(encoding="utf-8")
        for path in BODY_FILE.findall(text):
            path = path.strip("\"'`")
            assert path.startswith(".tmp/"), f"{name}: --body-file {path} is outside .tmp/"
            assert re.search(rf"rm -f [^\n]*{re.escape(path)}", text), \
                f"{name}: no `rm -f {path}` cleanup"


def test_3b_issue_drafts_scratch_is_removed():
    text = (WF / "3b-create-issue.md").read_text(encoding="utf-8")
    assert re.search(r"rm -f [^\n]*\.tmp/BT-<padded>-issue-drafts\.md", text), \
        "3b never deletes .tmp/BT-<padded>-issue-drafts.md after minting"


def test_3b_mints_every_issue_from_one_tmp_body_file():
    text = (WF / "3b-create-issue.md").read_text(encoding="utf-8")
    assert re.search(r"\*\*Generate \(Atomic Minting\):\*\* Execute `gh issue create --body-file \.tmp/3b-issue-body\.md`", text), \
        "3b step 4 must mint slices and epics via --body-file .tmp/3b-issue-body.md"
    assert "3b-epic-body" not in text


def _4a():
    return (WF / "4a-verify-and-ship.md").read_text(encoding="utf-8")


def _ref():
    return (ROOT / "src" / "references" / "pr-body-and-ship.md").read_text(encoding="utf-8")


def _ship():
    """4a plus the reference that holds step 5's body, risk-label and read-back detail."""
    return _4a() + chr(10) + _ref()


def test_4a_runs_release_bump_before_push_when_repo_has_one():
    text = _4a()
    assert "scripts/release.py" in text, "4a never mentions the release.py bump the CI bump-guard requires"
    assert text.index("scripts/release.py") < text.index("Push the branch"), "release bump must precede the push"


def test_4a_closing_lines_are_bare_and_read_back():
    text = _ship()
    assert "Closes #<n>." in text, "closing lines must be the bare `Closes #<n>.` form that GitHub links"
    assert "closingIssuesReferences" in text, "4a must read back the PR's closing links after create/edit"


def test_4a_closing_readback_has_a_bounded_fallback():
    text = _ship()
    assert "[NO-AUTOCLOSE" in text and "once" in text, "read-back needs a single retry then an explicit fallback"


# --- BT-137: clean-tree guard, stratos-pr body, risk label, draft gate -------------------------

def _3d():
    return (WF / "3d-implement-issue.md").read_text(encoding="utf-8")


def _3z():
    return (WF / "3z-afk-loop.md").read_text(encoding="utf-8")


def test_4a_clean_tree_guard_precedes_context_isolation():
    text = _4a()
    for token in ("git status --porcelain", "[UNCOMMITTED]"):
        assert token in text, f"4a lacks the clean-tree guard token {token!r}"
        assert text.index(token) < text.index("Context Isolation Rule"), f"{token!r} must precede the audit phase"


def test_4a_named_gate_ship_only_runs_the_guard():
    text = _4a()
    line = next(l for l in text.splitlines() if l.startswith("> **Named gate — `ship-only`"))
    assert "clean-tree guard" in line, "ship-only skips Phase 1, so its named-gate line must say the guard runs first"


def test_4a_no_unaudited_safety_net_commit():
    text = _4a()
    assert "Safety net for uncommitted slice files" not in text, "4a must not commit unaudited slice files"
    assert text.index("scripts/release.py") < text.index("Push the branch")


def test_3d_phase3_requires_clean_tree():
    text = _3d()
    phase3 = text[text.index("## Phase 3"):]
    assert "git status --porcelain" in phase3, "3d Phase 3 must require a clean tree for done"


def test_4a_pr_body_is_a_stratos_pr_block():
    text = _ship()
    for token in ("```stratos-pr", "risk:one-way", "gh label create", "references/merge-risk-paths.md",
                  "PENDING", "[DRAFT-RULE]"):
        assert token in text, f"4a missing {token!r}"
    assert "noting the re-verification" not in text, "re-verification comment has no consumer"
    assert "AC↔test coverage table (if audited)" not in text, "AC table no longer belongs in the PR body"


def test_4a_step5_points_at_the_reference_instead_of_inlining_it():
    step5 = _step5()
    assert "references/pr-body-and-ship.md" in step5
    for moved in ("```stratos-pr", "gh label create", "[NO-AUTOCLOSE"):
        assert moved not in step5, f"{moved!r} belongs in references/pr-body-and-ship.md"


def test_4a_deletes_the_3d_plan_after_the_terminal_gate_and_3d_says_so():
    text = _4a()
    cleanup = text[text.index("10. **Cleanup:**"):text.index("11. Output:")]
    assert "rm -f .tmp/3d-plan-BT-<padded>.md" in cleanup and ".tmp/3d-suite-BT-<padded>.json" in cleanup
    assert text.index("9. **Terminal sync gate:**") < text.index("10. **Cleanup:**")
    assert "4a deletes it after ship" in _3d()


def test_4a_step8_adds_parent_closing_link():
    text = _4a()
    step8 = text[text.index("8. **Epic Check:**"):text.index("9. **Terminal sync gate:**")]
    assert "Closes #<parent>." in step8 and "closingIssuesReferences" in step8


def test_3z_ship_only_dispatch_passes_verdict_and_rounds():
    text = _3z()
    step3a = text[text.index("### Step 3A"):]
    for token in ("verdict", "audit_rounds", "needs_manual_qa", "post_merge"):
        assert token in step3a, f"3z Step 3A ship-only dispatch must pass {token!r}"


def _risk_rules():
    """(glob regex, tag) pairs parsed from the `<glob> → <tag>` table in the reference."""
    text = (ROOT / "src" / "references" / "merge-risk-paths.md").read_text(encoding="utf-8")
    rules = []
    for row in re.findall(r"^\|\s*(`[^|]+`)\s*\|\s*`([a-z-]+)`\s*\|", text, re.M):
        for glob in re.findall(r"`([^`]+)`", row[0]):
            rx = re.escape(glob).replace(r"\*\*/", "(?:.*/)?").replace(r"\*\*", ".*").replace(r"\*", "[^/]*")
            rules.append((re.compile(rf"^{rx}$"), row[1]))
    return rules


def test_merge_risk_paths_tag_sql_and_ci():
    rules = _risk_rules()
    def tags(path):
        return {t for rx, t in rules if rx.match(path)}

    assert tags("docs/database/x.sql") == {"db-migration"}
    assert tags("db/migrations/001_init.py") == {"db-migration"}
    assert tags(".github/workflows/ci.yml") == {"ci"}
    assert tags("src/workflows/4a-verify-and-ship.md") == set()


def test_pr_body_slice_id_regex_ignores_unscoped_commits():
    pspec = importlib.util.spec_from_file_location("pr_body", ROOT / "src" / "scripts" / "pr_body.py")
    pr_body = importlib.util.module_from_spec(pspec)
    pspec.loader.exec_module(pr_body)
    subjects = ["feat(BT-12): a", "fix(BT-12): b", "feat(BT-13): c", "release: prepare v1.0.0", "fix(ci): x", "chore: y"]
    assert sorted({pr_body.SCOPE_RE.match(s).group(1) for s in subjects if pr_body.SCOPE_RE.match(s)}) == ["12", "13"]


def test_build_ships_merge_risk_paths_into_4a():
    bspec = importlib.util.spec_from_file_location("build", ROOT / "build" / "build.py")
    build = importlib.util.module_from_spec(bspec)
    bspec.loader.exec_module(build)
    assert "merge-risk-paths.md" in build.closure_for(_4a(), ROOT / "src" / "references"),         "4a must cite references/merge-risk-paths.md so the build fans it into 4a's references/"


# --- BT-144 follow-up: 4a builds the PR body with pr_body.py instead of prose rules -------------

PR_BODY = ROOT / "src" / "scripts" / "pr_body.py"


def _step5():
    text = _4a()
    return text[text.index("5. **PR (one per feature branch):**"):text.index("6. **PR-link comment")]


def test_4a_step5_builds_the_body_with_pr_body_script_using_real_flags():
    step5 = _step5()
    call = re.search(r"python \.agents/scripts/pr_body\.py build ([^`]+)`", step5)
    assert call, "4a step 5 must call `pr_body.py build`"
    used = set(re.findall(r"--[a-z-]+", call.group(1)))
    pspec = importlib.util.spec_from_file_location("pr_body", PR_BODY)
    pr_body = importlib.util.module_from_spec(pspec)
    pspec.loader.exec_module(pr_body)
    build = pr_body.build_parser()._subparsers._group_actions[0].choices["build"]
    accepted = {flag for action in build._actions for flag in action.option_strings if flag.startswith("--")}
    assert {"--slice", "--summary", "--verdict", "--audit-rounds", "--prior-body-file"} <= used
    assert used <= accepted, f"{used - accepted} not accepted by pr_body.py"


def test_4a_step5_suite_reuse_goes_through_pr_body_suite():
    step5 = _step5()
    assert "python .agents/scripts/pr_body.py suite" in step5
    assert ".tmp/3d-suite-BT-<padded>.json" in _ref() and "Never delete these files" in _ref()


def test_4a_step5_drops_the_prose_rules_the_script_now_owns():
    step5 = _step5()
    for gone in ("**Slice rebuild:**", "**Closing lines:**", "**Test result:**", "git log --no-merges",
                 "subject matches"):
        assert gone not in step5, f"{gone!r}: rule lives in pr_body.py now, not in 4a prose"


def test_4a_step5_keeps_the_gh_side_of_the_body():
    step5 = _step5() + _ref()
    for token in ("--draft", "gh label create", "gh pr edit", "closingIssuesReferences", "[NO-AUTOCLOSE",
                  "references/merge-risk-paths.md"):
        assert token in step5, f"4a step 5 lost {token!r}"
    step8 = _4a()[_4a().index("8. **Epic Check:**"):_4a().index("9. **Terminal sync gate:**")]
    assert "pr_body.py build" in step8 and "--close-parent" in step8


def test_4a_step8_resaves_the_prior_body_before_the_rebuild():
    """Step 5 deletes `.tmp/4a-prior-body.md`; the `--close-parent` rebuild needs it back or earlier slices go PENDING."""
    text = _4a()
    step8 = text[text.index("8. **Epic Check:**"):text.index("9. **Terminal sync gate:**")]
    assert "gh pr view" in step8 and ".tmp/4a-prior-body.md" in step8, "step 8 must re-save the PR's current body"
    assert "--prior-body-file" in step8, "step 8 must pass the re-saved body to pr_body.py build"
    assert "PENDING" in step8 and "Closes" in step8, "step 8 must say what is lost without the prior body"
    assert step8.index(".tmp/4a-prior-body.md") < step8.index("--close-parent"), "re-save comes before the rebuild"


def test_pr_body_reference_documents_base_resolution_and_suite_reuse():
    ref = _ref()
    build = ref.split("## Build")[1].split("## Suite")[0]
    assert "--base" in build and "origin/HEAD" in build and "main" in build and "master" in build
    assert "[PR-BODY-ERROR]" in build and "status 2" in build, "no base resolved must be a fail-closed error"
    suite = ref.split("## Suite")[1].split("## Risk label")[0]
    assert "HEAD" in suite and "clean" in suite
    for ignored in (".memory/", "docs/", ".tmp/"):
        assert ignored in suite, f"suite reuse must name {ignored} as ignored for the clean-tree check"
