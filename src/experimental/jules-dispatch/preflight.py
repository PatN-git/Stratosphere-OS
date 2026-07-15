"""Preflight eligibility for a slice before Jules dispatch.

Eligible = the issue exists, carries `mode:AFK`, is not `tier:epic`, and states
acceptance criteria. Reuses canonical StratOS labels; invents none.
"""
import json
import subprocess

from jules_api import JulesError


def _default_issue_fetcher(slice_id, repo=None):
    args = ["gh", "issue", "view", str(slice_id), "--json", "number,title,body,labels,state"]
    if repo:
        args += ["--repo", repo]
    out = subprocess.run(args, capture_output=True, text=True)
    if out.returncode != 0:
        raise JulesError(0, f"gh issue view {slice_id} failed: {out.stderr.strip()}")
    return json.loads(out.stdout)


class PreflightResult:
    def __init__(self, ok, reason, issue=None):
        self.ok = ok
        self.reason = reason
        self.issue = issue

    def __repr__(self):
        return f"PreflightResult(ok={self.ok}, reason={self.reason!r})"


def preflight(slice_id, fetcher=None, repo=None):
    fetch = fetcher or (lambda sid: _default_issue_fetcher(sid, repo))
    try:
        issue = fetch(slice_id)
    except JulesError as e:
        return PreflightResult(False, str(e))
    labels = {lbl.get("name") for lbl in issue.get("labels", [])}
    if "tier:epic" in labels:
        return PreflightResult(False, f"{slice_id} is tier:epic — dispatch implementable slices, not epics", issue)
    if "mode:AFK" not in labels:
        return PreflightResult(False, f"{slice_id} lacks mode:AFK — not eligible for Jules dispatch", issue)
    body = (issue.get("body") or "").lower()
    if not any(marker in body for marker in ("acceptance criteria", "## acceptance", "acceptance:")):
        return PreflightResult(False, f"{slice_id} has no acceptance criteria — too underspecified to offload", issue)
    return PreflightResult(True, "ok", issue)
