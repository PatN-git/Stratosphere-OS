"""L3 Slice 4 - the per-phase artifact assertions.

Synthetic artifacts, no agent. Each checker is exercised both ways: a shape that
must pass, and the specific defect it exists to catch. The `3b` case drives the real
`reconcile.py` against the real shim, because "the gate reached [MIRROR-OK]" is the
one claim the harness must never take from a transcript.
"""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HARNESS = Path(__file__).resolve().parent.parent / "lifecycle-harness"
REPO = Path(__file__).resolve().parents[2]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


a = _load("l3_assertions", HARNESS / "assertions.py")
e = _load("l3_env_assert", HARNESS / "env.py")
gh = _load("l3_gh_assert", HARNESS / "shims" / "gh_shim.py")

CHILD = {"PATH": os.environ.get("PATH", ""),
         "SYSTEMROOT": os.environ.get("SYSTEMROOT", "")}


def project(tmp_path):
    proj = tmp_path / "project"
    (proj / ".memory").mkdir(parents=True)
    (proj / ".memory" / "STATUS.md").write_text("# STATUS\nno-active-task\n",
                                                encoding="utf-8")
    subprocess.run(["git", "init", str(proj)], capture_output=True, check=True)
    subprocess.run(["git", "-C", str(proj), "add", "-A"], capture_output=True)
    subprocess.run(["git", "-C", str(proj), "-c", "user.email=l3@x", "-c",
                    "user.name=L3", "commit", "-m", "seed"], capture_output=True)
    return proj


def ctx(proj, **kw):
    kw.setdefault("before", a.snapshot(proj))
    return a.Context(project=proj, child_env=CHILD, **kw)


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# --- 0a: the assertion is that nothing happened ------------------------------

def test_0a_passes_when_it_touched_nothing(tmp_path):
    proj = project(tmp_path)
    problems, _ = a.check("0a", ctx(proj))
    assert problems == []


def test_0a_fails_if_it_wrote_status(tmp_path):
    """0a:23 halts before any side effect."""
    proj = project(tmp_path)
    c = ctx(proj)
    write(proj / ".memory" / "STATUS.md", "# STATUS\nactive: BT-001\n")
    problems, _ = a.check("0a", c)
    assert any("STATUS.md" in p for p in problems)


def test_0a_fails_if_it_cut_a_branch(tmp_path):
    """0a:24 says NEVER create a branch, in those words."""
    proj = project(tmp_path)
    c = ctx(proj)
    subprocess.run(["git", "-C", str(proj), "branch", "feat/BT-001-x"],
                   capture_output=True)
    problems, _ = a.check("0a", c)
    assert any("NEVER create a branch" in p for p in problems)


# --- 1a: structural only, because findings are never reproducible ------------

RESEARCH = """---
type: research
title: "Research: flags"
sources:
  - resource: https://example.invalid/pricing
    title: Vendor pricing
---

## Cost & Viability Signals

Per-MAU tiers are published by four vendors, ranging from free to $0.05/MAU at
volume, with an enterprise tier that is quote-only. Two of the four publish an
explicit free ceiling, and paid conversion begins around 10k MAU. Ad spend on the
category keyword is sustained, which indicates a funded market rather than a
hobbyist one.
"""


def test_1a_passes_on_a_well_shaped_research_file(tmp_path):
    proj = project(tmp_path)
    write(proj / "docs" / "research" / "flags.md", RESEARCH)
    problems, _ = a.check("1a", ctx(proj))
    assert problems == []


def test_1a_fails_without_the_cost_section_2a_lifts_from(tmp_path):
    proj = project(tmp_path)
    write(proj / "docs" / "research" / "flags.md",
          RESEARCH.split("## Cost & Viability Signals")[0])
    problems, _ = a.check("1a", ctx(proj))
    assert any("Cost & Viability" in p for p in problems)


def test_1a_fails_when_no_file_was_written(tmp_path):
    problems, _ = a.check("1a", ctx(project(tmp_path)))
    assert problems == ["1a produced no docs/research/<slug>.md"]


# --- 1b ----------------------------------------------------------------------

