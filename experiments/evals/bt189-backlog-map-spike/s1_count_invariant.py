"""S1 helper: classify src/references/terminal-sync-invariant.md by sentence; apportion each physical line by character share."""
from pathlib import Path

SRC = Path(r"C:\Users\patri\Dev\Stratosphere-OS\src\references\terminal-sync-invariant.md")
M, G, S = "map-only", "gh-post-condition", "shared"
lines = SRC.read_text(encoding="utf-8").splitlines()

# line -> [(start-marker, class, label)]; markers cut the line in order, first segment starts at 0
SEG = {
    1: [("---", S, "frontmatter")], 2: [("description", S, "frontmatter")], 3: [("version", S, "frontmatter")],
    4: [("timestamp", S, "frontmatter")], 5: [("---", S, "frontmatter")],
    7: [("# Terminal", S, "title")],
    9: [("A workflow that writes", M, "dual-write must leave GH and map in agreement"),
        ("Completion bias makes", M, "trailing mirror write drops; corruption propagates"),
        ("The gate below is", S, "gate is a script exit code, not a checkbox")],
    11: [("## Gate", S, "heading")],
    12: [("At the end", S, "scope: ids touched")],
    14: [("```bash", S, "fence")], 15: [("python", S, "gate command")], 16: [("```", S, "fence")],
    18: [("- Non-zero exit", S, "halt, do not close/ship"),
         ("The output lists", M, "MIRROR-DRIFT map=x gh=y output")],
    19: [("- **Pass every id", S, "pass every id the phase wrote")],
    20: [("- `--fields`", M, "--fields subset of mirror fields")],
    21: [("- With `--fields status`", G, "closed == done (open on GitHub, map=done)")],
    22: [("- `--pr-id`", G, "PR-link comment with /pull/ URL"),
         ("A PR-link comment is", G, "full /pull/ URL, bare #n does not count")],
    24: [("## Heal", S, "heading")],
    25: [("For each", M, "upsert the missing write keyed by BT id"),
         ("**Never append**", M, "never append a row"),
         ("A stale blocker", G, "stale blocker: remove map cell AND GitHub removeBlockedBy edge"),
         ("Then **re-run", S, "re-run until exit 0"),
         ("Log each fix", M, "log [HEALED field BT-n]")],
    27: [("Batch heal", M, "--heal --source gh = map upsert for one kind"),
         ("When GitHub is the side", M, "--source map prints gh commands to match the map"),
         ("`open on GitHub, map=done`", G, "dropped gh issue close healed by gh issue close"),
         ("Manual kinds", M, "manual kinds heal by hand"),
         ("After a batch heal", M, "re-run once, no loop")],
    29: [("## Boundaries", S, "heading")],
    30: [("- **End-state", S, "end-state is the citing workflow's"),
         ("The gate asserts only", M, "gate asserts GH and BACKLOG agree"),
         ("Conditional transitions", S, "workflow decides conditional transitions; pass ids once writes done")],
    31: [("- **Offline", M, "offline: BACKLOG internal consistency only"),
         ("There is no GitHub", M, "offline is self-attested")],
    32: [("- **Never writes GitHub", S, "reconcile only reads GitHub"),
         ("`--heal` writes", M, "--heal writes the map only; GH fixes printed")],
    33: [("- **An edge is stale", G, "edge stale only when --edges says CLEAR"),
         ("A `[KEEP]` edge", G, "KEEP edge never removed"),
         ("a map missing", M, "map missing a KEEP edge = blocked_by drift")],
    34: [("- `/0d`", M, "0d nightly audit across all rows is advisory")],
}

tot = {M: 0.0, G: 0.0, S: 0.0}
cnt = {M: 0, G: 0, S: 0}
out = []
for ln, segs in SEG.items():
    text = lines[ln - 1]
    idx = [0] + [text.find(m) for m, _, _ in segs[1:]]
    assert all(i >= 0 for i in idx), (ln, idx)
    idx.append(len(text))
    for k, (m, c, lab) in enumerate(segs):
        w = (idx[k + 1] - idx[k]) / len(text)
        tot[c] += w
        cnt[c] += 1
        out.append((ln, c, round(w, 2), lab))
nb = [i + 1 for i, l in enumerate(lines) if l.strip()]
print("non-blank lines", len(nb), "uncovered", [i for i in nb if i not in SEG])
for o in out:
    print("| L%d | %s | %.2f | %s |" % o)
print({k: round(v, 2) for k, v in tot.items()}, cnt)
prose = {k: v for k, v in tot.items()}
print("excluding frontmatter (L1-5), title, headings, fences, command:")
# exclude lines of pure structure
skip = {1, 2, 3, 4, 5, 7, 11, 14, 15, 16, 24, 29}
t2 = {M: 0.0, G: 0.0, S: 0.0}
c2 = {M: 0, G: 0, S: 0}
for ln, c, w, lab in out:
    if ln in skip:
        continue
    t2[c] += w
    c2[c] += 1
print({k: round(v, 2) for k, v in t2.items()}, c2)
print("map share excl shared: %.1f%% (lines)  %.1f%% (sentences)" % (100 * t2[M] / (t2[M] + t2[G]), 100 * c2[M] / (c2[M] + c2[G])))
