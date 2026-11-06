"""Drift of CleanTechHub's map at several git refs vs a generated GitHub map (read-only)."""
import subprocess, sys, tempfile, os
sys.path.insert(0, "src/scripts")
from reconcile import parse_backlog

CTH = r"C:/Users/patri/Dev/CleanTechHub"
gen = parse_backlog(".tmp/bt189/verify.cth.md")


def norm(r):
    return {
        "status": r["status"],
        "labels": {l for l in r["labels"] if not l.startswith("status:")},
        "milestone": str(r["milestone"]).strip(),
        "parent": str(r["parent"]).strip(),
        "blocked_by": r["blocked_by"],
    }


def load(ref):
    if ref == "WORKTREE":
        return parse_backlog(CTH + "/.memory/BACKLOG_MAP.md")
    text = subprocess.run(["git", "-C", CTH, "show", f"{ref}:.memory/BACKLOG_MAP.md"],
                          capture_output=True, text=True, encoding="utf-8").stdout
    fd, p = tempfile.mkstemp(suffix=".md", dir=".tmp/bt189")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    rows = parse_backlog(p)
    os.remove(p)
    return rows


for ref in ["WORKTREE", "HEAD", "origin/main"]:
    live = load(ref)
    both = [i for i in live if i in gen]
    cols, rows_bad, open_bad = {}, set(), set()
    for i in both:
        a, b = norm(live[i]), norm(gen[i])
        for c in a:
            if a[c] != b[c]:
                cols[c] = cols.get(c, 0) + 1
                rows_bad.add(i)
                if gen[i]["status"] != "done":
                    open_bad.add(i)
    print(f"{ref}: rows {len(live)}, only-gh {len(set(gen) - set(live))}, "
          f"differ {len(rows_bad)} (open {len(open_bad)}), per col {cols}")
