"""S1 helper: count non-blank lines per classified range of src/scripts/reconcile.py. Read-only on the repo."""
import sys
from pathlib import Path

SRC = Path(r"C:\Users\patri\Dev\Stratosphere-OS\src\scripts\reconcile.py")
M, G, S = "map-only", "gh-post-condition", "shared"

# (start, end, class, unit, evidence)
R = [
    (1, 2, S, "shebang + docstring title", "plumbing"),
    (4, 6, M, "docstring: assert GH matches map mirror", "map-vs-GH equality contract"),
    (8, 8, M, "docstring: --fields = mirror fields written", "scopes the map diff"),
    (9, 12, G, "docstring: --pr-id PR-link check + closed==done", "GitHub-internal post-conditions"),
    (14, 14, M, "docstring: offline = map internal-consistency", "map-only fallback"),
    (15, 15, S, "docstring: contract pointer", "plumbing"),
    (17, 19, S, "docstring usage: --ids/--pr-id/--fields", "CLI plumbing"),
    (20, 22, M, "docstring usage: --all-open --summary, --heal", "map sweep and map heal"),
    (23, 23, G, "docstring usage: --edges", "blocker decision list"),
    (25, 32, M, "docstring: --heal paragraph", "map upsert / print GH cmds to match map"),
    (34, 37, G, "docstring: --edges paragraph", "D3 blocker predicate, PR merge state"),
    (39, 41, M, "docstring: --summary paragraph", "nightly drift counts/ages"),
    (42, 42, S, "docstring close", "plumbing"),
    (43, 50, S, "imports", "plumbing"),
    (52, 52, M, "STATE_DEFAULT", "nightly drift state file"),
    (55, 59, M, "_nightly_state", "only --summary/--date need it"),
    (61, 61, S, "STATUS_RE", "status:* label parse, used by both sides"),
    (62, 63, M, "NONE_TOKENS, ALL_FIELDS", "map cell tokens, mirror field set"),
    (64, 64, G, "SHIPPED", "D3 predicate constant"),
    (67, 68, S, "_bt", "id formatting"),
    (71, 81, M, "_row_cells", "parses a map table row"),
    (84, 100, M, "parse_backlog", "parses the map"),
    (103, 105, S, "issue_number", "BT id to issue number"),
    (108, 109, M, "_norm", "normalises map cell tokens"),
    (112, 114, M, "open_ids", "open rows of the map"),
    (117, 121, S, "_pr_body (lazy import)", "plumbing"),
    (124, 136, G, "ship_unit", "D1 ship unit for the blocker predicate (reads rows; re-point to gh fields)"),
    (139, 144, G, "effective_blockers", "own + parent epic blockers (reads rows; re-point)"),
    (147, 148, G, "_no_pr_state", "default merged_of"),
    (151, 176, G, "edge_verdict", "D3 predicate, PR merge state decides cross-unit"),
    (179, 187, G, "stale_blockers", "edge whose verdict is OK still stored (reads rows; re-point)"),
    (190, 195, G, "closed_on_github", "closed==done (as written compares row status)"),
    (198, 203, G, "open_on_github", "done but still open = dropped gh issue close"),
    (206, 249, M, "compare: status/milestone/labels/blocked_by/parent", "map-vs-GH field equality"),
    (250, 252, G, "compare: PR-link check", "comment with /pull/ URL on the issue"),
    (254, 254, M, "compare: return", "tail of the diff"),
    (257, 268, S, "_gh_json", "gh helper"),
    (271, 286, S, "fetch_issue", "gh helper"),
    (289, 293, S, "gh_available", "gh helper"),
    (296, 302, G, "_pr_state", "gh pr view state (sole consumer: merge-state predicate)"),
    (305, 321, G, "pr_merge_state", "last /pull/ comment -> PR merged/open/none"),
    (324, 335, G, "make_merged_of", "memoised merge-state lookup"),
    (338, 342, M, "KIND_PREFIXES, CHRONIC_NIGHTS", "drift-kind taxonomy for the nightly report"),
    (345, 347, M, "drift_kind", "classifies a drift text"),
    (350, 361, M, "classify", "nightly age of a drift item"),
    (364, 387, M, "summarize", "nightly drift summary"),
    (390, 391, M, "HEAL_KINDS, HEAL_CELL", "map column indexes"),
    (394, 409, M, "_gh_state", "GH value used to heal a map cell"),
    (412, 418, M, "_cell_text", "map cell text"),
    (421, 423, M, "_map_text", "map cell text"),
    (426, 431, S, "_graphql", "GH mutation command builder (used by CLEAR cmd and by heal)"),
    (434, 438, S, "_edge", "GH mutation command builder (used by CLEAR cmd and by heal)"),
    (441, 466, M, "gh_fix_commands", "commands that make GH match the map"),
    (469, 483, M, "upsert_cells", "rewrites map cells"),
    (486, 543, M, "heal", "--heal gh: upsert map; --heal map: print cmds to match map"),
    (546, 548, G, "edges_cmd: header", "D3 verdict runner"),
    (549, 552, M, "edges_cmd: absent-from-map ids", "EDGES-ABSENT is a map concept"),
    (553, 575, G, "edges_cmd: blockers / dependents", "BLOCKER-*/CLEAR/KEEP + removeBlockedBy cmd"),
    (578, 581, S, "main: def, parser, --ids", "CLI plumbing"),
    (582, 584, M, "CLI --all-open", "sweep of map rows"),
    (585, 585, G, "CLI --pr-id", "PR-link target"),
    (586, 588, M, "CLI --fields, --backlog", "mirror fields, map path"),
    (589, 591, M, "CLI --require-gh", "refuse unverified mirror"),
    (592, 607, M, "CLI --summary/--out/--keys-out/--state/--date/--heal/--kind/--source", "nightly + heal"),
    (608, 610, G, "CLI --edges", "blocker verdicts"),
    (611, 613, S, "main: parse_args, --edges exclusivity", "CLI plumbing"),
    (614, 614, M, "main: default fields", "mirror fields"),
    (615, 628, M, "main: heal/summary/date validation", "map-only flags"),
    (630, 632, M, "main: fields, parse_backlog, ids from map", "reads the map"),
    (633, 635, G, "main: merged_of + --edges dispatch", "blocker decision"),
    (636, 640, M, "main: --heal dispatch", "map heal"),
    (641, 641, M, "main: emit comment", "summary grouping"),
    (642, 643, G, "main: stale_blockers emit (--all-open)", "stale blocker edge"),
    (645, 652, S, "finish(): plain output", "output plumbing"),
    (653, 672, M, "finish(): summary/--out/--keys-out", "nightly report files"),
    (674, 685, M, "main: offline branch", "map internal consistency, require-gh"),
    (687, 689, S, "main: exit_code, loop head", "plumbing"),
    (690, 696, M, "main: absent-from-map / BT-LOCAL", "map-row concepts"),
    (697, 705, S, "main: fetch_issue per id", "gh fetch plumbing"),
    (706, 710, M, "main: row exists but GH issue not found", "map row with no issue"),
    (711, 712, G, "main: closed==done check", "state vs done"),
    (713, 719, M, "main: compare + emit drift", "map diff"),
    (720, 724, M, "main: summary all-fetch-failed guard", "nightly report guard"),
    (725, 726, S, "main: ok_line, finish", "plumbing"),
    (729, 730, S, "__main__", "plumbing"),
]

