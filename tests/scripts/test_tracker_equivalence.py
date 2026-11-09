"""tests/scripts/test_tracker_equivalence.py — Equivalence test suite for tracker.py (BT-247).

Tests 3 layers:
Layer 1: Dual-backend state & output equivalence (GitHub via gh_shim, Local via issues.py).
Layer 2: Invariants & failure parity (Single Status Invariant, [[A-005]] retry/halt contract).
Layer 3: Downstream gate compatibility (reconcile.py --expect/--with-edges and ice_read.py candidates).
"""
import copy
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import REPO_ROOT

SCRIPTS = REPO_ROOT / "src" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(REPO_ROOT / "tests" / "lifecycle-harness"))
import env
import issues
import reconcile

SHIM = REPO_ROOT / "tests" / "lifecycle-harness" / "shims" / "gh_shim.py"
TRACKER_PY = SCRIPTS / "tracker.py"

INITIAL_STORE = {
    "repo": "l3-harness/throwaway",
    "next_number": 1,
    "issues": {},
    "milestones": [],
    "labels": [
        {"name": "type:feature", "description": "", "color": ""},
        {"name": "type:bug", "description": "", "color": ""},
        {"name": "tier:epic", "description": "", "color": ""},
        {"name": "tier:slice", "description": "", "color": ""},
        {"name": "status:planned", "description": "", "color": ""},
        {"name": "status:in progress", "description": "", "color": ""},
        {"name": "status:in review", "description": "", "color": ""},
        {"name": "status:done", "description": "", "color": ""},
        {"name": "size:small", "description": "", "color": ""},
        {"name": "size:medium", "description": "", "color": ""},
        {"name": "size:large", "description": "", "color": ""},
        {"name": "mode:AFK", "description": "", "color": ""},
        {"name": "mode:HITL", "description": "", "color": ""},
        {"name": "scope:baseline", "description": "", "color": ""},
        {"name": "area:core", "description": "", "color": ""},
    ],
    "repos": [],
    "invocations": [],
    "unknown": [],
}


def normalize_stdout(text: str) -> str:
    """Normalize line endings and whitespace."""
    if text is None:
        return ""
    lines = [line.strip() for line in text.replace("\r\n", "\n").splitlines()]
    return "\n".join(line for line in lines if line)


def clean_store_data(store_json: dict) -> dict:
    """Return state dict excluding execution invocation logs."""
    data = copy.deepcopy(store_json)
    data.pop("invocations", None)
    data.pop("unknown", None)
    return data


def run_cmd(args, cwd, env_vars=None):
    merged_env = dict(os.environ)
    if env_vars:
        merged_env.update(env_vars)
    for v in ("GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN"):
        merged_env.pop(v, None)
    r = subprocess.run(args, cwd=str(cwd), env=merged_env, capture_output=True, text=True, encoding="utf-8")
    return r.returncode, r.stdout, r.stderr


# ==============================================================================
# Layer 1: GitHub Backend Equivalence
# ==============================================================================

