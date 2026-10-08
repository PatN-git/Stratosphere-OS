"""A fresh scaffold must pass its own memory lint (exit 0): the change that moved the
memory templates to OKF v0.2 `generated:` relies on it, and only the live L3 harness
asserted it before. Uses the committed dist bundle (drift-guarded by build-guard).
"""
import subprocess
import sys

from conftest import REPO_ROOT

PLUGIN = REPO_ROOT / "dist" / "skills" / "stratosphere-setup"


def test_fresh_scaffold_is_lint_clean(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    r = subprocess.run([sys.executable, str(PLUGIN / "scripts" / "scaffold.py")], cwd=tmp_path,
                       capture_output=True)
    assert r.returncode == 0, r.stdout.decode("utf-8", "replace")[-500:]
    v = subprocess.run([sys.executable, str(tmp_path / ".agents" / "scripts" / "validate_memory.py"),
                        "--path", ".memory"], cwd=tmp_path, capture_output=True)
    out = v.stdout.decode("utf-8", "replace")
    assert v.returncode == 0, out[-800:]


def test_rescaffold_treats_a_crlf_checkout_as_unchanged(tmp_path):
    """BT-154 F4: a CRLF checkout (core.autocrlf=true) of a placed managed file is not STALE."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    scaffold = [sys.executable, str(PLUGIN / "scripts" / "scaffold.py")]
    assert subprocess.run(scaffold, cwd=tmp_path, capture_output=True).returncode == 0
    rule = tmp_path / ".agents" / "rules" / "output-mode.md"
    rule.write_bytes(rule.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    out = subprocess.run(scaffold, cwd=tmp_path, capture_output=True).stdout.decode("utf-8", "replace")
    assert "STALE" not in out, out[-800:]
