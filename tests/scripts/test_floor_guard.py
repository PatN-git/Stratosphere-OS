"""BT-172: `floor_guard.py` flags changes that lower the quality bar and stays silent on tightening.

Seam: the CLI (exit code + output) run inside a throwaway git repo: exit 0 clean, 1 violation, 2 could-not-run.
Fixture strings that would trip the guard on this very file are built by concatenation (see the dogfood test).
"""
import shutil
import subprocess
import sys

import pytest

from conftest import _GIT_ENV, REPO_ROOT, commit, git

SCRIPTS = REPO_ROOT / "src" / "scripts"
GUARD = SCRIPTS / "floor_guard.py"

SKIP = "@pytest.mark." + "skip"
XFAIL = "@pytest.mark." + "xfail"
JS_ONLY = "it." + "only("
NOQA = "# no" + "qa: E501"
TYPE_IGNORE = "# type: " + "ignore"
ESLINT = "// eslint-" + "disable-next-line"
CI_SOFT = "continue-on-" + "error: true"
CI_TRUE = "pytest || " + "true"

TESTS_3 = "def test_a():\n    assert 1 == 1\n\n\ndef test_b():\n    assert 2 == 2\n\n\ndef test_c():\n    assert 3 == 3\n"
SETUP_CFG = "[coverage:report]\nfail_under = 80\n"
CODECOV = "coverage:\n  status:\n    project:\n      default:\n        target: 80%\n        threshold: 1%\n"
PKG = '{"jest": {"coverageThreshold": {"global": {\n  "lines": 80,\n  "branches": 70\n}}}}\n'
CI = "jobs:\n  t:\n    steps:\n      - run: pytest\n"
EXC = "# Architecture\n\n## Floor exceptions\n- skip tests/legacy/** — upstream flake (approved BT-1)\n"


def run_guard(repo, *args):
    return subprocess.run([sys.executable, str(GUARD), *args], cwd=repo, capture_output=True, text=True, env=_GIT_ENV)


def write(repo, rel, text):
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(text.encode("utf-8"))


def rm(repo, rel):
    (repo / rel).unlink()


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-b", "main")
    (tmp_path / ".git" / "info" / "exclude").write_text(".tmp/\n", encoding="utf-8")
    base = {"tests/test_app.py": TESTS_3, "app.py": "x = 1\n", "setup.cfg": SETUP_CFG, "codecov.yml": CODECOV,
            "package.json": PKG, ".github/workflows/ci.yml": CI, "db/schema.sql": "-- keep\ncreate table t(a int);\n",
            "tests/legacy/test_old.py": "def test_old():\n    assert True\n", ".memory/ARCHITECTURE.md": "# Architecture\n"}
    for rel, text in base.items():
        write(tmp_path, rel, text)
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-m", "chore: base")
    git(tmp_path, "checkout", "-b", "feat/x")
    return tmp_path


def test_a_clean_diff_exits_0(repo):
    write(repo, "app.py", "x = 2\n")
    out = run_guard(repo)
    assert out.returncode == 0, out.stdout + out.stderr
    assert "clean" in out.stdout


MOVES = {
    "skip-marker": (lambda r: write(r, "tests/test_app.py", SKIP + "\n" + TESTS_3), "skip"),
    "xfail-marker": (lambda r: write(r, "tests/test_app.py", XFAIL + "\n" + TESTS_3), "skip"),
    "js-only": (lambda r: write(r, "tests/app.test.js", JS_ONLY + "'x', () => {})\n"), "skip"),
    "untracked-skip": (lambda r: write(r, "tests/test_new.py", SKIP + "\ndef test_n():\n    assert 1\n"), "skip"),
    "py-suppress": (lambda r: write(r, "app.py", "import os  " + NOQA + "\n"), "suppress"),
    "type-ignore": (lambda r: write(r, "app.py", "x: int = ''  " + TYPE_IGNORE + "\n"), "suppress"),
    "js-suppress": (lambda r: write(r, "web.js", ESLINT + " no-undef\nfoo()\n"), "suppress"),
    "ci-soft-fail": (lambda r: write(r, ".github/workflows/ci.yml", CI + "        " + CI_SOFT + "\n"), "suppress"),
    "ci-or-true": (lambda r: write(r, ".github/workflows/ci.yml", CI.replace("pytest", CI_TRUE)), "suppress"),
    "test-file-deleted": (lambda r: rm(r, "tests/test_app.py"), "tests-removed"),
    "assertions-emptied": (lambda r: write(r, "tests/test_app.py", "def test_a():\n    pass\n"), "tests-removed"),
    "cov-lowered": (lambda r: write(r, "setup.cfg", SETUP_CFG.replace("80", "60")), "threshold"),
    "cov-key-removed": (lambda r: write(r, "setup.cfg", "[coverage:report]\n"), "threshold"),
    "jest-lowered": (lambda r: write(r, "package.json", PKG.replace('"lines": 80', '"lines": 70')), "threshold"),
    "codecov-drop-allowed-raised": (lambda r: write(r, "codecov.yml", CODECOV.replace("threshold: 1%", "threshold: 5%")), "threshold"),
    "codecov-target-lowered": (lambda r: write(r, "codecov.yml", CODECOV.replace("target: 80%", "target: 50%")), "threshold"),
    "exception-row-added": (lambda r: write(r, ".memory/ARCHITECTURE.md", EXC), "exception-added"),
}