def test_layer1_github_equivalence(tmp_path):
    root_legacy = tmp_path / "gh_legacy"
    root_cli = tmp_path / "gh_cli"
    root_legacy.mkdir()
    root_cli.mkdir()

    env_legacy = dict(os.environ)
    env_cli = dict(os.environ)
    env.install_shims(root_legacy, env_legacy)
    env.install_shims(root_cli, env_cli)

    store_legacy = root_legacy / "gh-store.json"
    store_cli = root_cli / "gh-store.json"
    store_legacy.write_text(json.dumps(INITIAL_STORE, indent=2), encoding="utf-8")
    store_cli.write_text(json.dumps(INITIAL_STORE, indent=2), encoding="utf-8")

    env_legacy["L3_GH_STORE"] = str(store_legacy)
    env_legacy["GH_SHIM_STORE"] = str(store_legacy)
    env_cli["L3_GH_STORE"] = str(store_cli)
    env_cli["GH_SHIM_STORE"] = str(store_cli)

    arch_content = "---\ntype: architecture\ntracker: github\n---\n# Architecture\n"
    for r in (root_legacy, root_cli):
        (r / ".memory").mkdir()
        (r / ".memory" / "ARCHITECTURE.md").write_text(arch_content, encoding="utf-8")
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=str(r), check=True)
        subprocess.run(["git", "config", "user.name", "T"], cwd=str(r), check=True)
        subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=str(r), check=True)
        subprocess.run(["git", "remote", "add", "origin", "https://github.com/l3-harness/throwaway.git"], cwd=str(r), check=True)

    gh_bin_legacy = str(root_legacy / "shims" / ("gh.exe" if os.name == "nt" else "gh"))
    gh_bin_cli = str(root_cli / "shims" / ("gh.exe" if os.name == "nt" else "gh"))

    def assert_step(legacy_argv, cli_argv):
        # Resolve bare "gh" to shim binary in legacy root
        if legacy_argv[0] == "gh":
            legacy_argv = [gh_bin_legacy] + legacy_argv[1:]
        rc_leg, out_leg, err_leg = run_cmd(legacy_argv, root_legacy, env_legacy)
        rc_cli, out_cli, err_cli = run_cmd(cli_argv, root_cli, env_cli)

        assert rc_cli == rc_leg, f"Exit code mismatch: cli={rc_cli} legacy={rc_leg}\ncli_err: {err_cli}\nleg_err: {err_leg}"
        norm_leg = normalize_stdout(out_leg)
        norm_cli = normalize_stdout(out_cli)
        # Try JSON comparison if both are JSON
        try:
            j_leg = json.loads(norm_leg)
            j_cli = json.loads(norm_cli)
            def strip_ts(obj):
                if isinstance(obj, dict):
                    return {k: strip_ts(v) for k, v in obj.items() if k != "updated"}
                if isinstance(obj, list):
                    return [strip_ts(x) for x in obj]
                return obj
            assert strip_ts(j_cli) == strip_ts(j_leg), f"JSON output mismatch for {cli_argv}"
        except (json.JSONDecodeError, ValueError):
            assert norm_cli == norm_leg, f"Output mismatch:\nCLI: {norm_cli}\nLEGACY: {norm_leg}"

        data_leg = clean_store_data(json.loads(store_legacy.read_text(encoding="utf-8")))
        data_cli = clean_store_data(json.loads(store_cli.read_text(encoding="utf-8")))
        assert data_cli == data_leg, f"Store state mismatch after {cli_argv}"

    # 1. ensure_label
    assert_step(
        ["gh", "label", "create", "area:ui", "--description", "UI components"],
        [sys.executable, str(TRACKER_PY), "ensure-label", "area:ui", "--description", "UI components"],
    )

    # 2. ensure_milestone
    assert_step(
        ["gh", "api", "repos/{owner}/{repo}/milestones", "-f", "title=v1.0.0"],
        [sys.executable, str(TRACKER_PY), "ensure-milestone", "v1.0.0"],
    )

    # 3. create (epic)
    body_file_leg = root_legacy / ".tmp" / "epic.md"
    body_file_cli = root_cli / ".tmp" / "epic.md"
    for bf in (body_file_leg, body_file_cli):
        bf.parent.mkdir(parents=True, exist_ok=True)
        bf.write_text("Epic body content\n", encoding="utf-8")

    assert_step(
        ["gh", "issue", "create", "--title", "Auth Epic", "--label", "type:feature,tier:epic,status:planned", "--milestone", "v1.0.0", "--body-file", str(body_file_leg)],
        [sys.executable, str(TRACKER_PY), "create", "--title", "Auth Epic", "--label", "type:feature,tier:epic,status:planned", "--milestone", "v1.0.0", "--body-file", str(body_file_cli)],
    )

    # 4. create (slice 1)
    assert_step(
        ["gh", "issue", "create", "--title", "Login Slice", "--label", "type:feature,tier:slice,size:small,status:planned", "--milestone", "v1.0.0", "--body-file", str(body_file_leg)],
        [sys.executable, str(TRACKER_PY), "create", "--title", "Login Slice", "--label", "type:feature,tier:slice,size:small,status:planned", "--milestone", "v1.0.0", "--body-file", str(body_file_cli)],
    )

    # 5. create (slice 2)
    assert_step(
        ["gh", "issue", "create", "--title", "DB Slice", "--label", "type:feature,tier:slice,size:small,status:planned", "--milestone", "v1.0.0", "--body-file", str(body_file_leg)],
        [sys.executable, str(TRACKER_PY), "create", "--title", "DB Slice", "--label", "type:feature,tier:slice,size:small,status:planned", "--milestone", "v1.0.0", "--body-file", str(body_file_cli)],
    )

    # 6. set_parent (slice 2 under epic 1)
    p_id = "I_l3000001"
    c_id = "I_l3000002"
    mutation_add_sub = f"mutation($p:ID!,$c:ID!){{addSubIssue(input:{{issueId:$p,subIssueId:$c}}){{issue{{number}}}}}}"
    assert_step(
        ["gh", "api", "graphql", "-f", f"query={mutation_add_sub}", "-f", f"p={p_id}", "-f", f"c={c_id}"],
        [sys.executable, str(TRACKER_PY), "set-parent", "BT-002", "BT-001"],
    )

    # 7. add_blocker (slice 2 blocked by slice 3)
    b_id = "I_l3000003"
    mutation_add_blk = f"mutation($i:ID!,$b:ID!){{addBlockedBy(input:{{issueId:$i,blockingIssueId:$b}}){{issue{{number}}}}}}"
    assert_step(
        ["gh", "api", "graphql", "-f", f"query={mutation_add_blk}", "-f", f"i={c_id}", "-f", f"b={b_id}"],
        [sys.executable, str(TRACKER_PY), "add-blocker", "BT-002", "BT-003"],
    )

    # 8. clear_blocker
    mutation_rem_blk = f"mutation($i:ID!,$b:ID!){{removeBlockedBy(input:{{issueId:$i,blockingIssueId:$b}}){{issue{{number}}}}}}"
    assert_step(
        ["gh", "api", "graphql", "-f", f"query={mutation_rem_blk}", "-f", f"i={c_id}", "-f", f"b={b_id}"],
        [sys.executable, str(TRACKER_PY), "clear-blocker", "BT-002", "BT-003"],
    )

    # Re-add blocker for read assertions
    assert_step(
        ["gh", "api", "graphql", "-f", f"query={mutation_add_blk}", "-f", f"i={c_id}", "-f", f"b={b_id}"],
        [sys.executable, str(TRACKER_PY), "add-blocker", "BT-002", "BT-003"],
    )

    # 9. set_status / set-status
    assert_step(
        ["gh", "issue", "edit", "2", "--remove-label", "status:planned", "--add-label", "status:in progress"],
        [sys.executable, str(TRACKER_PY), "set-status", "BT-002", "in progress"],
    )

    # 10. set_labels
    assert_step(
        ["gh", "issue", "edit", "2", "--add-label", "area:ui", "--remove-label", "size:small"],
        [sys.executable, str(TRACKER_PY), "set-labels", "BT-002", "--add-label", "area:ui", "--remove-label", "size:small"],
    )

    # 11. set_milestone
    assert_step(
        ["gh", "issue", "edit", "2", "--milestone", "v1.0.0"],
        [sys.executable, str(TRACKER_PY), "set-milestone", "BT-002", "v1.0.0"],
    )

    # 12. comment
    assert_step(
        ["gh", "issue", "comment", "2", "--body", "Status update comment"],
        [sys.executable, str(TRACKER_PY), "comment", "BT-002", "--body", "Status update comment"],
    )

    # 13. resume note comment
    resume_note = "<!-- stratos:resume -->\nBranch: feat-1 / Done: step1 / Open: step2 / Next step: step2 / Blockers: none"
    assert_step(
        ["gh", "issue", "comment", "2", "--body", resume_note],
        [sys.executable, str(TRACKER_PY), "comment", "BT-002", "--body", resume_note],
    )

    # 14. set_refs
    issue2_leg = json.loads(store_legacy.read_text(encoding="utf-8"))["issues"]["2"]
    old_body = issue2_leg["body"].rstrip()
    new_body = f"{old_body}\n\nRefs: [[L-001]], [[A-002]]"
    assert_step(
        ["gh", "issue", "edit", "2", "--body", new_body],
        [sys.executable, str(TRACKER_PY), "set-refs", "BT-002", "[[L-001]], [[A-002]]"],
    )

    # 15. set_body
    updated_body = "Brand new body for issue 2\n- **Impact:** 2.0\n- **Confidence:** 80%\n"
    assert_step(
        ["gh", "issue", "edit", "2", "--body", updated_body],
        [sys.executable, str(TRACKER_PY), "set-body", "BT-002", "--body", updated_body],
    )

    # 16. claim
    assert_step(
        ["gh", "issue", "edit", "2", "--add-assignee", "@me"],
        [sys.executable, str(TRACKER_PY), "claim", "BT-002"],
    )

    # 17. close
    assert_step(
        ["gh", "issue", "close", "3", "--reason", "completed"],
        [sys.executable, str(TRACKER_PY), "close", "BT-003", "--reason", "completed"],
    )

    # 18. reopen
    assert_step(
        ["gh", "issue", "reopen", "3"],
        [sys.executable, str(TRACKER_PY), "reopen", "BT-003"],
    )

    # 19. close_milestone
    assert_step(
        ["gh", "api", "-X", "PATCH", "repos/{owner}/{repo}/milestones/1", "-f", "state=closed"],
        [sys.executable, str(TRACKER_PY), "close-milestone", "1"],
    )

    # --------------------------------------------------------------------------
    # READS Equivalence
    # --------------------------------------------------------------------------
    # get
    assert_step(
        ["gh", "issue", "view", "2", "--json", "number,state,labels,milestone,parent,blockedBy,body"],
        [sys.executable, str(TRACKER_PY), "get", "BT-002"],
    )

    # list
    assert_step(
        ["gh", "issue", "list", "--json", "number,title,labels,milestone"],
        [sys.executable, str(TRACKER_PY), "list"],
    )

    # wip
    assert_step(
        ["gh", "issue", "list", "--state", "open", "--label", "status:in progress", "--json", "number,title,labels"],
        [sys.executable, str(TRACKER_PY), "wip"],
    )

    # resume_note
    assert_step(
        ["gh", "issue", "view", "2", "--json", "comments", "--jq", '[.comments[] | select(.body | startswith("<!-- stratos:resume -->"))] | last | .body'],
        [sys.executable, str(TRACKER_PY), "resume-note", "BT-002"],
    )

    # candidates
    assert_step(
        [sys.executable, str(SCRIPTS / "ice_read.py"), "candidates"],
        [sys.executable, str(TRACKER_PY), "candidates"],
    )

    # children
    assert_step(
        ["gh", "issue", "view", "1", "--json", "subIssues"],
        [sys.executable, str(TRACKER_PY), "children", "BT-001"],
    )

    # blockers
    assert_step(
        ["gh", "issue", "view", "2", "--json", "blockedBy"],
        [sys.executable, str(TRACKER_PY), "blockers", "BT-002"],
    )


