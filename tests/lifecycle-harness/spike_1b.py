#!/usr/bin/env python3
"""L3 Slice 0 spike - can a scripted responder drive `1b-concept-framing` alone?

This is the slice that decides whether L3 is buildable as scoped. `1b` is the hardest
gate in the chain: a 20-50 question grill the user must end (1b:64,68), plus two
pick-among-generated gates whose options do not exist until the agent invents them.
If a responder cannot get `1b` to a valid discovery brief with no human present, the
phase list shrinks - `1a`/`1b` move to L4-manual and L3 covers `2a` onward.

Run it:
    python tests/lifecycle-harness/spike_1b.py            # needs `claude` or `npx`
    python tests/lifecycle-harness/spike_1b.py --keep     # keep the project to inspect

Exit 0 = the responder drove `1b` to a brief that passes the structural checks.
Exit 2 = `claude` is not available here; nothing was proven either way.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).parent
REPO = HERE.parents[1]


def _load(name):
    spec = importlib.util.spec_from_file_location(f"l3_{name}", HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[f"l3_{name}"] = mod
    spec.loader.exec_module(mod)
    return mod


env_mod = _load("env")
responder_mod = _load("responder")
session_mod = _load("session")
prompts_mod = _load("prompts")

# Slice 3 owns the opening turn now. The spike reads it rather than keeping its own
# copy: two texts that must stay identical are one text that will not.
SENTINEL = prompts_mod.sentinel("1b")
OPENING = prompts_mod.load("1b")

# Structural only. Agent prose varies between runs and models; these do not (E3).
REQUIRED_SECTIONS = ["## Actor", "## Problem", "## Chosen Framing",
                     "## Non-Goals", "## Riskiest Assumption"]


def find_brief(project: Path) -> Path | None:
    candidates = sorted((project / "docs" / "discovery").glob("*.md")) \
        if (project / "docs" / "discovery").is_dir() else []
    return candidates[0] if candidates else None


def check_brief(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    problems = [s for s in REQUIRED_SECTIONS if s not in text]
    if "type: discovery-brief" not in text:
        problems.append("frontmatter is missing type: discovery-brief")
    body = text.split("## Actor", 1)[-1]
    if len(body.strip()) < 200:
        problems.append("brief is present but essentially empty")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", action="store_true", help="keep the temp project")
    ap.add_argument("--max-questions", type=int, default=10)
    ap.add_argument("--max-rounds", type=int, default=2)
    ap.add_argument("--model", default=session_mod.DRIVER_MODEL,
                    help="model driving 1b - the agent under test")
    ap.add_argument("--proxy-model", default=session_mod.PROXY_MODEL,
                    help="model answering as the user from the fixture")
    ap.add_argument("--auditor-model", default=session_mod.AUDITOR_MODEL,
                    help="model judging brief sufficiency")
    args = ap.parse_args()

    try:
        session_mod.probe()
    except session_mod.ClaudeUnavailable as exc:
        print(f"[skip] {exc}")
        print("[skip] Slice 0 is UNPROVEN here - install the claude CLI and re-run.")
        return 2

    fixture = (HERE / "fixture" / "topic.md").read_text(encoding="utf-8")

    with env_mod.lifecycle_env(REPO, keep=args.keep) as env:
        print(f"[env] project={env.project}")
        print(f"[models] driver={args.model} proxy={args.proxy_model} "
              f"auditor={args.auditor_model}")
        proxy = session_mod.ClaudeProxy(env=env.child_env, model=args.proxy_model)
        auditor = session_mod.ClaudeAuditor(env=env.child_env,
                                            model=args.auditor_model)
        resp = responder_mod.Responder(
            fixture=fixture, proxy=proxy,
            max_questions=args.max_questions, max_rounds=args.max_rounds)

        chat = session_mod.ClaudeSession(cwd=env.project, env=env.child_env,
                                          model=args.model)
        turn = chat.send(OPENING)

        def guard(t):
            """A failed turn is a driver failure, not a question to answer.

            Two distinct traps, both hit during Slice 0:
              * An EMPTY turn fed to the responder surfaces as "proxy returned
                nothing", which blames the proxy for a CLI problem.
              * A turn can carry `is_error` while still having text. "Not logged in
                - Please run /login" is a perfectly good string, so a text-only check
                passes it through and the harness cheerfully grills an error message
                for ten rounds.
            """
            # The login failure arrives EITHER as a structured error event OR as
            # plain stderr text that never parses as JSON, so check both surfaces.
            blob = (t.text + "\n" + "\n".join(t.raw)).lower()
            hint = ""
            if "not logged in" in blob or "/login" in blob:
                hint = ("\n  The CLI is unauthenticated in the temp HOME. Seeding "
                        "~/.claude/.credentials.json is NOT always enough; run "
                        "`claude /login` once for the CLI this harness resolves to, "
                        "or point CLAUDE_CLI at an already-authenticated binary.")
            if t.is_error:
                raise RuntimeError(
                    f"the agent reported an error turn: {t.text[:300]!r}{hint}")
            if not t.text.strip():
                tail = "\n".join(t.raw[-5:]) or "<no output at all>"
                raise RuntimeError(
                    "the agent produced an empty turn - the CLI is not driving."
                    f"{hint}\n  last stream lines:\n{tail}")
            return t

        def settle():
            """Audit the brief if one exists. Returns (ok, gaps) or None."""
            brief = find_brief(env.project)
            if brief is None:
                return None
            ok, gaps = auditor.judge(brief.read_text(encoding="utf-8"))
            print(f"[audit] sufficient={ok} gaps={gaps}")
            return ok, gaps

        try:
            guard(turn)
            while True:
                # The agent declaring itself finished is NOT the pass condition.
                # The first full-depth run reached the sentinel in three replies
                # and never audited anything, so [pass] meant only that the
                # headings existed. Sufficiency is the auditor's call, always.
                if SENTINEL in turn.text:
                    verdict = settle()
                    if verdict is None:
                        print("[fail] sentinel printed but no discovery brief exists")
                        return 1
                    ok, gaps = verdict
                    if ok:
                        break
                    seed = resp.next_round(gaps)
                    if seed is None:
                        print("[fail] rounds exhausted with gaps still open:")
                        for g in gaps:
                            print(f"        - {g}")
                        return 1
                    turn = guard(chat.send(seed))
                    continue

                answer = resp.reply(turn.text)
                print(f"[{resp.replies:>3}] {answer.source:<18} {answer.text[:80]!r}")
                turn = guard(chat.send(answer.text))

                if answer.source == "policy:budget":
                    verdict = settle()
                    if verdict and not verdict[0]:
                        seed = resp.next_round(verdict[1])
                        if seed is None:
                            print("[fail] rounds exhausted with gaps still open:")
                            for g in verdict[1]:
                                print(f"        - {g}")
                            return 1
                        turn = guard(chat.send(seed))
        except responder_mod.ResponderFailure as exc:
            print(f"[fail] {type(exc).__name__}: {exc}")
            return 1
        except RuntimeError as exc:
            print(f"[fail] {exc}")
            return 1

        brief = find_brief(env.project)
        if brief is None:
            print("[fail] agent printed the sentinel but wrote no discovery brief")
            return 1
        problems = check_brief(brief)
        if problems:
            print(f"[fail] {brief.name} is not a valid brief:")
            for p in problems:
                print(f"        - {p}")
            return 1

        print(f"[pass] {brief.name} written in {resp.replies} replies, "
              f"{resp.rounds_used} round(s)")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
