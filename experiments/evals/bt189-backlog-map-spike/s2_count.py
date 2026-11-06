"""Count BACKLOG-related chars per src md file. Read-only. Prints a markdown table + JSON."""
import re, json, sys
from pathlib import Path

ROOT = Path(r"C:\Users\patri\Dev\Stratosphere-OS\src")
# core: explicit map / mirror mention
CORE = re.compile(r"BACKLOG|\bBacklog\b|Label Registry|LABEL REGISTRY|map row|MIRROR-|mirror (write|field|the|row)|BACKLOG row|Blocked by. column", re.I)
# gate: sync-gate / heal text that exists only because of the mirror
GATE = re.compile(r"reconcile\.py|terminal-sync-invariant|Terminal sync gate|\[HEALED|heal per", re.I)
SKIP_PARTS = {"plan-html", "arch-drift-report-template.md", "__pycache__", "okf_viewer", "test", "output", "dev-skills", "experimental"}


def sentences(line):
    # split at sentence end followed by space+capital/backtick/bold, keep bullets whole when short
    parts = re.split(r"(?<=[.;!?])\s+(?=[A-Z`*(\[])", line)
    return parts


def count(path, pat):
    n_sent = n_line = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if pat.search(line):
            n_line += len(line) + 1
            n_sent += sum(len(s) + 1 for s in sentences(line) if pat.search(s))
    return n_sent, n_line


rows = []
files = [p for p in ROOT.rglob("*.md") if not (set(p.relative_to(ROOT).parts) & SKIP_PARTS) and p.name not in SKIP_PARTS]
for p in sorted(files):
    rel = p.relative_to(ROOT).as_posix()
    cs, cl = count(p, CORE)
    both = re.compile(CORE.pattern + "|" + GATE.pattern, re.I)
    gs, gl = count(p, both)
    total = len(p.read_text(encoding="utf-8"))
    if gl or gs:
        rows.append(dict(file=rel, total=total, core_sent=cs, core_line=cl, gate_sent=gs - cs, all_sent=gs, all_line=gl))

out = Path(r"C:\Users\patri\Dev\Stratosphere-OS\.tmp\bt189\s2_counts.json")
out.write_text(json.dumps(rows, indent=1), encoding="utf-8")
print("| file | file chars | core sentences | core full lines | +gate sentences | total sentences |")
for r in rows:
    print(f"| {r['file']} | {r['total']} | {r['core_sent']} | {r['core_line']} | {r['gate_sent']} | {r['all_sent']} |")
for key in ("core_sent", "core_line", "gate_sent", "all_sent"):
    for grp in ("workflows/", "references/", "commands/", "skills/", "rules/", "constitution/", "memory-templates/"):
        print(key, grp, sum(r[key] for r in rows if r["file"].startswith(grp)))
    print(key, "TOTAL", sum(r[key] for r in rows))
