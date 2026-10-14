"""BT-163 R7: `nightly_scan.py` counts tool calls and failures per session from both hosts' transcripts.

Seam: the CLI (stdout / --json) against SYNTHETIC transcripts built from the documented schema only:
Claude Code `<root>/<slug>/*.jsonl` (tool_use / tool_result.is_error) and Antigravity
`<root>/<id>/.system_generated/logs/transcript.jsonl` (steps with status / error / tool_calls[].args).
"""
import datetime
import json
import os
import re
import subprocess
import sys

import pytest

from conftest import REPO_ROOT

SCRIPT = REPO_ROOT / "src" / "scripts" / "nightly_scan.py"
UTC = datetime.timezone.utc
SINCE = "2026-10-13T12:00:00Z"


def iso(h, m=0, day=13):
    return f"2026-10-{day:02d}T{h:02d}:{m:02d}:00Z"


def slug_of(path):
    return re.sub(r"[^A-Za-z0-9]", "-", str(path))


def write(path, recs, mtime=None, raw=()):
    """Write dict records (and raw lines) as JSONL; mtime defaults to the newest timestamp inside."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(r) for r in recs] + list(raw)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    stamps = [r.get("timestamp") or r.get("created_at") for r in recs if isinstance(r, dict)]
    stamps = [datetime.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp() for s in stamps if s]
    t = mtime if mtime is not None else (max(stamps) if stamps else 0)
    os.utime(path, (t, t))
    return path


# --- Claude Code records ---------------------------------------------------------
def use(uid, name, inp, ts):
    return {"type": "assistant", "timestamp": ts, "sessionId": "s", "cwd": "SENTINEL_CWD", "gitBranch": "SENTINEL_BRANCH",
            "message": {"role": "assistant", "content": [
                {"type": "thinking", "thinking": "SENTINEL_THINK"},
                {"type": "text", "text": "SENTINEL_TEXT"},
                {"type": "tool_use", "id": uid, "name": name, "input": inp}]}}


def result(uid, err, ts):
    return {"type": "user", "timestamp": ts,
            "message": {"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": uid, "content": "SENTINEL_OUT", "is_error": err}]},
            "toolUseResult": {"stdout": "SENTINEL_STDOUT", "answers": {"SENTINEL_KEY": "SENTINEL_ANSWER"}}}


# --- Antigravity steps -----------------------------------------------------------
def step(ts, calls=(), status="DONE", error=None, kind="PLANNER_RESPONSE"):
    d = {"type": kind, "status": status, "created_at": ts, "step_index": 1,
         "tool_calls": [{"name": n, "args": a} for n, a in calls]}
    if error:
        d["error"] = error
    return d


@pytest.fixture
def env(tmp_path):
    project = (tmp_path / "my_proj.x").resolve()
    project.mkdir()
    return {"project": project, "claude": tmp_path / "claude", "agy": tmp_path / "agy", "tmp": tmp_path,
            "cdir": tmp_path / "claude" / slug_of(project)}


def run(env, *args, since=SINCE):
    cmd = [sys.executable, str(SCRIPT), "--project", str(env["project"]), "--claude-root", str(env["claude"]),
           "--agy-root", str(env["agy"])]
    if since:
        cmd += ["--since", since]
    out = subprocess.run(cmd + list(args), capture_output=True, text=True, encoding="utf-8")
    assert out.returncode == 0, out.stderr
    return out.stdout


def agy_session(env, sid, steps, **kw):
    return write(env["agy"] / sid / ".system_generated" / "logs" / "transcript.jsonl", steps, **kw)


def as_json(env, *args, **kw):
    return json.loads(run(env, "--json", *args, **kw))


def test_claude_counts_calls_pairs_errors_and_shows_only_name_and_command(env):
    write(env["cdir"] / "sess-a.jsonl", [
        use("u1", "Bash", {"command": "git status"}, iso(13, 0)), result("u1", False, iso(13, 1)),
        use("u2", "Bash", {"command": "git comit -m x"}, iso(13, 2)), result("u2", True, iso(13, 3)),
        use("u3", "Read", {"file_path": "C:/p/missing.md"}, iso(13, 4)), result("u3", True, iso(13, 5)),
        use("u4", "mcp__srv__tool", {"weird_SENTINEL_KEY2": "v"}, iso(13, 6)), result("u4", True, iso(13, 7))])
    write(env["cdir"] / "sess-b.jsonl", [use("v1", "Bash", {"command": "ls"}, iso(14)), result("v1", False, iso(14, 1))])
    out = run(env)
    assert "claude: 2 sessions · 5 tool calls · 3 errors" in out
    assert "  sess-a 2026-10-13T13:00:00Z calls=4 errors=3" in out and "  sess-b 2026-10-13T14:00:00Z calls=1 errors=0" in out
    assert out.index("sess-a") < out.index("sess-b")  # most errors first
    assert "    ! Bash  git comit -m x" in out and "    ! Read  C:/p/missing.md" in out
    assert "    ! mcp__srv__tool" in out and "git status" not in out  # a passing call is never listed
    assert "SENTINEL" not in out  # no unknown key name, text, thinking, output, cwd or branch
    assert "agy: transcript root not found" in out


def test_a_streamed_duplicate_tool_use_is_counted_once_and_an_orphan_result_is_still_an_error(env):
    write(env["cdir"] / "s.jsonl", [use("u1", "Bash", {"command": "x"}, iso(13)), use("u1", "Bash", {"command": "x"}, iso(13)),
                                    result("u1", False, iso(13, 1)), result("ghost", True, iso(13, 2))])
    s = as_json(env)["hosts"]["claude"]["sessions"][0]
    assert s["tool_calls"] == 1 and s["errors"] == 1 and s["failing"] == [{"tool": "?", "target": ""}]


def test_claude_scoping_to_the_project_folder_and_its_worktrees(env):
    write(env["cdir"] / "mine.jsonl", [use("u", "Bash", {"command": "a"}, iso(13))])
    wt = env["claude"] / (slug_of(env["project"]) + "--claude-worktrees-feat-x")
    write(wt / "wt.jsonl", [use("u", "Bash", {"command": "b"}, iso(13))])
    write(env["claude"] / (slug_of(env["project"]) + "-2") / "sibling.jsonl", [use("u", "Bash", {"command": "c"}, iso(13))])
    write(env["claude"] / "C--Users-someone-else" / "other.jsonl", [use("u", "Bash", {"command": "d"}, iso(13))])
    ids = {s["id"] for s in as_json(env)["hosts"]["claude"]["sessions"]}
    assert ids == {"mine", "wt"}


def test_agy_counts_calls_and_failing_steps(env):
    here = str(env["project"])
    agy_session(env, "brain-1", [
        step(iso(13, 0), [("run_command", {"CommandLine": "npm test", "Cwd": here})]),
        step(iso(13, 1), [("run_command", {"CommandLine": "git cmmit", "Cwd": here}),
                          ("view_file", {"AbsolutePath": here + os.sep + "a.md"})], status="ERROR", kind="GENERIC"),
        step(iso(13, 2), [("write_to_file", {"TargetFile": here + os.sep + "b.py"})], status="INVALID"),
        step(iso(13, 3), [("run_command", {"CommandLine": "ok", "Cwd": here})], error="SENTINEL_ERR"),
        step(iso(13, 4), [], status="ERROR", kind="CHECKPOINT"),
        step(iso(13, 5), [("run_command", {"CommandLine": "fine", "Cwd": here})], status="RUNNING")])
    out = run(env)
    assert "agy: 1 sessions · 6 tool calls · 4 errors" in out  # a failing step counts once, however many calls it has
    assert "  brain-1 2026-10-13T13:00:00Z calls=6 errors=4" in out
    assert "    ! run_command  git cmmit" in out and "    ! view_file  " + here + os.sep + "a.md" in out
    assert "    ! write_to_file  " + here + os.sep + "b.py" in out and "    ! run_command  ok" in out
    assert "    ! CHECKPOINT" in out and "npm test" not in out and "fine" not in out
    assert "SENTINEL" not in out


def test_agy_session_outside_the_project_is_ignored_and_a_prefix_sibling_does_not_match(env):
    other = str(env["tmp"] / "elsewhere")
    sibling = str(env["project"]) + "-other"
    agy_session(env, "outside", [step(iso(13), [("run_command", {"CommandLine": "x", "Cwd": other})], status="ERROR")])
    agy_session(env, "sibling", [step(iso(13), [("run_command", {"CommandLine": "x", "Cwd": sibling})], status="ERROR")])
    agy_session(env, "nopaths", [step(iso(13), [("search_web", {"Query": "SENTINEL_Q"})]), step(iso(13, 1), status="ERROR")])
    agy_session(env, "inside", [step(iso(13), [("view_file", {"AbsolutePath": str(env["project"] / "sub" / "f.md")})])])
    s = as_json(env)["hosts"]["agy"]["sessions"]
    assert [x["id"] for x in s] == ["inside"]


def test_agy_scope_is_judged_over_the_whole_session_but_counts_only_since_the_watermark(env):
    here = str(env["project"])
    agy_session(env, "long", [
        step(iso(9), [("run_command", {"CommandLine": "early", "Cwd": here})], status="ERROR"),   # before the watermark
        step(iso(13), [("run_command", {"CommandLine": "late"})], status="ERROR")])                # no path of its own
    s = as_json(env)["hosts"]["agy"]["sessions"][0]
    assert s["tool_calls"] == 1 and s["errors"] == 1 and s["start"] == "2026-10-13T13:00:00Z"
    assert s["failing"] == [{"tool": "run_command", "target": "late"}]


def test_since_filter_counts_only_later_records_and_drops_quiet_sessions(env):
    write(env["cdir"] / "mixed.jsonl", [
        use("e1", "Bash", {"command": "early"}, iso(8)), result("e1", True, iso(8, 1)),
        use("l1", "Bash", {"command": "late"}, iso(13)), result("l1", True, iso(13, 1))])
    write(env["cdir"] / "old.jsonl", [use("o", "Bash", {"command": "old"}, iso(7)), result("o", True, iso(7, 1))])
    write(env["cdir"] / "stale-mtime-only.jsonl", [use("m", "Bash", {"command": "m"}, iso(7)), result("m", True, iso(7, 1))],
          mtime=datetime.datetime(2026, 10, 14, tzinfo=UTC).timestamp())  # touched later, but no live record
    out = run(env)
    assert "claude: 1 sessions · 1 tool calls · 1 errors" in out and "mixed 2026-10-13T13:00:00Z calls=1 errors=1" in out
    assert "early" not in out and "old" not in out.replace("old.jsonl", "") and "stale-mtime-only" not in out
    assert "[NIGHTLY-SCAN since 2026-10-13T12:00:00Z" in out


def test_default_since_is_last_run_from_state_else_24_hours(env):
    now = datetime.datetime.now(UTC)
    ago = lambda h: (now - datetime.timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M:%SZ")
    write(env["cdir"] / "recent.jsonl", [use("a", "Bash", {"command": "r"}, ago(1))], mtime=now.timestamp())
    write(env["cdir"] / "midday.jsonl", [use("b", "Bash", {"command": "m"}, ago(3))], mtime=now.timestamp())
    write(env["cdir"] / "ancient.jsonl", [use("c", "Bash", {"command": "o"}, ago(30))], mtime=now.timestamp())

    ids = lambda: {s["id"] for s in as_json(env, since=None)["hosts"]["claude"]["sessions"]}
    assert ids() == {"recent", "midday"}  # no state file: the last 24 hours

    state = env["project"] / "docs" / "nightly" / ".last-run.json"
    state.parent.mkdir(parents=True)
    state.write_text(json.dumps({"last_run": ago(2)}), encoding="utf-8")
    assert ids() == {"recent"}  # last_run read through nightly_state (read-only)
    assert as_json(env, since=None)["since"] == ago(2)

    state.write_text("not json", encoding="utf-8")
    assert ids() == {"recent", "midday"}  # malformed state: fall back to 24 hours
    state.write_text(json.dumps({"last_run": "garbage"}), encoding="utf-8")
    assert ids() == {"recent", "midday"}
    before = state.read_bytes()
    run(env, since=None)
    assert state.read_bytes() == before  # the scan never writes the state


def test_since_flag_wins_over_state_and_a_bad_value_is_refused(env):
    state = env["project"] / "docs" / "nightly" / ".last-run.json"
    state.parent.mkdir(parents=True)
    state.write_text(json.dumps({"last_run": "2020-01-01T00:00:00Z"}), encoding="utf-8")
    assert as_json(env)["since"] == "2026-10-13T12:00:00Z"
    bad = subprocess.run([sys.executable, str(SCRIPT), "--since", "yesterday-ish"], capture_output=True, text=True)
    assert bad.returncode == 2 and "ISO 8601" in bad.stderr


def test_failing_target_is_one_line_cut_at_120_chars(env):
    long_cmd = "echo\tstart\n" + "x" * 300 + "\nend"
    write(env["cdir"] / "s.jsonl", [use("u", "Bash", {"command": long_cmd}, iso(13)), result("u", True, iso(13, 1))])
    target = as_json(env)["hosts"]["claude"]["sessions"][0]["failing"][0]["target"]
    assert len(target) == 120 and target.endswith("…") and "\n" not in target and "\t" not in target
    assert target.startswith("echo start xxx")
    short = "z" * 120
    write(env["cdir"] / "s.jsonl", [use("u", "Bash", {"command": short}, iso(13)), result("u", True, iso(13, 1))])
    assert as_json(env)["hosts"]["claude"]["sessions"][0]["failing"][0]["target"] == short  # exactly 120: untouched


def test_secret_looking_values_in_a_failing_command_are_masked(env):
    cmd = 'curl -H "Authorization: Bearer abc123SECRET" x; GITHUB_TOKEN=ghp_abcdefghijkl98 gh api; export API_KEY=zzz999'
    write(env["cdir"] / "s.jsonl", [use("u", "Bash", {"command": cmd}, iso(13)), result("u", True, iso(13, 1))])
    out = run(env)
    assert "abc123SECRET" not in out and "ghp_abcdefghijkl98" not in out and "zzz999" not in out and "***" in out


def test_only_allowed_fields_reach_the_output_in_both_modes(env):
    here = str(env["project"])
    write(env["cdir"] / "c.jsonl", [use("u", "Bash", {"command": "boom", "description": "SENTINEL_DESC"}, iso(13)),
                                    result("u", True, iso(13, 1))])
    agy_session(env, "g", [dict(step(iso(13), [("run_command", {"CommandLine": "boom2", "Cwd": here, "Blob": "SENTINEL_BLOB"})],
                                     status="ERROR"), content="SENTINEL_CONTENT", error="SENTINEL_ERR")])
    text, js = run(env), run(env, "--json")
    assert "SENTINEL" not in text and "SENTINEL" not in js
    for line in text.splitlines():  # nothing but the documented line shapes
        assert re.match(r"^(\[NIGHTLY-SCAN since \S+ · project .+\]|(claude|agy): \d+ sessions · \d+ tool calls · \d+ errors( · \d+ subagent transcripts)?"
                        r"|  (sub )?\S+ \S+ calls=\d+ errors=\d+ repeats=\d+|    ! \S+(  .*)?|skipped: \d+ unparsable/unknown records)$", line), line
    data = json.loads(js)
    assert set(data) == {"since", "project", "skipped", "hosts"} and set(data["hosts"]) == {"claude", "agy"}
    assert set(data["hosts"]["claude"]["sessions"][0]) == {"id", "sub", "start", "tool_calls", "errors", "repeats", "failing"}


def test_unparsable_and_unknown_records_are_counted_not_fatal(env):
    here = str(env["project"])
    write(env["cdir"] / "c.jsonl", [use("u", "Bash", {"command": "a"}, iso(13)), [1, 2], {"no_type": True},
                                    {"type": "assistant", "timestamp": iso(13, 1),
                                     "message": {"content": [{"type": "tool_use", "id": 5, "name": None}]}}],
          raw=["{not json", ""], mtime=datetime.datetime(2026, 10, 13, 13, tzinfo=UTC).timestamp())
    agy_session(env, "g", [step(iso(13), [("run_command", {"CommandLine": "x", "Cwd": here})]), {"hello": "world"}],
                raw=["<<<garbage>>>"], mtime=datetime.datetime(2026, 10, 13, 13, tzinfo=UTC).timestamp())
    out = run(env)
    assert "skipped: 6 unparsable/unknown records" in out  # claude: list, no-type, bad tool_use, bad json; agy: no-keys, bad json
    assert "claude: 1 sessions · 1 tool calls" in out and "agy: 1 sessions · 1 tool calls" in out


def test_missing_transcript_roots_are_reported_and_a_clean_scan_prints_zero_skipped(env):
    out = run(env)
    assert "claude: transcript root not found" in out and "agy: transcript root not found" in out
    assert out.rstrip().endswith("skipped: 0 unparsable/unknown records")
    assert json.loads(run(env, "--json"))["hosts"] == {"claude": None, "agy": None}


def test_long_failing_lists_are_capped_in_text_but_complete_in_json(env):
    recs = []
    for i in range(11):
        recs += [use(f"u{i}", "Bash", {"command": f"bad{i}"}, iso(13, i)), result(f"u{i}", True, iso(13, i, ) )]
    write(env["cdir"] / "s.jsonl", recs)
    out = run(env)
    assert out.count("    ! Bash") == 8 and "… +3 more failing calls" in out
    assert len(as_json(env)["hosts"]["claude"]["sessions"][0]["failing"]) == 11


def test_repeats_count_calls_whose_tool_and_target_already_appeared_in_the_session(env):
    here = str(env["project"])
    write(env["cdir"] / "s.jsonl", [
        use("a0", "Bash", {"command": "ls"}, iso(9)),  # before the watermark: seen, not counted
        use("a1", "Read", {"file_path": "x.md"}, iso(13)), use("a2", "Read", {"file_path": "x.md"}, iso(13, 1)),
        use("a3", "Read", {"file_path": "x.md"}, iso(13, 2)), use("a4", "Read", {"file_path": "y.md"}, iso(13, 3)),
        use("a5", "Bash", {"command": "ls"}, iso(13, 4)),
        use("a6", "mcp__s__t", {"k": 1}, iso(13, 5)), use("a7", "mcp__s__t", {"k": 1}, iso(13, 6)),  # no target: cannot tell
        use("a8", "Grep", {"pattern": "x.md"}, iso(13, 7))])  # same text, different tool
    s = as_json(env)["hosts"]["claude"]["sessions"][0]
    assert s["tool_calls"] == 8 and s["repeats"] == 3  # Read x.md twice more, Bash ls once more
    agy_session(env, "g", [step(iso(13), [("run_command", {"CommandLine": "npm test", "Cwd": here})]),
                           step(iso(13, 1), [("run_command", {"CommandLine": "npm test", "Cwd": here}),
                                             ("view_file", {"AbsolutePath": here + os.sep + "a"})])])
    assert as_json(env)["hosts"]["agy"]["sessions"][0]["repeats"] == 1
    assert "calls=8 errors=0 repeats=3" in run(env)


def test_claude_subagent_transcripts_are_scanned_and_attributed_to_their_session(env):
    uuid = "sess1"
    write(env["cdir"] / f"{uuid}.jsonl", [use("u", "Bash", {"command": "main"}, iso(13)), result("u", False, iso(13, 1))])
    sub = env["cdir"] / uuid / "subagents"
    write(sub / "a1.jsonl", [use("s1", "Bash", {"command": "sub boom"}, iso(13, 2)), result("s1", True, iso(13, 3)),
                                   use("s2", "Bash", {"command": "sub boom"}, iso(13, 4))])
    write(sub / "old.jsonl", [use("o", "Bash", {"command": "old"}, iso(7)), result("o", True, iso(7, 1))])
    write(env["cdir"] / uuid / "tool-results" / "d.jsonl", [use("t", "Bash", {"command": "NOT_A_TRANSCRIPT"}, iso(13))])
    write(env["cdir"] / "orph" / "subagents" / "b2.jsonl", [use("p", "Read", {"file_path": "o.md"}, iso(14))])
    out = run(env)
    assert "claude: 1 sessions · 4 tool calls · 1 errors · 2 subagent transcripts" in out  # subs are not sessions
    assert f"  sub {uuid}/a1 2026-10-13T13:02:00Z calls=2 errors=1 repeats=1" in out
    assert f"  {uuid} 2026-10-13T13:00:00Z calls=1 errors=0 repeats=0" in out and "  sub orph/b2 " in out
    assert "    ! Bash  sub boom" in out and "NOT_A_TRANSCRIPT" not in out and "old" not in out
    data = {s["id"]: s for s in as_json(env)["hosts"]["claude"]["sessions"]}
    assert data[f"{uuid}/a1"]["sub"] is True and data[uuid]["sub"] is False and len(data) == 4 - 1


def test_a_record_without_any_timestamp_is_not_counted(env):
    undated = use("u", "Bash", {"command": "x"}, iso(13))
    del undated["timestamp"]
    write(env["cdir"] / "s.jsonl", [undated, use("v", "Bash", {"command": "y"}, iso(13))], mtime=datetime.datetime(2026, 10, 14, tzinfo=UTC).timestamp())
    assert as_json(env)["hosts"]["claude"]["sessions"][0]["tool_calls"] == 1


def test_jwts_and_flag_style_secrets_are_masked_too(env):
    jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0In0.c2lnbmF0dXJl"
    cmd = f"curl {jwt}; tool --token abc111 --password=hunter22 --api-key k9999 --db-password p8888 --name keep"
    write(env["cdir"] / "s.jsonl", [use("u", "Bash", {"command": cmd}, iso(13)), result("u", True, iso(13, 1))])
    out = run(env)
    for leaked in (jwt, "eyJhbGci", "abc111", "hunter22", "k9999", "p8888"):
        assert leaked not in out, leaked
    assert "--name keep" in out and "--token=***" in out


def test_the_scan_is_wired_like_nightly_state():
    scaffold = (REPO_ROOT / "src" / "scripts" / "scaffold.py").read_text(encoding="utf-8")
    assert '"nightly_scan.py"' in scaffold
    verify = (REPO_ROOT / "tests" / "runners" / "verify_scripts.py").read_text(encoding="utf-8")
    assert 'rel_str == "scripts/nightly_scan.py"' in verify and '".agents/scripts/nightly_scan.py"' in verify
