---
type: plan
title: BT-217 Implementation Plan (0f Walk Me Through)
description: "How a Haiku 5.5 implementer builds BT-217 in its own worktree on top of PR #216 under an Opus lead, the hold-out evaluation that is the slice's acceptance, and the fold into #216."
generated:
  by: claude-code session (PatN-git)
  at: 2026-10-28
version: "1.0.0"
---

# BT-217 implementation plan

Review 2026-10-28 (independent, fresh context): 24 findings in `.tmp/bt217-plan-challenge.md` (main checkout). Owner decisions D1, D2, D3 and tiering are folded in (D2 full name, D3 ff, owner 2026-10-28; #216 will not merge before BT-217, so §7.1 step 6 is moot).

Sources: issue #217; `docs/plans/0f-walk-me-through-concept.md` v0.4.0; precedent `10ed067` (BT-209 added 0e). Anchors are from the local `improvement/BT-194-tracker-backend-no-map` @ `7ead6d5`; branch base `de1ad3a` (one later #216 commit, none of the targets touched). Re-anchor by text.

## 1. Findings (resolved below)

| # | Finding | Resolution |
|---|---|---|
| F1 | Registry scope is under-listed. 0e hand-edited 10 files (`git show --stat 10ed067`); BT-217 hand-edits 15. | §4 C3 lists every site. `dist/`, `.claude-plugin/marketplace.json` and `versions.json` come from the build only. |
| F2 | `watch <n>` is undefined, and 4a prints Watch items unnumbered. | 0f gets a Direction line; 4a numbers the Watch items (§4 C2). |
| F3 | `/0f` is not a registered command name. | D2. |
| F4 | The concept brief is untracked. | P0 commits the brief and this plan on the branch. |
| F5/F6 | #216 edits the same okf row, 4a, README, setup and harness, and has already bumped okf, 4a and setup. | D1 (fixed); version rule in §4. |
| F7 | `data_read` location is vague. | 0f names `.memory/ARCHITECTURE.md` frontmatter. The memory template is unchanged. |
| F8 | The real-record path is untestable (no project has a `data_read` key). | Recorded as **unverified** in Deviations. The hold-out tests the illustrative path. |
| F9 | Hold-out leakage. | Concrete cases never appear in this file or in any prompt before P3. Runners are barred from `docs/plans/` and `.tmp/` (§5). |
| F10 | Checker confirmation bias (BT-201: 77–90%). | Neutral claims, `file:line` or FALSE, and a two-pass check (§5 E4). |
| F11 | The worktree lacks `.agents/` and `.memory/` (gitignored). The pre-commit hook blocks commits without `.agents/scripts/test_gate.py`. | P0 step 3. |
| F12 | `.agents/scripts/check_suite.py` does not exist (issue AC and old self-check). | Use `dist/skills/stratosphere-setup/scripts/check_suite.py`. The AC mapping goes in Deviations. |
| F13 | The test gate refuses a commit of code not in a passing record, and `--suite` refuses a dirty tree. The full suite is `bash scripts/check.sh`. | P2 records before committing; P4 runs the one full suite at the final HEAD. |
| F14 | Shipping on the #216 branch gives `branch_ok: false` → `[BRANCH-UNIT]`. A suite record is reused only at the same HEAD. | P4: fold by ff, owner confirms at 4a. |
| F15 | `data_read` could hold a secret, and consumer `.memory/` is tracked. | The okf text says the key names the method; the secret stays in `.env`. |
| F16 | 4a Phase 1 bypasses BT-217's audit (size:medium, no trigger). | The hold-out is the evidence; recorded in Deviations. |
| F17 | Predict on a `tracker: local` ticket needs the `get` verb (`tracker-verbs.md`). | Body unchanged (citing it fans 4 references into 0f). Recorded as unverified. |

**Owner decisions**
- **D1 (fixed):** BT-217 sits on #216 and ships in its PR and release. It gets its own branch `feat/BT-217-walk-me-through` from the local #216 tip, in the worktree `C:\t\b217`. It never uses `.claude/worktrees/bt221` or the #216 branch until the P4 handshake. The fold is owner-gated. No push or merge without the owner.
- **D2 (fixed: full name):** `Unsure about one? /0f-walk-me-through watch <n>`. Evidence:
  - README:59: skills are "invoked as `/<name>`" on every host.
  - The build registers the directory name, and check_suite requires frontmatter name == directory.
  - User-facing mentions in `src/` use full names (`/3b-create-issue` 34×, `/4a-verify-and-ship` 15×); short forms appear only in agent-facing prose.
  - Whether `/0f` resolves is unverified on every host.
  - Cost: 15 characters, printed only when Watch items remain.
- **D3 (fixed: ff):** fold form (P4). With ff, the merge commit is the sync merge in BT-217, and 4a reuses the suite record. With `--no-ff` on the #216 branch, 4a re-runs the full suite (about 3 min on the ship path).

## 2. Roles, models and flow

| Role | Model | Why this tier | Never |
|---|---|---|---|
| Lead | Opus 5.5, the session running `/3d-implement-issue 217` | Diff review, case choice, claim extraction, git and the fold need judgment | Touch bt221 before the P4 handshake |
| Implementer (1) | **Haiku 5.5, effort high** | §4 is string-exact. The P2 verbatim diffs and the count tests catch slips. If Haiku stops on a judgment call or P2 rejects a prose edit, re-dispatch C1/C2 only, on Sonnet | Git writes; hand edits to `dist/`, `.agents/`, `.claude-plugin/`; VERSION; new tests |
| Hold-out runners (3) | Sonnet 5.5, one per case | They *are* the 0f under test. Sonnet is the lowest model the owner runs sessions on (assumption); Haiku would test a configuration nobody deploys | Read `docs/plans/`, `.tmp/`, other cases |
| Fact-checker (1) | Sonnet 5.5, effort high | Guards the riskiest assumption: a false TRUE ships a confident wrong trace. Independence from the lead matters more than size. Not downgraded | See verdict framing before pass 1 |
| Reader probe (1) | Haiku 5.5, no tools | Stands in for a non-technical reader; weaker means stricter | Read code |
| 0e runner (1) | Haiku 5.5, both messages in one run | Rote application of 0e; weaker is a stricter length and retention test. A fail is re-run on Sonnet before it counts | — |

No implementer split: C3's count tests go green only after C2's 0f is built, so the work is sequential. A second subagent costs about 70k fixed tokens for about 25 one-token edits.

Flow: **P0** setup → **P1** implementer → **P2** review and commits → **P3** hold-out (fix loop) → **P4** sync, full suite, handover, fold, `/4a`.

## 3. P0: lead setup
Bash. The lead's cwd is the main checkout. Anything inside the worktree runs as `cd /c/t/b217 && …`.
1. 3d Phase 0 and step 2 as written: blocker guard, `claim`, `set_status in progress` (GitHub backend).
2. 3d step 1 under D1 (owner decision > 3d's "branch from default", AGENTS §2; record as a deviation): `git worktree add -b feat/BT-217-walk-me-through C:/t/b217 improvement/BT-194-tracker-backend-no-map`. Use the local ref, not `origin/`: it carries #216's unpushed commits. Record the base SHA.
3. Untracked deps (F11): `cp -r /c/Users/patri/Dev/Stratosphere-OS/.agents /c/t/b217/ && cp -r /c/t/b217/src/scripts/. /c/t/b217/.agents/scripts/`. No `.memory/` in the worktree: the backend resolves to github (gh ready, no tracker branch), and the STATUS session line is skipped (deviation).
4. Copy the brief and this plan into `C:/t/b217/docs/plans/`. Commit `docs(BT-217): concept brief v0.4.0 and implementation plan v1.0.0` with explicit paths. The main-checkout copies stay untracked until the owner removes them.
5. Write `C:/t/b217/.tmp/3d-plan-BT-217.md`: §4, §6 and `## Deviations`. Owner approval of this plan is the 3d Phase 0.5 approval.
6. Dispatch Appendix A with `model: haiku`, `effort: high`, and no `isolation` (shares b217 through absolute paths). Check `get_usage` when it returns.

## 4. P1: implementer work (exact targets, all under `C:\t\b217`)

**Version rule:**
- The baseline is `git merge-base HEAD origin/main` (= main `b7329af` while #216 is open).
- Each changed `src/` file sits one increment above its main version, once per PR. `validate.py` is the arbiter.
- #216 has already bumped 4a (1.7.0→1.8.0) and setup (1.5.0→1.6.0): leave their `version` and `timestamp` as they are.
- New files start at `1.0.0`. Every bumped file gets `timestamp: <today>`.

### C1 Shared reference and 0e
- **New `src/references/plain-language.md`.** Frontmatter: `description` (cited by 0e and 0f only), `version: "1.0.0"`, `timestamp`. Three short sections:
  - **Content:** 0e's first `Rules:` bullet, moved verbatim except "the input" → "your source (0e: the message; 0f: the code and records read)".
  - **Words:** 0e's second `Rules:` bullet, verbatim.
  - **Economy:** the brief's five rules, verbatim from "Word economy". "Gloss only a term the user must keep using" stays.
- **`src/workflows/0e-plain-english.md`:**
  - Delete the `Rules:` block (the line and its 2 bullets).
  - Append to the opening paragraph: `Wording per \`references/plain-language.md\`.` Use the relative form: 0e hands no path to a subagent.
  - Caps: `≤ 250 words, ≤ 140 if nothing is asked` → `≤ 200 words, ≤ 120 if nothing is asked`.
  - Version 1.0.0 → 1.1.0, timestamp today. Change no other wording.

### C2 0f, rules and the 4a pointer
- **New `src/workflows/0f-walk-me-through.md`.**
  - Frontmatter exactly as 0e: `name`, `description` (from the draft), `disable-model-invocation: true`, `triggers: ["user"]`, `metadata: stratos.layer: lifecycle`, `stratos.mode: HITL`, `version: "1.0.0"`, `timestamp`.
  - Body = the brief's "Draft skill body", with two edits:
    - Direction gains: `` `watch <n>` → Predict on the n-th Watch item of the last ship halt in this conversation: the slice's acceptance criteria, the file it names, that file's tests. Item not in the conversation → ask for it. `` (F2)
    - Ground truth: "the `data_read` key in `ARCHITECTURE.md`" → "the `data_read` key in `.memory/ARCHITECTURE.md` frontmatter" (F7).
    - Nothing else. The sidecar is emitted by the build.
- **`src/rules/output-mode.md` §4.** In "Prefer the shortest phrasing that preserves intent (e.g. …)", insert ` for the reader` after `intent`. Version 2.0.0 → 2.0.1.
- **`src/rules/okf-protocol.md`, the `architecture` row** (L99). Insert before the cell's closing ` |`, after `` `tracker_branch` (local): `<repo>/issues` ``: `` `data_read` (optional): how `/0f-walk-me-through` reads one record, e.g. `supabase, read-only role`; it names the method, never the secret (that stays in `.env`); read-only credentials only, never an admin or service-role key. Absent: illustrative traces. `` (no bare `|`). Version 2.0.4 → 2.1.0: one minor above main's 2.0.3, absorbing #216's patch.
- **`src/workflows/4a-verify-and-ship.md` Phase 3 §3 Watch** (L67 only; L39 is the frozen auditor prompt, L64 is Dismissed):
  - `The Spec auditor's 60-79 findings (omit when empty), one line each.` → `The Spec auditor's 60-79 findings (omit when empty), numbered, one line each.`
  - `HITL shows what remains at the ship halt;` → ``HITL shows what remains at the ship halt, then, if any remain, the line `Unsure about one? /0f-walk-me-through watch <n>`;`` (D2 text).
  - Change nothing else: auditor prompts, thresholds, the 3z return and the Clean Exit Rule stay as they are. No version change (1.8.0).

### C3 Registry: lifecycle 24 → 25, total skills 28 → 29 (line numbers @ `7ead6d5`)
- `src/scripts/check_suite.py`: L4 `all 24` → `all 25`; L24 `The 24 Layer 1` → `The 25 Layer 1`; `"0f-walk-me-through",` after `"0e-plain-english",` (L26).
- `tests/scripts/test_check_suite.py`:
  - L46 `…_all_24_…` → `…_all_25_…`.
  - L49 and L261 `24/24` → `25/25`.
  - L72 `17/24` → `18/25`.
  - L114 `== 24` → `== 25`.
  - L502 `(24 lifecycle` → `(25 lifecycle`.
- `tests/framework/test_dist_bundle.py`: L1 `28 self-contained` → `29 self-contained`; L20 `= 29`; L21 `= 25`.
- `tests/install-harness/README.md` L26 `×28` → `×29`; L30 `28 skills, 24 HITL` → `29 skills, 25 HITL`.
- `tests/install-harness/run-L1.ps1` L34, L35, L49, L182, and `run-L1.sh` L32, L33, L48, L137: every count value and label 28 → 29 and 24 → 25. Stale `27` labels on these lines also → `29`.
- `tests/install-harness/run-L2.py` L99, L108: labels `28` → `29` (the value is computed).
- `src/commands/stratosphere-setup/SKILL.md` L97: `the 24 lifecycle skills` → `the 25 lifecycle skills`. No version change (1.6.0).
- `README.md`:
  - L80, L107, L147: `28` → `29`.
  - New row after L71 (the 0e row): `` | **0. Anytime** | `/0f-walk-me-through` | Traces why a result happened, or predicts how a ticket or change will behave, in plain words; ends in at most 3 calls for you. Read-only. | A result, ticket, or change | Walk-through + your calls | ``
- Never touch `build/build.py` VERSION or the README badge: `release.py` owns both, at ship.

### Implementer self-checks (in order; report the output, never "should pass")
All run as `cd /c/t/b217 && …`, with `TMP='C:\t' TEMP='C:\t'` on pytest.
1. After C1–C2: `python build/build.py && python build/validate.py`. Must be green, or report the exact error.
2. `python -m pytest -q tests/scripts/test_check_suite.py tests/framework/test_dist_bundle.py`. **Expect RED** on the counts (the observed RED for C3). Report the failing test names.
3. Do C3, then `python build/build.py && python build/validate.py`. Must be green.
4. `python dist/skills/stratosphere-setup/scripts/check_suite.py suite` → `[SUITE OK] 25/25 lifecycle skills present and intact in …`.
5. Repeat step 2. Must be GREEN.
6. `git status --short`: only §4 paths plus regenerated `dist/` and `.claude-plugin/marketplace.json`. `git ls-files --eol <changed files>` shows `w/lf` everywhere (L-004).

## 5. P3: hold-out evaluation (lead-run; the slice's acceptance)
All files go in `C:/t/b217/.tmp/bt217-holdout/`.
- **E1 cases.** The lead picks 3 cases after the C2 commit and writes them, with each repo's `git rev-parse HEAD`, to `cases.md`. Requirements:
  - ≥ 1 Trace and ≥ 1 Predict.
  - ≥ 1 in CleanTechHub (`C:\Users\patri\Dev\CleanTechHub`; it has no `data_read` key), and the stress case is a CleanTechHub Trace.
  - Nothing named in the brief, this plan or #216's deviations, and nothing near BT-195 (lifecycleGuard/Teamtailor, `tracker_facts`, `resolve_backend`, `pr_body` fail-open).
  - Pick by the question, before opening the code path.
- **E2 runs.** One Sonnet runner per case (Appendix B1). Its instructions are the built `dist/skills/0f-walk-me-through/` folder. It is read-only and runs nothing. Its answer goes to `out-<k>.md`; it returns its files-read list. A path under `docs/plans/` or `.tmp/` voids the run and costs a new case.
- **E3 length.** Deterministic: `len(text.split())` on each `out-<k>.md` (markup included, as the brief counted). Pass: ≤ 200. No agent.
- **E4 facts** (Appendix B2):
  - The lead extracts every behavior claim and stated value, including each call's "as built" option, as neutral numbered statements in `claims.md`. No verdict wording and no "would".
  - One Sonnet-high checker. **Pass 1:** each claim TRUE `file:line` / FALSE `file:line` / UNVERIFIABLE; verdicts are written to `verdicts.md` first. **Pass 2:** it reads the outputs, judges any behavior claim missing from `claims.md`, and checks that each illustrative value is labelled and phrased "would".
  - UNVERIFIABLE is allowed only for runtime facts the output itself marks unknown or illustrative; anything else counts as FALSE.
  - Pass: zero FALSE about behavior, and all illustrative values labelled.
- **E5 calls.** The Haiku probe gets the output inline and uses no tools. For each call it picks an option with a one-line reason, or says "can't answer without code". Pass: no "can't answer".
- **E6 0e regression.**
  - The lead takes two real agent messages from session transcripts (e.g. a 4a ship halt and a 3d plan halt). **Before** running 0e, it writes `e6-checklist.md`: every question and outward action in each source.
  - One Haiku runner gets inline the built `dist/skills/0e-plain-english/SKILL.md`, its `references/plain-language.md` and both messages. It uses no tools and returns two answers; the lead saves them as `e6-out-1.md` and `e6-out-2.md`.
  - The lead ticks the checklist and counts words with the E3 script. Pass: nothing dropped, and ≤ 200 words (≤ 120 when nothing is asked).
  - A Haiku fail is re-run once on Sonnet before it counts.
- **Fail loop.** Any FALSE behavior claim → the lead fixes the 0f Ground truth rules (commit, rebuild), then runs **new** cases, never the same ones. Record each round in `## Deviations`.
- **Budget.** 7 subagent runs (1 implementer, 3 runners, 1 checker, 1 probe, 1 0e runner): about 0.5M tokens at about 70k fixed each, with the Haiku runs cheaper. Check `get_usage` after each round. Hard stop at 60% of the 5-hour window, and stop to ask the owner after round 2.

## 6. AC → check map
| AC | Check | Who |
|---|---|---|
| Hold-out: no wrong behavior claim | E4 | Lead + checker |
| Illustrative values labelled, "would" | E4 | checker |
| Each output ≤ 200 words | E3 | script |
| Calls answerable without code | E5 | Haiku probe |
| ≥ 1 Trace, ≥ 1 Predict, ≥ 1 CleanTechHub, 1 no-`data_read` case | E1 | Lead |
| 0e keeps every question and outward action, within 200 / 120 | E6 | Haiku runner + lead pre-registered checklist + script |
| build + validate green; `25/25` (F12 path); full suite through the test gate | self-checks, P2, P4 | Implementer, then lead |

New repo tests: **none.** The count tests already pin the registry. Wording-presence tests were removed repo-wide (BT-211), and 0f writes no code. L-001 applies only if a scaffold-update test is added; none is planned.

## 7. P2: lead review and commits (in b217)
1. Read the full diff against §4. Reject any change outside §4, any reworded 0e rule, and any auditor-prompt change.
2. Verbatim checks (deterministic):
   - Diff the brief's "Draft skill body" fenced block against `src/workflows/0f-walk-me-through.md`. Only the 0e-style frontmatter keys and the two named body edits may differ.
   - Diff 0e's old `Rules:` bullets (`git show HEAD:src/workflows/0e-plain-english.md`) against the reference's Content and Words sections.
3. Gate record (F13): `TMP='C:\t' TEMP='C:\t' python .agents/scripts/test_gate.py record -- python -m pytest -q tests/scripts/test_check_suite.py tests/framework/test_dist_bundle.py`.
4. Commits, with explicit paths, `feat(BT-217): …`; check `git show --stat HEAD` after each:
   1. shared plain-language reference; 0e cites it, caps 200 / 120
   2. add 0f-walk-me-through; output-mode "for the reader"; okf `data_read` key; 4a numbered Watch and the 0f pointer
   3. lifecycle skills 24 → 25, bundle 28 → 29
   4. rebuild dist
5. `## Deviations`:
   - F1 (scope widened); F2/F3 (pointer and argument); F8 and F17 (unverified).
   - F12 (AC check_suite path); F16 (4a audit bypass); okf 2.0.4 → 2.1.0 absorption.
   - D1 base override, base SHA, no STATUS line.

## 7.1 P4: sync, full suite, fold, ship (D1)
1. **Sync** (never rebase). After P3 passes, at a clean tree: `cd /c/t/b217 && git merge --no-ff improvement/BT-194-tracker-backend-no-map`, using the local ref so unpushed #216 work comes in.
   - Conflicts in `src/` or tests: keep both sides. Each version ends one increment above main, of the larger kind.
   - Conflicts in generated files (`dist/`, marketplace, `versions.json`): run `python build/build.py`; never hand-merge them.
   - Then repeat P2 step 3 and commit.
2. **Full suite once** (3d step 6): `python .agents/scripts/floor_guard.py` (exit 0), then `TMP='C:\t' TEMP='C:\t' python .agents/scripts/test_gate.py record --suite BT-217 -- bash scripts/check.sh`. The tree must be clean afterwards.
3. **Handover (HITL).** Report the BT-217 tip SHA and the suite record. Ask the owner to bring the #216 session to a clean, committed stop. Push nothing.
4. **Fold, only after the owner confirms**, inside bt221 (a branch checked out there can only advance there):
   - `git -C .claude/worktrees/bt221 merge --ff-only feat/BT-217-walk-me-through` (D3).
   - Copy b217's `.tmp/3d-plan-BT-217.md` and `.tmp/3d-suite-BT-217.json` to bt221's `.tmp/`.
   - If ff fails because #216 moved, repeat steps 1–3.
   - D3 alternative: `--no-ff`; 4a then re-runs the suite.
5. **Ship:** `/4a-verify-and-ship 217` in bt221.
   - Phase 1 bypass is expected.
   - Phase 5 step 1 halts `[BRANCH-UNIT]`: the owner confirms the #216 branch (BT-222 precedent).
   - `release.py` is expected unchanged (5.0.0 is already a major over `v4.10.1`).
   - Push only after the step 3 confirmation. Never merge.
6. **Fallback: #216 merges first.** BT-217 gets its own PR from b217:
   - Merge `origin/main` and re-bump against the new main (4a 1.8.1, setup 1.6.1, okf 2.1.0 holds).
   - `release.py` derives a new version, which breaks "same release": owner decision.
7. Removing the worktree or the branch afterwards is the owner's call.

## 8. Why the 4a pointer line (claims checked against the #216 tip and PR records)
- **Watch items are where a human is weakest.** They are Spec-auditor findings scored 60–79 (4a L39, L67), so the auditor itself is unsure. They never block. HITL sees them at the ship halt (Phase 5 step 3, before the step 4 push), and the PR body keeps only their count. In code terms, "what, where, why unsure" invites "sounds good": the rubber stamp that 0f exists to fix.
- **They carry real gaps.**
  - BT-211 exists because 17 of 33 labelled gaps missed at ≥ 80 sat in the 60–79 band (#211).
  - PR #193: 3 of 4 Watch items were fixed. #216: BT-222's one item was fixed before ship.
  - Audited slices show 1–5 items each: BT-197 2, 198 2, 199 5, 219 3, 221 1, 222 1.
- **0f cannot reach the moment by itself.** It is manual-only (`disable-model-invocation`, Codex sidecar), so no agent may invoke it. The README row lists it, but nothing names it or its argument at the moment of doubt.
- **It is the cheapest permitted touchpoint.** One conditional printed line, about 25 tokens of 4a text per load, no ship-path time, and no auditor-prompt change (frozen after BT-201). Auto-running 0f per item was rejected: cost, ship-path minutes, rubber-stamp volume, and it breaks HITL.
- **It turns doubt into an action before the push.** `pin <n>` gives a Given/When/Then for 3d. Otherwise the item stays as built, now as a conscious choice.
- **Limits:**
  - HITL only: 3z AFK reports carry Watch lines without the pointer (non-goal).
  - Audited slices only: 4a Phase 1 bypasses HITL slices without a trigger (e.g. BT-200, BT-218, and BT-217 itself).
  - No halt when shipping is pre-authorized.
  - Needs F2 and F3.
  - Only opportunities can be counted (`watch` in PR audit lines). Use cannot, because 0f writes nothing.

## Appendix A: implementer dispatch (Agent: `model: haiku`, `effort: high`, no `isolation`)

```text
You implement StratOS issue BT-217 in the git worktree C:\t\b217 (branch feat/BT-217-walk-me-through, already checked out). Start every Bash call with `cd /c/t/b217 && `. Give every Read/Edit/Write path absolute, under C:\t\b217. Never touch C:\Users\patri\Dev\Stratosphere-OS or its .claude\worktrees.
Spec: C:\t\b217\docs\plans\0f-walk-me-through-implementation-plan.md, section 4 only (version rule, C1, C2, C3, self-checks). Source text: C:\t\b217\docs\plans\0f-walk-me-through-concept.md, sections "Word economy" and "Draft skill body". Read nothing else under docs/plans or .tmp.
Order: C1, C2, self-checks 1-2 (step 2 must be RED), C3, self-checks 3-6. Copy quoted text character for character and change only what section 4 names. Use the Edit tool for existing files and the Write tool for new ones (LF; never Python text-mode writes). Never hand-edit dist/, .agents/, .claude-plugin/, the build/build.py VERSION or the README badge: python build/build.py regenerates them.
No git writes (add, commit, stash, checkout, branch, merge, restore). Add no tests. In 4a, change nothing beyond the two Watch-sentence edits.
If an anchor text is missing, a line number is off by more than a few lines, or validate.py demands a bump that section 4 did not predict: stop and report. Do not guess.
Report in at most 250 words: files changed (one line each); each self-check command with its last output line(s), the RED included; deviations with reasons; anything unverified.
```

## Appendix B: eval prompts (fill `<…>`; one run each)

**B1 runner** (Agent: `model: sonnet`):
```text
Act as the assistant that received a user command. Your instructions are C:\t\b217\dist\skills\0f-walk-me-through\SKILL.md and the files in its references\ folder. Follow them exactly.
Repo: <path> at <sha> (check `git rev-parse HEAD` first; stop if it differs).
User: /0f-walk-me-through <case line>
Read-only: Read, Grep, Glob and `git show/log/grep` only. Run no scripts, tests, builds, database or network calls. Never open anything under docs/plans/ or .tmp/ in any repo.
Write only the answer the user would see to C:\t\b217\.tmp\bt217-holdout\out-<k>.md. Then reply with "Files read:" and one path per line, nothing else.
```

**B2 checker** (Agent: `model: sonnet`, `effort: high`):
```text
Fact-check claims about code. Repos: <path @ sha, …>; check `git rev-parse HEAD` first and stop on a mismatch. Read-only: no scripts or tests; write only the two files named below.
Pass 1: for each numbered claim in C:\t\b217\.tmp\bt217-holdout\claims.md, answer TRUE with file:line, FALSE with the file:line that contradicts it, or UNVERIFIABLE with the reason. A claim without a citation is FALSE. Write the verdicts to verdicts.md (same folder) before you read anything for pass 2.
Pass 2: read out-1.md to out-3.md. (a) List every behavior claim or stated value missing from claims.md and judge each as in pass 1. (b) For every illustrative value, say whether it is labelled illustrative and phrased "would" (yes/no). Append both to verdicts.md.
Reply in at most 200 words: counts per verdict, and every FALSE and every "no" line.
```
