#!/usr/bin/env python3
"""ci_gate.py: run the project's CI checks locally before a push, and triage CI once the feature PR is complete.

  ci_gate.py parity

parity: read `.github/workflows/*.yml`, keep the steps of `pull_request` jobs that are the project's own checks and
run them locally in order, stopping at the first failure. Output is JSON `{verdict: pass|fail|none|cannot_run,
steps, skipped, reason}`. Exit 0 pass/none, 1 fail, 2 could not run (never a pass).
Steps with secrets, expressions, deploys, `uses:` actions, services or environment-mutating installs are skipped and
reported, never guessed. Spec: references/ci-gate.md. Stdlib only; git and suite helpers come from pr_body.py
(shipped beside it).
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pr_body

KEY_RE = re.compile(r"""^(?P<k>"[^"]*"|'[^']*'|[^\s#\[{"'][^:]*?)\s*:(?:\s+(?P<v>.*))?$""")
BLOCK_RE = re.compile(r"^[|>][+-]?\d?$")
EXPR = "${{"
# (pattern over the whole `run:` text, reason): a hit skips the step even when an allow rule matches
DENY = (
    (re.compile(r"\b(?:deploy|publish|release)\b", re.I), "deploy/publish/release"),
    (re.compile(r"(?:^|[\s;&|(])gh\s"), "uses gh"),
    (re.compile(r"\bgit\s+push\b"), "git push"),
    (re.compile(r"\b(?:pip3?|python3?\s+-m\s+pip|uv\s+pip|pipx)\s+install\b"), "environment install"),
    (re.compile(r"\bnpm\s+(?:i|install)\s+(?:-g|--global)\b|\bsudo\b|\bapt(?:-get)?\b|\bbrew\b|\bchoco\b|\bwinget\b"),
     "environment install"),
    (re.compile(r"\b(?:curl|wget)\b"), "network download"),
    (re.compile(r"\bdocker\b"), "docker"),
)
ALLOW = re.compile(r"^(?:(?:npm|pnpm|yarn)\s+(?:ci|install|i|run|test|exec)\b|npx\s|pytest\b|python3?\s+\S|py\s+-\d?\s*\S|"
                   r"node\s+\S|bash\s+\S|sh\s+\S|make\b|go\s+test\b|cargo\s+(?:test|build|check)\b|\./\S)")
PR_IF = "github.event_name == 'pull_request'"


# --- a small YAML reader for GitHub workflows ---------------------------------------------------------------

def _strip_comment(value):
    quote = None
    for i, ch in enumerate(value):
        if quote:
            quote = None if ch == quote else quote
        elif ch in "\"'":
            quote = ch
        elif ch == "#" and (i == 0 or value[i - 1] in " \t"):
            return value[:i]
    return value


def _flow(inner):
    items, cur, quote = [], "", None
    for ch in inner:
        if quote:
            quote = None if ch == quote else quote
        elif ch in "\"'":
            quote = ch
        elif ch == ",":
            items.append(cur)
            cur = ""
            continue
        cur += ch
    items.append(cur)
    return [i for i in items if i.strip()]


def _scalar(value):
    v = _strip_comment(value).strip()
    if len(v) >= 2 and v[0] in "\"'" and v[-1] == v[0]:
        return v[1:-1]
    if v.startswith("[") and v.endswith("]"):
        return [_scalar(i) for i in _flow(v[1:-1])]
    return v


