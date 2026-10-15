"""BT-175: `spec_lint.py` decides the structural checklist items of a PRD and a discovery brief.

Seam: the CLI (stdout rule ids + exit code) run on throwaway docs: exit 0 clean, 1 findings, 2 could-not-run.
Each rule has one mutation of a conforming fixture; false-positive guards pin the real-document shapes
(rationale on a continuation line, deferred stories mirrored by text, `Survived (...)` status).
"""
import importlib.util
import re
import subprocess
import sys

import pytest

from conftest import REPO_ROOT

SCRIPTS = REPO_ROOT / "src" / "scripts"
LINT = SCRIPTS / "spec_lint.py"

PRD = """---
type: prd
title: "BT-001: Demo"
status: stable
---

# BT-001: Demo

## 1. Problem
- **Current experience:** slow.

## 2. Solution (user view)
Users get a faster page.

## 3. Goals
- Pages feel instant.

## 4. Non-Goals
- **Server rendering:** principled exclusion, the app stays a SPA.
- **Offline mode:** out of principle.
  *Rationale: adds a sync layer nobody asked for.*
- **Fake progress bars:** anti-dark-pattern exclusion.

## 5. Success Signals
- Load under 2s.

## 6. User Stories
### Journey Step 1: Entry
1. **[BASELINE]** As a visitor, I want a fast first paint, so that I stay. (ODI: - [unbacked])
### Journey Step 2: Core
2. **[DEFERRED]** As a visitor, I want cached lookups across navigation, so that repeat visits are free. (ODI: - [unbacked])

## 7. Constraints & Direction
- **Constraint:** keep the SPA.
- **Direction:** fetch in parallel.
- **Boundaries:** feature actions as capabilities.
  - **Always:** keep the loading state visible.
  - **Ask first:** none — nothing needs approval.
  - **Never:** show fake progress.
- **Refs:** `[A-006]`

## 8. Definition of Done
- First load under 2s on the pilot region.

## 9. Out of Scope
- **Deferred:** As a visitor, I want cached lookups across navigation (from §6 story #2)

## 10. Open Questions
1. Which region first? — owner: pm, blocking: N

## 11. Further Notes

## 12. Viability & Cost
- **Complexity Estimate:** 3
"""

BRIEF = """---
type: discovery-brief
title: "Discovery: slow first load"
status: ready-for-prd
---

# Discovery: slow first load

## Ask (verbatim)
> make it faster

## Vocabulary
- **First load:** the uncached page view.

## Actor
A regional job seeker on a mobile connection.

## Problem
First load takes too long on mobile.

## Established Facts (as of 2026-10-01)
- The hook fetches serially — source: src/hooks/useJobs.js
- Cold start is 3s — source: probe: node bench.js

## Chosen Framing
Performance gap rather than data bug.

## Success State
1. First load under 2s.

## Prior Art
none

## Non-Goals (early signal)
- SSR.

## Decoupled Follow-ups
- Offline cache: separate concern — existing: BT-12
- Image CDN: wanted later — candidate

## Constraints & Settled Decisions
- **Stay SPA:** yes — why: law A-006; rejected SSR.

## Open Questions
1. Which region first? — owner: pm, blocking: N

## Riskiest Assumption
- **Riskiest Assumption:** parallel fetch is enough.
- **Why Fatal:** else nothing improves.
- **Cheapest Test:** offline sample benchmark
- **Est. setup time:** 1 day
- **Status:** untested

## Recommended Next Step
- [x] `write-prd` — problem is sharp
- [ ] `create-issue` Build slice — this is a bug
- [ ] `create-issue` Spike — research needed first
- [ ] Dropped — do not build
"""


def lint(tmp_path, text, name="doc.md", *extra):
    p = tmp_path / name
    p.write_bytes(text.encode("utf-8"))
    return subprocess.run([sys.executable, str(LINT), str(p), *extra], capture_output=True, text=True, cwd=tmp_path)


def rules(out):
    return re.findall(r"\[SPEC-LINT\] \S+:\d+ ([\w-]+)", out.stdout)


def mutate(text, old, new):
    assert old in text, old
    return text.replace(old, new, 1)


def test_conforming_prd_passes(tmp_path):
    out = lint(tmp_path, PRD)
    assert out.returncode == 0, out.stdout + out.stderr
    assert "[SPEC-OK] 1 doc(s)" in out.stdout