BRIEF = """---
type: discovery-brief
title: "Discovery: local flag evaluation"
status: ready-for-prd
slug: local-feature-flag-evaluation
linked-prd: —
---

## Actor
A backend engineer.
"""


def test_1b_passes_on_a_valid_brief(tmp_path):
    proj = project(tmp_path)
    write(proj / "docs" / "discovery" / "flags.md", BRIEF)
    write(proj / ".memory" / "GLOSSARY.md",
          "## [[G-001]] Ruleset\nAvoid: config, flags file\n")
    problems, notes = a.check("1b", ctx(proj))
    assert problems == []


def test_1b_fails_on_a_status_outside_the_routing_vocab(tmp_path):
    """okf-protocol:55 - the discovery-brief type keeps a routing vocab, not the
    editorial one, precisely so this is checkable."""
    proj = project(tmp_path)
    write(proj / "docs" / "discovery" / "flags.md",
          BRIEF.replace("status: ready-for-prd", "status: stable"))
    problems, _ = a.check("1b", ctx(proj))
    assert any("routing vocab" in p for p in problems)


def test_1b_fails_on_a_glossary_term_with_no_avoid_list(tmp_path):
    proj = project(tmp_path)
    write(proj / "docs" / "discovery" / "flags.md", BRIEF)
    write(proj / ".memory" / "GLOSSARY.md", "## [[G-001]] Ruleset\nA set of rules.\n")
    problems, _ = a.check("1b", ctx(proj))
    assert any("Avoid:" in p for p in problems)


def test_1b_fails_when_the_slug_pre_allocates_a_bt_id(tmp_path):
    """1b:19 - numeric binding happens downstream at `gh issue create`."""
    proj = project(tmp_path)
    write(proj / "docs" / "discovery" / "flags.md",
          BRIEF.replace("slug: local-feature-flag-evaluation", "slug: BT-007-flags"))
    problems, _ = a.check("1b", ctx(proj))
    assert any("pre-allocates" in p for p in problems)


# --- 2a: the one true cross-phase hand-off -----------------------------------

PRD = """---
type: prd
title: "PRD: flags"
resource: https://github.com/l3-harness/throwaway/issues/1
status: stable
---

## 12. Viability & Cost
| Item | Cost |
|:--|:--|
| Vendor tier | $0.05/MAU |
"""


def test_2a_passes_when_linked_prd_was_written_back(tmp_path):
    proj = project(tmp_path)
    write(proj / "docs" / "prds" / "BT-001-flags.md", PRD)
    write(proj / "docs" / "discovery" / "flags.md",
          BRIEF.replace("linked-prd: —", "linked-prd: docs/prds/BT-001-flags.md"))
    problems, _ = a.check("2a", ctx(proj))
    assert problems == []


def test_2a_fails_when_the_brief_never_learned_about_the_prd(tmp_path):
    proj = project(tmp_path)
    write(proj / "docs" / "prds" / "BT-001-flags.md", PRD)
    write(proj / "docs" / "discovery" / "flags.md", BRIEF)
    problems, _ = a.check("2a", ctx(proj))
    assert any("linked-prd" in p for p in problems)


def test_2a_fails_on_a_draft_prd(tmp_path):
    proj = project(tmp_path)
    write(proj / "docs" / "prds" / "BT-001-flags.md",
          PRD.replace("status: stable", "status: draft"))
    write(proj / "docs" / "discovery" / "flags.md",
          BRIEF.replace("linked-prd: —", "linked-prd: docs/prds/BT-001-flags.md"))
    problems, _ = a.check("2a", ctx(proj))
    assert any("stable" in p for p in problems)


# --- 2b: Path C, and no generator MCP ----------------------------------------

DESIGN = """---
type: interface-design
title: "Interface: flag evaluation"
---

### [Path C · Non-UI] Interface Contract
`evaluate(ruleset, key, subject) -> Decision`

## Direction Alternatives (Considered)
Rejected: a remote decision endpoint.
"""


