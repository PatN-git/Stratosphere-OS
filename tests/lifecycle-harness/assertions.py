#!/usr/bin/env python3
"""L3 Slice 4 - what each phase must have left on disk.

Every check here reads an **artifact, its frontmatter, a sentinel, or the tool-use
stream** (E3). None reads agent prose: prose varies between runs and between models,
so an assertion on it fails for reasons that have nothing to do with the lifecycle.
Where a phase's outcome is a claim rather than a file - `3b`'s terminal sync, `3d`'s
tests - the harness re-runs the deterministic script itself instead of believing the
transcript.

Each checker returns `(problems, notes)`. A problem fails the run. A note is an
observation for Slice 9's report: something worth recording that is not, on its own,
proof of a defect. The split exists because a harness that fails on everything
surprising is a harness people stop running.
"""
from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

# Path A needs Stitch or the Claude Design MCP; Path C must reach none of them
# (fact 10). Matched against tool NAMES in the stream, which is where an MCP server
# announces itself.
GENERATOR_MCP = ("stitch", "claude-design", "claude_design", "designmcp")

DISCOVERY_STATUS = {"ready-for-prd", "exit-bug", "exit-spike", "dropped"}


@dataclass
class Context:
    """Everything a checker may look at. No transcript text beyond sentinels."""
    project: Path
    child_env: dict
    store: Path | None = None            # the gh shim's fixture store
    bare: Path | None = None             # the throwaway's origin
    tool_uses: list = field(default_factory=list)
    before: dict = field(default_factory=dict)   # snapshot taken before the phase
    final_text: str = ""                 # last turn, read ONLY for bracket tokens
    # Hand-off mode bounds each phase to a few turns, and an agent told to work at
    # minimum depth tends to finish in ONE - which means the responder never speaks
    # and no HITL gate ever fires. Anything that exists only behind a gate is
    # therefore unreachable in this mode, and a checker that failed on it would be
    # reporting the mode rather than the lifecycle.
    handoff: bool = False


# --- small readers -----------------------------------------------------------

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def frontmatter(text: str) -> dict:
    """Flat `key: value` pairs from the leading `---` block. Deliberately naive:
    the checks below want `type`, `status` and `linked-prd`, not a YAML parser."""
    if not text.startswith("---"):
        return {}
    block = text.split("---", 2)[1] if text.count("---") >= 2 else ""
    out = {}
    for line in block.splitlines():
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


# okf-protocol section 4: directory `index.md` files are listings and carry NO
# frontmatter; `log.md` is change history and carries none either. They sort before
# most slugs, so a naive "first match" picks up the index and then reports the
# artifact as having no `type:` - which is exactly what the first live 1a run did.
RESERVED = {"index.md", "log.md"}


def only(project: Path, pattern: str, exclude: tuple = ()) -> Path | None:
    """The one artifact a phase produced, ignoring the bundle's own furniture."""
    hits = [p for p in sorted(project.glob(pattern))
            if p.name not in RESERVED
            and not any(p.match(x) for x in exclude)]
    return hits[0] if hits else None


def brief_path(project: Path) -> Path | None:
    """`*.map.md` is a concept-map, a different OKF type in the same directory
    (registry: `discovery-brief` is `docs/discovery/*.md` EXCLUDING `*.map.md`)."""
    return only(project, "docs/discovery/*.md", exclude=("*.map.md",))


def tool_names(ctx: Context) -> list[str]:
    return [str(t.get("name", "")).lower() for t in ctx.tool_uses]


def ran_command(ctx: Context, needle: str) -> bool:
    """Did the phase run a command containing `needle`? Tool-use stream only."""
    return any(needle in str(t.get("input", "")) for t in ctx.tool_uses)


def branches(project: Path) -> set[str]:
    r = subprocess.run(["git", "-C", str(project), "branch", "--format=%(refname:short)"],
                       capture_output=True, text=True)
    return {b.strip() for b in r.stdout.splitlines() if b.strip()}


