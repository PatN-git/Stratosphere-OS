#!/usr/bin/env python3
"""tracker.py — Unified Python CLI Façade for tracker operations (BT-247).

Routes verbs and reads to either GitHub (gh) or Local (issues.py) based on
`tracker: github | local` resolved from .memory/ARCHITECTURE.md via reconcile.read_tracker.
Enforces the Single Status Invariant and [[A-005]] retry/halt contract.
"""
import argparse, json, re, sys, tempfile, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import issues, reconcile
from _tracker_common import NONE_TOKENS

ARCH_DEFAULT = reconcile.ARCH_DEFAULT
RETRY_DELAYS = reconcile.RETRY_DELAYS
_sleep = time.sleep


def resolve_backend(arch=ARCH_DEFAULT):
    tracker = reconcile.read_tracker(arch) or reconcile.resolve_backend(arch)
    if tracker in ("github", "local"):
        return tracker
    raise RuntimeError(f"[ERROR] Could not resolve tracker backend from {arch}")


def gh_run(args):
    """Execute gh command with 3 retries and backoff per [[A-005]]. Returns (rc, stdout, stderr)."""
    last_rc, last_out, last_err = 0, "", ""
    for attempt in range(len(RETRY_DELAYS) + 1):
        if attempt > 0:
            _sleep(RETRY_DELAYS[attempt - 1])
        rc, out, err = reconcile._gh_run(args)
        if rc == 0:
            return rc, out, err
        last_rc, last_out, last_err = rc, out, err
    return last_rc, last_out, last_err


def gh_run_check(args, out=print):
    rc, stdout, stderr = gh_run(args)
    if rc != 0:
        if stderr:
            sys.stderr.write(stderr if stderr.endswith("\n") else stderr + "\n")
        elif stdout:
            out(stdout.strip())
        return rc
    if stdout:
        out(stdout.strip())
    return 0


def to_gh_num(ident):
    val = str(ident).strip().lstrip("#")
    if val.startswith("BT-"):
        m = re.match(r"^BT-0*(\d+)$", val)
        if m:
            return m.group(1)
    return str(int(val)) if val.isdigit() else val


def gh_node_id(ident):
    rc, out, _ = gh_run(["issue", "view", to_gh_num(ident), "--json", "id", "-q", ".id"])
    return out.strip() if rc == 0 else None


def gh_sub_issue(mutation, pid, cid, out=print):
    q = f"mutation($p:ID!,$c:ID!){{{mutation}(input:{{issueId:$p,subIssueId:$c}}){{issue{{number}}}}}}"
    return gh_run_check(["api", "graphql", "-f", f"query={q}", "-f", f"p={pid}", "-f", f"c={cid}"], out=out)


def gh_blocked_by(mutation, iid, bid, out=print):
    q = f"mutation($i:ID!,$b:ID!){{{mutation}(input:{{issueId:$i,blockingIssueId:$b}}){{issue{{number}}}}}}"
    return gh_run_check(["api", "graphql", "-f", f"query={q}", "-f", f"i={iid}", "-f", f"b={bid}"], out=out)


def gh_set_status(ident, new_status, out=print):
    num = to_gh_num(ident)
    rc, view_out, err = gh_run(["issue", "view", num, "--json", "labels"])
    if rc != 0:
        if err:
            sys.stderr.write(err if err.endswith("\n") else err + "\n")
        return rc
    try:
        existing = [l["name"] for l in json.loads(view_out).get("labels", [])]
    except Exception:
        existing = []
    edit_args = ["issue", "edit", num]
    for l in existing:
        if l.startswith("status:"):
            edit_args.extend(["--remove-label", l])
    edit_args.extend(["--add-label", f"status:{new_status}"])
    return gh_run_check(edit_args, out=out)


def _write_temp(content):
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as tf:
        tf.write(content)
        return tf.name


def update_refs_body(body, refs):
    lines = (body or "").splitlines()
    if any(l.startswith("Refs:") for l in lines):
        return "\n".join(f"Refs: {refs}" if l.startswith("Refs:") else l for l in lines)
    sep = [] if lines and lines[-1] == "" else [""]
    return "\n".join(lines + sep + [f"Refs: {refs}"])


