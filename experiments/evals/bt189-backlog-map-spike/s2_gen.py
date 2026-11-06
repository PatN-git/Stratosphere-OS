"""Generate .tmp/bt189/s2-inventory.md from the hand-built site list + s2_counts.json."""
import json
from collections import Counter
from pathlib import Path

W = "workflows/"
R, MW, LW, G, D = "read", "mirror write", "local-only write", "gate/heal", "rule/definition"
REM, OFF = "removable", "offline-only"


def need(x):
    return f"needs GitHub equivalent ({x})"


S = [
    # --- workflows ---
    (W + "0a-start-session.md:23", R, "status", REM, "active set = `status:in progress` issues; `gh issue list --label` gives it"),
    (W + "0a-start-session.md:29-31", MW, "status (+ parent epic status)", REM, "`gh issue edit` literal at :30"),
    (W + "0b-stop-session.md:27 (a)", MW, "status=done; blocked_by clear", REM, "`removeBlockedBy` cmd printed by `reconcile --edges`"),
    (W + "0b-stop-session.md:27 (b)", LW, "row delete (retention)", REM, "moot without a map; retention rule not defined anywhere in src"),
    (W + "0b-stop-session.md:28", G, "blocked_by", REM, "reconcile gate after clear"),
    (W + "0b-stop-session.md:30", MW, "status=done (parent epic)", REM, "merge auto-close + board Action"),
    (W + "0b-stop-session.md:31 (a)", MW, "status, reopen/close", REM, "`gh issue reopen`/`close --reason \"not planned\"` literal"),
    (W + "0b-stop-session.md:31 (b)", G, "status", REM, "`reconcile --fields status`"),
    (W + "0b-stop-session.md:32", MW, "new row: labels, status:planned, milestone", REM, "issue created on GitHub in same step; `BT-LOCAL` not covered"),
    (W + "0d-nightly-consolidation.md:48-53", G, "all 5 mirror fields", REM, "Phase 3.6 drift check; vanishes with the mirror"),
    (W + "0d-nightly-consolidation.md:73-75", G, "all 5 (map cells written from gh)", REM, "`reconcile --heal`"),
    (W + "1b-concept-framing.md:36", R, "whole map", REM, "Load Memory step"),
    (W + "1b-concept-framing.md:39", R, "title/labels (overlap scan)", REM, "`gh issue list --search`"),
    (W + "1c-concept-map.md:37", MW, "map row (concept:map, status, milestone-exempt)", REM, "`gh issue create` literal in concept-map-operations.md:22"),
    (W + "1c-concept-map.md:38", LW, "BT-LOCAL row + `.map.md` file", OFF, "offline tracker form of create issue"),
    (W + "1c-concept-map.md:90", MW, "status=done", REM, "`gh issue close` at :90"),
    (W + "2a-write-prd.md:21", R, "whole map", REM, "load"),
    (W + "2a-write-prd.md:33", D, "minting rule (never scan map)", REM, "rule persists as 'id from `gh issue create`'; map clause drops"),
    (W + "2a-write-prd.md:45", R, "rows (synthesis input)", REM, "`gh issue list`"),
    (W + "2a-write-prd.md:96-100", MW, "Status, Labels, Milestone (provisional v1.0.0), ICE `-`, Ref", need("Ref; provisional milestone is map-only, GitHub epic has none until 3a"), "row has 9 cols; only Ref is not on GitHub"),
    (W + "2a-write-prd.md:107", D, "Label Registry pointer", REM, "`gh label list`"),
    (W + "2b-interface-design.md:26", MW, "status needs_spec->planned", REM, "`gh issue edit` literal"),
    (W + "2b-interface-design.md:103", MW, "status needs_spec->planned", REM, "`gh issue edit` literal"),
    (W + "2b-interface-design.md:106", LW, "Ref (memory ids)", need("Ref"), "no GitHub field; doc paths already live in the body"),
    (W + "2b-interface-design.md:110", D, "provisional milestone note", need("other: provisional milestone"), "drop 2a's map-only milestone or write it on GitHub"),
    (W + "3a-version-planning.md:35", R, "whole map", REM, "load"),
    (W + "3a-version-planning.md:36", R, "labels (tier:epic exists?)", REM, "`gh issue list --label tier:epic`"),
    (W + "3a-version-planning.md:41", R, "milestone (numbering fallback)", REM, "GitHub milestones are the 2nd authority already"),
    (W + "3a-version-planning.md:57", R, "rows (auditor input)", REM, "`gh issue view`"),
    (W + "3a-version-planning.md:71", MW, "milestone (epics)", REM, "milestone create/assign on GitHub in same step"),
    (W + "3a-version-planning.md:72", MW, "blocked_by", REM, "`addBlockedBy`"),
    (W + "3a-version-planning.md:74", G, "milestone, blocked_by", REM, "reconcile gate"),
    (W + "3b-create-issue.md:24", MW, "status needs_spec->planned", REM, "`gh issue edit` literal"),
    (W + "3b-create-issue.md:30", R, "Parent rows (siblings)", REM, "`gh issue view --json subIssues` is the primary"),
    (W + "3b-create-issue.md:101", D, "`BT-LOCAL-<n>` offline fallback", OFF, "id minting offline"),
    (W + "3b-create-issue.md:111", MW, "blocked_by (+ body text)", REM, "`addBlockedBy`"),
    (W + "3b-create-issue.md:112-115", MW, "full row: status, labels, milestone, parent, blocked_by, ICE, Ref", need("ICE, Ref"), "ICE raw metrics already in body (:101); Ref has no GitHub home"),
    (W + "3b-create-issue.md:116", G, "all 5", REM, "reconcile gate (fresh rows)"),
    (W + "3b-create-issue.md:123", D, "Label Registry + write new label to registry", REM, "`gh label list`/`create`"),
    (W + "3c-sprint-planning.md:21", R, "whole map", REM, "load"),
    (W + "3c-sprint-planning.md:26", G, "map entry + labels present ([MISSING-LABELS])", REM, "'lacks map entry' clause vanishes; label check = `gh issue view`"),
    (W + "3c-sprint-planning.md:29", R, "blocked_by (fallback)", REM, "`gh issue list --json blockedBy` is primary"),
    (W + "3c-sprint-planning.md:34", R, "ICE", need("ICE"), "recompute from body raw metrics + size label"),
    (W + "3c-sprint-planning.md:64", D, "[MISSING-LABELS] note", REM, "wording only"),
    (W + "3c-sprint-planning.md:72", MW, "labels (priority:*)", REM, "label edit on GitHub; no literal command"),
    (W + "3c-sprint-planning.md:73", MW, "milestone (sprint digit Z), status", REM, "sprint digit = GitHub milestone `vX.Y.Z`; no extra equivalent"),
    (W + "3c-sprint-planning.md:74", MW, "blocked_by", REM, "`addBlockedBy`"),
    (W + "3c-sprint-planning.md:76", G, "status, milestone, labels, blocked_by", REM, "reconcile gate"),
    (W + "3d-implement-issue.md:22", R, "milestone, parent", REM, "`gh issue view --json milestone,parent` fallback exists"),
    (W + "3d-implement-issue.md:26", MW, "status in progress (+ epic)", REM, "`gh issue edit` literal"),
    (W + "3d-implement-issue.md:51", R, "requirement bare ids", REM, "or issue (already 'map/issue')"),
    (W + "3z-afk-loop.md:30", R, "queue (status, ids)", REM, "`gh issue list`"),
    (W + "3z-afk-loop.md:34", R, "exists + status", REM, "`gh issue view`"),
    (W + "3z-afk-loop.md:40", R, "milestone, parent (unit key)", REM, "as 3d:22"),
    (W + "3z-afk-loop.md:51-53", MW, "status in progress (slice, parent epic)", REM, "`gh issue edit` literal :52"),
    (W + "3z-afk-loop.md:73", MW, "status=blocked", REM, "`gh issue edit` + `gh issue comment` literals"),
    (W + "3z-afk-loop.md:77", MW, "status=blocked", REM, "`gh issue edit` literal"),
    (W + "3z-afk-loop.md:118", D, "0b updates BACKLOG_MAP", REM, "wording"),
    (W + "4a-verify-and-ship.md:34", R, "parent", REM, "`gh issue view --json parent` fallback"),
    (W + "4a-verify-and-ship.md:86", MW, "status=done (+close)", REM, "`gh issue edit` + `gh issue close` literals"),
    (W + "4a-verify-and-ship.md:87", MW, "status=in review", REM, "`gh issue edit` literal"),
    (W + "4a-verify-and-ship.md:88", MW, "blocked_by clear", REM, "`removeBlockedBy` cmd"),
    (W + "4a-verify-and-ship.md:98", MW, "status in review (epic), blocked_by clear", REM, "`gh issue edit` + `removeBlockedBy`"),
    (W + "4a-verify-and-ship.md:100-101", G, "status, blocked_by (+pr-link)", REM, "reconcile gate; PR-link half is GitHub-only already"),
    (W + "4a-verify-and-ship.md:102", R, "parent, status (draft rule)", REM, "`gh issue view --json subIssues`"),
    (W + "4b-audit-architecture-drift.md:26", R, "active items", REM, "`gh issue list`"),
    (W + "4b-audit-architecture-drift.md:65", R, "in-progress rows (collision)", REM, "`gh issue list --label`"),
    (W + "4b-audit-architecture-drift.md:75", R, "in-progress rows (collision)", REM, "same"),
    (W + "4c-codebase-health-audit.md:57-58", R, "status:in progress modules", REM, "`gh issue list --label`"),
    # --- skills / commands ---
    ("skills/load-memory/SKILL.md:21", R, "whole map (WIP conflicts)", REM, "`gh issue list --label`"),
    ("commands/stratosphere-setup/SKILL.md:38", D, "template file list", REM, "template removed"),
    ("commands/stratosphere-setup/SKILL.md:79", D, "connect-GitHub prompt text", REM, "wording"),
    ("commands/stratosphere-setup/SKILL.md:83", LW, "local file-based issue tracking fallback", OFF, "the offline tracker backend"),
    ("commands/stratosphere-setup/SKILL.md:122", D, "memory file list", REM, "list"),
    ("commands/stratosphere-setup/SKILL.md:214", D, "tracked-file rationale", REM, "list"),
    ("commands/stratosphere-setup/SKILL.md:233", LW, "Label Registry (write confirmed label set)", REM, "`gh label list` is the source; registry only needed offline"),
    ("commands/stratosphere-setup/SKILL.md:268", LW, "Label Registry (final resolved set)", REM, "same"),
    ("commands/stratosphere-setup/SKILL.md:291-292", MW, "seed rows from GitHub issues (BT padded)", REM, "read from GitHub, nothing to mirror"),
    ("commands/stratosphere-setup/SKILL.md:357", D, "registry authoritative after Checkpoint 6", REM, "rule"),
    ("commands/stratosphere-update/SKILL.md:19", D, "backlog data never overwritten", REM, "wording"),
    ("commands/stratosphere-update/SKILL.md:119", D, "`.stratosphere-new` merge target", REM, "file-merge machinery"),
    ("commands/stratosphere-update/SKILL.md:152", G, "BT id set + row count unchanged", REM, "corroboration check; scaffold.py:234-257 backs it"),
    # --- references ---
    ("references/concept-map-operations.md:26", MW, "map row", REM, "`gh issue create` literal :22"),
    ("references/concept-map-operations.md:28", LW, "BT-LOCAL row", OFF, "offline create"),
    ("references/github-issue-relations.md:23", LW, "Parent/Blocked by cols + body text fallback", OFF, "gh-absent fallback"),
    ("references/issue-templates.md:24", MW, "status=done", REM, "text in Spike template"),
    ("references/issue-templates.md:59", D, "Parent mirrors sub-issue + column", REM, "wording"),
    ("references/issue-templates.md:60", D, "Blocked by mirrors edge + column", REM, "wording"),
    ("references/pr-body-and-ship.md:31", R, "labels (tier:epic rows)", REM, "already has `--epic` fallback when map absent (CI)"),
    ("references/terminal-sync-invariant.md:9-20", G, "all 5 (gate contract)", REM, "whole reference exists only for the mirror"),
    ("references/terminal-sync-invariant.md:25-27", G, "heal (upsert map cell, `--source map` cmds)", REM, "same"),
    ("references/terminal-sync-invariant.md:30-32", D, "boundaries; offline = self-attested", OFF, "offline: map is the only store"),
    # --- rules / constitution / templates ---
    ("rules/memory-protocol.md:51", D, "BT-xxx -> BACKLOG_MAP.md ownership table", REM, "[always_on]"),
    ("rules/memory-protocol.md:91", D, "pre-authorised map writes (Ref/status)", REM, "[always_on]"),
    ("rules/memory-protocol.md:107-110", D, "id minting; Parent/Blocked by columns", REM, "[always_on]; minting stays, column wording goes"),
    ("rules/okf-protocol.md:55", D, "status in BACKLOG not frontmatter", REM, "[glob]"),
    ("rules/okf-protocol.md:97", D, "type `backlog` registry row", REM, "[glob]"),
    ("constitution/AGENTS.md", D, "none (0 mentions)", REM, "[always_on] nothing to remove"),
    ("memory-templates/BACKLOG_MAP.md:18-35", D, "rules block (SOS:BLOCK backlog-rules)", REM, "whole file is the mirror"),
    ("memory-templates/BACKLOG_MAP.md:37-51", D, "Label Registry + Milestone definition", REM, "vocabulary needs a new home (reference file); GitHub is source"),
    ("memory-templates/BACKLOG_MAP.md:53-59", D, "table header (9 cols)", REM, "ICE + Ref cols: see 2a/3b"),
    ("memory-templates/STATUS.md:13", D, "authoritative active set note", REM, "wording"),
    ("memory-templates/LEARNINGS.md:27", LW, "temporary TODOs -> BACKLOG_MAP.md", need("other: local TODO sink"), "no GitHub form unless a TODO issue"),
    # --- scripts ---
    ("scripts/reconcile.py:1-45", D, "module contract", REM, "docstring"),
    ("scripts/reconcile.py:71-101", R, "parse 9-col rows (status, labels, milestone, parent, blocked_by)", REM, "`gh issue list --json` replaces parser"),
    ("scripts/reconcile.py:112-189", R, "open_ids, ship_unit, effective_blockers, edge_verdict, stale_blockers", REM, "blocker predicate reads map rows; needs per-issue gh reads (cost)"),
    ("scripts/reconcile.py:190-256", G, "compare map vs gh (status, milestone, labels, parent, blocked_by, closed, pr_link)", REM, "gate disappears"),
    ("scripts/reconcile.py:394-466", G, "gh_fix_commands: map -> GitHub cmds", REM, "the cmds are the verbs themselves"),
    ("scripts/reconcile.py:469-545", LW, "upsert_cells / heal: rewrites map cells from gh", REM, "only exists to fix drift"),
    ("scripts/reconcile.py:546-575", R, "edges_cmd (CLEAR/KEEP decisions)", REM, "keep logic; swap row source"),
    ("scripts/reconcile.py:578-725", G, "main gate, MIRROR-DRIFT/UNVERIFIED, `[local-only]` path", REM, "offline `[local-only]` self-check stays for offline backend"),
    ("scripts/pr_body.py:14", D, "docstring (tier:epic rows)", REM, "doc"),
    ("scripts/pr_body.py:308-315", R, "backlog_rows (fails open)", REM, "map optional already"),
    ("scripts/pr_body.py:318-324", R, "epic_ids (label tier:epic)", REM, "`--epic` flag exists"),
    ("scripts/pr_body.py:327-336,356", R, "backlog_parents (parent)", REM, "`gh issue view --json parent`"),
    ("scripts/validate_memory.py:84-98", LW, "autofix writes `[[id]]` into table cell parts[8]", need("Ref"), "NB parts[8] is ICE under the 9-col schema, Ref is parts[9]: probable stale index"),
    ("scripts/validate_memory.py:164", G, "BACKLOG_MAP in lint scope", REM, "scope list"),
    ("scripts/validate_memory.py:205-260", G, "ID format, duplicate ids, taxonomy labels on rows", REM, "label taxonomy has no GitHub-side lint"),
    ("scripts/validate_memory.py:489", G, "skip trust tags for backlog", REM, "one line"),
    ("scripts/scaffold.py:36", D, "KNOWN_BLOCK_IDS (backlog-rules, label-canonical, backlog-header)", REM, "drift-guarded by test"),
    ("scripts/scaffold.py:234-257", G, "cheap corroboration: BT id set + row count", REM, "update-flow merge check"),
    ("scripts/okf_view.py:41-56", R, "ID definitions index from table rows", REM, "skip file"),
]

