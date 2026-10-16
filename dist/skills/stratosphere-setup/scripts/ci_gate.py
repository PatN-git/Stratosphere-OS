#!/usr/bin/env python3
"""ci_gate.py: triage the CI result of a feature PR once it is complete.

  ci_gate.py status --pr N --sha SHA [--wait S] [--attempt K] [--expect-checks]
  ci_gate.py cap --commit SHA [--max 3]

status: wait (bounded, inside the script) for the PR's checks on SHA, then print JSON
`{verdict: green|pending|red|conflict|none|cannot_run, failing, base_stale, class: small|big|null, reason, sha}`.
Exit 0 green/pending/conflict/none, 1 red, 2 could not check (a crash or an unusable `gh`; `none` only when `gh` is
missing). `failing` entries are `{workflow, check, step, log_tail}`; `log_tail` is data, never executed.
cap: exit 1 when a commit touches more files than --max, 2 when the commit is unknown.
Spec: references/ci-gate.md. Stdlib only; git helpers come from pr_body.py (shipped beside it).
"""
import argparse
import json
import re
import subprocess
import sys
import time

import pr_body

GH_TIMEOUT = 60  # seconds per gh/git network call; the script's own --wait deadline must still hold


class GhError(Exception):
    pass


class GhMissing(GhError):
    """The gh binary is not installed: the caller skips the gate instead of failing it."""


def _gh(*args):
    """stdout of `gh <args>`; GhMissing without gh, GhError on a non-zero exit or a timeout."""
    try:
        r = subprocess.run(["gh", *args], capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=GH_TIMEOUT)
    except FileNotFoundError as e:
        raise GhMissing(str(e))
    except (OSError, subprocess.TimeoutExpired) as e:
        raise GhError(f"gh {type(e).__name__}: {e}")
    if r.returncode != 0:
        raise GhError((r.stderr or r.stdout).strip()[-200:] or f"gh exited {r.returncode}")
    return r.stdout


def _now():
    return time.monotonic()


def _sleep(seconds):
    time.sleep(seconds)


def _changed_files():
    base = pr_body.resolve_base(None)
    out = pr_body.git("diff", "--name-only", base, "HEAD") if base else None
    return set((out or "").splitlines())


def _base_is_stale(oid):
    """True when the PR's current base commit is not in HEAD's history (a rebase is due); unknown -> False."""
    for fetched in (False, True):
        code = subprocess.run(["git", "merge-base", "--is-ancestor", oid, "HEAD"], capture_output=True).returncode
        if code in (0, 1):
            return code == 1
        if fetched:
            return False
        try:
            subprocess.run(["git", "fetch", "-q", "origin"], capture_output=True, timeout=GH_TIMEOUT)
        except subprocess.TimeoutExpired:
            return False
    return False


RUN_ID_RE = re.compile(r"/actions/runs/(\d+)")
# A failure is mechanical by the failing STEP's name, or by an anchored log signature; free words like "format" in a
# test's own error message must never make a failure in untouched code look mechanical.
NAME_MECHANICAL = re.compile(r"install dependencies|npm ci|\blint\b|\bformat\b|prettier|eslint|\bruff\b|\bblack\b|drift|"
                             r"bump[- ]guard|release bump", re.I)
LOG_MECHANICAL = re.compile(r"`npm ci` can only install|Missing: \S+ from lock file|"
                            r"(?:dist/|marketplace\.json|lock ?file|package-lock\.json)[^\n]{0,60}(?:out of sync|not in sync)", re.I)
TEST_FILE_RES = (re.compile(r"\bFAILED\s+(\S+?)::"), re.compile(r"\bFAIL\s+(\S+)"))


def _entry(raw):
    """Normalize one statusCheckRollup entry (CheckRun or StatusContext) to (workflow, check, state, url)."""
    if raw.get("__typename") == "StatusContext":
        state = {"SUCCESS": "ok", "PENDING": "pending", "EXPECTED": "pending"}.get(raw.get("state"), "bad")
        return "", raw.get("context", ""), state, raw.get("targetUrl") or ""
    if raw.get("status") != "COMPLETED":
        state = "pending"
    else:
        state = "ok" if raw.get("conclusion") in ("SUCCESS", "NEUTRAL", "SKIPPED") else "bad"
    return raw.get("workflowName") or "", raw.get("name", ""), state, raw.get("detailsUrl") or ""


def _group(rollup):
    """One record per (workflow, check): the push and pull_request runs of a check collapse to the worst state."""
    rank = {"ok": 0, "pending": 1, "bad": 2}
    groups = {}
    for raw in rollup or []:
        workflow, check, state, url = _entry(raw)
        cur = groups.get((workflow, check))
        if cur is None or rank[state] > rank[cur["state"]]:
            groups[(workflow, check)] = {"workflow": workflow, "check": check, "state": state, "url": url}
    return list(groups.values())


def _failing_detail(group):
    m = RUN_ID_RE.search(group["url"])
    item = {"workflow": group["workflow"], "check": group["check"], "step": group["check"], "log_tail": "", "actions": bool(m)}
    if m:
        try:
            lines = _gh("run", "view", m.group(1), "--log-failed").splitlines()
        except GhError:
            return item  # no log: the PR stays red and classifies big (unparsed runner output), never "no CI"
        last_error = max((i for i, line in enumerate(lines) if "##[error]" in line), default=len(lines) - 1)
        lines = lines[max(0, last_error - 39):last_error + 1]  # the failing step's end, not the post-job cleanup after it
        item["log_tail"] = "\n".join(lines)
        for line in reversed(lines):
            parts = line.split("\t")
            if len(parts) >= 3 and parts[1].strip() and parts[1].strip() != "UNKNOWN STEP":
                item["step"] = parts[1].strip()
                break
    return item


