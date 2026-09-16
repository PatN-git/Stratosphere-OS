#!/usr/bin/env python3
"""L3 Slice 2 - a `gh` that answers from a JSON store instead of GitHub.

A real repo per run costs API calls, needs a token with `delete_repo` scope, leaves
residue when a run is killed, and makes CI flaky on a GitHub outage. This makes the
default lane deterministic and free. It is not a substitute for reality - that is
what `--live-gh` is for (Slice 6).

Three rules shape everything here:

  * **`auth status` must succeed.** `reconcile.py:160` treats a failing `gh auth
    status` as "offline" and prints `[local-only - GitHub not checked]`, returning 0
    without ever emitting `[MIRROR-OK]`. A shim whose auth check fails therefore
    turns the terminal-sync gate into a no-op that still passes.
  * **The store is authoritative.** `3b` writes `BACKLOG_MAP.md` from what this
    returns, and `reconcile.py` then compares the two. If the shim invents state per
    call rather than keeping it, the mirror and the source diverge by construction.
  * **An unknown subcommand fails loudly**, with the full argv recorded. A shim that
    shrugs and exits 0 makes every downstream assertion meaningless, and the gap it
    hides is exactly the undocumented GitHub surface Slice 9 wants reported.

The surface implemented is what the TESTED CHAIN uses, found with
`grep -rhoE '\\bgh [a-z-]+( [a-z-]+)?' src/workflows/ src/references/ src/scripts/`:
`issue create|edit|view|list|comment|close`, `pr create|view|ready`, `api graphql`,
`api repos/.../milestones`, `auth status`, `version`, and `repo create|delete|list`.
`gh release view`, `gh project`, `gh label list`, `gh secret|variable set` and
`gh repo view` exist in the repo but only inside `stratosphere-setup` and
`stratosphere-update`, which L3 never drives - so they are deliberately absent and
will fail loudly if a phase reaches for one.

The store lives at `$L3_GH_STORE`. There is no default: a shim that quietly invents
a store in the current directory would split state across phases and pass anyway.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

VERSION = "gh version 0.0.0-l3-shim (l3-lifecycle-harness)"
REPO = "l3-harness/throwaway"

# E1. A real token in the environment means a call that escapes the shim reaches
# the real GitHub as the developer. Refuse rather than serve the call.
TOKEN_VARS = ("GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN")

EXIT_UNKNOWN = 1
EXIT_NO_STORE = 3
EXIT_REAL_TOKEN = 4


def store_path() -> Path:
    p = os.environ.get("L3_GH_STORE")
    if not p:
        raise Failure(EXIT_NO_STORE,
                      "L3_GH_STORE is not set, so there is no fixture store to "
                      "answer from. The harness sets it; a bare `gh` call outside "
                      "a run must not be served.")
    return Path(p)


class Failure(Exception):
    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code


def load() -> dict:
    path = store_path()
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"repo": REPO, "next_number": 1, "issues": {}, "milestones": [],
            "repos": [], "invocations": [], "unknown": []}


def save(state: dict) -> None:
    store_path().write_text(json.dumps(state, indent=2, sort_keys=True),
                            encoding="utf-8")


# --- argv handling -----------------------------------------------------------

def take(argv: list[str], *names: str) -> str | None:
    """Last value of a flag, `--flag v` or `--flag=v`. None when absent."""
    found = None
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in names and i + 1 < len(argv):
            found = argv[i + 1]
            i += 2
            continue
        for n in names:
            if a.startswith(n + "="):
                found = a[len(n) + 1:]
        i += 1
    return found


def take_all(argv: list[str], *names: str) -> list[str]:
    """Every value of a repeatable flag, splitting comma lists (`-l a,b`)."""
    out: list[str] = []
    i = 0
    while i < len(argv):
        a = argv[i]
        val = None
        if a in names and i + 1 < len(argv):
            val = argv[i + 1]
            i += 1
        else:
            for n in names:
                if a.startswith(n + "="):
                    val = a[len(n) + 1:]
        if val is not None:
            out += [v.strip() for v in val.split(",") if v.strip()]
        i += 1
    return out


def positional(argv: list[str]) -> list[str]:
    """Bare arguments, skipping flags and their values."""
    out, skip = [], False
    for i, a in enumerate(argv):
        if skip:
            skip = False
            continue
        if a.startswith("-"):
            skip = "=" not in a and i + 1 < len(argv) and not argv[i + 1].startswith("-")
            continue
        out.append(a)
    return out


_JQ = re.compile(r"^\.([A-Za-z_][A-Za-z0-9_]*)$")


def apply_jq(data, expr: str):
    """The only jq the chain uses is `-q .id`, from github-issue-relations.md:9.

    Anything else fails by name rather than returning something plausible: a
    silently wrong node id produces a mutation against the wrong issue.
    """
    m = _JQ.match(expr.strip())
    if not m:
        raise Failure(EXIT_UNKNOWN,
                      f"the shim implements only `-q .<field>`, not {expr!r}")
    if not isinstance(data, dict) or m.group(1) not in data:
        raise Failure(EXIT_UNKNOWN, f"no field {m.group(1)!r} to select")
    return data[m.group(1)]


# --- the issue store ---------------------------------------------------------

def node_id(number: int) -> str:
    return f"I_l3{number:06d}"


def by_node_id(state: dict, nid: str) -> dict | None:
    return next((i for i in state["issues"].values() if i["id"] == nid), None)


def mint(state: dict, *, title: str, body: str, labels: list[str],
         milestone: str | None, is_pr: bool = False, draft: bool = False) -> dict:
    """One monotonic counter for issues AND pull requests.

    GitHub shares numbering across the two, which is why `2a:32` and `3b:66` both
    forbid predicting the next number. Sharing it here keeps that hazard real
    instead of letting the shim hand out numbers the real thing never would.
    """
    number = state["next_number"]
    state["next_number"] = number + 1
    kind = "pull" if is_pr else "issues"
    issue = {
        "number": number,
        "id": node_id(number),
        "title": title or "",
        "body": body or "",
        "labels": [{"name": n} for n in labels],
        "milestone": {"title": milestone} if milestone else None,
        "state": "OPEN",
        "comments": [],
        "subIssues": [],
        "blockedBy": [],
        "parent": None,
        "assignees": [],
        "isPR": is_pr,
        "isDraft": draft,
        "mergeStateStatus": "CLEAN",
        "url": f"https://github.com/{state['repo']}/{kind}/{number}",
    }
    state["issues"][str(number)] = issue
    return issue


def get(state: dict, number: str) -> dict:
    issue = state["issues"].get(str(number).lstrip("#"))
    if issue is None:
        raise Failure(EXIT_UNKNOWN, f"no issue #{number} in the fixture store")
    return issue


def project(issue: dict, fields: list[str]) -> dict:
    """`--json a,b` returns exactly those fields, as real `gh` does.

    `reconcile.py:130-133` asks for `blockedBy` and `parent` in their own calls and
    skips a field the response omits, so returning extras would mask a field the
    real `gh` does not expose.
    """
    unknown = [f for f in fields if f not in issue]
    if unknown:
        raise Failure(EXIT_UNKNOWN,
                      f"unknown JSON field(s) for issue: {', '.join(unknown)}")
    return {f: issue[f] for f in fields}


def brief(issue: dict) -> dict:
    """The shape a nested reference takes: `subIssues`, `parent`, `blockedBy`."""
    return {"number": issue["number"], "title": issue["title"],
            "state": issue["state"]}


# --- subcommands -------------------------------------------------------------

def cmd_issue(state: dict, argv: list[str]) -> str:
    action, rest = argv[0], argv[1:]
    if action == "create":
        issue = mint(state,
                     title=take(rest, "--title", "-t") or "",
                     body=_body(rest),
                     labels=take_all(rest, "--label", "-l"),
                     milestone=take(rest, "--milestone", "-m"))
        issue["assignees"] = take_all(rest, "--assignee", "-a")
        return issue["url"]

    if action == "edit":
        issue = get(state, positional(rest)[0])
        remove = set(take_all(rest, "--remove-label"))
        add = take_all(rest, "--add-label")
        names = [l["name"] for l in issue["labels"] if l["name"] not in remove]
        names += [a for a in add if a not in names]
        issue["labels"] = [{"name": n} for n in names]
        ms = take(rest, "--milestone", "-m")
        if ms is not None:
            issue["milestone"] = {"title": ms} if ms else None
        body = _body(rest)
        if body:
            issue["body"] = body
        issue["assignees"] += take_all(rest, "--add-assignee")
        return issue["url"]

    if action == "view":
        issue = get(state, positional(rest)[0])
        fields = take(rest, "--json")
        jq = take(rest, "-q", "--jq")
        if not fields:
            return f"#{issue['number']}\t{issue['title']}\t{issue['state']}"
        data = project(issue, [f.strip() for f in fields.split(",") if f.strip()])
        if jq:
            return str(apply_jq(data, jq))
        return json.dumps(data)

    if action == "list":
        want_state = (take(rest, "--state") or "open").upper()
        labels = set(take_all(rest, "--label", "-l"))
        rows = [i for i in state["issues"].values() if not i["isPR"]]
        if want_state != "ALL":
            rows = [i for i in rows if i["state"] == want_state]
        if labels:
            rows = [i for i in rows
                    if labels <= {l["name"] for l in i["labels"]}]
        rows.sort(key=lambda i: i["number"])
        fields = take(rest, "--json")
        if not fields:
            return "\n".join(f"#{i['number']}\t{i['title']}\t{i['state']}"
                             for i in rows)
        names = [f.strip() for f in fields.split(",") if f.strip()]
        return json.dumps([project(i, names) for i in rows])

    if action == "comment":
        issue = get(state, positional(rest)[0])
        issue["comments"].append({"body": _body(rest) or ""})
        return f"{issue['url']}#issuecomment-{len(issue['comments'])}"

    if action == "close":
        issue = get(state, positional(rest)[0])
        issue["state"] = "CLOSED"
        return f"Closed issue #{issue['number']}"

    raise Failure(EXIT_UNKNOWN, f"unknown subcommand: gh issue {action}")


def _body(argv: list[str]) -> str:
    """`--body`, or `--body-file` read from disk. `-F` is body-file for issues."""
    path = take(argv, "--body-file", "-F")
    if path:
        if path == "-":
            return sys.stdin.read()
        return Path(path).read_text(encoding="utf-8")
    return take(argv, "--body", "-b") or ""


def cmd_pr(state: dict, argv: list[str]) -> str:
    action, rest = argv[0], argv[1:]
    if action == "create":
        pr = mint(state,
                  title=take(rest, "--title", "-t") or "",
                  body=_body(rest),
                  labels=take_all(rest, "--label", "-l"),
                  milestone=None,
                  is_pr=True,
                  draft="--draft" in rest or "-d" in rest)
        pr["base"] = take(rest, "--base", "-B") or "main"
        pr["head"] = take(rest, "--head", "-H") or ""
        return pr["url"]

    if action == "view":
        pr = get(state, positional(rest)[0])
        fields = take(rest, "--json")
        jq = take(rest, "-q", "--jq")
        if not fields:
            return f"#{pr['number']}\t{pr['title']}\t{pr['state']}"
        data = project(pr, [f.strip() for f in fields.split(",") if f.strip()])
        return str(apply_jq(data, jq)) if jq else json.dumps(data)

    if action == "ready":
        pr = get(state, positional(rest)[0])
        pr["isDraft"] = False
        return f"Pull request #{pr['number']} is marked as ready for review"

    raise Failure(EXIT_UNKNOWN, f"unknown subcommand: gh pr {action}")


_MUTATION = re.compile(r"\b(addSubIssue|addBlockedBy|removeBlockedBy)\b")


def cmd_api(state: dict, argv: list[str]) -> str:
    if argv[0] == "graphql":
        return _graphql(state, argv[1:])
    path = argv[0]
    if re.match(r"^repos/[^/]+/[^/]+/milestones/?$", path):
        return json.dumps(state["milestones"])
    raise Failure(EXIT_UNKNOWN, f"unknown REST path: gh api {path}")


def _fields(argv: list[str]) -> dict:
    out = {}
    i = 0
    while i < len(argv):
        if argv[i] in ("-f", "-F", "--field", "--raw-field") and i + 1 < len(argv):
            k, _, v = argv[i + 1].partition("=")
            out[k] = v
            i += 2
            continue
        i += 1
    return out


def _graphql(state: dict, argv: list[str]) -> str:
    """The three mutations `3b` and `4a` use, per github-issue-relations.md.

    Node ids arrive already resolved, because the documented form nests
    `gh issue view <n> --json id -q .id` inside the call - so an unresolvable id
    here means the shim handed out one it cannot recognise, which is a bug worth
    failing on rather than a relation worth silently dropping.
    """
    args = _fields(argv)
    query = args.get("query", "")
    m = _MUTATION.search(query)
    if not m:
        raise Failure(EXIT_UNKNOWN,
                      f"the shim implements addSubIssue/addBlockedBy/"
                      f"removeBlockedBy, not: {query[:200]!r}")
    name = m.group(1)

    def resolve(key: str) -> dict:
        nid = args.get(key)
        issue = by_node_id(state, nid) if nid else None
        if issue is None:
            raise Failure(EXIT_UNKNOWN,
                          f"{name}: no issue with node id {nid!r} in the store")
        return issue

    if name == "addSubIssue":
        parent, child = resolve("p"), resolve("c")
        if not any(s["number"] == child["number"] for s in parent["subIssues"]):
            parent["subIssues"].append(brief(child))
        child["parent"] = brief(parent)
        subject = parent
    else:
        issue, blocker = resolve("i"), resolve("b")
        blocked = [b for b in issue["blockedBy"] if b["number"] != blocker["number"]]
        if name == "addBlockedBy":
            blocked.append(brief(blocker))
        issue["blockedBy"] = blocked
        subject = issue

    return json.dumps({"data": {name: {"issue": {"number": subject["number"]}}}})


def cmd_repo(state: dict, argv: list[str]) -> str:
    """Enough for Slice 6's shape to be exercised without a real repo."""
    action, rest = argv[0], argv[1:]
    if action == "create":
        name = positional(rest)[0] if positional(rest) else state["repo"]
        state["repos"].append(name)
        return f"https://github.com/{name}"
    if action == "delete":
        name = positional(rest)[0] if positional(rest) else state["repo"]
        state["repos"] = [r for r in state["repos"] if r != name]
        return f"Deleted repository {name}"
    if action == "list":
        return "\n".join(state["repos"])
    raise Failure(EXIT_UNKNOWN, f"unknown subcommand: gh repo {action}")


