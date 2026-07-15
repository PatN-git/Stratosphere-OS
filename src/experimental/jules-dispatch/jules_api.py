"""Jules API adapter (v1alpha) — the single HTTP module for the jules-dispatch pack.

One seam only: an injectable `caller(method, path, body, query)` so tests run fully
offline (see tests/test_jules.py ReplayCaller). No vendor-abstraction layer.

Contract pinned in CONTRACT.md (alpha — confirm on first live run). The created PR
URL lives at session.outputs[].pullRequest.url.
"""
import json
import urllib.error
import urllib.request
from urllib.parse import urlencode

BASE = "https://jules.googleapis.com/v1alpha"


class JulesError(Exception):
    """Any Jules API failure. `retry_after` is set for 429s when the server sends it."""
    def __init__(self, status, message, retry_after=None):
        super().__init__(f"[{status}] {message}")
        self.status = status
        self.message = message
        self.retry_after = retry_after


def _default_caller(api_key):
    """Real HTTP caller. Reads the key into the X-Goog-Api-Key header."""
    def call(method, path, body=None, query=None):
        url = BASE + path
        if query:
            url += "?" + urlencode(query)
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("X-Goog-Api-Key", api_key)
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            retry_after = e.headers.get("Retry-After") if e.headers else None
            raise JulesError(e.code, f"{method} {path}: {e.reason}", retry_after=retry_after)
        except urllib.error.URLError as e:
            raise JulesError(0, f"{method} {path}: {e.reason}")
    return call


class JulesClient:
    def __init__(self, api_key=None, caller=None):
        if caller is None:
            if not api_key:
                raise JulesError(0, "JulesClient needs either api_key or an injected caller")
            caller = _default_caller(api_key)
        self._call = caller

    def list_sources(self):
        return self._call("GET", "/sources").get("sources", [])

    def create_session(self, source, prompt, *, title=None, auto_pr=True,
                       require_plan_approval=True, starting_branch=None):
        ctx = {"source": source}
        if starting_branch:
            ctx["githubRepoContext"] = {"startingBranch": starting_branch}
        body = {
            "prompt": prompt,
            "sourceContext": ctx,
            "requirePlanApproval": bool(require_plan_approval),
            "automationMode": "AUTO_CREATE_PR" if auto_pr else "AUTOMATION_MODE_UNSPECIFIED",
        }
        if title:
            body["title"] = title
        return self._call("POST", "/sessions", body=body)

    def get_session(self, session_id):
        return self._call("GET", f"/sessions/{session_id}")

    def list_activities(self, session_id, since=None):
        query = {"pageSize": 30}
        if since:
            query["createTime"] = since  # poll marker per docs
        return self._call("GET", f"/sessions/{session_id}/activities", query=query).get("activities", [])

    def find_pr_url(self, session_id):
        """Return the created PR URL (session.outputs[].pullRequest.url) or None."""
        session = self.get_session(session_id)
        for out in (session.get("outputs") or []):
            pr = (out or {}).get("pullRequest") or {}
            if pr.get("url"):
                return pr["url"]
        return None