@pytest.mark.parametrize("name", sorted(MOVES))
def test_flags_each_move(repo, name):
    mutate, rule = MOVES[name]
    mutate(repo)
    out = run_guard(repo)
    assert out.returncode == 1, out.stdout + out.stderr
    assert f"[{rule}]" in out.stdout


TIGHTENING = {
    "cov-raised": lambda r: write(r, "setup.cfg", SETUP_CFG.replace("80", "90")),
    "codecov-drop-allowed-lowered": lambda r: write(r, "codecov.yml", CODECOV.replace("threshold: 1%", "threshold: 0.5%")),
    "jest-raised": lambda r: write(r, "package.json", PKG.replace('"lines": 80', '"lines": 90')),
    "new-threshold": lambda r: write(r, "setup.cfg", SETUP_CFG + "\n[tool:x]\nfail_under = 10\n"),
    "tests-added": lambda r: write(r, "tests/test_app.py", TESTS_3 + "\n\ndef test_d():\n    assert 4 == 4\n"),
    "docs-mention-suppression": lambda r: write(r, "docs/guide.md", "Avoid " + NOQA + " and " + SKIP + ".\n"),
    "ml-fit-call": lambda r: write(r, "tests/test_model.py", "def test_m(model):\n    model.fit(1)\n    assert model\n"),
    "cov-moved-between-files": lambda r: (write(r, "setup.cfg", "[coverage:report]\n"),
                                          write(r, "pyproject.toml", "[tool.coverage.report]\nfail_under = 80\n")),
    "tests-moved-between-files": lambda r: (write(r, "tests/test_app.py", "def test_a():\n    assert 1 == 1\n"),
                                            write(r, "tests/test_more.py", "def test_b():\n    assert 2 == 2\n\n\ndef test_c():\n    assert 3 == 3\n")),
    "sql-comment-line-removed": lambda r: write(r, "db/schema.sql", "-- other\ncreate table t(a int);\n"),
}


@pytest.mark.parametrize("name", sorted(TIGHTENING))
def test_silent_on_tightening(repo, name):
    TIGHTENING[name](repo)
    out = run_guard(repo)
    assert out.returncode == 0, out.stdout + out.stderr


def test_a_removed_suppression_and_skip_are_silent(tmp_path):
    git(tmp_path, "init", "-b", "main")
    write(tmp_path, "tests/test_app.py", SKIP + "\n" + TESTS_3)
    write(tmp_path, "app.py", "import os  " + NOQA + "\n")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-m", "chore: base")
    git(tmp_path, "checkout", "-b", "feat/x")
    write(tmp_path, "tests/test_app.py", TESTS_3)
    write(tmp_path, "app.py", "import os\n")
    assert run_guard(tmp_path).returncode == 0


def test_could_not_run_is_exit_2_and_distinct(tmp_path, repo):
    elsewhere = tmp_path.parent / (tmp_path.name + "-nogit")
    elsewhere.mkdir()
    out = run_guard(elsewhere)
    assert out.returncode == 2
    assert "COULD-NOT-RUN" in out.stderr
    assert "VIOLATION" not in out.stdout + out.stderr and "clean" not in out.stdout
    bad_base = run_guard(repo, "--base", "no-such-ref")
    assert bad_base.returncode == 2 and "COULD-NOT-RUN" in bad_base.stderr


def test_no_resolvable_default_branch_is_exit_2(tmp_path):
    git(tmp_path, "init", "-b", "trunk")
    commit(tmp_path, "chore: base")
    out = run_guard(tmp_path)
    assert out.returncode == 2 and "COULD-NOT-RUN" in out.stderr


def test_exception_row_on_default_tip_silences_and_a_row_in_the_diff_never_does(tmp_path):
    git(tmp_path, "init", "-b", "main")
    write(tmp_path, ".memory/ARCHITECTURE.md", EXC)
    write(tmp_path, "tests/legacy/test_old.py", "def test_old():\n    assert True\n")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-m", "chore: base")
    git(tmp_path, "checkout", "-b", "feat/x")
    write(tmp_path, "tests/legacy/test_old.py", SKIP + "\ndef test_old():\n    assert True\n")
    assert run_guard(tmp_path).returncode == 0  # approved on main by a human
    write(tmp_path, "tests/other/test_new.py", SKIP + "\ndef test_n():\n    assert 1\n")
    out = run_guard(tmp_path)
    assert out.returncode == 1 and "tests/other/test_new.py" in out.stdout  # the row does not cover this path
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-m", "feat: x")
    write(tmp_path, ".memory/ARCHITECTURE.md", EXC + "- skip tests/other/** — me, myself (approved BT-9)\n")
    out = run_guard(tmp_path)
    assert out.returncode == 1 and "[exception-added]" in out.stdout and "tests/other/test_new.py" in out.stdout


