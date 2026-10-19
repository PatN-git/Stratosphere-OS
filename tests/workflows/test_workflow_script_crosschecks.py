#!/usr/bin/env python3
"""Cross-checks between workflow/reference markdown and the scripts or build output they depend on.

Kept from the per-workflow wording suites: each test here fails when markdown and code drift apart
(a literal the script rejects, a flag the CLI lacks, a reference the build does not fan out).
Phrase-presence pins live nowhere; load-bearing rules belong in build/validate.py or check_suite.
"""
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
WF = SRC / "workflows"
DIST = ROOT / "dist" / "skills"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


rec = _load("reconcile", SRC / "scripts" / "reconcile.py")
pr_body = _load("pr_body", SRC / "scripts" / "pr_body.py")
build = _load("build", ROOT / "build" / "build.py")


def _4a() -> str:
    return (WF / "4a-verify-and-ship.md").read_text(encoding="utf-8")


def _step5() -> str:
    text = _4a()
    return text[text.index("5. **PR (one per feature branch):**"):text.index("6. **PR-link comment")]


# --- reconcile.py ---------------------------------------------------------------------------

def test_4a_step6_comment_satisfies_reconcile_pr_link():
    m = re.search(r'gh issue comment <n> --body "([^"]+)"', _4a())
    assert m, "4a step 6 has no `gh issue comment <n> --body \"...\"` literal"
    body = m.group(1).replace("<pr-url>", "https://github.com/o/r/pull/9").replace("<pr>", "9")
    drift = rec.compare({}, {"comments": [{"body": body}]}, set(), True)
    assert drift == [], f"step 6 comment {body!r} fails the reconcile PR-link check: {drift}"


def test_a_slice_without_a_github_milestone_drifts_from_its_backlog_row():
    row = {"status": "planned", "labels": set(), "milestone": "v1.0.0", "parent": "—", "blocked_by": set()}
    gh = {"labels": [{"name": "status:planned"}], "milestone": None}
    assert any("milestone" in d for d in rec.compare(row, gh, set(rec.ALL_FIELDS), False))
    gh["milestone"] = {"title": "v1.0.0"}
    assert not any("milestone" in d for d in rec.compare(row, gh, set(rec.ALL_FIELDS), False))


# --- pr_body.py and the merge-risk reference --------------------------------------------------

def _risk_rules():
    """(glob regex, tag) pairs parsed from the `<glob> -> <tag>` table in the reference."""
    text = (SRC / "references" / "merge-risk-paths.md").read_text(encoding="utf-8")
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
    subjects = ["feat(BT-12): a", "fix(BT-12): b", "feat(BT-13): c", "release: prepare v1.0.0", "fix(ci): x", "chore: y"]
    assert sorted({pr_body.SCOPE_RE.match(s).group(1) for s in subjects if pr_body.SCOPE_RE.match(s)}) == ["12", "13"]


def test_4a_step5_builds_the_body_with_pr_body_script_using_real_flags():
    call = re.search(r"python \.agents/scripts/pr_body\.py build ([^`]+)`", _step5())
    assert call, "4a step 5 must call `pr_body.py build`"
    used = set(re.findall(r"--[a-z-]+", call.group(1)))
    sub = pr_body.build_parser()._subparsers._group_actions[0].choices["build"]
    accepted = {flag for action in sub._actions for flag in action.option_strings if flag.startswith("--")}
    assert {"--slice", "--summary", "--verdict", "--audit-rounds", "--prior-body-file"} <= used
    assert used <= accepted, f"{used - accepted} not accepted by pr_body.py"


# --- contract_check.py ------------------------------------------------------------------------

def test_every_workflow_call_uses_only_real_contract_check_flags():
    script = SRC / "scripts" / "contract_check.py"
    out = subprocess.run([sys.executable, str(script), "--help"], capture_output=True, text=True).stdout
    flags = set(re.findall(r"--[a-z]+", out))
    call = re.compile(r"python \.agents/scripts/contract_check\.py ([^`]+)`")
    seen = 0
    for name in ("2a-write-prd.md", "2b-interface-design.md", "2c-reconcile-specs.md"):
        for args in call.findall((WF / name).read_text(encoding="utf-8")):
            seen += 1
            used = set(re.findall(r"--[a-z]+", args))
            assert used <= flags, f"{name}: {used - flags} not accepted by contract_check.py"
    assert seen >= 3


# --- build fan-out (dist) ---------------------------------------------------------------------

def test_build_ships_merge_risk_paths_into_4a():
    assert "merge-risk-paths.md" in build.closure_for(_4a(), SRC / "references"), \
        "4a must cite references/merge-risk-paths.md so the build fans it into 4a's references/"


def test_red_flags_cite_code_smell_baseline_in_the_form_the_build_fans_out():
    """build.py copies only `references/<file>.md` citations; a bare basename left 2b and 4b without the file."""
    flags = (SRC / "references" / "design-red-flags.md").read_text(encoding="utf-8")
    assert "`references/code-smell-baseline.md`" in flags
    for skill in ("2b-interface-design", "4b-audit-architecture-drift"):
        assert (DIST / skill / "references" / "code-smell-baseline.md").is_file(), skill


def test_build_ships_the_ladder_into_0b():
    assert (DIST / "0b-stop-session" / "references" / "environment-fix-ladder.md").is_file()


def test_3b_ships_no_report_template():
    refs = DIST / "3b-create-issue" / "references"
    for tpl in ("health-audit-report-template.md", "arch-drift-report-template.md"):
        assert not (refs / tpl).exists(), f"3b ships {tpl}; audit-to-slices.md must not cite report templates"