counts_kind = Counter(s[1] for s in S)
counts_disp = Counter("needs GitHub equivalent" if s[3].startswith("needs") else s[3] for s in S)
counts_need = Counter()
for s in S:
    if s[3].startswith("needs"):
        counts_need[s[3]] += 1

rows = json.loads(Path(r"C:\Users\patri\Dev\Stratosphere-OS\.tmp\bt189\s2_counts.json").read_text(encoding="utf-8"))

out = []
w = out.append
w("# BT-189 s2 - BACKLOG_MAP inventory (analyst A2)\n")
w("Scope: `src/` only (excludes `dist/`, `.agents/`, `.claude/worktrees/`). Read-only analysis. Line numbers are `src/` as of branch `feat/BT-190-lifecycle-status-pr-scope`.\n")
w("## A. Site inventory\n")
w("Kinds: `read` | `mirror write` | `local-only write` | `gate/heal` | `rule/definition`. Disposition: `removable` (a GitHub write/read already exists) | `needs GitHub equivalent (<what>)` | `offline-only`.\n")
w("| # | file:line | kind | field(s) touched | disposition | note |")
w("|--:|:--|:--|:--|:--|:--|")
for i, s in enumerate(S, 1):
    w(f"| {i} | `{s[0]}` | {s[1]} | {s[2]} | {s[3]} | {s[4]} |")
