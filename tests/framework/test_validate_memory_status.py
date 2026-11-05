"""BT-218: STATUS.md is folder state only, so validate_memory.py warns when it outgrows its
budget or is tracked by git, and does not lint the per-task resume files under `.memory/resume/`.
Both STATUS checks are warnings (exit 2), never errors."""
import subprocess
import sys

from conftest import REPO_ROOT

SCRIPT = REPO_ROOT / "src" / "scripts" / "validate_memory.py"
FM = "---\ntype: status\ntitle: Status\ngenerated:\n  by: test\n  at: 2026-10-27\nversion: \"2.0.0\"\n---\n"


def status(root, body="# STATUS\n"):
    p = root / ".memory" / "STATUS.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(FM + body, encoding="utf-8")
    return p


def git(root, *args):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


def run(root):
    r = subprocess.run([sys.executable, str(SCRIPT), "--path", ".memory"], cwd=root, capture_output=True)
    return r.returncode, r.stdout.decode("utf-8", errors="replace")


def test_status_over_budget_warns(tmp_path):
    status(tmp_path, "x" * 3100)
    code, out = run(tmp_path)
    assert code == 2, out
    assert "STATUS.md is" in out and "budget 3,000" in out, out


def test_status_within_budget_is_clean(tmp_path):
    status(tmp_path)
    code, out = run(tmp_path)
    assert code == 0, out


def test_tracked_status_warns_with_the_fix(tmp_path):
    status(tmp_path)
    git(tmp_path, "init", "-q")
    git(tmp_path, "add", ".memory/STATUS.md")
    code, out = run(tmp_path)
    assert code == 2, out
    assert "tracked by git" in out and "git rm --cached" in out, out


def test_ignored_status_is_clean(tmp_path):
    status(tmp_path)
    git(tmp_path, "init", "-q")
    (tmp_path / ".gitignore").write_text(".memory/STATUS.md\n", encoding="utf-8")
    git(tmp_path, "add", ".gitignore")
    code, out = run(tmp_path)
    assert code == 0, out


def test_resume_notes_are_not_okf_linted(tmp_path):
    status(tmp_path)
    note = tmp_path / ".memory" / "resume" / "BT-007.md"
    note.parent.mkdir(parents=True)
    note.write_text("<!-- stratos:resume -->\nBranch: x\nNext step: y\n", encoding="utf-8")
    code, out = run(tmp_path)
    assert code == 0, out


def test_scaffold_ignores_status_and_resume_notes(tmp_path):
    sys.path.insert(0, str(REPO_ROOT / "src" / "scripts"))
    import scaffold
    (tmp_path / ".gitignore").write_text(".tmp/\n", encoding="utf-8")
    scaffold.reconcile_gitignore(tmp_path, dry_run=False)
    lines = (tmp_path / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert ".memory/STATUS.md" in lines and ".memory/resume/" in lines, lines
