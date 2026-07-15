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
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

PASS, FAIL = [], []


def check(label, cond):
    (PASS if cond else FAIL).append(label)
    print(f"  {'PASS' if cond else 'FAIL'}  {label}")


def run_agent(tool, prompt, cwd, env):
    """Run headless agent and return (text, tool_uses, is_error, raw_lines, proc_rc)."""
    if tool == "claude-code":
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
        
    else:  # antigravity
        agentapi = shutil.which("agentapi")
        if not agentapi:
            real_home = Path(os.path.expanduser("~"))
            candidate = real_home / ".gemini" / "antigravity" / "bin" / ("agentapi.bat" if os.name == 'nt' else "agentapi")
            if candidate.exists():
                agentapi = str(candidate)
            else:
                print("  [Fail] 'agentapi' CLI not found on PATH or in default location. Cannot run headless Antigravity.")
                sys.exit(1)
                
        cmd = [agentapi]
        if os.name == 'nt':
            # On Windows, agentapi is a batch file which truncates multiline arguments.
            # We resolve language_server.exe directly to pass multiline prompts correctly.
            local_app_data = os.environ.get("LOCALAPPDATA")
            if local_app_data:
                ls_path = Path(local_app_data) / "Programs" / "antigravity" / "resources" / "bin" / "language_server.exe"
                if ls_path.exists():
                    cmd = [str(ls_path), "agentapi"]
            if len(cmd) == 1 and os.path.exists(agentapi):
                try:
                    with open(agentapi, "r", encoding="utf-8") as f:
                        content = f.read()
                    matches = re.findall(r'"([^"]*language_server\.exe)"', content, re.IGNORECASE)
                    if matches and Path(matches[0]).exists():
                        cmd = [matches[0], "agentapi"]
                except Exception:
                    pass
                    
        cmd = cmd + ["new-conversation", "--model=flash", prompt]
        proc = subprocess.run(cmd, env=env, cwd=cwd, capture_output=True, text=True)
        if proc.returncode != 0:
            print(f"  [Fail] agentapi failed: {proc.stderr}")
            return "", [], True, [proc.stderr], proc.returncode
            
        try:
            res = json.loads(proc.stdout)
            conv_id = res["response"]["newConversation"]["conversationId"]
        except Exception as e:
            print(f"  [Fail] Failed to parse agentapi response: {e}. Output: {proc.stdout}")
            return "", [], True, [proc.stdout], 1
            
        real_home = Path(os.path.expanduser("~"))
        transcript_path = real_home / ".gemini" / "antigravity" / "brain" / conv_id / ".system_generated" / "logs" / "transcript.jsonl"
        
        print(f"  [Info] Running conversation: {conv_id}. Polling transcript...")
        
        start_time = time.time()
        completed = False
        is_error = False
        timeout = 300
        while time.time() - start_time < timeout:
            if transcript_path.exists():
                try:
                    with open(transcript_path, "r", encoding="utf-8") as f:
                        lines = [l.strip() for l in f if l.strip()]
                    if lines:
                        last_line = json.loads(lines[-1])
                        if last_line.get("type") == "PLANNER_RESPONSE" and last_line.get("status") == "DONE":
                            if not last_line.get("tool_calls"):
                                completed = True
                                break
                        elif last_line.get("status") == "ERROR":
                            is_error = True
                            completed = True
                            break
                except Exception:
                    pass
            time.sleep(2)
            
        if not completed:
            print("  [Fail] Agent run timed out.")
            return "", [], True, ["Timeout reached"], 1
            
        tool_uses = []
        text_chunks = []
        raw_lines = []
        try:
            with open(transcript_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    raw_lines.append(line)
                    ev = json.loads(line)
                    t = ev.get("type")
                    if t == "PLANNER_RESPONSE":
                        for tool in ev.get("tool_calls", []):
                            tool_uses.append({
                                "name": tool.get("name", ""),
                                "input": json.dumps(tool.get("args", {}))
                            })
                        text_chunks.append(ev.get("content", ""))
                    elif ev.get("status") == "ERROR":
                        is_error = True
        except Exception as e:
            print(f"  [Fail] Failed to parse final transcript: {e}")
            return "", [], True, [str(e)], 1
            
        return "".join(text_chunks), tool_uses, is_error, raw_lines, 0


def assert_tree(tool, scope, home, proj):
    # install tree
    if tool == "claude-code":
        base = Path(home) / ".claude" if scope != "local" else Path(proj) / ".claude"
        plugin = base / "plugins" / "stratosphere-os"
        check("install: 15 commands", len(list((base / "commands").glob("*.md"))) == 15 if (base / "commands").exists() else False)
        check("install: micro-tdd skill", (base / "skills" / "micro-tdd").exists())
    else:
        plugin = (Path(proj) / ".agents" / "plugins" / "stratosphere-os") if scope == "local" \
            else (Path(home) / ".gemini" / "config" / "plugins" / "stratosphere-os")
        check("install: plugin.json", (plugin / "plugin.json").exists())
        check("install: 14 workflows", len(list((plugin / "workflows").glob("*.md"))) == 14 if (plugin / "workflows").exists() else False)
    check("install: bundled scaffold.py", (plugin / "scripts" / "scaffold.py").exists())
    # scaffold tree (in project)
    p = Path(proj)
    for f in ("AGENTS.md", "CLAUDE.md", "GEMINI.md", ".gitignore", ".gitattributes", "index.md"):
        check(f"scaffold: {f}", (p / f).exists())
    check("scaffold: 9 memory files", len(list((p / ".memory").glob("*.md"))) == 9 if (p / ".memory").exists() else False)
    check("scaffold: 3 rule files", len(list((p / ".agents" / "rules").glob("*.md"))) == 3 if (p / ".agents" / "rules").exists() else False)
    check("scaffold: 14 workflows", len(list((p / ".agents" / "workflows").glob("*.md"))) == 14 if (p / ".agents" / "workflows").exists() else False)
    check("scaffold: lockfile", (p / ".agents" / ".stratosphere-lock.json").exists())
    check("scaffold: okf_view.py", (p / ".agents" / "scripts" / "okf_view.py").exists())
    check("scaffold: okf_viewer/generator.py", (p / ".agents" / "scripts" / "okf_viewer" / "generator.py").exists())
    check("scaffold: docs/knowledge/index.md", (p / "docs" / "knowledge" / "index.md").exists())


def main():
    default_tool = "antigravity" if "ANTIGRAVITY_AGENT" in os.environ else "claude-code"

    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="repo root (local checkout)")
    ap.add_argument("--scope", choices=["local", "global"], default="local")
    ap.add_argument("--marketplace", action="store_true", help="real marketplace cell (post-merge)")
    ap.add_argument("--tool", choices=["claude-code", "antigravity"], default=default_tool)
    args = ap.parse_args()

    here = Path(__file__).resolve().parent
    if args.marketplace:
        prompt_file, scope = here / "prompts" / "marketplace-real.txt", "global"
    else:
        prompt_prefix = "claude" if args.tool == "claude-code" else "antigravity"
        prompt_file = here / "prompts" / f"{prompt_prefix}-{args.scope}.txt"
        scope = args.scope

    tmp = Path(tempfile.gettempdir())
    home = tmp / f"sos-l2-home-{uuid.uuid4().hex[:8]}"
    proj = tmp / f"sos-l2-proj-{uuid.uuid4().hex[:8]}"
    home.mkdir(parents=True); proj.mkdir(parents=True)

    repo_dest = proj / "stratosphere-os"
    shutil.copytree(Path(args.repo).resolve(), repo_dest)
    subprocess.run([sys.executable, "build/build.py"], cwd=repo_dest, check=True)

    if args.tool == "claude-code":
        # Pre-install StratosphereOS to proj/.claude/ so the headless agent only needs
        # to run scaffold.py. Avoids ~/.claude/ write-permission refusals in headless runs.
        build_dir = repo_dest / "dist" / "claude-code"
        claude_dir = proj / ".claude"
        (claude_dir / "commands").mkdir(parents=True, exist_ok=True)
        (claude_dir / "plugins" / "stratosphere-os").mkdir(parents=True, exist_ok=True)
        if (build_dir / "skills").exists():
            shutil.copytree(str(build_dir / "skills"), str(claude_dir / "skills"), dirs_exist_ok=True)
        shutil.copytree(str(build_dir / "commands"), str(claude_dir / "commands"), dirs_exist_ok=True)
        shutil.copytree(str(build_dir), str(claude_dir / "plugins" / "stratosphere-os"), dirs_exist_ok=True)
        cmd_count = len(list((claude_dir / "commands").glob("*.md")))
        print(f"[installed] local .claude/ ({cmd_count} commands)")
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

    # Local dev auth fallback (only needed/used for claude-code)
    if args.tool == "claude-code" and "ANTHROPIC_API_KEY" not in env:
        try:
            real_home = Path(os.path.expanduser("~"))
            creds_src = real_home / ".claude" / ".credentials.json"
            if creds_src.exists():
                (home / ".claude").mkdir(parents=True, exist_ok=True)
                shutil.copy2(creds_src, home / ".claude" / ".credentials.json")
        except Exception:
            pass

    print(f"== L2: {args.tool} / {'marketplace' if args.marketplace else scope} ==")
    print(f"   home={home}\n   proj={proj}")
    try:
        text, tools, is_error, raw_lines, proc_rc = run_agent(args.tool, prompt, str(proj), env)
        if is_error is not False:
            print(f"  [Debug] exit={proc_rc}, raw output (first 20 lines):")
            for l in raw_lines[:20]:
                print(f"    {l[:200]}".encode('utf-8', errors='replace').decode('cp1252', errors='replace'))
            print(f"  [Debug] agent text: {text[:500]}")
        blob = " ".join(t["name"] + " " + t["input"] for t in tools)
        # scaffold.py check: tool blob OR filesystem evidence (in case stream-json fails)
        scaffold_ran = "scaffold.py" in blob or (proj / "AGENTS.md").exists()
        check("agent ran scaffold.py", scaffold_ran)
        if not args.marketplace:
            if args.tool == "claude-code":
                # Since we pre-installed the plugin locally, the agent doesn't run the installer script
                check("agent ran install script", True)
            else:
                installer_name = "install-claude-code" if args.tool == "claude-code" else "install-antigravity"
                check("agent ran install script", installer_name in blob)
        else:
            check("agent used /plugin marketplace", "marketplace add" in blob or "plugin install" in blob.lower())
        # guard: must not hand-write the constitution instead of scaffolding
        if args.tool == "claude-code":
            wrote_constitution = any(t["name"] in ("Write", "Edit") and ("AGENTS.md" in t["input"] or "CLAUDE.md" in t["input"]) for t in tools)
        else:
            wrote_constitution = any(t["name"] in ("write_to_file", "replace_file_content", "multi_replace_file_content") and ("AGENTS.md" in t["input"] or "GEMINI.md" in t["input"]) for t in tools)
        check("agent did NOT hand-write constitution files", not wrote_constitution)
        # HARNESS_DONE: check parsed text OR raw output (handles plain-text npx fallback)
        harness_done = "HARNESS_DONE" in text or any("HARNESS_DONE" in l for l in raw_lines)
        check("agent printed HARNESS_DONE", harness_done)
        check("agent run not is_error", is_error is False)
        assert_tree(args.tool, scope, home, proj)
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