w("")
w(f"**Total sites: {len(S)}**\n")
w("| kind | sites |\n|:--|--:|")
for k in (R, MW, LW, G, D):
    w(f"| {k} | {counts_kind[k]} |")
w("")
w("| disposition | sites |\n|:--|--:|")
for k in (REM, "needs GitHub equivalent", OFF):
    w(f"| {k} | {counts_disp[k]} |")
w("")
w("Needs-GitHub-equivalent detail:\n")
for k, v in counts_need.items():
    w(f"- {k}: {v}")
w("")
w("**Not map-aware (verified by grep, zero BACKLOG/map references):** `nightly_scan.py`, `nightly_state.py`, `test_gate.py`, `ci_gate.py`, `floor_guard.py`, `contract_check.py`, `check_suite.py` (its hit is an unrelated 'Mirrors build/build.py' comment), `src/constitution/*`, `src/github/sync-labels-to-project.yml` (label -> Project board Action; acts on GitHub labels, never reads the map).")
w("**Outside `src/` but coupled (not inventoried):** `tests/framework/test_status_label_contract.py`, `test_bump_guard.py`, `test_update_flow.py`, `tests/lifecycle/*`, `tests/lifecycle-harness/*`, `tests/jules/test_jules_dispatch.py`, `tests/fixtures/legacy/validate_memory.v4.0.0.py`.\n")
w("Findings worth a decision:\n")
w("1. **Map-only values.** Three things exist only in the map: `ICE` (score; raw metrics are also in the issue body, 3b:101), `Ref` (memory ids; 2a:96, 2b:106, 3b:112, validate_memory autofix), and 2a's provisional milestone `v1.0.0` (2a:100 / 2b:110: GitHub epic has no milestone until 3a, so that cell is intentionally map != GitHub and 3a's gate only checks `milestone` after 3a assigns it).")
w("2. **Blocker predicate reads the map.** `reconcile.py --edges` (3d:20, 3z:40, 4a:88/98, 0b:27) decides CLEAR/KEEP from map rows (parent, milestone, labels, status, blocked_by). Dropping the map means this becomes N `gh issue view --json` reads, or one `gh issue list --state all --json number,labels,milestone,parent,blockedBy,state` (single call, no per-id cost).")
w("3. **Already map-optional.** `pr_body.py` fails open when the map is absent and has `--epic`; 3d/3z/4a already say 'BACKLOG row, else `gh issue view`'. These read sites are the cheapest to drop.")
w("4. **Probable latent bug.** `validate_memory.py:84-98` autofix targets `parts[8]`; with a leading empty split cell and 9 columns that is ICE, not Ref (`parts[9]`).")
w("5. **Retention rule undefined.** 0b:27 says 'before deleting any row (per retention)' but no retention rule for map rows exists in `src/` (grep).\n")

