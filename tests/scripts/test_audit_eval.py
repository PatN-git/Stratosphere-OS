"""Dev-only audit test corpus: label matching, scoring and packet completeness (scripts/dev/audit_eval_*.py).

Seam: the pure functions of the two scripts plus `file_diffs` over a throwaway git repo.
"""
import importlib.util
import subprocess
from pathlib import Path

import pytest

from conftest import REPO_ROOT


def load(name):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / "scripts" / "dev" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


score = load("audit_eval_score")
build = load("audit_eval_build")

LABEL = {"id": "g1", "ac": "exit 2 halts", "cls": "text-absent", "key_terms": ["could not check", "exit 2", "cannot_run"], "min_terms": 2}


def finding(conf, text, ac=""):
    return {"ac": ac, "conf": conf, "text": text}


def test_a_finding_matches_a_label_when_enough_key_terms_appear_case_insensitively():
    assert score.matches(LABEL, finding(90, "Status exit 2 never halts [CI-RED] Could Not Check"))
    assert not score.matches(LABEL, finding(90, "exit 2 is untested"))  # one of two required terms
    assert score.matches({**LABEL, "min_terms": 1}, finding(90, "exit 2 is untested"))
    assert score.matches(LABEL, finding(90, "gap", ac="cannot_run and exit 2"))  # the AC column counts too


@pytest.mark.parametrize("conf,expected", [(95, "found"), (80, "found"), (79, "watch"), (60, "watch"), (59, "missed")])
def test_the_confidence_bands_decide_found_watch_or_missed(conf, expected):
    assert score.classify(LABEL, [finding(conf, "exit 2 could not check")]) == expected


def test_the_best_matching_finding_wins_and_a_non_matching_one_is_ignored():
    fs = [finding(65, "exit 2 could not check"), finding(88, "something else entirely")]
    assert score.classify(LABEL, fs) == "watch"
    assert score.classify(LABEL, fs + [finding(85, "cannot_run exit 2")]) == "found"


def test_a_run_reports_recall_at_80_and_at_60_and_unmatched_findings():
    labels = [LABEL, {"id": "g2", "ac": "tool timeout", "cls": "text-absent", "key_terms": ["timeout"], "min_terms": 1},
              {"id": "g3", "ac": "x", "cls": "missing-test", "key_terms": ["zzz"], "min_terms": 1}]
    fs = [finding(90, "exit 2 could not check"), finding(70, "no timeout instruction"), finding(85, "style nit"), finding(65, "other")]
    run = score.score_run(labels, fs)
    assert run["status"] == {"g1": "found", "g2": "watch", "g3": "missed"}
    assert (run["recall80"], run["recall60"]) == (1 / 3, 2 / 3)
    assert (run["unmatched80"], run["unmatched_watch"]) == (1, 1)


def test_triage_promotes_confirmed_watch_items_and_separates_noise_from_lost_gaps():
    labels = [LABEL, {"id": "g2", "ac": "timeout", "cls": "text-absent", "key_terms": ["timeout"], "min_terms": 1}]
    watch = [finding(70, "exit 2 could not check"), finding(65, "no timeout instruction"), finding(62, "naming nit"), finding(61, "other nit")]
    verdicts = {0: "confirmed", 1: "refuted", 2: "refuted", 3: "confirmed"}
    out = score.triage_outcome(labels, watch, verdicts)
    assert out == {"promoted_labels": ["g1"], "lost_labels": ["g2"], "noise_removed": 1, "unlabeled_confirmed": 1, "unclear": 0}


def test_an_unclear_verdict_neither_promotes_nor_counts_as_removed_noise():
    out = score.triage_outcome([LABEL], [finding(70, "exit 2 could not check"), finding(61, "nit")], {0: "unclear", 1: "unclear"})
    assert out == {"promoted_labels": [], "lost_labels": ["g1"], "noise_removed": 0, "unlabeled_confirmed": 0, "unclear": 2}


def test_detection_probability_and_flaky_gaps_across_repeats():
    runs = [{"status": {"g1": "found", "g2": "missed"}}, {"status": {"g1": "found", "g2": "found"}}, {"status": {"g1": "found", "g2": "watch"}}]
    p = score.detection(runs)
    assert p == {"g1": 1.0, "g2": 1 / 3}
    assert score.flaky(p) == ["g2"] and score.stable(p) == ["g1"]


def test_a_control_case_counts_every_finding_at_80_as_a_false_flag():
    run = score.score_run([], [finding(90, "a"), finding(82, "b"), finding(70, "c")])
    assert run["unmatched80"] == 2 and run["recall80"] is None


AC = ("### Acceptance Criteria\n- `npm run test:drift` exits 0\n- halts `[CI-RED] could not check` on exit 2\n"
      "- reads `cannot_run` and `src/lib/driftGuard.js`; see `failure after the first read is pending; a missing`\n- `python -m pytest tests -k x`\n")


def test_the_lint_flags_absent_identifiers_and_halt_text_and_skips_commands_paths_and_fragments():
    corpus = "def cannot_run(): pass\n"
    out = score.absent_literals(AC, corpus, ["src/lib/driftGuard.js"])
    assert out == ["[CI-RED] could not check"]  # commands, present identifiers, present paths and prose fragments are not flagged


def test_the_lint_flags_a_path_literal_that_is_not_among_the_changed_paths():
    out = score.absent_literals("- `src/other/file.js` changes\n", "x", ["src/lib/a.js"])
    assert out == ["src/other/file.js"]


def test_a_label_counts_as_caught_by_the_lint_when_an_absent_literal_holds_a_key_term():
    label = {"id": "g1", "key_terms": ["could not check", "exit 2"], "min_terms": 2}
    assert score.lint_catches(label, ["[CI-RED] could not check"])
    assert not score.lint_catches(label, ["something_else"])


def test_the_packet_names_every_changed_path_and_carries_the_whole_issue_body():
    case = {"slice": "BT-9", "issue": 9}
    body = "### Acceptance Criteria\n- [ ] a thing\n\n### Notes\nNot building: replay."
    packet = build.build_packet(case, body, ["src/a.py", "tests/test_a.py"], {"src/a.py": "+x", "tests/test_a.py": "(no textual diff: binary, mode-only or net-unchanged)"}, "abc1234", "def5678")
    assert "### src/a.py" in packet and "### tests/test_a.py" in packet
    assert "Not building: replay." in packet and "- tests/test_a.py" in packet.split("## Changed paths")[1].split("## Diff")[0]


def test_file_diffs_marks_untextual_paths_and_truncates_long_ones(tmp_path):
    def git(*a):
        subprocess.run(["git", "-C", str(tmp_path), *a], check=True, capture_output=True)
    git("init", "-b", "main")
    git("config", "user.name", "t")
    git("config", "user.email", "t@example.com")
    (tmp_path / "long.txt").write_text("a\n", encoding="utf-8")
    (tmp_path / "same.txt").write_text("s\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-m", "base")
    (tmp_path / "long.txt").write_text("\n".join(f"line{i}" for i in range(build.MAX_FILE_DIFF_LINES + 50)), encoding="utf-8")
    git("commit", "-am", "grow")
    out = build.file_diffs(tmp_path, "HEAD~1", "HEAD", ["long.txt", "same.txt"])
    assert "[truncated:" in out["long.txt"] and out["same.txt"].startswith("(no textual diff")
