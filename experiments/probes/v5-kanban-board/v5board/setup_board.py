"""Throwaway local-tracker repo with hostile titles for the real-browser board check."""
import json
import subprocess
import sys
from pathlib import Path

WT = Path(r"C:\Users\patri\Dev\Stratosphere-OS\.claude\worktrees\bt221")
ISSUES = str(WT / "src" / "scripts" / "issues.py")
DIR = Path(__file__).resolve().parent
ROOT = DIR / "repo"
ENV = {"TMP": str(DIR.parents[3] / ".tmp"), "TEMP": str(DIR.parents[3] / ".tmp"), "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
       "GIT_COMMITTER_EMAIL": "t@t", "PATH": __import__("os").environ["PATH"], "SYSTEMROOT": __import__("os").environ.get("SYSTEMROOT", "")}


def run(*cmd, **kw):
    r = subprocess.run(cmd, cwd=ROOT, env=ENV, capture_output=True, text=True, encoding="utf-8", **kw)
    if r.returncode:
        sys.exit(f"FAIL {cmd}: {r.stdout}{r.stderr}")
    return r.stdout.strip()


if ROOT.exists():
    sys.exit("repo exists; delete repo first")
ROOT.mkdir(parents=True)
run("git", "init", "-q", "-b", "main")
(ROOT / ".memory").mkdir()
(ROOT / ".memory" / "ARCHITECTURE.md").write_text('---\ntype: architecture\ntracker: local\nversion: "1.0.0"\n---\n# A\n', encoding="utf-8")
(ROOT / ".gitignore").write_text(".tmp/\n", encoding="utf-8")
run("git", "add", "-A")
run("git", "commit", "-q", "-m", "init")
run("python", ISSUES, "init")

TITLES = [
    ("plain", "Plain card"),
    ("backslash", "Path C:\\new\\table and \\n literal"),
    ("script", "</script><img src=x onerror=\"document.title='PWNED'\">"),
    ("quotes", "Quote ' and \" and `tick`"),
    ("amp", "Fish & chips <b>bold</b> &lt;x&gt;"),
    ("hyphen", "Pre-fetch -> cache -> serve"),
    ("sep", "Line\u2028sep\u2029here"),
]
BODY = ROOT.parent / "body.md"
BODY.write_text("body" + chr(10), encoding="utf-8")
ids = {}
for key, title in TITLES:
    out = run("python", ISSUES, "create", "--title", title, "--label", "type:feature,tier:slice,size:small,mode:AFK,priority:high",
              "--status", "planned", "--body-file", str(BODY))
    ids[key] = out.strip().splitlines()[-1]
lab = run("python", ISSUES, "create", "--title", "Label with apostrophe", "--label", "type:feature,tier:slice,size:small,mode:AFK",
          "--status", "planned", "--body-file", str(BODY))
ids["lab"] = lab.strip().splitlines()[-1]
(ROOT / "ids.json").write_text(json.dumps(ids, indent=1), encoding="utf-8")
print(json.dumps(ids, indent=1))
print(run("python", ISSUES, "board", "--web", "--out", ".tmp/render/board.html"))