# ---- B ----
w("## B. Text cost\n")
w("Method: per `src/**/*.md` (workflows, skills, commands, references, rules, templates; `plan-html` and `arch-drift-report-template.md` excluded as false positives of the word 'backlog'). A line counts if it matches CORE = `BACKLOG|Backlog|Label Registry|map row|MIRROR-|mirror write/field/the/row`; GATE adds `reconcile.py|terminal-sync-invariant|Terminal sync gate|[HEALED|heal per` (text that exists only because of the mirror gate). **Sentence-level** = only the matching sentence(s) of each line (headline number); **full-line** = the whole line/bullet (upper bound). Characters = `len()` of text + 1 per line. Script: `.tmp/bt189/s2_count.py`.\n")


def grp(prefix):
    return [r for r in rows if r["file"].startswith(prefix)]


w("### B1. Per-file table (all files with any match)\n")
w("| file | file chars | CORE (sentence) | CORE (full line) | +GATE (sentence) | CORE+GATE (sentence) |")
w("|:--|--:|--:|--:|--:|--:|")
order = sorted(rows, key=lambda r: (-r["all_sent"]))
for r in order:
    w(f"| {r['file']} | {r['total']} | {r['core_sent']} | {r['core_line']} | {r['gate_sent']} | {r['all_sent']} |")