def parse_yaml(text):
    """Parse the subset workflows use: maps, sequences, `|`/`>` blocks, flow lists, quoted scalars. Else best effort."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    pos = [0]

    def indent(line):
        return len(line) - len(line.lstrip(" "))

    def peek():
        while pos[0] < len(lines) and (not lines[pos[0]].strip() or lines[pos[0]].lstrip().startswith("#")):
            pos[0] += 1
        if pos[0] >= len(lines):
            return None
        return indent(lines[pos[0]]), lines[pos[0]].strip()

    def is_item(content):
        return content == "-" or content.startswith("- ")

    def block(min_indent):
        p = peek()
        if p is None or p[0] < min_indent:
            return None
        return sequence(p[0]) if is_item(p[1]) else mapping(p[0])

    def block_scalar(parent, style):
        buf, base = [], None
        while pos[0] < len(lines):
            line = lines[pos[0]]
            if not line.strip():
                buf.append("")
                pos[0] += 1
                continue
            ind = indent(line)
            if ind <= parent:
                break
            base = ind if base is None else base
            buf.append(line[base:] if ind >= base else line.strip())
            pos[0] += 1
        while buf and buf[-1] == "":
            buf.pop()
        return "\n".join(buf) if style == "|" else " ".join(x for x in buf if x)

    def mapping(ind):
        out = {}
        while True:
            p = peek()
            if p is None or p[0] != ind or is_item(p[1]):
                return out
            m = KEY_RE.match(p[1])
            pos[0] += 1
            if not m:
                continue
            key, val = m["k"].strip("\"'"), (m["v"] or "").strip()
            bare = _strip_comment(val).strip()
            if BLOCK_RE.match(bare):
                out[key] = block_scalar(ind, bare[0])
            elif bare == "":
                nxt = peek()
                nested = nxt is not None and (nxt[0] > ind or (nxt[0] == ind and is_item(nxt[1])))
                out[key] = block(nxt[0]) if nested else None
            else:
                out[key] = _scalar(val)

    def sequence(ind):
        out = []
        while True:
            p = peek()
            if p is None or p[0] != ind or not is_item(p[1]):
                return out
            line = lines[pos[0]]
            after = line[ind + 1:]
            content = after.strip()
            if content == "":
                pos[0] += 1
                nxt = peek()
                out.append(block(nxt[0]) if nxt is not None and nxt[0] > ind else None)
            elif KEY_RE.match(content):
                col = ind + 1 + (len(after) - len(after.lstrip()))
                lines[pos[0]] = " " * col + content
                out.append(mapping(col))
            else:
                pos[0] += 1
                out.append(_scalar(content))

    doc = block(0)
    return doc if isinstance(doc, dict) else {}


# --- which steps are the project's own checks --------------------------------------------------------------

def _events(doc):
    on = doc.get("on")
    if isinstance(on, str):
        return {on}
    if isinstance(on, list):
        return {str(e) for e in on}
    return set(on) if isinstance(on, dict) else set()


def _pr_true(cond):
    c = re.sub(r"^\$\{\{\s*|\s*\}\}$", "", str(cond or "").strip()).strip()
    return c == "" or c.replace('"', "'") == PR_IF


def _job_skip(job):
    if job.get("services"):
        return "services"
    if isinstance(job.get("defaults"), dict) and (job["defaults"].get("run") or {}):
        return "job defaults.run"
    if not _pr_true(job.get("if")):
        return "if: not PR-true"
    return None


def _step_skip(step):
    if step.get("uses"):
        return "uses: action"
    run = str(step.get("run") or "")
    env = step.get("env") if isinstance(step.get("env"), dict) else {}
    if EXPR in run or EXPR in str(step.get("working-directory") or "") or any(EXPR in str(v) for v in env.values()):
        return "expression"
    if not _pr_true(step.get("if")):
        return "if: not PR-true"
    for rx, why in DENY:
        if rx.search(run):
            return why
    if not any(ALLOW.match(line.strip()) for line in run.splitlines()):
        return "not a project check"
    return None


def select_steps(text, source):
    """(selected, skipped) for the `pull_request` jobs of one workflow file's text."""
    doc = parse_yaml(text)
    if "pull_request" not in _events(doc):
        return [], []
    selected, skipped = [], []
    for jname, job in (doc.get("jobs") or {}).items():
        if not isinstance(job, dict):
            continue
        job_why = _job_skip(job)
        for n, step in enumerate(job.get("steps") or [], 1):
            if not isinstance(step, dict) or not (step.get("run") or step.get("uses")):
                continue
            name = str(step.get("name") or step.get("run") or step.get("uses")).splitlines()[0][:80]
            why = job_why or _step_skip(step)
            if why:
                skipped.append({"workflow": source, "job": jname, "name": name, "reason": why})
                continue
            env = step.get("env") if isinstance(step.get("env"), dict) else {}
            selected.append({"workflow": source, "job": jname, "name": name, "run": str(step["run"]),
                             "cwd": step.get("working-directory") or ".", "env": {k: str(v) for k, v in env.items()}})
    return selected, skipped


# --- running them -------------------------------------------------------------------------------------------

