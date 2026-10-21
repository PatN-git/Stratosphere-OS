"""Dev-only seeded defects for the audit test corpus (scripts/dev/audit_eval_mutate.py): each mutation makes exactly one labeled gap."""
import importlib.util

from conftest import REPO_ROOT

spec = importlib.util.spec_from_file_location("audit_eval_mutate", REPO_ROOT / "scripts" / "dev" / "audit_eval_mutate.py")
mut = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mut)

PY = '''import pytest


def test_missing_cited_reference_is_a_fatal_build_error(tmp_path):
    out = run(tmp_path)
    assert out.code == 1
    assert "missing reference" in out.err
    assert out.err.count("x") == 3


def test_cheap(tmp_path):
    assert run(tmp_path).code == 0


def test_replaces_foreign_skills_but_keeps_own(tmp_path):
    assert (tmp_path / "a").exists()
'''

JS = '''describe("watcher", () => {
  it("flags a deprecated model in the report", () => {
    const r = run("gemini-3.5-flash");
    expect(r.flagged).toBe(true);
    expect(r.rows.length).toBe(2);
  });

  it("is quiet", () => {
    expect(run("x").flagged).toBe(false);
  });
});
'''


def test_delete_test_removes_the_python_test_with_most_assertions_and_keeps_the_rest_valid():
    new, info = mut.delete_test(PY, "tests/test_x.py")
    assert "def test_missing_cited_reference_is_a_fatal_build_error" not in new
    assert "def test_cheap" in new and "def test_replaces_foreign_skills_but_keeps_own" in new
    assert info["cls"] == "missing-test" and "cited" in info["terms"] and "reference" in info["terms"]
    compile(new, "x.py", "exec")


def test_delete_test_removes_a_js_it_block_up_to_its_closing_line():
    new, info = mut.delete_test(JS, "tests/x.test.js")
    assert "flags a deprecated model" not in new and 'it("is quiet"' in new
    assert new.count("{") == new.count("}")
    assert info["cls"] == "missing-test" and any("deprecated" in t for t in info["terms"])


def test_weaken_assertion_turns_the_first_pinned_value_into_an_existence_check():
    new, info = mut.weaken_assertion(PY, "tests/test_x.py")
    assert "assert out.code == 1" not in new and "assert out.code is not None" in new
    assert info["cls"] == "unpinned-case"
    new_js, info_js = mut.weaken_assertion(JS, "tests/x.test.js")
    assert "expect(r.flagged).toBeDefined()" in new_js and "expect(r.flagged).toBe(true)" not in new_js
    assert info_js["cls"] == "unpinned-case"


def test_remove_literal_swaps_the_first_occurrence_for_a_plausible_near_miss_and_labels_it_text_absent():
    new, info = mut.remove_literal("print('[CI-RED] could not check')\nx = '[CI-RED] could not check'\n", "[CI-RED] could not check")
    assert new.count("[CI-RED] could not check") == 1 and "ci-red could not check" in new
    assert info["cls"] == "text-absent" and info["terms"] == ["[ci-red] could not check"]
    assert mut.remove_literal("nothing here", "[CI-RED]") is None


def test_delete_step_drops_a_workflow_line_that_runs_a_script_and_labels_a_wiring_omission():
    md = "1. Prepare.\n2. Run `python .agents/scripts/floor_guard.py` before the push.\n3. Push.\n"
    new, info = mut.delete_step(md, "src/workflows/4a.md")
    assert "floor_guard" not in new and "3. Push." in new
    assert info["cls"] == "wiring-omission" and "floor_guard" in info["terms"]
    assert mut.delete_step("no steps here\n", "x.md") is None


def test_mutations_can_be_limited_to_what_the_slice_added():
    added = {"def test_cheap(tmp_path):", "assert run(tmp_path).code == 0"}
    new, info = mut.delete_test(PY, "tests/test_x.py", allow=lambda name: name == "test_cheap")
    assert "def test_cheap" not in new and "def test_missing_cited_reference_is_a_fatal_build_error" in new
    assert mut.delete_test(PY, "tests/test_x.py", allow=lambda name: False) is None
    new2, _ = mut.weaken_assertion(PY, "tests/test_x.py", allow_line=lambda s: s in added)
    assert "assert run(tmp_path).code is not None" in new2 and "assert out.code == 1" in new2
    assert mut.remove_literal("a = '[CI-RED] x'", "[CI-RED] x", allow=lambda lit: False) is None


def test_generic_words_are_not_used_as_ac_literals():
    body = "### Acceptance Criteria\n- `status` is shown\n- `cannot_run` exits 2\n- `[CI-RED] could not check` halts\n- `x` ok\n- `ci_gate.py` runs\n"
    assert mut._ac_literals(body) == ["cannot_run", "[CI-RED] could not check"]


def test_a_mutation_that_finds_nothing_returns_none():
    assert mut.delete_test("x = 1\n", "src/a.py") is None
    assert mut.weaken_assertion("x = 1\n", "src/a.py") is None


def test_the_label_is_built_by_construction_from_the_mutation_info():
    info = {"cls": "missing-test", "desc": "the test for X was removed", "terms": ["alpha", "beta", "gamma"], "file": "tests/t.py"}
    label = mut.make_label("so-BT-9-m1", info)
    assert label["cls"] == "missing-test" and label["label_confidence"] == "high" and label["min_terms"] == 2
    assert label["key_terms"] == ["alpha", "beta", "gamma"] and "tests/t.py" in label["evidence"]
    single = mut.make_label("x", {**info, "terms": ["only"]})
    assert single["min_terms"] == 1
