"""Scratch local-tracker repo for the real-mouse drag-and-drop check."""
import json, os, subprocess, sys
from pathlib import Path

WT = Path(r"C:\Users\patri\Dev\Stratosphere-OS\.claude\worktrees\bt221")
ISSUES = str(WT / "src" / "scripts" / "issues.py")
BASE = Path(r"C:\t\v5dnd")
ROOT = BASE / "repo"
ENV = {"TMP": r"C:\t", "TEMP": r"C:\t", "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
       "GIT_COMMITTER_EMAIL": "t@t", "PATH": os.environ["PATH"], "SYSTEMROOT": os.environ.get("SYSTEMROOT", "")}


def run(*cmd):
    r = subprocess.run(cmd, cwd=ROOT, env=ENV, capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        sys.exit(f"FAIL {cmd}: {r.stdout}{r.stderr}")
    return r.stdout.strip()


if ROOT.exists():
    sys.exit("repo exists; delete it first")
ROOT.mkdir(parents=True)
run("git", "init", "-q", "-b", "main")
(ROOT / ".memory").mkdir()
(ROOT / ".memory" / "ARCHITECTURE.md").write_text('---\ntype: architecture\ntracker: local\nversion: "1.0.0"\n---\n# A\n', encoding="utf-8")
(ROOT / ".gitignore").write_text(".tmp/\n", encoding="utf-8")
run("git", "add", "-A")
run("git", "commit", "-q", "-m", "init")
run("python", ISSUES, "init")
body = BASE / "body.md"
body.write_text("body\n", encoding="utf-8")
LAB = "type:feature,tier:slice,size:small,mode:AFK,priority:high"
ids = {}
specs = [
    ("plain", "Plain card", "planned", None),
    ("script", "</script><img src=x onerror=\"document.title='PWNED'\"> & <b>bold</b>", "planned", None),
    ("second", "Second card", "planned", None),
]
for key, title, st, blk in specs:
    cmd = ["python", ISSUES, "create", "--title", title, "--label", LAB, "--status", st, "--body-file", str(body)]
    ids[key] = run(*cmd).splitlines()[-1]
ids["gated"] = run("python", ISSUES, "create", "--title", "Gated card", "--label", LAB, "--status", "blocked",
                   "--blocked-by", ids["plain"], "--body-file", str(body)).splitlines()[-1]
(BASE / "ids.json").write_text(json.dumps(ids, indent=1), encoding="utf-8")
print(json.dumps(ids, indent=1))
print(run("python", ISSUES, "board", "--web", "--out", ".tmp/render/board.html"))
print(run("python", ISSUES, "board"))