# ==============================================================================
# Layer 1: Local Backend Equivalence
# ==============================================================================

def test_layer1_local_equivalence(tmp_path):
    repo_legacy = tmp_path / "repo_legacy"
    repo_cli = tmp_path / "repo_cli"
    repo_legacy.mkdir()
    repo_cli.mkdir()

    branch = "test-tracker/issues"
    arch = f"---\ntype: architecture\ntracker: local\ntracker_branch: {branch}\n---\n# Architecture\n"

    for r in (repo_legacy, repo_cli):
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=str(r), check=True)
        subprocess.run(["git", "config", "user.name", "T"], cwd=str(r), check=True)
        subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=str(r), check=True)
        (r / ".memory").mkdir()
        (r / ".memory" / "ARCHITECTURE.md").write_text(arch, encoding="utf-8")
        # init tracker store
        subprocess.run([sys.executable, str(SCRIPTS / "issues.py"), "init"], cwd=str(r), check=True)

    def assert_local_step(legacy_argv, cli_argv):
        rc_leg, out_leg, err_leg = run_cmd(legacy_argv, repo_legacy)
        rc_cli, out_cli, err_cli = run_cmd(cli_argv, repo_cli)

        assert rc_cli == rc_leg, f"Exit code mismatch: cli={rc_cli} legacy={rc_leg}\ncli_err: {err_cli}\nleg_err: {err_leg}"
        norm_leg = normalize_stdout(out_leg)
        norm_cli = normalize_stdout(out_cli)
        try:
            j_leg = json.loads(norm_leg)
            j_cli = json.loads(norm_cli)
            def strip_ts(obj):
                if isinstance(obj, dict):
                    return {k: strip_ts(v) for k, v in obj.items() if k != "updated"}
                if isinstance(obj, list):
                    return [strip_ts(x) for x in obj]
                return obj
            assert strip_ts(j_cli) == strip_ts(j_leg), f"JSON output mismatch for {cli_argv}"
        except (json.JSONDecodeError, ValueError):
            assert norm_cli == norm_leg, f"Output mismatch:\nCLI: {norm_cli}\nLEGACY: {norm_leg}"

    # 1. ensure_label
    assert_local_step(
        [sys.executable, str(SCRIPTS / "issues.py"), "label", "area:ui"],
        [sys.executable, str(TRACKER_PY), "ensure-label", "area:ui"],
    )

    # 2. ensure_milestone (local no-op)
    assert_local_step(
        [sys.executable, "-c", "import sys; sys.exit(0)"],
        [sys.executable, str(TRACKER_PY), "ensure-milestone", "v1.0.0"],
    )

    # 3. create (epic)
    bf_leg = repo_legacy / ".tmp" / "epic.md"
    bf_cli = repo_cli / ".tmp" / "epic.md"
    for bf in (bf_leg, bf_cli):
        bf.parent.mkdir(parents=True, exist_ok=True)
        bf.write_text("Epic body text\n", encoding="utf-8")

    assert_local_step(
        [sys.executable, str(SCRIPTS / "issues.py"), "create", "--title", "Auth Epic", "--label", "type:feature,tier:epic,status:planned", "--milestone", "v1.0.0", "--body-file", str(bf_leg)],
        [sys.executable, str(TRACKER_PY), "create", "--title", "Auth Epic", "--label", "type:feature,tier:epic,status:planned", "--milestone", "v1.0.0", "--body-file", str(bf_cli)],
    )

    # 4. create (slice 1)
    assert_local_step(
        [sys.executable, str(SCRIPTS / "issues.py"), "create", "--title", "Login Slice", "--label", "type:feature,tier:slice,size:small,status:planned", "--milestone", "v1.0.0", "--body-file", str(bf_leg)],
        [sys.executable, str(TRACKER_PY), "create", "--title", "Login Slice", "--label", "type:feature,tier:slice,size:small,status:planned", "--milestone", "v1.0.0", "--body-file", str(bf_cli)],
    )

    # 5. create (slice 2)
    assert_local_step(
        [sys.executable, str(SCRIPTS / "issues.py"), "create", "--title", "DB Slice", "--label", "type:feature,tier:slice,size:small,status:planned", "--milestone", "v1.0.0", "--body-file", str(bf_leg)],
        [sys.executable, str(TRACKER_PY), "create", "--title", "DB Slice", "--label", "type:feature,tier:slice,size:small,status:planned", "--milestone", "v1.0.0", "--body-file", str(bf_cli)],
    )

    epic_id = "BT-LOCAL-auth-epic"
    s1_id = "BT-LOCAL-login-slice"
    s2_id = "BT-LOCAL-db-slice"

    # 6. set_parent
    assert_local_step(
        [sys.executable, str(SCRIPTS / "issues.py"), "set", s1_id, "--parent", epic_id],
        [sys.executable, str(TRACKER_PY), "set-parent", s1_id, epic_id],
    )

    # 7. add_blocker
    assert_local_step(
        [sys.executable, str(SCRIPTS / "issues.py"), "set", s1_id, "--add-blocker", s2_id],
        [sys.executable, str(TRACKER_PY), "add-blocker", s1_id, s2_id],
    )

    # 8. clear_blocker
    assert_local_step(
        [sys.executable, str(SCRIPTS / "issues.py"), "set", s1_id, "--remove-blocker", s2_id],
        [sys.executable, str(TRACKER_PY), "clear-blocker", s1_id, s2_id],
    )

    # Re-add blocker for reads
    assert_local_step(
        [sys.executable, str(SCRIPTS / "issues.py"), "set", s1_id, "--add-blocker", s2_id],
        [sys.executable, str(TRACKER_PY), "add-blocker", s1_id, s2_id],
    )

    # 9. set_status
    assert_local_step(
        [sys.executable, str(SCRIPTS / "issues.py"), "set", s1_id, "--status", "in progress"],
        [sys.executable, str(TRACKER_PY), "set-status", s1_id, "in progress"],
    )

    # 10. set_labels
    assert_local_step(
        [sys.executable, str(SCRIPTS / "issues.py"), "set", s1_id, "--add-label", "area:ui", "--remove-label", "size:small"],
        [sys.executable, str(TRACKER_PY), "set-labels", s1_id, "--add-label", "area:ui", "--remove-label", "size:small"],
    )

    # 11. set_milestone
    assert_local_step(
        [sys.executable, str(SCRIPTS / "issues.py"), "set", s1_id, "--milestone", "v1.0.0"],
        [sys.executable, str(TRACKER_PY), "set-milestone", s1_id, "v1.0.0"],
    )

    # 12. comment
    assert_local_step(
        [sys.executable, str(SCRIPTS / "issues.py"), "comment", s1_id, "--body", "Work in progress"],
        [sys.executable, str(TRACKER_PY), "comment", s1_id, "--body", "Work in progress"],
    )

    # 13. resume note comment (folder state in .memory/resume/<id>.md)
    resume_note = "<!-- stratos:resume -->\nBranch: feat-1 / Done: 0 / Open: 1 / Next step: test / Blockers: none"
    assert_local_step(
        [sys.executable, str(SCRIPTS / "issues.py"), "comment", s1_id, "--body", resume_note],
        [sys.executable, str(TRACKER_PY), "comment", s1_id, "--body", resume_note],
    )
    # Check resume note files match
    assert (repo_legacy / ".memory" / "resume" / f"{s1_id}.md").read_text(encoding="utf-8") == \
           (repo_cli / ".memory" / "resume" / f"{s1_id}.md").read_text(encoding="utf-8")

    # 14. set_refs
    refs_body = "Epic body text\n\nRefs: [[L-001]], [[A-002]]\n"
    ref_f_leg = repo_legacy / ".tmp" / "refs.md"
    ref_f_cli = repo_cli / ".tmp" / "refs.md"
    for rf in (ref_f_leg, ref_f_cli):
        rf.write_text(refs_body, encoding="utf-8")

    assert_local_step(
        [sys.executable, str(SCRIPTS / "issues.py"), "set", epic_id, "--body-file", str(ref_f_leg)],
        [sys.executable, str(TRACKER_PY), "set-refs", epic_id, "[[L-001]], [[A-002]]"],
    )

    # 15. set_body
    assert_local_step(
        [sys.executable, str(SCRIPTS / "issues.py"), "set", s1_id, "--body-file", str(bf_leg)],
        [sys.executable, str(TRACKER_PY), "set-body", s1_id, "--body-file", str(bf_cli)],
    )

    # 16. claim
    assert_local_step(
        [sys.executable, str(SCRIPTS / "issues.py"), "claim", s1_id, "--by", "branch-test"],
        [sys.executable, str(TRACKER_PY), "claim", s1_id, "--by", "branch-test"],
    )

    # 17. close
    assert_local_step(
        [sys.executable, str(SCRIPTS / "issues.py"), "close", s2_id, "--reason", "completed"],
        [sys.executable, str(TRACKER_PY), "close", s2_id, "--reason", "completed"],
    )

    # 18. reopen
    assert_local_step(
        [sys.executable, str(SCRIPTS / "issues.py"), "reopen", s2_id],
        [sys.executable, str(TRACKER_PY), "reopen", s2_id],
    )

    # 19. close_milestone (local no-op)
    assert_local_step(
        [sys.executable, "-c", "import sys; sys.exit(0)"],
        [sys.executable, str(TRACKER_PY), "close-milestone", "v1.0.0"],
    )

    # READS
    assert_local_step(
        [sys.executable, str(SCRIPTS / "issues.py"), "get", s1_id],
        [sys.executable, str(TRACKER_PY), "get", s1_id],
    )
    assert_local_step(
        [sys.executable, str(SCRIPTS / "issues.py"), "list"],
        [sys.executable, str(TRACKER_PY), "list"],
    )
    assert_local_step(
        [sys.executable, str(SCRIPTS / "issues.py"), "wip"],
        [sys.executable, str(TRACKER_PY), "wip"],
    )
    assert_local_step(
        [sys.executable, "-c", f"import sys, pathlib; p = pathlib.Path('.memory/resume/{s1_id}.md'); sys.stdout.write(p.read_text(encoding='utf-8') if p.exists() else '')"],
        [sys.executable, str(TRACKER_PY), "resume-note", s1_id],
    )
    assert_local_step(
        [sys.executable, str(SCRIPTS / "ice_read.py"), "candidates"],
        [sys.executable, str(TRACKER_PY), "candidates"],
    )
    assert_local_step(
        [sys.executable, str(SCRIPTS / "issues.py"), "children", epic_id],
        [sys.executable, str(TRACKER_PY), "children", epic_id],
    )
    assert_local_step(
        [sys.executable, str(SCRIPTS / "issues.py"), "blockers", s1_id],
        [sys.executable, str(TRACKER_PY), "blockers", s1_id],
    )

    # Assert tree and content equivalence on tracker branch
    _, sha_leg, _ = run_cmd(["git", "rev-parse", f"refs/heads/{branch}"], repo_legacy)
    _, sha_cli, _ = run_cmd(["git", "rev-parse", f"refs/heads/{branch}"], repo_cli)
    _, files_leg, _ = run_cmd(["git", "ls-tree", "-r", "--name-only", sha_leg.strip()], repo_legacy)
    _, files_cli, _ = run_cmd(["git", "ls-tree", "-r", "--name-only", sha_cli.strip()], repo_cli)
    assert files_cli == files_leg, "Tracker branch file list differs!"

    for fp in files_leg.splitlines():
        if not fp.strip():
            continue
        _, text_leg, _ = run_cmd(["git", "show", f"{sha_leg.strip()}:{fp.strip()}"], repo_legacy)
        _, text_cli, _ = run_cmd(["git", "show", f"{sha_cli.strip()}:{fp.strip()}"], repo_cli)
        norm_leg_file = re.sub(r"^updated:.*$", "updated: <timestamp>", text_leg, flags=re.M)
        norm_cli_file = re.sub(r"^updated:.*$", "updated: <timestamp>", text_cli, flags=re.M)
        assert norm_cli_file == norm_leg_file, f"File {fp} content differs on tracker branch!"