def pick_bash(which, git_bash):
    """Git Bash wins; a PATH bash is fine unless it is the WSL launcher in System32 (a different Linux)."""
    if git_bash:
        return git_bash
    if which and not re.search(r"[\\/]system32[\\/]bash\.exe$", which, re.I):
        return which
    return None


def find_bash():
    git_bash = None
    if os.name == "nt":
        try:
            exec_path = subprocess.run(["git", "--exec-path"], capture_output=True, text=True).stdout.strip()
            cand = Path(exec_path).parents[2] / "usr" / "bin" / "bash.exe"
            git_bash = str(cand) if exec_path and cand.is_file() else None
        except (OSError, IndexError):
            git_bash = None
    return pick_bash(shutil.which("bash"), git_bash)


def _signatures(cmd):
    tokens = pr_body._tokens(cmd)
    for i, tok in enumerate(tokens[:-1]):  # drop a leading `...test_gate.py record [--suite X] --` wrapper
        if pr_body._launcher(tok) == "test_gate.py" and tokens[i + 1] == "record" and "--" in tokens[i:]:
            tokens = tokens[i + tokens[i:].index("--") + 1:]
            break
    sigs, seg = set(), []
    for tok in tokens + [";"]:
        if tok not in pr_body.SEGMENT_BREAKS:
            seg.append(tok)
            continue
        t, seg = seg, []
        if t and pr_body._launcher(t[0]) == "npx":
            t = t[1:]
        if len(t) >= 3 and pr_body._launcher(t[0]) in ("python", "python3", "py") and t[1] == "-m":
            t = t[2:]
        if not t:
            continue
        head = pr_body._launcher(t[0])
        if head in ("bash", "sh") and len(t) >= 2:
            sigs.add((head, t[1]))
        elif head in ("npm", "yarn", "pnpm"):
            sigs.add((head, *[x for x in t[1:] if x != "run"][:1]))
        else:
            sigs.add((head,))
    return sigs


def covered_by_suite(cmd, record):
    """True when `cmd` is a full-suite run and `record` (a reusable suite record) ran the same runner or script."""
    return (not pr_body.is_scoped(cmd)) and bool(_signatures(cmd) & _signatures(record["cmd"]))


def tracked_changes():
    out = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, encoding="utf-8").stdout
    return {line[3:] for line in out.splitlines() if line and not line.startswith("??")}


def tail(text, n=20):
    return "\n".join(text.splitlines()[-n:])


def cmd_parity(args):
    wfdir = Path(".github") / "workflows"
    selected, skipped = [], []
    for f in sorted(wfdir.glob("*.y*ml")) if wfdir.is_dir() else []:
        s, k = select_steps(f.read_text(encoding="utf-8-sig"), f.name)
        selected += s
        skipped += k
    result = {"verdict": "none", "steps": [], "skipped": skipped, "reason": ""}
    if not selected:
        return emit(result, 0)
    record = pr_body.reusable_suite(".tmp")
    bash = find_bash()
    before = tracked_changes()
    for step in selected:
        entry = {k: step[k] for k in ("workflow", "job", "name")}
        entry["cmd"] = step["run"].splitlines()[0][:120]
        result["steps"].append(entry)
        if record and covered_by_suite(step["run"], record):
            entry["status"] = "covered"
            continue
        if bash is None:
            result.update(verdict="cannot_run", reason="no usable bash on this host")
            entry["status"] = "not run"
            return emit(result, 2)
        env = {**os.environ, "CI": "true", **step["env"]}
        run = subprocess.run([bash, "--noprofile", "--norc", "-eo", "pipefail", "-c", step["run"]], cwd=step["cwd"],
                             env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
        entry["status"] = "pass" if run.returncode == 0 else "fail"
        if run.returncode != 0:
            entry["tail"] = tail(run.stdout + run.stderr)
            result.update(verdict="fail", reason=f"step failed: {step['name']}")
            return emit(result, 1)
    changed = sorted(tracked_changes() - before)
    if changed:
        result.update(verdict="fail", reason="tree changed", changed=changed)
        return emit(result, 1)
    result["verdict"] = "pass"
    return emit(result, 0)


def emit(result, code):
    print(json.dumps(result, ensure_ascii=False))
    return code


def build_parser():
    p = argparse.ArgumentParser(prog="ci_gate.py", description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("parity")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    return {"parity": cmd_parity}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