def cmd_create(a, backend, out=print):
    if backend == "github":
        cmd = ["issue", "create", "--title", a.title]
        all_labels = [x.strip() for l in (a.label or []) for x in l.split(",") if x.strip()]
        if a.status:
            all_labels.append(f"status:{a.status}")
        if all_labels:
            cmd.extend(["--label", ",".join(all_labels)])
        if a.milestone:
            cmd.extend(["--milestone", a.milestone])
        if a.body_file:
            cmd.extend(["--body-file", a.body_file])
        elif a.body is not None:
            cmd.extend(["--body", a.body])
        rc, stdout, stderr = gh_run(cmd)
        if rc != 0:
            if stderr:
                sys.stderr.write(stderr if stderr.endswith("\n") else stderr + "\n")
            return rc
        if stdout:
            out(stdout.strip())
        m = re.search(r"/issues/(\d+)", stdout.strip())
        if m:
            num = m.group(1)
            if a.parent:
                cmd_set_parent(argparse.Namespace(id=num, parent=a.parent, arch=a.arch), backend, out=lambda x: None)
            if a.blocked_by:
                for b in a.blocked_by.split(","):
                    if b.strip():
                        cmd_blocker(argparse.Namespace(id=num, blocker=b.strip(), arch=a.arch), backend, clear=False, out=lambda x: None)
        return 0
    cmd = ["create", "--title", a.title]
    for l in a.label or []:
        cmd.extend(["--label", l])
    for k in ("status", "milestone", "parent", "blocked_by"):
        v = getattr(a, k, None)
        if v:
            cmd.extend([f"--{k.replace('_', '-')}", v])
    if a.body_file:
        cmd.extend(["--body-file", a.body_file])
    elif a.body is not None:
        tfn = _write_temp(a.body)
        try:
            return issues.main(cmd + ["--body-file", tfn], out=out)
        finally:
            Path(tfn).unlink(missing_ok=True)
    return issues.main(cmd, out=out)


def cmd_set_status(a, backend, out=print):
    return gh_set_status(a.id, a.status, out=out) if backend == "github" else issues.main(["set", a.id, "--status", a.status], out=out)


def cmd_set_labels(a, backend, out=print):
    if backend == "github":
        args = ["issue", "edit", to_gh_num(a.id)]
        for flag, items in (("--add-label", a.add_label), ("--remove-label", a.remove_label)):
            for l in items or []:
                for item in l.split(","):
                    if item.strip():
                        args.extend([flag, item.strip()])
        return gh_run_check(args, out=out)
    cmd = ["set", a.id]
    for l in a.add_label or []:
        cmd.extend(["--add-label", l])
    for l in a.remove_label or []:
        cmd.extend(["--remove-label", l])
    return issues.main(cmd, out=out)


def cmd_ensure_label(a, backend, out=print):
    if backend == "github":
        cmd = ["label", "create", a.name] + (["--description", a.description] if a.description else []) + (["--color", a.color] if a.color else [])
        return gh_run_check(cmd, out=out)
    return issues.main(["label", a.name], out=out)


def cmd_set_milestone(a, backend, out=print):
    if backend == "github":
        num = to_gh_num(a.id)
        flag = ["--remove-milestone"] if (not a.milestone or a.milestone in NONE_TOKENS) else ["--milestone", a.milestone]
        return gh_run_check(["issue", "edit", num] + flag, out=out)
    return issues.main(["set", a.id, "--milestone", a.milestone], out=out)


def cmd_set_parent(a, backend, out=print):
    if backend == "github":
        cid = gh_node_id(a.id)
        if not cid:
            return 1
        if a.parent and a.parent not in NONE_TOKENS:
            pid = gh_node_id(a.parent)
            return gh_sub_issue("addSubIssue", pid, cid, out=out) if pid else 1
        rc, vout, _ = gh_run(["issue", "view", to_gh_num(a.id), "--json", "parent"])
        p_num = json.loads(vout).get("parent", {}).get("number") if rc == 0 else None
        return gh_sub_issue("removeSubIssue", gh_node_id(p_num), cid, out=out) if p_num else 0
    return issues.main(["set", a.id, "--parent", a.parent or "—"], out=out)


def cmd_blocker(a, backend, clear=False, out=print):
    if backend == "github":
        iid, bid = gh_node_id(a.id), gh_node_id(a.blocker)
        if not iid or not bid:
            return 1
        return gh_blocked_by("removeBlockedBy" if clear else "addBlockedBy", iid, bid, out=out)
    return issues.main(["set", a.id, "--remove-blocker" if clear else "--add-blocker", a.blocker], out=out)


def cmd_close(a, backend, out=print):
    if backend == "github":
        return gh_run_check(["issue", "close", to_gh_num(a.id), "--reason", a.reason or "completed"], out=out)
    return issues.main(["close", a.id, "--reason", a.reason or "completed"], out=out)


