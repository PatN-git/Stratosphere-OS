"""Dispatch bounded slices to Jules — single or sequential batch.

Batch is a SEQUENTIAL loop (single-writer ledger, no write race); each created
session still runs in parallel on Jules's side. State lives only in the ledger
`.memory/jules-ledger.jsonl` (no invented GitHub labels). Idempotent.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

from jules_api import JulesError

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
        "session_id": session.get("id") or session.get("name"),
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
