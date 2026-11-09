"""Behaviour of .github/workflows/sync-labels-to-project.yml (label -> Projects board).

Runs the workflow's real `script:` body under node against a stubbed GitHub API and
records which Status option it writes. Key contract (docs/status-label-contract.md):
an issue closed as completed is `done` on EVERY event, not only the `closed` one -
otherwise a later label edit on a closed issue that still carries `status:planned`
resets its card (seen on #109).
"""
import json
import os
import re
import shutil
import subprocess
import textwrap

import pytest

from conftest import REPO_ROOT

WORKFLOW = REPO_ROOT / "src" / "github" / "sync-labels-to-project.yml"
NODE = shutil.which("node")
pytestmark = pytest.mark.skipif(not NODE, reason="node not available")

OPTIONS = {"planned": "o-planned", "needs_spec": "o-spec", "in progress": "o-prog",
           "in review": "o-rev", "blocked": "o-blk", "done": "o-done"}

RUNNER = r"""
const [script, scenario] = [process.env.SCRIPT, JSON.parse(process.env.SCENARIO)];
const updates = [];
const options = Object.entries(JSON.parse(process.env.OPTIONS)).map(([name, id]) => ({name, id}));
const liveNodeEnv = process.env.LIVE_NODE;
const liveNode = liveNodeEnv === 'null' ? null : (liveNodeEnv ? JSON.parse(liveNodeEnv) : {
  state: scenario.issue.state ? scenario.issue.state.toUpperCase() : 'OPEN',
  stateReason: scenario.issue.state_reason ? scenario.issue.state_reason.toUpperCase() : null,
  labels: { nodes: scenario.issue.labels || [] }
});
const github = { graphql: async (q, v) => {
  if (q.includes('node(') || q.includes('... on Issue')) {
    if (process.env.GRAPHQL_ERROR === 'true') throw new Error('GraphQL query failed');
    return { node: liveNode };
  }
  if (q.includes('projectV2(')) return { user: { projectV2: { id: 'P', fields: { nodes: [
    { id: 'F-status', name: 'Status', options }] } } }, organization: null };
  if (q.includes('addProjectV2ItemById')) return { addProjectV2ItemById: { item: { id: 'ITEM' } } };
  if (q.includes('updateProjectV2ItemFieldValue')) { updates.push(v.optionId); return {}; }
  throw new Error('unexpected query: ' + q);
}};
const context = { repo: { owner: 'o' }, payload: scenario };
const core = { warning: () => {} };
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
new AsyncFunction('github', 'context', 'core', script)(github, context, core)
  .then(() => console.log(JSON.stringify(updates)));
"""


def script_body():
    text = WORKFLOW.read_text(encoding="utf-8")
    block = text.split("script: |\n", 1)[1]
    return textwrap.dedent(block)


def run(action, state, reason, labels, live_node=None, graphql_error=False):
    scenario = {"action": action, "issue": {
        "number": 1, "node_id": "N", "state": state, "state_reason": reason,
        "labels": [{"name": n} for n in labels]}}
    env = {**os.environ, "SCRIPT": script_body(), "SCENARIO": json.dumps(scenario), "OPTIONS": json.dumps(OPTIONS),
           "PROJECT_TOKEN": "t", "PROJECT_OWNER": "o", "PROJECT_OWNER_TYPE": "user",
           "PROJECT_NUMBER": "2", "DRY_RUN": "false"}
    if live_node is not None:
        env["LIVE_NODE"] = json.dumps(live_node) if live_node is not False else "null"
    if graphql_error:
        env["GRAPHQL_ERROR"] = "true"
    r = subprocess.run([NODE, "-e", RUNNER], env=env, capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout.strip().splitlines()[-1])


def test_open_issue_follows_its_status_label():
    assert run("labeled", "open", None, ["status:in review", "type:feature"]) == ["o-rev"]


def test_closed_event_sets_done():
    assert run("closed", "closed", "completed", ["status:planned"]) == ["o-done"]


def test_later_label_edit_on_a_completed_issue_stays_done():
    # the #109 regression: closed as completed, label still status:planned, then a label edit
    assert run("labeled", "closed", "completed", ["status:planned", "type:feature"]) == ["o-done"]


def test_reopen_restores_the_status_label():
    assert run("reopened", "open", None, ["status:blocked"]) == ["o-blk"]
    assert run("reopened", "open", None, ["type:feature"]) == ["o-planned"]


def test_not_planned_close_is_not_forced_done():
    assert run("closed", "closed", "not_planned", ["status:blocked"]) == ["o-blk"]


def test_concept_issues_are_excluded():
    assert run("labeled", "open", None, ["concept:map", "status:planned"]) == []


def test_workflow_defines_per_issue_concurrency():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert re.search(r"concurrency:\s*\n\s*group:\s*sync-labels-to-project-\$\{\{\s*github\.event\.issue\.number\s*\}\}\s*\n\s*cancel-in-progress:\s*false", text), (
        "workflow must define per-issue concurrency group with cancel-in-progress: false"
    )


def test_stale_unlabeled_payload_recovers_live_closed_state():
    # Stale unlabeled webhook payload (open, no status label) arriving after issue is closed completed
    live_node = {
        "state": "CLOSED",
        "stateReason": "COMPLETED",
        "labels": {"nodes": [{"name": "status:done"}, {"name": "type:feature"}]}
    }
    assert run("unlabeled", "open", None, ["type:feature"], live_node=live_node) == ["o-done"]


def test_stale_unlabeled_payload_recovers_live_in_review_label():
    # Stale unlabeled webhook payload (open, only type label) arriving after status:in review was set
    live_node = {
        "state": "OPEN",
        "stateReason": None,
        "labels": {"nodes": [{"name": "status:in review"}, {"name": "type:feature"}]}
    }
    assert run("unlabeled", "open", None, ["type:feature"], live_node=live_node) == ["o-rev"]


def test_live_query_fallback_on_error():
    # If GraphQL query fails, falls back gracefully to context.payload.issue
    assert run("labeled", "open", None, ["status:in review", "type:feature"], graphql_error=True) == ["o-rev"]
    assert run("closed", "closed", "completed", ["status:planned"], graphql_error=True) == ["o-done"]

