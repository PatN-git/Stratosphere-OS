"""BT-163: `nightly_state.py` is the only writer of docs/nightly/.last-run.json.

Seam: the CLI (stdout + the JSON it writes) against a throwaway state file.
"""
import json
import subprocess
import sys

import pytest

from conftest import REPO_ROOT

SCRIPT = REPO_ROOT / "src" / "scripts" / "nightly_state.py"


@pytest.fixture
def state(tmp_path):
    return tmp_path / "docs" / "nightly" / ".last-run.json"


def run(state, *args, date="2026-10-13", stdin=None):
    return subprocess.run([sys.executable, str(SCRIPT), "--state", str(state), "--date", date, *args],
                          capture_output=True, text=True, input=stdin)


def read(state):
    return json.loads(state.read_text(encoding="utf-8"))


def test_missing_file_is_empty_history_and_first_sighting_is_night_one(state):
    assert run(state, "slugs").stdout == ""
    out = run(state, "findings", "--slugs", "shell-quoting,stale-path")
    assert out.returncode == 0 and out.stdout.splitlines() == ["shell-quoting nights=1", "stale-path nights=1"]
    assert read(state)["findings"]["stale-path"] == {"first": "2026-10-13", "last": "2026-10-13", "nights": 1}
    assert "last_run" not in read(state)  # not stamped yet


def test_old_last_run_only_format_reads_as_empty_history_and_keeps_last_run(state):
    state.parent.mkdir(parents=True)
    state.write_text(json.dumps({"last_run": "2026-10-09T08:00:00+00:00"}), encoding="utf-8")
    assert run(state, "slugs").stdout == ""
    run(state, "findings", "--slugs", "file-reread")
    data = read(state)
    assert data["last_run"] == "2026-10-09T08:00:00+00:00"
    assert data["findings"]["file-reread"]["nights"] == 1 and data["drift"] == {}


def test_malformed_or_bom_state_does_not_crash(state):
    state.parent.mkdir(parents=True)
    state.write_bytes(b"\xef\xbb\xbf" + json.dumps({"last_run": "x", "findings": "bad", "drift": [1]}).encode())
    assert run(state, "findings", "--slugs", "a").returncode == 0
    state.write_text("not json", encoding="utf-8")
    assert run(state, "findings", "--slugs", "a").returncode == 0


def test_a_later_night_increments_and_the_same_night_does_not(state):
    run(state, "findings", "--slugs", "shell-quoting", date="2026-10-09")
    assert run(state, "findings", "--slugs", "shell-quoting", date="2026-10-09").stdout.strip() == "shell-quoting nights=1"
    assert run(state, "findings", "--slugs", "shell-quoting").stdout.strip() == "shell-quoting nights=2"
    assert run(state, "findings", "--slugs", "shell-quoting").stdout.strip() == "shell-quoting nights=2"
    assert read(state)["findings"]["shell-quoting"] == {"first": "2026-10-09", "last": "2026-10-13", "nights": 2}
    assert run(state, "slugs").stdout.split() == ["shell-quoting"]


def test_findings_unseen_for_90_days_are_pruned_on_the_next_write(state):
    run(state, "findings", "--slugs", "old,recent", date="2026-07-01")
    run(state, "findings", "--slugs", "recent", date="2026-09-20")
    run(state, "stamp", "--now", "2026-10-13T01:00:00+00:00")  # 104 days after `old`, 23 after `recent`
    assert set(read(state)["findings"]) == {"recent"}


def test_drift_keys_unseen_tonight_are_dropped_and_ages_accumulate(state):
    keys = "BT-215|blocked_by\nBT-216|labels\n"
    out = run(state, "drift", "--keys-file", "-", date="2026-10-09", stdin=keys)
    assert out.returncode == 0 and "2 keys · 0 dropped" in out.stdout
    run(state, "drift", "--keys-file", "-", date="2026-10-13", stdin="BT-215|blocked_by\nBT-300|status\n")
    drift = read(state)["drift"]
    assert set(drift) == {"BT-215|blocked_by", "BT-300|status"}
    assert drift["BT-215|blocked_by"] == {"first": "2026-10-09", "last": "2026-10-13", "nights": 2}
    assert drift["BT-300|status"]["nights"] == 1


def test_drift_is_idempotent_within_a_night_and_reads_a_keys_file(state, tmp_path):
    f = tmp_path / "keys.txt"
    f.write_text("BT-1|labels\n\nBT-1|labels\n", encoding="utf-8")  # blank lines and duplicates ignored
    for _ in range(2):
        assert run(state, "drift", "--keys-file", str(f)).returncode == 0
    assert read(state)["drift"]["BT-1|labels"]["nights"] == 1
    f.write_text("", encoding="utf-8")
    assert "0 keys · 1 dropped" in run(state, "drift", "--keys-file", str(f)).stdout
    assert read(state)["drift"] == {}


def test_stamp_sets_last_run_and_keeps_findings_and_drift(state):
    run(state, "findings", "--slugs", "a")
    run(state, "drift", "--keys-file", "-", stdin="BT-1|labels\n")
    run(state, "stamp", "--now", "2026-10-13T22:00:00+02:00")
    data = read(state)
    assert data["last_run"] == "2026-10-13T22:00:00+02:00"
    assert "a" in data["findings"] and "BT-1|labels" in data["drift"]
    assert set(data) == {"last_run", "findings", "drift"}  # no sessions_reviewed or other keys


def test_written_json_has_no_bom_and_lf_endings(state):
    run(state, "findings", "--slugs", "a")
    raw = state.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf") and b"\r" not in raw and raw.endswith(b"\n")


def test_bad_slug_or_key_is_refused_without_writing(state):
    assert run(state, "findings", "--slugs", "Bad Slug").returncode == 2
    assert run(state, "drift", "--keys-file", "-", stdin="no-pipe-here\n").returncode == 2
    assert run(state, "findings", "--slugs", "a", date="13-10-2026").returncode == 2
    assert not state.exists()


def test_a_leftover_tmp_file_never_corrupts_state_and_is_replaced(state):
    run(state, "findings", "--slugs", "a")
    state.with_name(state.name + ".tmp").write_text("{half", encoding="utf-8")  # crashed earlier write
    assert run(state, "slugs").stdout.split() == ["a"]
    assert run(state, "findings", "--slugs", "b").returncode == 0
    assert set(read(state)["findings"]) == {"a", "b"}
    assert not state.with_name(state.name + ".tmp").exists()


def test_state_and_date_flags_work_after_the_command_too(state):
    out = subprocess.run([sys.executable, str(SCRIPT), "findings", "--slugs", "a", "--state", str(state),
                          "--date", "2026-09-01"], capture_output=True, text=True)
    assert out.returncode == 0 and read(state)["findings"]["a"]["first"] == "2026-09-01"
    # a flag given before the command is not overridden by the subparser default
    assert run(state, "findings", "--slugs", "a").stdout.strip() == "a nights=2"


def test_keys_with_extra_pipes_are_refused(state):
    assert run(state, "drift", "--keys-file", "-", stdin="a|b|c\n").returncode == 2
    assert run(state, "drift", "--keys-file", "-", stdin="|kind\n").returncode == 2
    assert not state.exists()


def test_reconcile_gate_runs_without_nightly_state(tmp_path):
    # reconcile.py is every workflow's terminal gate; only --summary may need nightly_state.py.
    import shutil
    shutil.copy(REPO_ROOT / "src" / "scripts" / "reconcile.py", tmp_path / "reconcile.py")
    r = subprocess.run([sys.executable, str(tmp_path / "reconcile.py"), "--help"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
