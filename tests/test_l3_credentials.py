"""L3 - the harness's own credential store.

Observed on 2026-09-16, and the reason this exists: a smoke run refreshed the token
it had been lent, the provider ROTATED the refresh token, the new one was written
into the temp HOME and deleted at teardown - and the copy still sitting in the real
`~/.claude` was superseded. The next run got "OAuth session expired and could not be
refreshed", after which the CLI blanked its copy. One run silently invalidated the
developer's own CLI login.

Nothing here touches a real credential: every test builds its own file.
"""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

HARNESS = Path(__file__).parent / "lifecycle-harness"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


e = _load("l3_env_creds", HARNESS / "env.py")


def creds(path: Path, access="tok-access", refresh="tok-refresh"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"claudeAiOauth": {
        "accessToken": access, "refreshToken": refresh,
        "expiresAt": 1789595606732}}), encoding="utf-8")
    return path


def blanked(path: Path):
    """What the CLI leaves behind when a refresh fails: the shape, none of the
    substance. Storing this would turn one bad run into every later run."""
    return creds(path, access="", refresh="")


# --- which credential a run is given -----------------------------------------

def test_the_harness_store_wins_over_the_developers(tmp_path):
    store = creds(tmp_path / "store" / ".credentials.json")
    home = tmp_path / "home"
    creds(home / ".claude" / ".credentials.json")
    assert e.credentials_source(home, store) == store


def test_the_developers_file_bootstraps_an_empty_store(tmp_path):
    """Read once, to get started. Never written to."""
    store = tmp_path / "store" / ".credentials.json"
    home = tmp_path / "home"
    theirs = creds(home / ".claude" / ".credentials.json")
    assert e.credentials_source(home, store) == theirs


def test_a_blanked_store_falls_through_to_the_developers(tmp_path):
    store = blanked(tmp_path / "store" / ".credentials.json")
    home = tmp_path / "home"
    theirs = creds(home / ".claude" / ".credentials.json")
    assert e.credentials_source(home, store) == theirs


def test_no_usable_credential_anywhere_is_reported_not_guessed(tmp_path):
    assert e.credentials_source(tmp_path / "home",
                                tmp_path / "store" / ".credentials.json") is None


def test_a_file_that_is_not_json_is_not_a_credential(tmp_path):
    store = tmp_path / "store" / ".credentials.json"
    store.parent.mkdir(parents=True)
    store.write_text("<html>sign in</html>", encoding="utf-8")
    assert e.credentials_source(tmp_path / "home", store) is None


def test_seeding_puts_it_where_the_cli_looks(tmp_path):
    store = creds(tmp_path / "store" / ".credentials.json")
    temp_home = tmp_path / "temp-home"
    temp_home.mkdir()
    e._seed_credentials(tmp_path / "real-home", temp_home, store)
    assert (temp_home / ".claude" / ".credentials.json").exists()


# --- keeping the rotation -----------------------------------------------------

def test_a_refreshed_token_is_preserved_for_the_next_run(tmp_path):
    temp_home = tmp_path / "temp-home"
    creds(temp_home / ".claude" / ".credentials.json", access="rotated-access",
          refresh="rotated-refresh")
    store = tmp_path / "store" / ".credentials.json"

    assert e.preserve_credentials(temp_home, store) is True
    kept = json.loads(store.read_text(encoding="utf-8"))["claudeAiOauth"]
    assert kept["refreshToken"] == "rotated-refresh"


def test_a_blanked_credential_never_overwrites_a_good_one(tmp_path):
    """The exact failure that made this necessary: the CLI blanks the file when a
    refresh fails, and storing that would poison every later run."""
    temp_home = tmp_path / "temp-home"
    blanked(temp_home / ".claude" / ".credentials.json")
    store = creds(tmp_path / "store" / ".credentials.json", refresh="still-good")

    assert e.preserve_credentials(temp_home, store) is False
    assert json.loads(store.read_text(encoding="utf-8")
                      )["claudeAiOauth"]["refreshToken"] == "still-good"


def test_a_credential_that_was_only_seeded_is_not_preserved(tmp_path):
    """Preserving what was merely handed to the run would copy the developer's
    credential into the store whether or not it still worked - and a store holding
    a known-stale token is worse than an empty one, because it hides that nothing
    was ever refreshed. Observed: an --env-only run did exactly this."""
    temp_home = tmp_path / "temp-home"
    fresh = creds(temp_home / ".claude" / ".credentials.json")
    store = tmp_path / "store" / ".credentials.json"

    assert e.preserve_credentials(temp_home, store, seeded=e.digest(fresh)) is False
    assert not store.exists()


