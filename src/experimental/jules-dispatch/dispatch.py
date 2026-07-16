"""Dispatch bounded slices to Jules — single or sequential batch.

Batch is a SEQUENTIAL loop (single-writer ledger, no write race); each created
session still runs in parallel on Jules's side. State lives only in the ledger
`.memory/jules-ledger.jsonl` (no invented GitHub labels). Idempotent.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

from jules_api import JulesError, session_id_of

LEDGER_REL = Path(".memory") / "jules-ledger.jsonl"


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_ledger(path):
    p = Path(path)
    if not p.exists():
        return []
    rows = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _append(path, row):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def build_prompt(issue):
    """Prompt = issue title + body (which carries the acceptance criteria). Nothing
    else — conventions come from the repo's AGENTS.md, env from Jules's UI snapshot."""
    title = (issue.get("title") or "").strip()
    body = (issue.get("body") or "").strip()
    return f"{title}\n\n{body}".strip()


def dispatch_one(client, source, slice_id, issue, ledger_path, *, starting_branch=None, now=None):
    """Create one Jules session; append a DISPATCHED ledger row. No-op if the slice is
    already DISPATCHED/DONE (idempotent)."""
    for r in load_ledger(ledger_path):
        if r.get("slice_id") == slice_id and r.get("state") in ("DISPATCHED", "DONE"):
            return {"slice_id": slice_id, "state": r["state"], "noop": True, "session_id": r.get("session_id")}
    session = client.create_session(
        source, build_prompt(issue), title=str(slice_id),
        auto_pr=True, require_plan_approval=True, starting_branch=starting_branch,
    )
    row = {
        "slice_id": slice_id,
        "session_id": session_id_of(session),
        "source": source,
        "title": str(slice_id),
        "created_at": now or _now(),
        "state": "DISPATCHED",
    }
    _append(ledger_path, row)
    return row


def dispatch_many(client, source, items, ledger_path, *, max_sessions=3, starting_branch=None, now=None):
    """items: list of (slice_id, issue), already eligibility/dep-filtered. Sequential;
    a single failure -> FAILED row, others continue; respects max_sessions."""
    results, dispatched = [], 0
    for slice_id, issue in items:
        if dispatched >= max_sessions:
            results.append({"slice_id": slice_id, "state": "SKIPPED_CAP"})
            continue
        try:
            row = dispatch_one(client, source, slice_id, issue, ledger_path,
                               starting_branch=starting_branch, now=now)
            results.append(row)
            if not row.get("noop"):
                dispatched += 1
        except JulesError as e:
            frow = {"slice_id": slice_id, "state": "FAILED", "reason": str(e), "created_at": now or _now()}
            _append(ledger_path, frow)
            results.append(frow)
    return results


def select_eligible(slices):
    """Filter a candidate slice list (e.g. a sprint) to dispatchable ones:
    require mode:AFK + tier:slice, drop tier:epic, drop any with an unmet blocked_by."""
    done = {s["slice_id"] for s in slices if s.get("state") == "done"}
    out = []
    for s in slices:
        if s.get("state") == "done":
            continue  # already complete — don't re-dispatch
        labels = set(s.get("labels", []))
        if "mode:AFK" not in labels or "tier:slice" not in labels or "tier:epic" in labels:
            continue
        if any(b not in done for b in s.get("blocked_by", [])):
            continue
        out.append(s)
    return out


def _sprint_candidates(repo=None):
    """mode:AFK issues via gh, shaped for select_eligible. Fetches BOTH states so the
    `done` set (closed issues) is populated for dependency gating; carries the full
    issue under `_issue` so preflight reuses it (no N+1 re-fetch). `Blocked-by:` body
    tokens must be issue numbers to match slice_id (documented in SKILL.md)."""
    import subprocess
    args = ["gh", "issue", "list", "--label", "mode:AFK", "--state", "all",
            "--json", "number,title,body,labels,state", "--limit", "200"]
    if repo:
        args += ["--repo", repo]
    out = subprocess.run(args, capture_output=True, text=True)
    if out.returncode != 0:
        raise JulesError(0, f"gh issue list failed: {out.stderr.strip()}")
    slices = []
    for iss in json.loads(out.stdout or "[]"):
        blocked = []
        for line in (iss.get("body") or "").splitlines():
            low = line.lower()
            if low.startswith("blocked-by:") or low.startswith("blocked by:"):
                blocked = [b.strip().lstrip("#") for b in line.split(":", 1)[1].split(",") if b.strip()]
        closed = str(iss.get("state", "")).upper() in ("CLOSED", "DONE")
        slices.append({"slice_id": str(iss["number"]),
                       "labels": [lbl.get("name") for lbl in iss.get("labels", [])],
                       "blocked_by": blocked,
                       "state": "done" if closed else "open",
                       "_issue": iss})
    return slices


def main(argv=None, *, client=None, issue_fetcher=None, sprint_lister=None):
    """CLI. `client`/`issue_fetcher`/`sprint_lister` are injectable for offline tests;
    they default to the real Jules client, gh issue-view, and gh issue-list."""
    import argparse
    from preflight import preflight

    ap = argparse.ArgumentParser(description="Dispatch bounded mode:AFK slices to Google Jules (opt-in, experimental).")
    ap.add_argument("--slice", action="append", default=[], help="slice/issue id (repeatable)")
    ap.add_argument("--sprint", action="store_true", help="dispatch all eligible open mode:AFK+tier:slice issues")
    ap.add_argument("--source", required=True, help="Jules source name (list via jules_api.list_sources)")
    ap.add_argument("--repo", help="owner/name for gh (default: current repo)")
    ap.add_argument("--max-sessions", type=int, default=3)
    ap.add_argument("--starting-branch", default="main")
    ap.add_argument("--ledger", default=str(LEDGER_REL))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    sprint_lister = sprint_lister or _sprint_candidates
    items = []
    if args.sprint:
        for cand in select_eligible(sprint_lister(args.repo)):
            iss = cand.get("_issue")
            fetch = (lambda _s, _i=iss: _i) if iss is not None else issue_fetcher
            pf = preflight(cand["slice_id"], fetcher=fetch, repo=args.repo)
            if not pf.ok:
                print(f"[{cand['slice_id']}] SKIP: {pf.reason}")
                continue
            items.append((cand["slice_id"], pf.issue))
    else:
        for sid in args.slice:
            pf = preflight(sid, fetcher=issue_fetcher, repo=args.repo)
            if not pf.ok:
                print(f"[{sid}] SKIP: {pf.reason}")
                continue
            items.append((sid, pf.issue))

    if not items:
        print("Nothing to dispatch.")
        return 0
    if args.dry_run:
        for sid, _ in items:
            print(f"[dry-run] would dispatch {sid}")
        return 0

    if client is None:
        from config import load_api_key
        from jules_api import JulesClient
        client = JulesClient(api_key=load_api_key())
    for r in dispatch_many(client, args.source, items, args.ledger,
                           max_sessions=args.max_sessions, starting_branch=args.starting_branch):
        extra = f" session={r['session_id']}" if r.get("session_id") else ""
        print(f"[{r.get('slice_id')}] {r.get('state')}{extra}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