def head(project: Path) -> str:
    r = subprocess.run(["git", "-C", str(project), "rev-parse", "HEAD"],
                       capture_output=True, text=True)
    return r.stdout.strip()


def snapshot(project: Path, bare: Path | None = None) -> dict:
    """Taken before a phase, so "unchanged" is checkable rather than assumed."""
    status = project / ".memory" / "STATUS.md"
    backlog = project / ".memory" / "BACKLOG_MAP.md"
    snap = {
        "status_md": read(status) if status.exists() else None,
        "backlog_md": read(backlog) if backlog.exists() else None,
        "branches": branches(project),
        "head": head(project),
    }
    if bare is not None:
        r = subprocess.run(["git", "--git-dir", str(bare), "rev-parse", "HEAD"],
                           capture_output=True, text=True)
        snap["bare_head"] = r.stdout.strip()
    return snap


def store_state(ctx: Context) -> dict:
    if ctx.store and ctx.store.exists():
        return json.loads(read(ctx.store))
    return {"issues": {}, "invocations": []}


# --- per phase ---------------------------------------------------------------

def check_0a(ctx: Context):
    """`0a:23` halts before any side effect; `0a:24` says NEVER create a branch.

    The assertion is that nothing happened. A greenfield `0a` that writes STATUS.md
    or cuts a branch has broken the one rule its own text states twice.
    """
    problems, notes = [], []
    status = ctx.project / ".memory" / "STATUS.md"
    if ctx.before.get("status_md") is not None and status.exists():
        if read(status) != ctx.before["status_md"]:
            problems.append("0a wrote STATUS.md, but it halts before any side effect "
                            "(0a:23)")
    new = branches(ctx.project) - ctx.before.get("branches", set())
    if new:
        problems.append(f"0a created branch(es) {sorted(new)} - 0a:24 says NEVER "
                        "create a branch")
    return problems, notes


def check_1a(ctx: Context):
    """Structural only: `1a` searches live, so its findings are never reproducible
    (fact 9). What must hold is the shape of the file it leaves."""
    problems, notes = [], []
    doc = only(ctx.project, "docs/research/*.md")
    if doc is None:
        return ["1a produced no docs/research/<slug>.md"], notes
    text = read(doc)
    fm = frontmatter(text)
    if fm.get("type") != "research":
        problems.append(f"{doc.name}: type is {fm.get('type')!r}, not 'research'")
    if "sources:" not in text:
        problems.append(f"{doc.name}: no sources: list in frontmatter (1a:103)")
    else:
        block = text.split("sources:", 1)[1].split("---", 1)[0]
        entries = [ln for ln in block.splitlines() if ln.strip().startswith("-")]
        if not entries:
            problems.append(f"{doc.name}: sources: is empty")
        if not all("resource" in ln or "resource" in block for ln in entries):
            problems.append(f"{doc.name}: a source entry carries no `resource`")
    if "## Cost & Viability Signals" not in text:
        problems.append(f"{doc.name}: no `## Cost & Viability Signals` section "
                        "(1a:100) - 2a lifts its cost table from it")
    else:
        section = text.split("## Cost & Viability Signals", 1)[1].split("\n## ", 1)[0]
        if section.count("[Unknown]") and len(section.strip()) < 200:
            problems.append(f"{doc.name}: Cost & Viability Signals is all [Unknown] "
                            "- the fixture was chosen so this gate can fire")
    return problems, notes


