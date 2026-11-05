"""Same probe against the pre-fix keydown handler (HEAD template body spliced back in), to show the RED state."""
import subprocess
from pathlib import Path

wt = Path(r"C:\Users\patri\Dev\Stratosphere-OS\.claude\worktrees\bt221")
new = Path(r"C:\t\v5board\repo\.tmp\render\keyprobe.html").read_text(encoding="utf-8")
head_tpl = subprocess.run(["git", "show", "HEAD:src/skills/plan-html/assets/templates/board.html"], cwd=wt, capture_output=True,
                          text=True, encoding="utf-8").stdout
cur_tpl = (wt / "src/skills/plan-html/assets/templates/board.html").read_text(encoding="utf-8")


def handler(t):
    a = t.index("  document.addEventListener('keydown'")
    b = t.index("// The payload box holds exactly")
    return t[a:b]


assert handler(cur_tpl) in new
old = new.replace(handler(cur_tpl), handler(head_tpl))
Path(r"C:\t\v5board\repo\.tmp\render\keyprobe_old.html").write_text(old, encoding="utf-8")
print("ok")
