"""L3 model pinning - the harness must not inherit an ambient model setting.

~/.claude/settings.json here sets `model: opus[1m]`. Without an explicit --model
every call inherits it, including the proxy calls that only read a 4KB fixture -
and the result stops being reproducible on another machine or in CI.
"""
import importlib.util
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "lifecycle-harness" / "session.py"
_spec = importlib.util.spec_from_file_location("l3_session_models", _SRC)
s = importlib.util.module_from_spec(_spec)
sys.modules["l3_session_models"] = s
_spec.loader.exec_module(s)


def test_model_is_always_passed_explicitly():
    cmd = s.build_cmd("hi", model="sonnet")
    assert "--model" in cmd and cmd[cmd.index("--model") + 1] == "sonnet"


def test_no_model_means_no_flag():
    assert "--model" not in s.build_cmd("hi", model=None)


def test_resume_and_model_coexist():
    cmd = s.build_cmd("hi", model="opus", resume="abc-123")
    assert cmd[cmd.index("--resume") + 1] == "abc-123"
    assert cmd[cmd.index("--model") + 1] == "opus"


def test_roles_are_not_all_the_same_model():
    """The proxy is the most-called and simplest role; it must not default to the
    driver's model, or the cheapest calls become the most expensive ones."""
    assert s.PROXY_MODEL != s.DRIVER_MODEL
    assert s.AUDITOR_MODEL != s.DRIVER_MODEL


def test_prompt_and_permissions_survive_model_wiring():
    cmd = s.build_cmd("the prompt", model="haiku")
    assert cmd[cmd.index("-p") + 1] == "the prompt"
    assert "--dangerously-skip-permissions" in cmd
    assert "stream-json" in cmd
