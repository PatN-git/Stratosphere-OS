"""`--status`: deterministic, human-invoked poll of dispatched Jules sessions.

Reports PR readiness and hands off — it NEVER merges, never enables auto-merge, and
never invokes another workflow (`4a`/`3z`/`3d`). Verification is the human's job:
`gh pr checkout <pr>` in a real clone, then `/4a_verify-and-ship`, then merge.
"""
import json
import subprocess
from pathlib import Path

from dispatch import LEDGER_REL, load_ledger
from jules_api import JulesError


def _rewrite(path, rows):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def _pr_url_from(session):
    for out in (session.get("outputs") or []):
        pr = (out or {}).get("pullRequest") or {}
        if pr.get("url"):
            return pr["url"]
    return None


def _default_ci_status(pr_url):
    """Read-only CI status via gh. Never merges."""
    out = subprocess.run(
        ["gh", "pr", "view", pr_url, "--json", "state,statusCheckRollup"],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        return "unknown"
    try:
        data = json.loads(out.stdout)
    except Exception:
        return "unknown"
    checks = data.get("statusCheckRollup") or []
    if not checks:
        return f"{data.get('state', '?')} (no checks)"
    concl = [c.get("conclusion") or c.get("status") or "?" for c in checks]
    return f"{data.get('state', '?')} checks={concl}"


def status(client, ledger_path, *, ci_fetcher=None, printer=print):
    """Poll each DISPATCHED row; report PR readiness; flip to DONE/FAILED. Returns rows."""
    ci_fetcher = ci_fetcher or _default_ci_status
    rows = load_ledger(ledger_path)
    changed = False
    for r in rows:
        if r.get("state") != "DISPATCHED":
            continue  # DONE/FAILED already reconciled — idempotent skip
        sid = r.get("session_id")
        try:
            session = client.get_session(sid)
        except JulesError as e:
            r["state"], r["reason"] = "FAILED", str(e)
            changed = True
            printer(f"[{r['slice_id']}] session error: {e}")
            continue
        pr_url = _pr_url_from(session)
        if pr_url:
            ci = ci_fetcher(pr_url)
            printer(f"[{r['slice_id']}] PR ready: {pr_url}  (CI: {ci})")
            printer(f"    -> to verify: gh pr checkout {pr_url} in a real clone, run /4a_verify-and-ship, then merge yourself")
            r["state"], r["pr_url"] = "DONE", pr_url
            changed = True
        elif session.get("state") == "FAILED":
            r["state"], r["reason"] = "FAILED", "Jules session FAILED"
            changed = True
            printer(f"[{r['slice_id']}] Jules session FAILED")
        else:
            printer(f"[{r['slice_id']}] still running (state={session.get('state')})")
    if changed:
        _rewrite(ledger_path, rows)
    return rows


def main(argv=None):
    import argparse
    from config import load_api_key
    from jules_api import JulesClient

    ap = argparse.ArgumentParser(description="Poll dispatched Jules sessions; report PR readiness (deterministic, zero-LLM).")
    ap.add_argument("--ledger", default=str(LEDGER_REL))
    args = ap.parse_args(argv)

    status(JulesClient(api_key=load_api_key()), args.ledger)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