# ==============================================================================
# Layer 2: Invariants & Failure Parity
# ==============================================================================

def test_layer2_single_status_invariant_github(tmp_path):
    root = tmp_path / "gh_inv"
    root.mkdir()
    child = dict(os.environ)
    env.install_shims(root, child)
    store = root / "gh-store.json"

    # Seed an issue with two status labels to test invariant enforcement
    state = copy.deepcopy(INITIAL_STORE)
    state["issues"]["1"] = {
        "number": 1,
        "id": "I_l3000001",
        "title": "Invariant Issue",
        "body": "Body",
        "labels": [{"name": "status:planned"}, {"name": "status:blocked"}, {"name": "type:bug"}],
        "milestone": None,
        "state": "OPEN",
        "comments": [],
        "subIssues": [],
        "blockedBy": [],
        "parent": None,
        "assignees": [],
        "isPR": False,
        "isDraft": False,
        "url": "https://github.com/l3-harness/throwaway/issues/1",
    }
    state["next_number"] = 2
    store.write_text(json.dumps(state, indent=2), encoding="utf-8")
    child["L3_GH_STORE"] = str(store)

    (root / ".memory").mkdir()
    (root / ".memory" / "ARCHITECTURE.md").write_text("---\ntype: architecture\ntracker: github\n---\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=str(root), check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=str(root), check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=str(root), check=True)
    subprocess.run(["git", "remote", "add", "origin", "https://github.com/l3-harness/throwaway.git"], cwd=str(root), check=True)

    # Run set-status to "in progress"
    rc, out, err = run_cmd([sys.executable, str(TRACKER_PY), "set-status", "BT-001", "in progress"], root, child)
    assert rc == 0, f"set-status failed: {err}"

    data = json.loads(store.read_text(encoding="utf-8"))
    issue_labels = [l["name"] for l in data["issues"]["1"]["labels"]]
    status_labels = [l for l in issue_labels if l.startswith("status:")]
    assert status_labels == ["status:in progress"], f"Single status invariant violated: {status_labels}"
    assert "type:bug" in issue_labels


def test_layer2_single_status_invariant_local(tmp_path):
    root = tmp_path / "local_inv"
    root.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=str(root), check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=str(root), check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=str(root), check=True)
    (root / ".memory").mkdir()
    (root / ".memory" / "ARCHITECTURE.md").write_text("---\ntype: architecture\ntracker: local\ntracker_branch: test-inv/issues\n---\n", encoding="utf-8")
    subprocess.run([sys.executable, str(SCRIPTS / "issues.py"), "init"], cwd=str(root), check=True)

    # Create issue
    rc, out, err = run_cmd([sys.executable, str(TRACKER_PY), "create", "--title", "Local Invariant", "--label", "type:bug"], root)
    assert rc == 0, err
    issue_id = out.strip()

    # Set status
    rc, out, err = run_cmd([sys.executable, str(TRACKER_PY), "set-status", issue_id, "in progress"], root)
    assert rc == 0, err

    rc_get, out_get, _ = run_cmd([sys.executable, str(TRACKER_PY), "get", issue_id], root)
    assert rc_get == 0
    issue = json.loads(out_get)
    assert issue["status"] == "in progress"
    assert not any(l.startswith("status:") for l in issue["labels"])