PRD_MUTATIONS = {
    "prd-sections": lambda t: mutate(t, "## 8. Definition of Done\n- First load under 2s on the pilot region.\n", ""),
    "prd-nongoals": lambda t: mutate(t, "- **Fake progress bars:** anti-dark-pattern exclusion.\n", ""),
    "prd-s7-clean": lambda t: mutate(t, "- **Direction:** fetch in parallel.", "- **Direction:** edit `src/hooks/useJobs.js` to fetch in parallel."),
    "prd-deferred-mirror": lambda t: mutate(t, "- **Deferred:** As a visitor, I want cached lookups across navigation (from §6 story #2)",
                                           "- **Deferred:** something unrelated"),
    "prd-no-slices": lambda t: mutate(t, "## 8. Definition of Done", "## Slices\n- Slice 1: do it\n\n## 8. Definition of Done"),
    "prd-open-in-s10": lambda t: mutate(t, "## 3. Goals\n", "## 3. Goals\n> open: what is instant?\n"),
    "prd-boundaries": lambda t: mutate(t, "  - **Never:** show fake progress.\n", ""),
}


@pytest.mark.parametrize("rule", sorted(PRD_MUTATIONS))
def test_prd_rule_flags_its_mutation_and_nothing_else(tmp_path, rule):
    out = lint(tmp_path, PRD_MUTATIONS[rule](PRD))
    assert out.returncode == 1, out.stdout
    assert set(rules(out)) == {rule}, out.stdout
    assert "[SPEC-OK]" not in out.stdout


def test_findings_carry_file_and_line(tmp_path):
    out = lint(tmp_path, PRD_MUTATIONS["prd-open-in-s10"](PRD))
    line = next(l for l in out.stdout.splitlines() if "prd-open-in-s10" in l)
    n = int(re.search(r":(\d+) ", line).group(1))
    assert PRD_MUTATIONS["prd-open-in-s10"](PRD).splitlines()[n - 1].startswith("> open:")


@pytest.mark.parametrize("old,new", [
    ("- **Direction:** fetch in parallel.", "- **Direction:** use Next.js or Node.js or `vercel-labs/skills`."),
    ("- **Direction:** fetch in parallel.", "- **Direction:** run `/2b-interface-design` and see `https://example.com/a/b`."),
    ("## 1. Problem\n", "## 1. Problem\n```\n## 99. not a section\n```\n"),
    ("## 3. Goals\n", "## 3. Goals\n```\n> open: shown as a code sample\n```\n"),
])
def test_real_document_shapes_do_not_raise_false_alarms(tmp_path, old, new):
    out = lint(tmp_path, mutate(PRD, old, new))
    assert out.returncode == 0, out.stdout


def test_a_deferred_story_mirrored_by_text_without_a_story_number_passes(tmp_path):
    text = mutate(PRD, "(from §6 story #2)", "")
    assert lint(tmp_path, text).returncode == 0


def test_boundaries_tier_values_may_sit_on_nested_sub_bullets(tmp_path):
    text = mutate(PRD, "  - **Always:** keep the loading state visible.\n", "  - **Always:**\n    - keep the loading state visible.\n")
    assert lint(tmp_path, text).returncode == 0


def test_a_boundaries_tier_with_none_needs_a_reason(tmp_path):
    out = lint(tmp_path, mutate(PRD, "none — nothing needs approval.", "none"))
    assert rules(out) == ["prd-boundaries"]


def test_untyped_or_foreign_doc_and_missing_file_are_could_not_run(tmp_path):
    out = lint(tmp_path, "# just notes\n")
    assert out.returncode == 2 and "[SPEC-ERROR]" in out.stdout + out.stderr
    gone = subprocess.run([sys.executable, str(LINT), str(tmp_path / "nope.md")], capture_output=True, text=True)
    assert gone.returncode == 2 and "[SPEC-ERROR]" in gone.stdout + gone.stderr


def test_findings_never_echo_the_source_line(tmp_path):
    secret = "AKIA-SECRET-TOKEN-1234567890"
    text = mutate(PRD, "- **Direction:** fetch in parallel.", f"- **Direction:** edit `src/{secret}/key.js`.")
    out = lint(tmp_path, text)
    assert out.returncode == 1 and secret not in out.stdout


# --- discovery brief ----------------------------------------------------------------------------------------------

def test_conforming_brief_passes(tmp_path):
    out = lint(tmp_path, BRIEF)
    assert out.returncode == 0, out.stdout + out.stderr
    assert "[SPEC-OK] 1 doc(s)" in out.stdout