def test_output_never_echoes_the_source_line(repo):
    write(repo, "app.py", 'pw = "hunter2-SECRET"  ' + "# no" + "qa: S105\n")
    out = run_guard(repo)
    assert out.returncode == 1 and "app.py:1" in out.stdout
    assert "hunter2" not in out.stdout + out.stderr


def test_diff_parsing_survives_prefix_config_and_crlf(repo):
    git(repo, "config", "diff.noprefix", "true")
    git(repo, "config", "diff.mnemonicPrefix", "true")
    write(repo, "tests/test_app.py", (SKIP + "\n" + TESTS_3).replace("\n", "\r\n"))
    out = run_guard(repo)
    assert out.returncode == 1 and "tests/test_app.py:1" in out.stdout
    assert "\r" not in out.stdout


def test_guard_source_and_tests_are_clean_under_itself(tmp_path):
    git(tmp_path, "init", "-b", "main")
    commit(tmp_path, "chore: base")
    git(tmp_path, "checkout", "-b", "feat/x")
    for src, rel in ((GUARD, "scripts/floor_guard.py"), (SCRIPTS / "pr_body.py", "scripts/pr_body.py"),
                     (REPO_ROOT / "tests" / "scripts" / "test_floor_guard.py", "tests/scripts/test_floor_guard.py")):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, tmp_path / rel)
    out = run_guard(tmp_path)
    assert out.returncode == 0, out.stdout + out.stderr


ARCH_TIP = (
    "# Architecture\n\n## Structural Rules\n"
    "- **[[A-003]] [LAW]** Keep files under 400 lines. Check: tests/standards/size.test.js (tolerance 10%)\n"
    "- **[[A-004]] [LAW]** A rule with no binding.\n\n"
    "## Floor exceptions\n- A-003 **/*.test.* — tests exempt\n"
)


def _tip_repo(tmp_path, arch=ARCH_TIP):
    git(tmp_path, "init", "-b", "main")
    write(tmp_path, ".memory/ARCHITECTURE.md", arch)
    write(tmp_path, "app.py", "x = 1\n")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-m", "chore: base")
    git(tmp_path, "checkout", "-b", "feat/x")
    return tmp_path


def test_a_rule_id_row_added_on_the_branch_is_a_violation_and_prints_no_info(tmp_path):
    repo = _tip_repo(tmp_path, "# Architecture\n")
    write(repo, ".memory/ARCHITECTURE.md", "# Architecture\n\n## Floor exceptions\n- A-003 src/big.js — legacy, split later\n")
    out = run_guard(repo)
    assert out.returncode == 1 and "[exception-added]" in out.stdout and "A-003 src/big.js" in out.stdout
    assert "info:" not in out.stdout


def test_default_tip_rule_id_rows_and_bound_rules_are_printed_on_a_clean_run(tmp_path):
    repo = _tip_repo(tmp_path)
    write(repo, "app.py", "x = 2\n")
    out = run_guard(repo)
    assert out.returncode == 0, out.stdout + out.stderr
    assert "info: exception A-003 **/*.test.*" in out.stdout
    assert "info: bound A-003 tests/standards/size.test.js" in out.stdout
    assert "A-004" not in out.stdout  # an unbound rule is not listed


def test_removing_a_row_on_the_branch_is_silent_and_the_tip_still_governs(tmp_path):
    repo = _tip_repo(tmp_path)
    write(repo, ".memory/ARCHITECTURE.md", ARCH_TIP.replace("- A-003 **/*.test.* — tests exempt\n", ""))
    out = run_guard(repo)
    assert out.returncode == 0, out.stdout + out.stderr
    assert "info: exception A-003 **/*.test.*" in out.stdout  # the human-merged tip, not the branch copy


def test_a_check_marker_added_only_on_the_branch_is_not_honoured(tmp_path):
    repo = _tip_repo(tmp_path)
    write(repo, ".memory/ARCHITECTURE.md",
          ARCH_TIP.replace("A rule with no binding.", "A rule with no binding. Check: tests/standards/x.test.js"))
    out = run_guard(repo)
    assert out.returncode == 0, out.stdout + out.stderr
    assert "bound A-004" not in out.stdout and "bound A-003" in out.stdout


def test_only_memory_rule_ids_are_exception_rows(tmp_path):
    repo = _tip_repo(tmp_path, "# Architecture\n")
    write(repo, ".memory/ARCHITECTURE.md",
          "# Architecture\n\n## Floor exceptions\n- BT-214 src/x.js — a backlog id is not a rule\n- a-003 src/y.js — lower case\n- A-03 src/z.js — two digits\n")
    out = run_guard(repo)
    assert out.returncode == 0, out.stdout + out.stderr