lines = SRC.read_text(encoding="utf-8").splitlines()
nb = {i + 1 for i, l in enumerate(lines) if l.strip()}
cov = {}
for s, e, c, u, ev in R:
    for i in range(s, e + 1):
        if i in nb:
            if i in cov:
                print("OVERLAP", i)
            cov[i] = c
missing = sorted(nb - set(cov))
print("total lines", len(lines), "non-blank", len(nb), "uncovered non-blank:", missing)
tot = {M: 0, G: 0, S: 0}
rows = []
for s, e, c, u, ev in R:
    n = sum(1 for i in range(s, e + 1) if i in nb)
    tot[c] += n
    rows.append((u, f"L{s}-{e}" if s != e else f"L{s}", n, c, ev))
for r in rows:
    print("| " + " | ".join(str(x) for x in r) + " |")
print(tot, "classified (excl shared):", tot[M] + tot[G], "map-only share %.1f" % (100 * tot[M] / (tot[M] + tot[G])))
# strict: gh units that do not read map rows
strict_g = 0
for s, e, c, u, ev in R:
    if c == G and u in ("SHIPPED", "_pr_state", "pr_merge_state", "make_merged_of", "compare: PR-link check", "CLI --pr-id", "CLI --edges", "docstring: --pr-id PR-link check + closed==done", "docstring usage: --edges", "docstring: --edges paragraph"):
        strict_g += sum(1 for i in range(s, e + 1) if i in nb)
print("strict gh (never reads rows)", strict_g)