def test_a_changed_credential_is_preserved_even_with_a_seed_recorded(tmp_path):
    temp_home = tmp_path / "temp-home"
    seeded = e.digest(creds(temp_home / ".claude" / ".credentials.json"))
    creds(temp_home / ".claude" / ".credentials.json", refresh="rotated")
    store = tmp_path / "store" / ".credentials.json"

    assert e.preserve_credentials(temp_home, store, seeded=seeded) is True


def test_nothing_to_preserve_is_not_an_error(tmp_path):
    assert e.preserve_credentials(tmp_path / "empty-home",
                                  tmp_path / "store" / ".credentials.json") is False


def test_the_store_is_never_inside_the_developers_claude_directory():
    """E1 watches `~/.claude`. The harness's own credential lives outside it, so
    preserving a rotation is not a write into the path the run must not touch."""
    assert Path.home() / ".claude" not in e.HARNESS_STORE.parents


def test_the_store_sits_where_the_cli_writes_it():
    """`$HOME/.claude/.credentials.json`, under the harness's own HOME. A bare file
    beside that HOME made a successful `--login` read as a failed one: the CLI had
    written exactly where it should, and the harness looked one directory up."""
    assert e.HARNESS_STORE == e.HARNESS_HOME / ".claude" / ".credentials.json"


def test_preserving_writes_only_to_the_store(tmp_path):
    temp_home = tmp_path / "temp-home"
    creds(temp_home / ".claude" / ".credentials.json", refresh="rotated")
    real_home = tmp_path / "real-home"
    theirs = creds(real_home / ".claude" / ".credentials.json", refresh="untouched")
    store = tmp_path / "store" / ".credentials.json"

    e.preserve_credentials(temp_home, store)
    assert json.loads(theirs.read_text(encoding="utf-8")
                      )["claudeAiOauth"]["refreshToken"] == "untouched"


# --- failing fast rather than mid-phase ---------------------------------------

def test_a_run_with_no_credential_refuses_before_building_anything(monkeypatch,
                                                                   capsys, tmp_path):
    r = _load("l3_run_creds", HARNESS / "run-L3.py")
    monkeypatch.setattr(r.env_mod, "credentials_source", lambda *a, **kw: None)
    assert r.preflight_credentials(["0a"]) == 2
    out = capsys.readouterr().out
    assert "--login" in out
    assert "ROTATES" in out


def test_env_only_needs_no_credential(monkeypatch):
    r = _load("l3_run_creds2", HARNESS / "run-L3.py")
    monkeypatch.setattr(r.env_mod, "credentials_source", lambda *a, **kw: None)
    assert r.preflight_credentials([]) is None


# --- a rotation must survive a run that is stopped from outside ---------------

class _Env:
    def __init__(self, home, digest=None):
        self.home = home
        self.credential_digest = digest


def test_a_rotation_is_written_the_moment_it_happens(tmp_path):
    """Teardown is not a promise anyone can keep: SIGKILL cannot be caught, and a
    run stopped by a task runner never reaches its `finally`. Two runs were stopped
    mid-flight here; each had rotated its token and took the rotation with it, and
    the next run could not authenticate at all."""
    home = tmp_path / "home"
    seeded = e.digest(creds(home / ".claude" / ".credentials.json"))
    env = _Env(home, digest=seeded)
    store = tmp_path / "store" / ".credentials.json"

    # nothing refreshed yet
    assert e.checkpoint_credentials(env, store) is False

    creds(home / ".claude" / ".credentials.json", refresh="rotated-once")
    assert e.checkpoint_credentials(env, store) is True
    assert json.loads(store.read_text(encoding="utf-8")
                      )["claudeAiOauth"]["refreshToken"] == "rotated-once"

    # a second checkpoint with no further change is a no-op
    assert e.checkpoint_credentials(env, store) is False


def test_each_rotation_replaces_the_last(tmp_path):
    """A phase can rotate more than once across a chain; the store keeps the newest."""
    home = tmp_path / "home"
    creds(home / ".claude" / ".credentials.json")
    env = _Env(home)
    store = tmp_path / "store" / ".credentials.json"
    for token in ("first", "second", "third"):
        creds(home / ".claude" / ".credentials.json", refresh=token)
        assert e.checkpoint_credentials(env, store) is True
    assert json.loads(store.read_text(encoding="utf-8")
                      )["claudeAiOauth"]["refreshToken"] == "third"


def test_a_blanked_credential_is_never_checkpointed(tmp_path):
    home = tmp_path / "home"
    blanked(home / ".claude" / ".credentials.json")
    store = creds(tmp_path / "store" / ".credentials.json", refresh="still-good")
    assert e.checkpoint_credentials(_Env(home), store) is False
    assert json.loads(store.read_text(encoding="utf-8")
                      )["claudeAiOauth"]["refreshToken"] == "still-good"


def test_checkpointing_with_no_environment_is_not_an_error(tmp_path):
    """The signal handler may fire before the environment exists."""
    assert e.checkpoint_credentials(None, tmp_path / "store.json") is False