def check_1b(ctx: Context):
    problems, notes = [], []
    doc = brief_path(ctx.project)
    if doc is None:
        return ["1b produced no docs/discovery/<slug>.md"], notes
    text = read(doc)
    fm = frontmatter(text)
    if fm.get("type") != "discovery-brief":
        problems.append(f"{doc.name}: type is {fm.get('type')!r}, not 'discovery-brief'")
    if fm.get("status") not in DISCOVERY_STATUS:
        problems.append(f"{doc.name}: status {fm.get('status')!r} is outside the "
                        f"routing vocab {sorted(DISCOVERY_STATUS)}")
    if re.match(r"^BT-\d", fm.get("slug", "")):
        problems.append(f"{doc.name}: slug pre-allocates a BT id, which 1b:19 forbids")
    research = only(ctx.project, "docs/research/*.md")
    if research and research.stem not in text:
        notes.append(f"{doc.name} does not cite the 1a research file "
                     f"({research.name}) - the hand-off is by convention only")
    glossary = ctx.project / ".memory" / "GLOSSARY.md"
    if glossary.exists():
        g = read(glossary)
        if not re.search(r"\[\[G-\d{3}\]\]", g):
            # Observed 2026-09-16: the brief carried a full `## Vocabulary` section -
            # four terms, each with its `Avoid:` list - and GLOSSARY.md still held
            # only its template placeholder. Promotion is gated on 1b:96 ("Promote
            # to GLOSSARY?"), the run finished in one turn, so the gate never fired.
            # The vocabulary is in the document; the shared memory layer that
            # `3d:42`'s avoid-drift check reads is empty.
            message = ("no [[G-xxx]] term reached GLOSSARY.md (1b:96), so 3d:42's "
                       "avoid-drift check has nothing to read")
            (notes if ctx.handoff else problems).append(
                message + (" - unreachable in hand-off mode, where no gate fires"
                           if ctx.handoff else ""))
        elif "Avoid:" not in g:
            problems.append("a glossary term was added with no `Avoid:` list (1b:96)")
    return problems, notes


def check_2a(ctx: Context):
    """The one true cross-phase hand-off: `linked-prd` written back into the brief."""
    problems, notes = [], []
    doc = only(ctx.project, "docs/prds/BT-*.md")
    if doc is None:
        return ["2a produced no docs/prds/BT-*.md"], notes
    text = read(doc)
    fm = frontmatter(text)
    if fm.get("type") != "prd":
        problems.append(f"{doc.name}: type is {fm.get('type')!r}, not 'prd'")
    if fm.get("status") != "stable":
        problems.append(f"{doc.name}: status is {fm.get('status')!r}; Phase 4 passing "
                        "means 'stable'")
    if "## 12" not in text and "§12" not in text and "Viability & Cost" not in text:
        problems.append(f"{doc.name}: no §12 Viability & Cost section")
    brief = brief_path(ctx.project)
    if brief is None:
        problems.append("the 1b brief vanished, so the hand-off cannot be checked")
    else:
        linked = frontmatter(read(brief)).get("linked-prd", "")
        if not linked or linked in ("—", "-", ""):
            problems.append("2a did not write `linked-prd` back into the 1b brief - "
                            "the one cross-phase hand-off the chain depends on")
    return problems, notes


def check_2b(ctx: Context):
    """Path C is the only branch fully exercisable headlessly (fact 10)."""
    problems, notes = [], []
    doc = only(ctx.project, "docs/design/BT-*-interface.md")
    if doc is None:
        return ["2b produced no docs/design/BT-*-interface.md"], notes
    text = read(doc)
    fm = frontmatter(text)
    if fm.get("type") != "interface-design":
        problems.append(f"{doc.name}: type is {fm.get('type')!r}, not 'interface-design'")
    # The template heads this `### [Path C · Non-UI] Interface Contract` - an H3
    # carrying its path marker, not a bare `## Interface Contract`. Asserting the
    # invented shape failed a design doc that was correct; match the words the
    # template actually uses, and take the marker as the proof of Path C.
    if "Interface Contract" not in text:
        problems.append(f"{doc.name}: no Interface Contract section - Path C is the "
                        "non-UI contract path, and that section is its product")
    elif "Path C" not in text:
        problems.append(f"{doc.name}: an Interface Contract with no `[Path C · Non-UI]` "
                        "marker - the path taken is not recorded in the document")
    if "## Direction Alternatives (Considered)" not in text:
        problems.append(f"{doc.name}: the rejected directions were not recorded "
                        "(2b:50)")
    used = [n for n in tool_names(ctx) if any(g in n for g in GENERATOR_MCP)]
    if used:
        problems.append(f"a generator MCP was reached on the non-UI path: {used}")
    if not sorted(ctx.project.glob("docs/design/BT-*-directions.html")):
        notes.append("no directions HTML was produced; on Path C the 3 lo-fi layouts "
                     "are a UI step, so this is expected rather than a defect")
    if ctx.bare is not None:
        r = subprocess.run(["git", "--git-dir", str(ctx.bare), "log", "--oneline", "-1"],
                           capture_output=True, text=True)
        if r.returncode != 0 or not r.stdout.strip():
            notes.append("nothing was pushed to the throwaway origin; 2a/2b push "
                         "their generated document by design (AGENTS.md 4)")
    return problems, notes


