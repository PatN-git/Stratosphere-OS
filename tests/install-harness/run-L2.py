#!/usr/bin/env python3
"""L2 - headless Claude Code agent E2E for the install/onboarding flow.

Drives `claude -p` (same approach as .agents/skills/skill-creator/scripts/run_eval.py)
inside an isolated temp HOME + temp project, with a fully pre-answered prompt so the
agent never needs an interactive answer (no AskUserQuestion can block a headless run).

It asserts the agent drove the DETERMINISTIC scripts (install-* / scaffold.py /
sync_skills.py) rather than hand-copying files, and that the resulting tree matches
what L1 checks. Requires the `claude` CLI on PATH, authenticated, with network access.

Usage:
  python run-L2.py --repo <repo-root> --scope local
  python run-L2.py --repo <repo-root> --scope global
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


def check(label, cond):
    (PASS if cond else FAIL).append(label)
    print(f"  {'PASS' if cond else 'FAIL'}  {label}")


def run_agent(prompt, cwd, env):
    """Run `claude -p` and return (text_chunks, tool_uses, is_error)."""
    cmd = ["claude", "-p", prompt, "--output-format", "stream-json",
           "--verbose", "--include-partial-messages", "--dangerously-skip-permissions"]
           
    if os.name == 'nt' and shutil.which("claude") is None:
        if shutil.which("npx.cmd"):
            print("  [Warn] 'claude' not found natively (likely Windows Store VFS issue). Falling back to npx.cmd...")
            cmd = ["npx.cmd", "-y", "@anthropic-ai/claude-code@2.1.170"] + cmd[1:]
        else:
            print("  [Fail] 'claude' not found and 'npx.cmd' not available. Cannot run headless agent.")
            sys.exit(1)
            
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


def assert_tree(tool, scope, home, proj):
    # install tree
    if tool == "claude-code":
        base = Path(home) / ".claude" if scope != "local" else Path(proj) / ".claude"
        plugin = base / "plugins" / "stratosphere-os"
        check("install: 16 commands", len(list((base / "commands").glob("*.md"))) == 16 if (base / "commands").exists() else False)
        check("install: micro-tdd skill", (base / "skills" / "micro-tdd").exists())
    else:
        plugin = (Path(proj) / ".agents" / "plugins" / "stratosphere-os") if scope == "local" \
            else (Path(home) / ".gemini" / "config" / "plugins" / "stratosphere-os")
        check("install: plugin.json", (plugin / "plugin.json").exists())
        check("install: 11 workflows", len(list((plugin / "workflows").glob("*.md"))) == 11 if (plugin / "workflows").exists() else False)
    check("install: bundled scaffold.py", (plugin / "scripts" / "scaffold.py").exists())
    # scaffold tree (in project)
    p = Path(proj)
    for f in ("AGENT.md", "CLAUDE.md", "GEMINI.md", ".gitignore"):
        check(f"scaffold: {f}", (p / f).exists())
    check("scaffold: 8 memory files", len(list((p / ".memory").glob("*.md"))) == 8 if (p / ".memory").exists() else False)
    check("scaffold: 11 workflows", len(list((p / ".agents" / "workflows").glob("*.md"))) == 11 if (p / ".agents" / "workflows").exists() else False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="repo root (local checkout)")
    ap.add_argument("--scope", choices=["local", "global"], default="local")
    ap.add_argument("--marketplace", action="store_true", help="real marketplace cell (post-merge)")
    args = ap.parse_args()

    here = Path(__file__).resolve().parent
    if args.marketplace:
        prompt_file, scope = here / "prompts" / "marketplace-real.txt", "global"
    else:
        prompt_file = here / "prompts" / f"claude-{args.scope}.txt"
        scope = args.scope

    tmp = Path(tempfile.gettempdir())
    home = tmp / f"sos-l2-home-{uuid.uuid4().hex[:8]}"
    proj = tmp / f"sos-l2-proj-{uuid.uuid4().hex[:8]}"
    home.mkdir(parents=True); proj.mkdir(parents=True)

    repo_dest = proj / "stratosphere-os"
    shutil.copytree(Path(args.repo).resolve(), repo_dest)
    subprocess.run([sys.executable, "build/build.py"], cwd=repo_dest, check=True)
    prompt = prompt_file.read_text(encoding="utf-8").replace("<REPO>", str(repo_dest))

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
        check("agent ran scaffold.py", "scaffold.py" in blob)
        if not args.marketplace:
            check("agent ran install script", "install-claude-code" in blob)
        else:
            check("agent used /plugin marketplace", "marketplace add" in blob or "plugin install" in blob.lower())
        # guard: must not hand-write the constitution instead of scaffolding
        wrote_constitution = any(t["name"] in ("Write", "Edit") and ("AGENT.md" in t["input"] or "CLAUDE.md" in t["input"]) for t in tools)
        check("agent did NOT hand-write constitution files", not wrote_constitution)
        check("agent printed HARNESS_DONE", "HARNESS_DONE" in text)
        check("agent run not is_error", is_error is False)
        assert_tree("claude-code", scope, home, proj)
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