def cmd_reopen(a, backend, out=print):
    if backend == "github":
        rc = gh_run_check(["issue", "reopen", to_gh_num(a.id)], out=out)
        return gh_set_status(a.id, a.status, out=out) if (rc == 0 and a.status) else rc
    return issues.main(["reopen", a.id] + (["--status", a.status] if a.status else []), out=out)


def cmd_comment(a, backend, out=print):
    flag = ["--body-file", a.body_file] if a.body_file else ["--body", a.body or ""]
    return gh_run_check(["issue", "comment", to_gh_num(a.id)] + flag, out=out) if backend == "github" else issues.main(["comment", a.id] + flag, out=out)


def cmd_set_refs(a, backend, out=print):
    if backend == "github":
        num = to_gh_num(a.id)
        rc, vout, err = gh_run(["issue", "view", num, "--json", "body", "-q", ".body"])
        if rc != 0:
            if err:
                sys.stderr.write(err if err.endswith("\n") else err + "\n")
            return rc
        return gh_run_check(["issue", "edit", num, "--body", update_refs_body(vout, a.refs)], out=out)
    issue = issues.Tracker(a.arch).store().get(a.id)
    return cmd_set_body(argparse.Namespace(id=a.id, body=update_refs_body(issue.get("body", ""), a.refs), body_file=None, arch=a.arch), backend, out=out)


def cmd_set_body(a, backend, out=print):
    if backend == "github":
        args = ["issue", "edit", to_gh_num(a.id)] + (["--body-file", a.body_file] if a.body_file else ["--body", a.body or ""])
        return gh_run_check(args, out=out)
    if a.body_file:
        return issues.main(["set", a.id, "--body-file", a.body_file], out=out)
    tfn = _write_temp(a.body or "")
    try:
        return issues.main(["set", a.id, "--body-file", tfn], out=out)
    finally:
        Path(tfn).unlink(missing_ok=True)


def cmd_claim(a, backend, out=print):
    if backend == "github":
        return gh_run_check(["issue", "edit", to_gh_num(a.id), "--add-assignee", "@me"], out=out)
    return issues.main(["claim", a.id] + (["--by", a.by] if a.by else []), out=out)


def cmd_get(a, backend, out=print):
    return gh_run_check(["issue", "view", to_gh_num(a.id), "--json", "number,state,labels,milestone,parent,blockedBy,body"], out=out) if backend == "github" else issues.main(["get", a.id], out=out)


def cmd_list(a, backend, out=print):
    if backend == "github":
        cmd = ["issue", "list", "--json", "number,title,labels,milestone"]
        if getattr(a, "state", None):
            cmd.extend(["--state", a.state])
        for l in getattr(a, "label", None) or []:
            cmd.extend(["--label", l])
        return gh_run_check(cmd, out=out)
    cmd = ["list"]
    for k in ("status", "milestone", "parent"):
        v = getattr(a, k, None)
        if v:
            cmd.extend([f"--{k}", v])
    for l in getattr(a, "label", None) or []:
        cmd.extend(["--label", l])
    if getattr(a, "all", False):
        cmd.append("--all")
    return issues.main(cmd, out=out)


def cmd_wip(a, backend, out=print):
    return gh_run_check(["issue", "list", "--state", "open", "--label", "status:in progress", "--json", "number,title,labels"], out=out) if backend == "github" else issues.main(["wip"], out=out)


def cmd_resume_note(a, backend, out=print):
    if backend == "github":
        jq = '[.comments[] | select(.body | startswith("<!-- stratos:resume -->"))] | last | .body'
        return gh_run_check(["issue", "view", to_gh_num(a.id), "--json", "comments", "--jq", jq], out=out)
    note = issues.at_top(".memory/resume") / f"{a.id}.md"
    if note.is_file():
        out(note.read_text(encoding="utf-8").strip())
    return 0


def cmd_children(a, backend, out=print):
    return gh_run_check(["issue", "view", to_gh_num(a.id), "--json", "subIssues"], out=out) if backend == "github" else issues.main(["children", a.id], out=out)


def cmd_blockers(a, backend, out=print):
    return gh_run_check(["issue", "view", to_gh_num(a.id), "--json", "blockedBy"], out=out) if backend == "github" else issues.main(["blockers", a.id], out=out)