def check_0a_second(ctx: Context):
    problems, notes = [], []
    status = ctx.project / ".memory" / "STATUS.md"
    if not status.exists():
        return ["STATUS.md does not exist"], notes
    if ctx.before.get("status_md") == read(status):
        notes.append("0a did not update STATUS.md on the second run; with a backlog "
                     "present it should restore an active task")
    new = branches(ctx.project) - ctx.before.get("branches", set())
    if new:
        problems.append(f"0a created branch(es) {sorted(new)} - only 3d creates "
                        "branches (AGENTS.md 4)")
    return problems, notes


def check_3b(ctx: Context):
    """The store is authoritative: `3b` writes BACKLOG_MAP from what gh returned."""
    problems, notes = [], []
    state = store_state(ctx)
    issues = [i for i in state["issues"].values() if not i.get("isPR")]
    if not issues:
        return ["3b minted no issues in the fixture store"], notes
    backlog = ctx.project / ".memory" / "BACKLOG_MAP.md"
    if not backlog.exists():
        return ["BACKLOG_MAP.md does not exist"], notes
    text = read(backlog)
    missing = [f"BT-{i['number']:03d}" for i in issues
               if f"BT-{i['number']:03d}" not in text]
    if missing:
        problems.append(f"issues minted with no BACKLOG_MAP row: {missing}")
    if ctx.before.get("backlog_md") == text:
        problems.append("BACKLOG_MAP.md is untouched, so nothing was mirrored")
    elif "generated:" in text:
        before_at = re.search(r"at:\s*(\S+)", ctx.before.get("backlog_md") or "")
        now_at = re.search(r"at:\s*(\S+)", text)
        if before_at and now_at and before_at.group(1) == now_at.group(1):
            problems.append("BACKLOG_MAP generated.at was not refreshed (3b:69)")
    ids = ",".join(f"BT-{i['number']:03d}" for i in issues)
    ok, out = mirror_ok(ctx, ids)
    if not ok:
        problems.append(f"the terminal sync gate did not reach [MIRROR-OK]: "
                        f"{out.strip()[:300]}")
    return problems, notes


def mirror_ok(ctx: Context, ids: str):
    """Run the real gate ourselves rather than believing the transcript.

    `--require-gh` is what the terminal gates pass: without a reachable GitHub it
    exits 3 with `[MIRROR-UNVERIFIED]` instead of the fail-open `[local-only]`, so
    reaching `[MIRROR-OK]` proves the shim was found AND believed.
    """
    script = ctx.project / ".agents" / "scripts" / "reconcile.py"
    if not script.exists():
        return False, f"no reconcile.py at {script}"
    r = subprocess.run(["python", str(script), "--require-gh", "--ids", ids],
                       cwd=str(ctx.project), env=ctx.child_env,
                       capture_output=True, text=True)
    return "[MIRROR-OK" in r.stdout, r.stdout + r.stderr