w("")
tot = lambda k, p="": sum(r[k] for r in rows if r["file"].startswith(p))
w("### B2. Totals\n")
w("| group | CORE (sentence) | CORE (full line) | +GATE | CORE+GATE (sentence) |")
w("|:--|--:|--:|--:|--:|")
for name, p in (("workflows/", "workflows/"), ("references/", "references/"), ("commands/ (setup, update)", "commands/"), ("skills/", "skills/"), ("rules/", "rules/"), ("memory-templates/", "memory-templates/"), ("**all**", "")):
    w(f"| {name} | {tot('core_sent', p)} | {tot('core_line', p)} | {tot('gate_sent', p)} | {tot('all_sent', p)} |")
w("")
w("**One total: 19,070 chars of BACKLOG-related text (CORE, sentence-level); 22,555 chars with the mirror-only gate text; 29,385 chars at full-line upper bound (CORE).** Of the CORE total, workflows = 12,417 (65%).\n")
w("Top 5 workflows (CORE+GATE sentence chars; CORE alone in brackets): 3z-afk-loop 2,267 (2,026) | 4a-verify-and-ship 2,266 (1,695) | 3c-sprint-planning 1,896 (1,522) | 0b-stop-session 1,840 (1,405) | 3b-create-issue 1,399 (1,166).\n")
w("Caveat: some GATE text also serves non-mirror duties (`reconcile --edges` blocker predicate, PR-link check), so CORE+GATE overstates what disappears with the map; CORE understates multi-sentence mirror bullets where only the first sentence names the map.\n")
w("### B3. Always-loaded text\n")
w("Always-on = `trigger: always_on` rules + the constitution (`AGENTS.md`, loaded via `CLAUDE.md` `@AGENTS.md`). `okf-protocol.md` is `trigger: glob` (`.memory/**`, `docs/**`) so it is conditional, listed for reference.\n")
w("| file | chars | loading | BACKLOG-related (sentence) | (full line) |")
w("|:--|--:|:--|--:|--:|")
al = [("constitution/AGENTS.md", 8965, "always (constitution)", 0, 0), ("rules/memory-protocol.md", 6749, "always_on", 789, 1140), ("rules/output-mode.md", 2598, "always_on", 0, 0), ("rules/okf-protocol.md", 9557, "glob (.memory/**, docs/**)", 181, 373), ("constitution/CLAUDE.md + GEMINI.md", 172 + 314, "pointer files (one per host)", 0, 0)]
for a in al:
    w(f"| {a[0]} | {a[1]} | {a[2]} | {a[3]} | {a[4]} |")