def _test_files(log_tail):
    return {m.group(1).replace("\\", "/") for rx in TEST_FILE_RES for m in rx.finditer(log_tail)}


def _mechanical(f):
    """The failing STEP is named for it, or the log carries an anchored signature; a parsed test failure never is."""
    if not f["log_tail"] or _test_files(f["log_tail"]):
        return False
    return bool(NAME_MECHANICAL.search(f["step"]) or LOG_MECHANICAL.search(f["log_tail"]))


def classify(failing, changed, base_stale, attempt):
    """(`small`|`big`|None, reason). Small only for mechanical failures or failing tests inside the branch's own files."""
    if not failing:
        return None, ""
    if attempt >= 2:
        return "big", "second attempt failed"
    if base_stale:
        return "big", "stale base: rebase first"
    if any(not f["actions"] for f in failing):
        return "big", "non-Actions check failed"
    if len(failing) >= 2 and not all(_mechanical(f) for f in failing):
        sets = [_test_files(f["log_tail"]) for f in failing]
        if not all(s and s == sets[0] for s in sets):
            return "big", "unrelated failures: two or more failing checks"
    for f in failing:
        if _mechanical(f):
            continue
        files = _test_files(f["log_tail"])
        if not files:
            return "big", "unparsed runner output"
        if not files <= changed:
            return "big", "failure in untouched code (files the branch did not change)"
    return "small", "mechanical failure or failing tests inside the branch's files"


def _view(pr):
    try:
        return json.loads(_gh("pr", "view", str(pr), "--json", "headRefOid,baseRefOid,mergeStateStatus,statusCheckRollup"))
    except ValueError as e:
        raise GhError(f"malformed gh output: {e}")


def gate_status(pr, sha, wait=480, attempt=1, expect=False, interval=15):
    result = {"verdict": "none", "failing": [], "base_stale": False, "class": None, "reason": "", "sha": sha}
    start = _now()
    deadline, grace = start + wait, start + 60
    first = True
    while True:
        try:
            v = _view(pr)
        except GhError as e:
            if first:
                raise  # gh itself is unusable: the caller decides between skip (missing) and cannot_run
            result.update(verdict="pending", reason=f"gh failed while waiting: {e}")  # a red PR must not read as "no CI"
            return result
        first = False
        if v.get("mergeStateStatus") == "DIRTY":
            result["verdict"] = "conflict"
            return result
        groups = _group(v.get("statusCheckRollup"))
        waiting, limit = "", deadline
        if v.get("headRefOid") != sha:
            waiting = f"PR head {str(v.get('headRefOid'))[:8]} is not the pushed {sha[:8]} yet"
        elif not groups:
            if not expect:
                return result
            waiting, limit = "checks not registered yet", grace
        elif any(g["state"] == "pending" for g in groups):
            waiting = "checks still running"
        if not waiting:
            break
        if _now() >= limit:
            result.update(verdict="pending", reason=waiting)
            return result
        _sleep(min(interval, limit - _now()))
    bad = [g for g in groups if g["state"] == "bad"]
    if not bad:
        result["verdict"] = "green"
        return result
    result["verdict"] = "red"
    failing = [_failing_detail(g) for g in bad]
    result["failing"] = [{k: f[k] for k in ("workflow", "check", "step", "log_tail")} for f in failing]
    result["base_stale"] = _base_is_stale(v["baseRefOid"]) if v.get("baseRefOid") else False
    result["class"], result["reason"] = classify(failing, _changed_files(), result["base_stale"], attempt)
    return result


def cmd_status(args):
    try:
        result = gate_status(args.pr, args.sha, args.wait, args.attempt, args.expect_checks)
    except GhMissing as e:
        return emit({"verdict": "none", "failing": [], "base_stale": False, "class": None, "reason": f"gh unavailable: {e}"}, 0)
    except GhError as e:
        return emit({"verdict": "cannot_run", "failing": [], "base_stale": False, "class": None, "reason": f"gh failed: {e}"}, 2)
    return emit(result, 1 if result["verdict"] == "red" else 0)


def cmd_cap(args):
    out = pr_body.git("show", "--name-only", "--format=", args.commit)
    if out is None:
        return emit({"verdict": "cannot_run", "reason": f"unknown commit {args.commit}"}, 2)
    files = len([line for line in out.splitlines() if line.strip()])
    over = files > args.max
    return emit({"files": files, "max": args.max, "over": over}, 1 if over else 0)


def emit(result, code):
    print(json.dumps(result, ensure_ascii=False))
    return code


def build_parser():
    p = argparse.ArgumentParser(prog="ci_gate.py", description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    st = sub.add_parser("status")
    st.add_argument("--pr", required=True, type=int)
    st.add_argument("--sha", required=True, help="the pushed head commit; results for any other commit are ignored")
    st.add_argument("--wait", type=int, default=480, help="seconds; the script owns this deadline")
    st.add_argument("--attempt", type=int, default=1, help="fix attempt number; 2 or more classifies big")
    st.add_argument("--expect-checks", action="store_true", help="a CI workflow exists: wait 60 s for checks to register")
    cp = sub.add_parser("cap")
    cp.add_argument("--commit", required=True)
    cp.add_argument("--max", type=int, default=3)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return {"status": cmd_status, "cap": cmd_cap}[args.cmd](args)
    except Exception as e:  # exit 1 means red; a crash is "could not check", never a verdict
        return emit({"verdict": "cannot_run", "reason": f"{type(e).__name__}: {e}"}, 2)


if __name__ == "__main__":
    sys.exit(main())