BRIEF_MUTATIONS = {
    "brief-sections": lambda t: mutate(t, "## Actor\nA regional job seeker on a mobile connection.\n\n", ""),
    "brief-rat": lambda t: mutate(t, "- **Status:** untested", "- **Status:** maybe"),
    "brief-followups": lambda t: mutate(t, "- Image CDN: wanted later — candidate", "- Image CDN: wanted later"),
    "brief-facts": lambda t: mutate(t, "- The hook fetches serially — source: src/hooks/useJobs.js", "- The hook fetches serially"),
    "brief-decisions": lambda t: mutate(t, "— why: law A-006; rejected SSR.", "— law A-006."),
    "brief-next-step": lambda t: mutate(t, "- [ ] Dropped — do not build", "- [x] Dropped — do not build"),
}


@pytest.mark.parametrize("rule", sorted(BRIEF_MUTATIONS))
def test_brief_rule_flags_its_mutation_and_nothing_else(tmp_path, rule):
    out = lint(tmp_path, BRIEF_MUTATIONS[rule](BRIEF))
    assert out.returncode == 1, out.stdout
    assert set(rules(out)) == {rule}, out.stdout


@pytest.mark.parametrize("old,new", [
    ("- **Status:** untested", "- **Status:** Survived (S1 spike validated the sidecar; mitigations locked)."),
    ("- **Cheapest Test:** offline sample benchmark", "- **Cheapest Test:** run 7 interviews with maintainers this week"),
    ("- **Cheapest Test:** offline sample benchmark", "- **Cheapest Test:**\n  1. offline sample benchmark\n  2. a rough mock"),
    ("- Cold start is 3s — source: probe: node bench.js", "- Cold start is 3s — probe: node bench.js"),
    ("## Established Facts (as of 2026-10-01)\n- The hook fetches serially — source: src/hooks/useJobs.js\n- Cold start is 3s — source: probe: node bench.js\n\n", ""),
    ("- Offline cache: separate concern — existing: BT-12\n- Image CDN: wanted later — candidate\n", "- none\n"),
    ("## Constraints & Settled Decisions\n- **Stay SPA:** yes — why: law A-006; rejected SSR.", "## Constraints\n- **Stay SPA:** yes."),
    ("## Problem\n", "## Problem\n```\n## Actor\n- [x] fake\n```\n"),
])
def test_real_brief_shapes_do_not_raise_false_alarms(tmp_path, old, new):
    out = lint(tmp_path, mutate(BRIEF, old, new))
    assert out.returncode == 0, out.stdout


def test_vocabulary_needs_a_defined_term(tmp_path):
    out = lint(tmp_path, mutate(BRIEF, "- **First load:** the uncached page view.", "see below"))
    assert rules(out) == ["brief-sections"]


def test_next_step_with_no_choice_is_flagged(tmp_path):
    out = lint(tmp_path, mutate(BRIEF, "- [x] `write-prd` — problem is sharp", "- [ ] `write-prd` — problem is sharp"))
    assert rules(out) == ["brief-next-step"]


def test_two_docs_in_one_call_report_each_by_name(tmp_path):
    bad = tmp_path / "bad.md"
    bad.write_text(BRIEF_MUTATIONS["brief-rat"](BRIEF), encoding="utf-8")
    good = tmp_path / "good.md"
    good.write_text(PRD, encoding="utf-8")
    out = subprocess.run([sys.executable, str(LINT), str(good), str(bad)], capture_output=True, text=True)
    assert out.returncode == 1 and "bad.md:" in out.stdout and "good.md" not in out.stdout


# --- the script and the templates stay in step --------------------------------------------------------------------

def _module():
    spec = importlib.util.spec_from_file_location("spec_lint", LINT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_prd_sections_match_the_prd_template():
    template = (REPO_ROOT / "src" / "references" / "PRD-template.md").read_text(encoding="utf-8")
    body = template.split("## Artifact body")[1]
    heads = {int(n): t.strip() for n, t in re.findall(r"^## (\d+)\. (.+)$", body, re.M)}
    assert _module().PRD_SECTIONS == heads


def test_brief_required_sections_and_rat_statuses_match_the_brief_template():
    mod = _module()
    template = (REPO_ROOT / "src" / "references" / "discovery_brief_template.md").read_text(encoding="utf-8")
    body = template.split("## Artifact body")[1]
    keys = {mod.heading_key(h) for h in re.findall(r"^## (.+)$", body, re.M)}
    assert set(mod.BRIEF_REQUIRED) <= keys
    status = re.search(r"\*\*Status:\*\* ([a-z |]+)$", body, re.M).group(1)
    assert set(mod.RAT_STATUSES) == {s.strip() for s in status.split("|")}