def dispatch(state: dict, argv: list[str]) -> tuple[str, str]:
    """Return (stdout, stderr) for one invocation."""
    if argv[0] in ("version", "--version"):
        return VERSION, ""
    if argv[0] == "auth":
        if argv[1:2] == ["status"]:
            # Real `gh` writes this to stderr and exits 0. reconcile.py:139 keys
            # only off the exit code, and a non-zero one there silently downgrades
            # the terminal-sync gate to [local-only].
            return "", (f"github.com\n  x Logged in to github.com as l3-harness "
                        f"(L3 shim)\n  - Active account: true\n")
        raise Failure(EXIT_UNKNOWN, f"unknown subcommand: gh auth {argv[1:]}")
    table = {"issue": cmd_issue, "pr": cmd_pr, "api": cmd_api, "repo": cmd_repo}
    handler = table.get(argv[0])
    if handler is None or len(argv) < 2:
        raise Failure(EXIT_UNKNOWN, f"unknown command: gh {' '.join(argv)}")
    return handler(state, argv[1:]), ""


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    live = [v for v in TOKEN_VARS if os.environ.get(v)]
    if live:
        print(f"[l3-shim] refusing to run: a real GitHub token is visible in the "
              f"environment ({', '.join(live)}). The shimmed lane must not be able "
              f"to reach GitHub at all (E1).", file=sys.stderr)
        return EXIT_REAL_TOKEN

    if not argv:
        print(VERSION)
        return 0

    try:
        state = load()
    except Failure as exc:
        print(f"[l3-shim] {exc}", file=sys.stderr)
        return exc.code

    state["invocations"].append(argv)
    try:
        out, err = dispatch(state, argv)
    except Failure as exc:
        state["unknown"].append(argv)
        save(state)
        print(f"[l3-shim] {exc}\n[l3-shim] full argv: {argv}", file=sys.stderr)
        return exc.code
    except Exception as exc:                       # never a silent success
        state["unknown"].append(argv)
        save(state)
        print(f"[l3-shim] {type(exc).__name__}: {exc}\n"
              f"[l3-shim] full argv: {argv}", file=sys.stderr)
        return EXIT_UNKNOWN

    save(state)
    if out:
        print(out)
    if err:
        print(err, file=sys.stderr, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