w("")
w("**Always-loaded total: 18,312 chars** (AGENTS.md 8,965 + memory-protocol 6,749 + output-mode 2,598), of which **789 chars (4.3%) are BACKLOG-related**, all in `memory-protocol.md` (lines 51, 91, 107-110). `AGENTS.md` has none. Conditional okf-protocol adds 181 more when `.memory`/`docs` are touched. Not counted: the 1,609-char `BACKLOG_MAP.md` template rules/registry block and the live `.memory/BACKLOG_MAP.md` (every row is read by 0a/1b/2a/3a/3c/3z/load-memory; size grows with the backlog, not measured here).\n")

# ---- C ----
w("## C. Verb fit\n")
w("Every distinct WRITE kind the workflows make to issue state. GitHub literals are the `gh`/GraphQL forms present in `src/` today (file:line). 'Local' = plausible form in a local-markdown backend (the Backlog table row).\n")
w("| # | write kind | tracker verb | GitHub form today (file:line) | local-markdown form | fit |")
w("|--:|:--|:--|:--|:--|:--|")
C = [
    ("create issue", "`create(kind, title, body, labels, milestone, parent, blockers) -> id`", "`gh issue create --title .. --label .. --milestone .. --body-file .tmp/3b-issue-body.md` (3b:100, epic literal 3b:108; 2a:31; concept-map-operations.md:22,38); id = returned number, zero-padded", "append row; id `BT-LOCAL-<slug>`", "fit (verb returns the id). Gap: no `BT-LOCAL -> BT-nnn` promote-on-connect workflow exists ('until synced', 2a:33)"),
    ("set status", "`set_status(id, status)` (backend removes the other `status:*`)", "`gh issue edit <n> --remove-label status:* ... --add-label status:X` (0a:30, 3d:26, 3z:52/73/77, 4a:86-87/98, 2b:26/103, 3b:24, 0b:31); board Action then moves the Project column (`src/github/sync-labels-to-project.yml`)", "edit Status cell", "fit; verb must own the single-status invariant (0a:30 lists 5 removes by hand)"),
    ("add/remove label (non-status)", "`set_labels(id, add, remove)`", "`gh issue edit <n> --add-label/--remove-label` (3c:72 priority, no literal; reconcile.py:454); registry side: `gh label list`/`gh label create` (setup:238, 3b:123)", "edit Labels cell + Label Registry list", "fit. Label *creation* (`ensure_label`) is a separate admin verb (setup-time)"),
    ("set milestone", "`set_milestone(id, name)` + `ensure_milestone(name)` + `close_milestone(name)`", "`gh issue edit <n> --milestone` (reconcile.py:450; `--milestone` at mint 3b:104); create: no literal (3a:71, 3c:73); close: `gh api -X PATCH repos/{owner}/{repo}/milestones/<n> -f state=closed` (3a:69); list: `gh api repos/{owner}/{repo}/milestones` (3a:43, 3b:104)", "edit Milestone cell; milestone open/closed derived (no open_issues count; compute from rows)", "fit with 3 verbs. `open_issues==0` close precondition (3a:20) is a query the local backend computes"),
    ("set parent", "`set_parent(child, parent)` / `clear_parent`", "`addSubIssue` GraphQL (github-issue-relations.md:12; 3b:105, 1c:41; reconcile.py:460); `removeSubIssue` (rel.md:14)", "edit Parent cell (single value)", "fit"),
    ("add blocker", "`add_blocker(id, blocker)`", "`addBlockedBy` GraphQL (rel.md:17; 3a:72, 3b:111, 3c:74, 1c:41; reconcile.py:463)", "append bare id to Blocked by cell", "fit"),
    ("clear blocker", "`clear_blocker(id, blocker)`", "`removeBlockedBy` GraphQL (rel.md:19; 4a:88/98, 0b:27; reconcile.py:465,572)", "remove id from Blocked by cell", "fit as a write. The CLEAR/KEEP *decision* (ship unit, PR merged) uses git + `gh pr view` state, backend-neutral only if the read verbs return milestone/parent/labels"),
    ("set ICE", "`set_ice(id, score, I, C)` or derive-on-read", "NONE today: ICE is written only to the map ICE column (3b:113) plus raw metrics in the issue body at creation (3b:101); 3c:34 reads the map", "edit ICE cell", "MISFIT: local-only column. GitHub form would be an issue-body edit (`gh issue edit --body-file`, not used anywhere) or a Project number field; cheaper: no verb, recompute from body metrics + size label (3c:34 already recomputes when empty)"),
    ("set Ref (memory ids)", "`set_refs(id, ids)`", "NONE: Ref column is local-only; doc paths already live in the issue body (BACKLOG_MAP template rule)", "edit Ref cell (2a:96, 2b:106, 3b:112, validate_memory autofix)", "MISFIT: pointers into `.memory/` have no GitHub field. Options: body line `Refs: L-012, A-003`, or keep Ref in a non-map place; offline = cell"),
    ("close / reopen", "`close(id, reason)` / `reopen(id)`", "`gh issue close <n> --reason completed` (4a:86); `--reason \"not planned\"` (0b:31); `gh issue close <ticket#>` (concept-map-operations.md:92); `gh issue reopen <n>` (3d:26, 0b:31)", "Status = done (`closed == done`, template rule)", "partial MISFIT: on GitHub the unit PR merge closes epics via `Closes #<n>` (4a:96, pr-body-and-ship.md:43) with no tracker call; a local backend has no PR so 0b done-detection must call `close` explicitly"),
    ("comment (PR-link, notes)", "`comment(id, body)`", "`gh issue comment <n> --body \"Shipped in PR #<pr> - <url>\"` (4a:84); `[STUCK]` (3z:73); sprint sync (3c:75, no literal); resolution (concept-map-operations.md:88)", "append dated line under a per-issue log, or no-op", "fit as a verb. PR-link content is GitHub-only (needs a PR URL); the gate's `--pr-id` check (reconcile.py) is GitHub-only and has no local meaning"),
    ("set issue body", "`set_body(id, body)` / `append_body`", "no literal `gh issue edit --body` in src; prose at 2a:95 (summary + doc link), 2b:105 (design link), 3b `--body-file` at create", "MISFIT: the table has only Title. Needs a per-issue body file (e.g. `docs/issues/BT-LOCAL-n.md`)", "MISFIT: issue bodies carry Acceptance Criteria (read by 4a:38 via `gh issue view`), Dependencies/Design path (3d:26), PRD/design links; local-markdown backend needs body storage, not just a row"),
    ("assign (claim)", "`claim(id)`", "`gh issue edit <N> --add-assignee @me` (1c:51; concept-map-operations.md:55)", "no Owner column", "MISFIT (minor): no local column; local form = no-op or a 'claimed' note"),
    ("PR create/edit/ready/label", "NOT a tracker verb", "`gh pr create/edit/ready`, `gh label create risk:one-way` + `gh pr edit --add-label` (4a:79-102, pr-body-and-ship.md:40)", "n/a (4a has `local-only` mode)", "MISFIT by design: pull requests are a VCS-host concept; keep outside the tracker verb set"),
    ("read verbs (support)", "`get(id)`, `list(filter)`, `children(id)`, `blockers(id)`", "`gh issue view --json milestone,parent,subIssues,blockedBy,state` (3d:22, 3b:30, 4a:90, rel.md:21); `gh issue list --label/--state --json` (1c:25, 3c:29, 4b:81)", "table scan", "fit; needed to replace the 33 read sites"),
]
for i, c in enumerate(C, 1):
    w(f"| {i} | {c[0]} | {c[1]} | {c[2]} | {c[3]} | {c[4]} |")
w("")
w("**Verb set:** create, set_status, set_labels (+ensure_label), set_milestone (+ensure/close_milestone), set_parent, add_blocker, clear_blocker, close/reopen, comment, plus reads (get/list/children/blockers). **MISFITS:** set ICE (local-only column), set Ref (local-only column), set issue body (no table equivalent), claim (no column); partial misfit: close (merge auto-close is GitHub-only); PR operations are out of scope for the tracker interface.\n")
Path(r"C:\Users\patri\Dev\Stratosphere-OS\.tmp\bt189\s2-inventory.md").write_text("\n".join(out), encoding="utf-8")
print(len(S), dict(counts_kind), dict(counts_disp), dict(counts_need))
print({k: sum(1 for s in S if s[1] == R and s[3] == k) for k in (REM,)})