def check_3d(ctx: Context):
    problems, notes = [], []
    new = branches(ctx.project) - ctx.before.get("branches", set())
    on = subprocess.run(["git", "-C", str(ctx.project), "branch", "--show-current"],
                        capture_output=True, text=True).stdout.strip()
    if not new and on in ("main", "master", ""):
        problems.append("3d created no feature branch and is still on the default "
                        "branch - 3d is the only creator of branches (AGENTS.md 4)")
    if head(ctx.project) == ctx.before.get("head"):
        problems.append("3d committed nothing")
    tests = sorted(ctx.project.glob("tests/test_*.py")) + \
        sorted(ctx.project.glob("test_*.py"))
    if not tests:
        notes.append("no test files found in the project, so 'tests green' could "
                     "not be checked")
    else:
        r = subprocess.run(["python", "-m", "pytest", "-q"], cwd=str(ctx.project),
                           env=ctx.child_env, capture_output=True, text=True)
        if r.returncode != 0:
            problems.append(f"the slice's own tests do not pass: "
                            f"{(r.stdout or r.stderr)[-400:]}")
    return problems, notes


VERDICTS = ("[PASS]", "[UNCOVERED]", "[SKIP]")


def check_4a(ctx: Context):
    """`audit-only` is Phases 1-4: a verdict, and nothing else moved (fact 7)."""
    problems, notes = [], []
    if not any(v in ctx.final_text for v in VERDICTS):
        problems.append(f"4a produced none of the verdict tokens {VERDICTS}")
    if head(ctx.project) != ctx.before.get("head"):
        problems.append("4a audit-only moved HEAD; it must touch no commit")
    new = branches(ctx.project) - ctx.before.get("branches", set())
    if new:
        problems.append(f"4a audit-only created branch(es) {sorted(new)}")
    state = store_state(ctx)
    prs = [i for i in state["issues"].values() if i.get("isPR")]
    if prs:
        problems.append(f"4a audit-only opened {len(prs)} pull request(s); ship-only "
                        "is out of scope (facts 7, 12)")
    if ctx.bare is not None:
        before_bare = ctx.before.get("bare_head")
        now = subprocess.run(["git", "--git-dir", str(ctx.bare), "rev-parse", "HEAD"],
                             capture_output=True, text=True).stdout.strip()
        if before_bare is not None and now != before_bare:
            problems.append("4a audit-only pushed to the throwaway origin")
    return problems, notes


def check_0b(ctx: Context):
    problems, notes = [], []
    status = ctx.project / ".memory" / "STATUS.md"
    if not status.exists():
        return ["STATUS.md does not exist"], notes
    if read(status) == ctx.before.get("status_md"):
        problems.append("0b wrote no STATUS.md fields (0b step 2)")
    r = subprocess.run(["python", str(ctx.project / ".agents" / "scripts" /
                                      "validate_memory.py"), "--path", ".memory"],
                       cwd=str(ctx.project), env=ctx.child_env,
                       capture_output=True, text=True)
    if r.returncode != 0:
        problems.append(f"validate_memory.py exits {r.returncode} after 0b "
                        f"(0b step 9): {(r.stdout or '')[-300:]}")
    if not ran_command(ctx, "okf_view.py"):
        problems.append("0b did not run okf_view.py (step 10) - nothing in the "
                        "tool-use stream names it")
    # Promotion to `verified` needs >=2 occurrences across tasks and belongs to 0d,
    # so a single run appending it is a defect rather than thoroughness.
    for name in ("LEARNINGS.md", "GLOSSARY.md"):
        doc = ctx.project / ".memory" / name
        if doc.exists() and re.search(r"^\s*-?\s*verified:", read(doc), re.M):
            problems.append(f"{name} carries `verified` after a single run; "
                            "promotion needs >=2 occurrences and belongs to 0d")
    return problems, notes


CHECKS = {
    "0a": check_0a,
    "1a": check_1a,
    "1b": check_1b,
    "2a": check_2a,
    "2b": check_2b,
    "0a-second": check_0a_second,
    "3b": check_3b,
    "3d": check_3d,
    "4a": check_4a,
    "0b": check_0b,
}


def check(phase: str, ctx: Context):
    checker = CHECKS.get(phase)
    if checker is None:
        raise KeyError(f"no artifact assertions defined for phase {phase!r}")
    return checker(ctx)