def test_2b_passes_on_path_c(tmp_path):
    proj = project(tmp_path)
    write(proj / "docs" / "design" / "BT-001-interface.md", DESIGN)
    problems, notes = a.check("2b", ctx(proj, tool_uses=[{"name": "Write"}]))
    assert problems == []
    assert any("directions HTML" in n for n in notes), "the absence should be a note"


def test_2b_fails_when_a_generator_mcp_was_reached(tmp_path):
    """Fact 10: Path A needs Stitch or the Claude Design MCP. Reaching one on a
    non-UI fixture means the run was not on Path C at all."""
    proj = project(tmp_path)
    write(proj / "docs" / "design" / "BT-001-interface.md", DESIGN)
    problems, _ = a.check("2b", ctx(proj, tool_uses=[
        {"name": "mcp__stitch__generate_screen", "input": "{}"}]))
    assert any("generator MCP" in p for p in problems)


def test_2b_fails_without_the_interface_contract(tmp_path):
    proj = project(tmp_path)
    write(proj / "docs" / "design" / "BT-001-interface.md",
          DESIGN.replace("Interface Contract", "Screens"))
    problems, _ = a.check("2b", ctx(proj))
    assert any("Interface Contract" in p for p in problems)


# --- 0a second run -----------------------------------------------------------

def test_0a_second_fails_on_a_retired_status_field_or_a_new_branch(tmp_path):
    proj = project(tmp_path)
    c = ctx(proj)
    problems, notes = a.check("0a-second", c)
    assert problems == []

    write(proj / ".memory" / "STATUS.md", "# STATUS\n- **Current Branch:** feat/x\n")
    problems, _ = a.check("0a-second", c)
    assert any("retired" in p for p in problems)
    write(proj / ".memory" / "STATUS.md", "# STATUS\n")

    subprocess.run(["git", "-C", str(proj), "branch", "feat/BT-002-y"],
                   capture_output=True)
    problems, _ = a.check("0a-second", c)
    assert any("only 3d creates branches" in p for p in problems)


# --- 3b: the store and the gate, run rather than believed ---------------------

# The retired v5 store: no backend may leave one (BT-221 moved the local tracker to the `<repo>/issues` branch).
OLD_MAP = "| ID | Title | Status |\n|:---|:---|:---|\n| BT-LOCAL-x | X | planned |\n"
MAP = Path(".memory") / "BACKLOG_MAP.md"  # relative to a project root
ARCH = Path(".memory") / "ARCHITECTURE.md"
SCRIPTS = ("issues.py", "_tracker_common.py", "_ice.py", "reconcile.py", "nightly_state.py", "ice_read.py", "pr_body.py")
GIT_ID = {"GIT_AUTHOR_NAME": "L3", "GIT_AUTHOR_EMAIL": "l3@x", "GIT_COMMITTER_NAME": "L3",
          "GIT_COMMITTER_EMAIL": "l3@x"}
SLICE = "type:feature,tier:slice,mode:AFK,size:small"
AC_BODY = "### Overview\nParse.\n\n### Acceptance Criteria (Verifiable)\n- [ ] Parses the ruleset\n"


def _shimmed(tmp_path, monkeypatch):
    child = {"PATH": os.environ.get("PATH", "")}
    e.install_shims(tmp_path, child)
    for key in ("PATH", "PYTHONPATH", "L3_GH_STORE"):
        monkeypatch.setenv(key, child[key])
    for var in gh.TOKEN_VARS:
        monkeypatch.delenv(var, raising=False)
    return child


def _project_with_reconcile(tmp_path):
    proj = project(tmp_path)
    scripts = proj / ".agents" / "scripts"
    scripts.mkdir(parents=True)
    for name in SCRIPTS:  # reconcile imports nightly_state; every script imports _tracker_common (issues and ice_read also _ice)
        (scripts / name).write_text(
            (REPO / "src" / "scripts" / name).read_text(encoding="utf-8"),
            encoding="utf-8")
    return proj