VERB_DISPATCH = {
    "create": cmd_create, "set-status": cmd_set_status, "set-labels": cmd_set_labels,
    "ensure-label": cmd_ensure_label, "set-milestone": cmd_set_milestone,
    "ensure-milestone": lambda a, b, out=print: gh_run_check(["api", "repos/{owner}/{repo}/milestones", "-f", f"title={a.title}"], out=out) if b == "github" else 0,
    "close-milestone": lambda a, b, out=print: gh_run_check(["api", "-X", "PATCH", f"repos/{{owner}}/{{repo}}/milestones/{a.name}", "-f", "state=closed"], out=out) if b == "github" else 0,
    "set-parent": cmd_set_parent, "add-blocker": lambda a, b, out=print: cmd_blocker(a, b, clear=False, out=out),
    "clear-blocker": lambda a, b, out=print: cmd_blocker(a, b, clear=True, out=out),
    "close": cmd_close, "reopen": cmd_reopen, "comment": cmd_comment, "set-refs": cmd_set_refs,
    "set-body": cmd_set_body, "claim": cmd_claim, "get": cmd_get, "list": cmd_list,
    "wip": cmd_wip, "resume-note": cmd_resume_note, "candidates": lambda a, b, out=print: __import__("ice_read").main(["candidates", "--arch", a.arch]),
    "children": cmd_children, "blockers": cmd_blockers,
}


def build_parser():
    p = argparse.ArgumentParser(description="Unified Python CLI Façade for tracker operations.")
    p.add_argument("--arch", default=ARCH_DEFAULT, help="ARCHITECTURE.md path")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("create")
    sp.add_argument("--title", required=True); sp.add_argument("--label", action="append")
    sp.add_argument("--status"); sp.add_argument("--milestone"); sp.add_argument("--parent"); sp.add_argument("--blocked-by")
    g = sp.add_mutually_exclusive_group(); g.add_argument("--body"); g.add_argument("--body-file")

    sp = sub.add_parser("set-status"); sp.add_argument("id"); sp.add_argument("status")
    sp = sub.add_parser("set-labels"); sp.add_argument("id"); sp.add_argument("--add-label", action="append"); sp.add_argument("--remove-label", action="append")
    sp = sub.add_parser("ensure-label"); sp.add_argument("name"); sp.add_argument("--description"); sp.add_argument("--color")
    sp = sub.add_parser("set-milestone"); sp.add_argument("id"); sp.add_argument("milestone")
    sub.add_parser("ensure-milestone").add_argument("title")
    sub.add_parser("close-milestone").add_argument("name")
    sp = sub.add_parser("set-parent"); sp.add_argument("id"); sp.add_argument("parent")
    for name in ("add-blocker", "clear-blocker"):
        sp = sub.add_parser(name); sp.add_argument("id"); sp.add_argument("blocker")

    sp = sub.add_parser("close"); sp.add_argument("id"); sp.add_argument("--reason", default="completed")
    sp = sub.add_parser("reopen"); sp.add_argument("id"); sp.add_argument("--status")
    sp = sub.add_parser("comment"); sp.add_argument("id")
    g = sp.add_mutually_exclusive_group(required=True); g.add_argument("--body"); g.add_argument("--body-file")

    sp = sub.add_parser("set-refs"); sp.add_argument("id"); sp.add_argument("refs")
    sp = sub.add_parser("set-body"); sp.add_argument("id")
    g = sp.add_mutually_exclusive_group(required=True); g.add_argument("--body"); g.add_argument("--body-file")

    sp = sub.add_parser("claim"); sp.add_argument("id"); sp.add_argument("--by")
    for name in ("get", "children", "blockers", "resume-note"):
        sub.add_parser(name).add_argument("id")

    sp = sub.add_parser("list")
    sp.add_argument("--status"); sp.add_argument("--label", action="append"); sp.add_argument("--milestone")
    sp.add_argument("--parent"); sp.add_argument("--state"); sp.add_argument("--all", action="store_true")

    sub.add_parser("wip"); sub.add_parser("candidates")
    return p


def main(argv=None, out=print):
    raw_args = list(sys.argv[1:] if argv is None else argv)
    for i, a in enumerate(raw_args):
        if not a.startswith("-"):
            c = a.replace("_", "-")
            raw_args[i] = "clear-blocker" if c in ("remove-blocker",) else c
            break
    p = build_parser()
    a = p.parse_args(raw_args)
    try:
        backend = resolve_backend(a.arch)
    except Exception as e:
        sys.stderr.write(str(e) + "\n")
        return 1
    handler = VERB_DISPATCH.get(a.cmd)
    return handler(a, backend, out=out) if handler else 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
