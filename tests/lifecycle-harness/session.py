#!/usr/bin/env python3
"""L3 Slice 0 - multi-turn Claude driver, plus the isolated Proxy and Auditor.

`run-L2.py` spawns one `claude -p` with `stdin=DEVNULL` and reads the stream to the
end. That is enough for a single-shot install, but a lifecycle gate is a conversation.
`ClaudeSession` keeps the conversation by capturing `session_id` from the first turn
and passing `--resume` on every turn after it, so each turn is its own process and a
hung turn cannot wedge the run.

`ClaudeProxy` and `ClaudeAuditor` deliberately do NOT use `ClaudeSession`. Each call
is a fresh session in an empty working directory: no project files, no history, no
sight of the draft brief. That isolation is the whole reason the proxy's answers are
worth anything - see responder.py.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

# Pinned so a CLI release cannot silently change harness behaviour. Keep in step
# with tests/install-harness/run-L2.py.
NPX_PACKAGE = "@anthropic-ai/claude-code@2.1.170"


class ClaudeUnavailable(RuntimeError):
    """Neither `claude` nor `npx` is usable, so nothing can be driven."""


def _version_key(name: str) -> tuple:
    """Numeric version sort. Lexicographic would rank 2.1.9 above 2.1.10."""
    parts = []
    for chunk in re.split(r"[._-]", name):
        parts.append((0, int(chunk)) if chunk.isdigit() else (1, 0))
    return tuple(parts)


def _bundled_cli() -> Path | None:
    """The Claude desktop app ships its own CLI, off PATH.

    On Windows it lands in %APPDATA%\\Claude\\claude-code\\<version>\\claude.exe. Without
    this, a machine that plainly has Claude installed falls through to npx, which
    downloads a different (pinned, older) build - so the harness would test a CLI the
    developer is not using.
    """
    roots = [Path(os.environ.get("APPDATA", "")) / "Claude" / "claude-code",
             Path.home() / ".claude" / "local",
             Path(os.environ.get("LOCALAPPDATA", "")) / "Claude" / "claude-code"]
    found = []
    for root in roots:
        if not root.is_dir():
            continue
        for child in root.iterdir():
            for exe in (child / "claude.exe", child / "claude"):
                if exe.is_file():
                    found.append((_version_key(child.name), exe))
    return max(found)[1] if found else None


def _base_cmd() -> list[str]:
    override = os.environ.get("CLAUDE_CLI")
    if override:
        return [override]
    if shutil.which("claude"):
        return ["claude"]
    bundled = _bundled_cli()
    if bundled:
        return [str(bundled)]
    npx = shutil.which("npx.cmd") or shutil.which("npx")
    if npx:
        return [npx, "-y", NPX_PACKAGE]
    raise ClaudeUnavailable(
        "no claude CLI found: not in $CLAUDE_CLI, not on PATH, not bundled with the "
        "desktop app, and npx is unavailable")


def probe(timeout: int = 120) -> None:
    """Confirm the CLI runs, not just that a binary is on PATH.

    `npx` is almost always present, so `shutil.which` alone reports success and the
    run then dies mid-grill with empty turns. Failing here instead costs one cheap
    invocation and produces a diagnosis rather than a mystery.
    """
    cmd = _base_cmd() + ["--version"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ClaudeUnavailable(f"{' '.join(cmd)} did not run: {exc}") from exc
    if r.returncode != 0 or not r.stdout.strip():
        raise ClaudeUnavailable(
            f"{' '.join(cmd)} exited {r.returncode} with no version output; "
            f"stderr: {(r.stderr or '').strip()[:300]}")


@dataclass
class Turn:
    text: str
    tool_uses: list[dict] = field(default_factory=list)
    is_error: bool | None = None
    raw: list[str] = field(default_factory=list)


def _run(cmd: list[str], cwd, env, timeout: int) -> tuple[Turn, str | None]:
    proc = subprocess.Popen(cmd, cwd=str(cwd), env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                            text=True, encoding="utf-8", errors="replace")
    turn, session_id = Turn(text=""), None
    text_parts: list[str] = []
    try:
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            turn.raw.append(line)
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            session_id = ev.get("session_id") or session_id
            if ev.get("type") == "assistant":
                for block in ev.get("message", {}).get("content", []):
                    if block.get("type") == "tool_use":
                        turn.tool_uses.append({"name": block.get("name", ""),
                                               "input": json.dumps(block.get("input", {}))})
                    elif block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
            elif ev.get("type") == "result":
                turn.is_error = ev.get("is_error")
                if not text_parts and ev.get("result"):
                    text_parts.append(str(ev["result"]))
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        raise TimeoutError(f"turn exceeded {timeout}s")
    turn.text = "\n".join(text_parts).strip()
    return turn, session_id


class ClaudeSession:
    """One continuing conversation, resumed turn by turn."""

    def __init__(self, cwd, env=None, timeout: int = 900):
        self.cwd, self.env, self.timeout = Path(cwd), env or dict(os.environ), timeout
        self.session_id: str | None = None
        self.turns: list[Turn] = []

    def send(self, prompt: str) -> Turn:
        cmd = _base_cmd() + ["-p", prompt, "--output-format", "stream-json",
                             "--verbose", "--dangerously-skip-permissions"]
        if self.session_id:
            cmd += ["--resume", self.session_id]
        turn, sid = _run(cmd, self.cwd, self.env, self.timeout)
        # Only adopt the first id: --resume must keep pointing at one conversation.
        self.session_id = self.session_id or sid
        self.turns.append(turn)
        return turn


def _ask_isolated(prompt: str, env, timeout: int) -> str:
    """One throwaway session in an empty directory. No project, no history."""
    with tempfile.TemporaryDirectory(prefix="l3-isolated-") as empty:
        cmd = _base_cmd() + ["-p", prompt, "--output-format", "stream-json",
                             "--verbose", "--dangerously-skip-permissions"]
        turn, _ = _run(cmd, empty, env, timeout)
    return turn.text


class ClaudeProxy:
    """Answers as the user, knowing only the fixture (responder.Proxy)."""

    def __init__(self, env=None, timeout: int = 300):
        self.env, self.timeout = env or dict(os.environ), timeout

    def answer(self, question: str, fixture: str) -> str:
        prompt = (
            "You are standing in for a product owner being interviewed about a concept.\n"
            "Below is everything you know. Answer ONLY from it, in first person, in at "
            "most four sentences. Be concrete and take a position - do not hedge, do not "
            "ask a question back, do not mention that you are given a document.\n"
            "If the document genuinely does not cover the question, answer with your best "
            "reading of the positions it does state.\n\n"
            f"=== WHAT YOU KNOW ===\n{fixture}\n=== END ===\n\n"
            f"Interviewer's question:\n{question}")
        return _ask_isolated(prompt, self.env, self.timeout)


_VERDICT = re.compile(r"\{.*\}", re.S)


class ClaudeAuditor:
    """Judges whether a draft brief is good enough to proceed (responder.Auditor)."""

    def __init__(self, env=None, timeout: int = 300):
        self.env, self.timeout = env or dict(os.environ), timeout

    def judge(self, brief: str) -> tuple[bool, list[str]]:
        prompt = (
            "You are auditing a discovery brief for sufficiency, not for style.\n"
            "It is sufficient when a reader could write a PRD from it without going back "
            "to the author: the actor is specific, the problem is concrete, the chosen "
            "framing is stated with its rejected alternatives, non-goals exist, and the "
            "riskiest assumption names a cheap test.\n"
            "Reply with ONLY a JSON object: "
            '{\"sufficient\": true|false, \"gaps\": [\"...\"]}. '
            "Each gap must name what is missing and be answerable in one question.\n\n"
            f"=== BRIEF ===\n{brief}\n=== END ===")
        raw = _ask_isolated(prompt, self.env, self.timeout)
        m = _VERDICT.search(raw)
        if not m:
            # Unparseable verdict is a FAIL, never a pass: a gate that cannot be read
            # must not wave the run through.
            return False, [f"auditor returned no JSON verdict: {raw[:200]!r}"]
        try:
            v = json.loads(m.group(0))
        except json.JSONDecodeError:
            return False, [f"auditor verdict was not valid JSON: {m.group(0)[:200]!r}"]
        return bool(v.get("sufficient")), [str(g) for g in v.get("gaps", [])]