def test_layer2_a005_retry_halt_contract(tmp_path, monkeypatch):
    """Assert [[A-005]]: on gh failure, retries 3 times with backoff, exits non-zero, zero local fallback files."""
    root = tmp_path / "gh_fail"
    root.mkdir()
    (root / ".memory").mkdir()
    (root / ".memory" / "ARCHITECTURE.md").write_text("---\ntype: architecture\ntracker: github\n---\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=str(root), check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=str(root), check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=str(root), check=True)
    subprocess.run(["git", "remote", "add", "origin", "https://github.com/l3-harness/throwaway.git"], cwd=str(root), check=True)

    attempts = []

    def failing_gh(args):
        attempts.append(args)
        return 1, "", "transient connection refused"

    # We run tracker.py via python with failing gh shim or monkeypatched reconcile._gh_run
    # Let's write a small runner script in root to test retry count & zero fallback files
    runner = root / "run_fail_test.py"
    runner.write_text(f"""
import sys
from pathlib import Path
sys.path.insert(0, r"{SCRIPTS}")
import reconcile
import tracker

reconcile.RETRY_DELAYS = (0.01, 0.01, 0.01)
attempts = []

def fail_run(args):
    attempts.append(args)
    return 1, "", "simulated gh failure"

reconcile._gh_run = fail_run
tracker.RETRY_DELAYS = (0.01, 0.01, 0.01)

rc = tracker.main(["get", "BT-001"])
assert rc != 0, f"Expected non-zero exit, got {{rc}}"
assert len(attempts) == 4, f"Expected 4 attempts (1 initial + 3 retries), got {{len(attempts)}}"
print(f"RETRY_OK: {{len(attempts)}}")
""", encoding="utf-8")

    rc, out, err = run_cmd([sys.executable, str(runner)], root)
    assert rc == 0, f"A-005 contract failed:\nstdout: {out}\nstderr: {err}"
    assert "RETRY_OK: 4" in out

    # Assert ZERO local fallback files created
    assert not (root / "docs" / "issues").exists(), "Local fallback files written under docs/issues!"
    assert not (root / ".memory" / "resume").exists(), "Local fallback files written under .memory/resume!"


# ==============================================================================
# Layer 3: Downstream Gate Compatibility
# ==============================================================================

def test_layer3_downstream_gate_compatibility_github(tmp_path):
    root = tmp_path / "gh_l3"
    root.mkdir()
    child = dict(os.environ)
    env.install_shims(root, child)
    store = root / "gh-store.json"
    store.write_text(json.dumps(INITIAL_STORE, indent=2), encoding="utf-8")
    child["L3_GH_STORE"] = str(store)

    (root / ".memory").mkdir()
    (root / ".memory" / "ARCHITECTURE.md").write_text("---\ntype: architecture\ntracker: github\n---\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=str(root), check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=str(root), check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=str(root), check=True)
    subprocess.run(["git", "remote", "add", "origin", "https://github.com/l3-harness/throwaway.git"], cwd=str(root), check=True)

    # Use tracker.py to create epic, slice, set status, parent, metrics
    run_cmd([sys.executable, str(TRACKER_PY), "create", "--title", "L3 Epic", "--label", "type:feature,tier:epic,status:planned", "--milestone", "v1.0.0"], root, child)
    run_cmd([sys.executable, str(TRACKER_PY), "create", "--title", "L3 Slice", "--label", "type:feature,tier:slice,size:small,status:planned", "--milestone", "v1.0.0", "--body", "- **Impact:** 2.0\n- **Confidence:** 80%\n"], root, child)
    run_cmd([sys.executable, str(TRACKER_PY), "set-parent", "BT-002", "BT-001"], root, child)
    run_cmd([sys.executable, str(TRACKER_PY), "set-status", "BT-002", "planned"], root, child)

    # Assert reconcile.py gate passes
    rc, out, err = run_cmd([sys.executable, str(SCRIPTS / "reconcile.py"), "--ids", "BT-002,BT-001", "--expect", "BT-002:status=planned;BT-001:status=planned", "--with-edges", "blockers"], root, child)
    assert rc == 0, f"reconcile gate failed:\nstdout: {out}\nstderr: {err}"
    assert "[MIRROR-OK" in out

    # Assert ice_read.py candidates produces identical output to tracker.py candidates
    rc_ice, out_ice, _ = run_cmd([sys.executable, str(SCRIPTS / "ice_read.py"), "candidates"], root, child)
    rc_trk, out_trk, _ = run_cmd([sys.executable, str(TRACKER_PY), "candidates"], root, child)
    assert rc_ice == 0 and rc_trk == 0
    assert normalize_stdout(out_trk) == normalize_stdout(out_ice)
    assert "BT-002" in out_trk


def test_layer3_downstream_gate_compatibility_local(tmp_path):
    root = tmp_path / "local_l3"
    root.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=str(root), check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=str(root), check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=str(root), check=True)
    (root / ".memory").mkdir()
    (root / ".memory" / "ARCHITECTURE.md").write_text("---\ntype: architecture\ntracker: local\ntracker_branch: test-inv/issues\n---\n", encoding="utf-8")
    subprocess.run([sys.executable, str(SCRIPTS / "issues.py"), "init"], cwd=str(root), check=True)

    # Use tracker.py to create epic and slice
    rc1, out1, _ = run_cmd([sys.executable, str(TRACKER_PY), "create", "--title", "Local Epic", "--label", "type:feature,tier:epic,status:planned", "--milestone", "v1.0.0"], root)
    rc2, out2, _ = run_cmd([sys.executable, str(TRACKER_PY), "create", "--title", "Local Slice", "--label", "type:feature,tier:slice,size:small,status:planned", "--milestone", "v1.0.0"], root)
    assert rc1 == 0 and rc2 == 0
    epic_id = out1.strip()
    slice_id = out2.strip()

    run_cmd([sys.executable, str(TRACKER_PY), "set-parent", slice_id, epic_id], root)
    run_cmd([sys.executable, str(TRACKER_PY), "set-status", slice_id, "planned"], root)

    # Assert reconcile.py gate passes
    rc, out, err = run_cmd([sys.executable, str(SCRIPTS / "reconcile.py"), "--ids", f"{slice_id},{epic_id}", "--expect", f"{slice_id}:status=planned;{epic_id}:status=planned", "--with-edges", "blockers"], root)
    assert rc == 0, f"reconcile gate failed on local:\nstdout: {out}\nstderr: {err}"
    assert "[MIRROR-OK" in out

    # Assert ice_read.py candidates produces identical output to tracker.py candidates
    rc_ice, out_ice, _ = run_cmd([sys.executable, str(SCRIPTS / "ice_read.py"), "candidates"], root)
    rc_trk, out_trk, _ = run_cmd([sys.executable, str(TRACKER_PY), "candidates"], root)
    assert rc_ice == 0 and rc_trk == 0
    assert normalize_stdout(out_trk) == normalize_stdout(out_ice)
    assert slice_id in out_trk