def _issues(proj, *argv):
    r = subprocess.run([sys.executable, str(proj / ".agents" / "scripts" / "issues.py"), *argv], cwd=str(proj),
                       env={**os.environ, **GIT_ID}, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    return r.stdout.strip()


def _local_3b(tmp_path, monkeypatch, *, labels=SLICE, body=AC_BODY, mint=True, mint_issue=False, map_file=False):
    child = _shimmed(tmp_path, monkeypatch)
    proj = _project_with_reconcile(tmp_path)
    _issues(proj, "init")
    epic = _issues(proj, "create", "--title", "Flag evaluation", "--label", "type:feature,tier:epic")
    before = a.snapshot(proj)
    if mint_issue:
        gh.main(["issue", "create", "--title", "Ruleset parsing"])
    if mint:
        write(tmp_path / "body.md", body)
        _issues(proj, "create", "--title", "Ruleset parsing", "--label", labels, "--parent", epic,
                "--body-file", str(tmp_path / "body.md"))
    if map_file:
        write(proj / MAP, OLD_MAP)
    c = a.Context(project=proj, child_env={**os.environ}, store=Path(child["L3_GH_STORE"]), before=before)
    return a.check("3b", c)[0]


def test_3b_local_passes_when_it_creates_a_checked_slice_and_touches_no_github(tmp_path, monkeypatch):
    assert _local_3b(tmp_path, monkeypatch) == []


def test_3b_local_fails_when_no_slice_was_created(tmp_path, monkeypatch):
    problems = _local_3b(tmp_path, monkeypatch, mint=False)
    assert any("no slice" in p for p in problems), problems


def test_3b_local_fails_when_a_slice_body_has_no_acceptance_criteria(tmp_path, monkeypatch):
    problems = _local_3b(tmp_path, monkeypatch, body="### Overview\nParse.\n")
    assert any("BT-LOCAL-ruleset-parsing" in p and "Acceptance Criteria" in p for p in problems), problems


def test_3b_local_fails_when_issues_check_finds_a_bad_label_set(tmp_path, monkeypatch):
    problems = _local_3b(tmp_path, monkeypatch, labels="type:feature,tier:slice,mode:AFK")
    assert any("issues.py check" in p and "size:" in p for p in problems), problems


def test_3b_local_fails_when_a_backlog_map_exists(tmp_path, monkeypatch):
    problems = _local_3b(tmp_path, monkeypatch, map_file=True)
    assert any("BACKLOG_MAP.md" in p for p in problems), problems


def test_3b_local_fails_when_it_created_a_github_issue(tmp_path, monkeypatch):
    problems = _local_3b(tmp_path, monkeypatch, mint_issue=True)
    assert any("never touches GitHub" in p for p in problems)


# --- 3d ----------------------------------------------------------------------

def test_3d_fails_when_nothing_was_committed_and_no_branch_was_cut(tmp_path):
    proj = project(tmp_path)
    problems, _ = a.check("3d", ctx(proj))
    assert any("feature branch" in p for p in problems)
    assert any("committed nothing" in p for p in problems)


def test_3d_fails_without_a_session_line_or_with_a_retired_field(tmp_path):
    proj = project(tmp_path)
    write(proj / ".memory" / "STATUS.md", "# STATUS\n- **Active Issue / PRD:** BT-001\n")
    problems, _ = a.check("3d", ctx(proj))
    assert any("session line" in p for p in problems)
    assert any("retired" in p for p in problems)


def test_3d_passes_with_a_branch_and_a_commit(tmp_path):
    proj = project(tmp_path)
    write(proj / ".memory" / "STATUS.md", GOOD_STATUS)
    before = a.snapshot(proj)
    subprocess.run(["git", "-C", str(proj), "checkout", "-b", "feat/BT-001-flags"],
                   capture_output=True)
    write(proj / "flags.py", "def evaluate(rules, key, subject):\n    return False\n")
    subprocess.run(["git", "-C", str(proj), "add", "-A"], capture_output=True)
    subprocess.run(["git", "-C", str(proj), "-c", "user.email=l3@x", "-c",
                    "user.name=L3", "commit", "-m", "feat(BT-001): parse"],
                   capture_output=True)
    problems, notes = a.check("3d", a.Context(project=proj, child_env=CHILD,
                                              before=before))
    assert problems == []
    assert any("no test files" in n for n in notes)


# --- 4a: audit-only moves nothing --------------------------------------------

def test_4a_passes_on_a_verdict_with_no_mutation(tmp_path):
    proj = project(tmp_path)
    c = ctx(proj, final_text=f"[PASS] Slice verified.\nL3-4A-COMPLETE")
    problems, _ = a.check("4a", c)
    assert problems == []


def test_4a_fails_when_it_opened_a_pull_request(tmp_path, monkeypatch):
    """Facts 7 and 12: ship-only is out of scope, and audit-only must not reach it."""
    child = _shimmed(tmp_path, monkeypatch)
    gh.main(["pr", "create", "--title", "feat(BT-001)", "--draft"])
    proj = project(tmp_path)
    c = a.Context(project=proj, child_env=CHILD, store=Path(child["L3_GH_STORE"]),
                  before=a.snapshot(proj), final_text="[PASS]")
    problems, _ = a.check("4a", c)
    assert any("pull request" in p for p in problems)


def test_4a_fails_without_a_verdict_token(tmp_path):
    proj = project(tmp_path)
    problems, _ = a.check("4a", ctx(proj, final_text="I have finished the audit."))
    assert any("verdict" in p for p in problems)


# --- 0b ----------------------------------------------------------------------

GOOD_STATUS = "# STATUS\n- **Last Sync:** 2026-10-27\n- **Sessions:**\n  - BT-001 · feat/BT-001-flags · 2026-10-27\n"


def _validator(proj, exit_code):
    scripts = proj / ".agents" / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    (scripts / "validate_memory.py").write_text(
        f"import sys\nsys.exit({exit_code})\n", encoding="utf-8")


def test_0b_passes_when_it_synced_status_and_ran_the_scripts(tmp_path):
    proj = project(tmp_path)
    before = a.snapshot(proj)
    _validator(proj, 0)
    write(proj / ".memory" / "STATUS.md", GOOD_STATUS)
    c = a.Context(project=proj, child_env=CHILD, before=before, tool_uses=[
        {"name": "Bash", "input": '{"command": "python .agents/scripts/okf_view.py"}'}])
    problems, _ = a.check("0b", c)
    assert problems == []


def test_0b_fails_without_last_sync_or_with_a_retired_field(tmp_path):
    proj = project(tmp_path)
    before = a.snapshot(proj)
    _validator(proj, 0)
    write(proj / ".memory" / "STATUS.md", "# STATUS\n- **Next Immediate Step:** x\n")
    problems, _ = a.check("0b", a.Context(project=proj, child_env=CHILD, before=before, tool_uses=[
        {"name": "Bash", "input": '{"command": "python okf_view.py"}'}]))
    assert any("Last Sync" in p for p in problems)
    assert any("retired" in p for p in problems)


def test_0b_fails_when_okf_view_never_ran(tmp_path):
    proj = project(tmp_path)
    before = a.snapshot(proj)
    _validator(proj, 0)
    write(proj / ".memory" / "STATUS.md", GOOD_STATUS)
    problems, _ = a.check("0b", a.Context(project=proj, child_env=CHILD,
                                          before=before))
    assert any("okf_view.py" in p for p in problems)


def test_0b_fails_if_a_single_run_promoted_a_memory_to_verified(tmp_path):
    """Promotion needs >=2 occurrences across tasks and belongs to 0d."""
    proj = project(tmp_path)
    before = a.snapshot(proj)
    _validator(proj, 0)
    write(proj / ".memory" / "STATUS.md", GOOD_STATUS)
    write(proj / ".memory" / "LEARNINGS.md",
          "## [[L-001]] Local evaluation\nverified: true\n")
    c = a.Context(project=proj, child_env=CHILD, before=before, tool_uses=[
        {"name": "Bash", "input": '{"command": "python okf_view.py"}'}])
    problems, _ = a.check("0b", c)
    assert any("verified" in p for p in problems)


# --- the contract itself -----------------------------------------------------

def test_every_driven_phase_has_a_checker():
    prompts = _load("l3_prompts_assert", HARNESS / "prompts.py")
    assert set(a.CHECKS) == set(prompts.PHASES)


def test_an_unknown_phase_is_a_loud_error(tmp_path):
    with pytest.raises(KeyError):
        a.check("9z", ctx(project(tmp_path)))


# --- what a gate-less mode can and cannot assert ------------------------------

def test_1b_fails_on_an_unpromoted_glossary_at_full_depth(tmp_path):
    """1b:96 gates promotion on a user confirmation. At full depth the responder
    answers it, so an empty glossary is a real miss."""
    proj = project(tmp_path)
    write(proj / "docs" / "discovery" / "flags.md", BRIEF)
    write(proj / ".memory" / "GLOSSARY.md", "- **[[G-XXX]]** Example Term: ...\n")
    problems, _ = a.check("1b", ctx(proj))
    assert any("GLOSSARY.md" in p for p in problems)


def test_1b_only_notes_it_in_handoff_mode(tmp_path):
    """Observed 2026-09-16: the brief carried four terms with their Avoid: lists and
    GLOSSARY.md still held its placeholder. The run finished in ONE turn, so the
    responder never spoke and no gate fired. Failing here would report the mode."""
    proj = project(tmp_path)
    write(proj / "docs" / "discovery" / "flags.md", BRIEF)
    write(proj / ".memory" / "GLOSSARY.md", "- **[[G-XXX]]** Example Term: ...\n")
    problems, notes = a.check("1b", ctx(proj, handoff=True))
    assert problems == []
    assert any("3d:42" in n for n in notes)


def test_a_promoted_glossary_still_needs_its_avoid_list_in_either_mode(tmp_path):
    proj = project(tmp_path)
    write(proj / "docs" / "discovery" / "flags.md", BRIEF)
    write(proj / ".memory" / "GLOSSARY.md", "- **[[G-001]]** Ruleset: a set of rules.\n")
    for handoff in (False, True):
        problems, _ = a.check("1b", ctx(proj, handoff=handoff))
        assert any("Avoid:" in p for p in problems)


def test_an_index_md_is_never_mistaken_for_the_artifact(tmp_path):
    """okf-protocol section 4: directory indexes are listings with no frontmatter,
    and `index.md` sorts before most slugs. The first live 1a run reported the
    artifact as having no `type:` because of exactly this."""
    proj = project(tmp_path)
    write(proj / "docs" / "research" / "index.md", "# Research\n\n- [x](x.md)\n")
    write(proj / "docs" / "research" / "local-flags.md", RESEARCH)
    assert a.only(proj, "docs/research/*.md").name == "local-flags.md"
    problems, _ = a.check("1a", ctx(proj))
    assert problems == []


def test_a_concept_map_is_not_the_discovery_brief(tmp_path):
    """The registry puts both in docs/discovery/; `discovery-brief` excludes
    `*.map.md`, which is the `concept-map` type."""
    proj = project(tmp_path)
    write(proj / "docs" / "discovery" / "flags.map.md", "---\ntype: concept-map\n---\n")
    write(proj / "docs" / "discovery" / "flags.md", BRIEF)
    assert a.brief_path(proj).name == "flags.md"


VERDICT_TURNS = """[PASS] Slice verified.
Writing the coverage map."""

NO_VERDICT_TURNS = """I read the tests and the acceptance criteria.
Done."""


def test_4a_accepts_a_verdict_from_any_turn_of_the_phase(tmp_path):
    """A verdict is a product of the PHASE, not of its closing turn. 4a emitted one
    on one run and not on another; reading only the last turn cannot tell an absent
    verdict from one stated a turn earlier."""
    proj = project(tmp_path)
    problems, _ = a.check("4a", ctx(proj, final_text="Done. L3-4A-COMPLETE",
                                    phase_text=VERDICT_TURNS))
    assert problems == []


def test_4a_still_fails_when_no_turn_carried_a_verdict(tmp_path):
    proj = project(tmp_path)
    problems, _ = a.check("4a", ctx(proj, final_text="Done.",
                                    phase_text=NO_VERDICT_TURNS))
    assert any("verdict" in p for p in problems)
