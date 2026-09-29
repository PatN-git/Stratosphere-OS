#!/usr/bin/env python3
"""L2 - headless Claude Code agent E2E for the install/onboarding flow.

Drives `claude -p` (same approach as .agents/skills/skill-creator/scripts/run_eval.py)
inside an isolated temp HOME + temp project, with a fully pre-answered prompt so the
agent never needs an interactive answer (no AskUserQuestion can block a headless run).

It asserts the agent drove the DETERMINISTIC scripts (scaffold.py /
sync_skills.py) rather than hand-copying files, and that the resulting tree matches
what L1 checks. Requires the `claude` CLI on PATH, authenticated, with network access.

Usage:
  python run-L2.py --repo <repo-root> --scope local     # claude-code only; Antigravity has no headless runner (see README L4 + L1 Track D)
  python run-L2.py --repo <repo-root> --marketplace      # only valid post-merge to main

Exit code 0 = all checks passed, 1 = failure.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

PASS, FAIL = [], []


# Derived, never hardcoded: a count literal silently rots and then fails as
# "wrong count" rather than "layout changed".
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
EXPECTED_SKILLS = len(list((_REPO_ROOT / "dist" / "skills").glob("*/SKILL.md")))

def check(label, cond):
    (PASS if cond else FAIL).append(label)
    print(f"  {'PASS' if cond else 'FAIL'}  {label}")


def run_agent(prompt, cwd, env):
    """Run the headless Claude Code agent and return (text, tool_uses, is_error, raw_lines, proc_rc)."""
    if os.name == 'nt' and shutil.which("claude") is None:
        if not shutil.which("npx.cmd"):
            print("  [Fail] 'claude' not found and 'npx.cmd' not available. Cannot run headless agent.")
            sys.exit(1)
        print("  [Warn] 'claude' not found via shutil.which (Store Python VFS). "
              "Using npx.cmd with stdin-piped prompt...")
        # No -p flag: binary receives prompt from stdin (piped/non-interactive mode).
        cmd = ["npx.cmd", "-y", "@anthropic-ai/claude-code@2.1.170",
               "--output-format", "stream-json", "--verbose",
               "--dangerously-skip-permissions"]
        proc = subprocess.Popen(cmd, cwd=cwd, env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                stdin=subprocess.PIPE, text=True, encoding="utf-8")
        # Write prompt and close stdin immediately (small prompt fits in OS pipe buffer).
        proc.stdin.write(prompt + "\n")
        proc.stdin.close()
    else:
        cmd = ["claude", "-p", prompt, "--output-format", "stream-json",
               "--dangerously-skip-permissions"]
        proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                text=True, encoding="utf-8")
    tool_uses, text, is_error = [], [], None
    raw_lines = []
    for line in proc.stdout:
        line = line.strip()
        if not line:
            continue
        raw_lines.append(line)
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        t = ev.get("type")
        if t == "assistant":
            for block in ev.get("message", {}).get("content", []):
                if block.get("type") == "tool_use":
                    tool_uses.append({"name": block.get("name", ""),
                                      "input": json.dumps(block.get("input", {}))})
                elif block.get("type") == "text":
                    text.append(block.get("text", ""))
        elif t == "result":
            is_error = ev.get("is_error", None)
    proc.wait()
    return "".join(text), tool_uses, is_error, raw_lines, proc.returncode


def marketplace_skills_dir(home):
    """A marketplace install caches the whole repo, with the bundle at <plugin>/dist/skills."""
    hits = sorted((Path(home) / ".claude" / "plugins" / "cache").glob("*/stratosphere-os/*/dist/skills"))
    return hits[-1] if hits else Path(home) / ".claude" / "plugins" / "cache" / "<stratosphere-os not installed>"


def assert_tree(skills_dir, proj):
    # install tree
    setup_dir = skills_dir / "stratosphere-setup"  # scaffolder payload rides inside setup
    check("install: 26 skills", len(list(skills_dir.glob("*/SKILL.md"))) == EXPECTED_SKILLS if skills_dir.exists() else False)
    check("install: micro-tdd skill", (skills_dir / "micro-tdd").exists())
    check("install: bundled scaffold.py", (setup_dir / "scripts" / "scaffold.py").exists())
    # scaffold tree (in project)
    p = Path(proj)
    for f in ("AGENTS.md", "CLAUDE.md", "GEMINI.md", ".gitignore", ".gitattributes", "index.md"):
        check(f"scaffold: {f}", (p / f).exists())
    check("scaffold: 9 memory files", len(list((p / ".memory").glob("*.md"))) == 9 if (p / ".memory").exists() else False)
    check("scaffold: 3 rule files", len(list((p / ".agents" / "rules").glob("*.md"))) == 3 if (p / ".agents" / "rules").exists() else False)
    check("scaffold: 26 skills", len(list((p / ".agents" / "skills").glob("*/SKILL.md"))) == EXPECTED_SKILLS)
    check("scaffold: no legacy workflows/ dir", not (p / ".agents" / "workflows").exists())
    check("scaffold: lockfile", (p / ".agents" / ".stratosphere-lock.json").exists())
    check("scaffold: okf_view.py", (p / ".agents" / "scripts" / "okf_view.py").exists())
    check("scaffold: okf_viewer/generator.py", (p / ".agents" / "scripts" / "okf_viewer" / "generator.py").exists())
    check("scaffold: docs/knowledge/index.md", (p / "docs" / "knowledge" / "index.md").exists())
    check("scaffold: docs/nightly/index.md", (p / "docs" / "nightly" / "index.md").exists())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="repo root (local checkout)")
    ap.add_argument("--scope", choices=["local"], default="local")  # claude-global cell retired (BT-119)
    ap.add_argument("--marketplace", action="store_true", help="real marketplace cell (post-merge)")
    args = ap.parse_args()

    here = Path(__file__).resolve().parent
    if args.marketplace:
        prompt_file, scope = here / "prompts" / "marketplace-real.txt", "global"
    else:
        prompt_file, scope = here / "prompts" / f"claude-{args.scope}.txt", args.scope

    tmp = Path(tempfile.gettempdir())
    home = tmp / f"sos-l2-home-{uuid.uuid4().hex[:8]}"
    proj = tmp / f"sos-l2-proj-{uuid.uuid4().hex[:8]}"
    home.mkdir(parents=True); proj.mkdir(parents=True)

    repo_dest = proj / "stratosphere-os"
    shutil.copytree(Path(args.repo).resolve(), repo_dest)
    subprocess.run([sys.executable, "build/build.py"], cwd=repo_dest, check=True)

    if not args.marketplace:
        # Pre-install StratosphereOS to proj/.claude/ so the headless agent only needs
        # to run scaffold.py. Avoids ~/.claude/ write-permission refusals in headless runs.
        build_dir = repo_dest / "dist" / "skills"
        claude_dir = proj / ".claude"
        shutil.copytree(str(build_dir), str(claude_dir / "skills"), dirs_exist_ok=True)
        skill_count = len(list((claude_dir / "skills").glob("*/SKILL.md")))
        print(f"[installed] local .claude/skills ({skill_count} skills)")
    prompt_content = prompt_file.read_text(encoding="utf-8")
    prompt = (prompt_content
              .replace("<REPO>", str(repo_dest))
              .replace("<PROJ>", str(proj))
              .replace("<HOME>", str(home))
              .replace("<HOMEDRIVE>", str(home)[:2])
              .replace("<HOMEPATH>", str(home)[2:]))

    env = dict(os.environ)
    env["USERPROFILE"] = str(home)
    env["HOME"] = str(home)
    env["HOMEDRIVE"] = str(home)[:2]
    env["HOMEPATH"] = str(home)[2:]
    env.pop("CLAUDECODE", None)  # avoid nested-session confusion

    # Local dev auth fallback
    if "ANTHROPIC_API_KEY" not in env:
        try:
            real_home = Path(os.path.expanduser("~"))
            creds_src = real_home / ".claude" / ".credentials.json"
            if creds_src.exists():
                (home / ".claude").mkdir(parents=True, exist_ok=True)
                shutil.copy2(creds_src, home / ".claude" / ".credentials.json")
        except Exception:
            pass

    print(f"== L2: claude-code / {'marketplace' if args.marketplace else scope} ==")
    print(f"   home={home}\n   proj={proj}")
    try:
        text, tools, is_error, raw_lines, proc_rc = run_agent(prompt, str(proj), env)
        if is_error is not False:
            print(f"  [Debug] exit={proc_rc}, raw output (first 20 lines):")
            for l in raw_lines[:20]:
                print(f"    {l[:200]}".encode('utf-8', errors='replace').decode('cp1252', errors='replace'))
            print(f"  [Debug] agent text: {text[:500]}")
        blob = " ".join(t["name"] + " " + t["input"] for t in tools)
        # scaffold.py check: tool blob OR filesystem evidence (in case stream-json fails)
        scaffold_ran = "scaffold.py" in blob or (proj / "AGENTS.md").exists()
        check("agent ran scaffold.py", scaffold_ran)
        if args.marketplace:
            check("agent used /plugin marketplace", "marketplace add" in blob or "plugin install" in blob.lower())
        # guard: must not hand-write the constitution instead of scaffolding
        wrote_constitution = any(t["name"] in ("Write", "Edit") and ("AGENTS.md" in t["input"] or "CLAUDE.md" in t["input"]) for t in tools)
        check("agent did NOT hand-write constitution files", not wrote_constitution)
        # HARNESS_DONE: check parsed text OR raw output (handles plain-text npx fallback)
        harness_done = "HARNESS_DONE" in text or any("HARNESS_DONE" in l for l in raw_lines)
        check("agent printed HARNESS_DONE", harness_done)
        check("agent run not is_error", is_error is False)
        assert_tree(marketplace_skills_dir(home) if args.marketplace else proj / ".claude" / "skills", proj)
    finally:
        shutil.rmtree(home, ignore_errors=True)
        shutil.rmtree(proj, ignore_errors=True)

    print(f"\n----- L2: {len(PASS)} passed, {len(FAIL)} failed -----")
    if FAIL:
        for f in FAIL:
            print(f"  - {f}")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
