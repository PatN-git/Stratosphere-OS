# Notes, runner 01 (CTH = CleanTechHub, SOS = C:\t\b217)

Paths: J = CTH src/lib/ingestion, G = CTH src/lib/gemini.

## Q1 ingested job status (entry: .github/workflows/job-ingestion-cron.yml:5 cron `0 2 * * *` + :56 `node scripts/run-job-ingestion.js` -> run-job-ingestion.js:422 runAtsIngestionBatch -> adapters.js:197 upsertJobCandidates -> supabaseClient.js:43 buildJobRows -> writeJobRows)
Claim: score>=85 and no disqualifier -> live. Applies when: buildJobRows (jobRowBuilder.js:255-268, 162). Exceptions found: disqualifiers (jobRowBuilder.js:158) = unreachable link (99), foreign location (113), generic talent pool (123), portal fallback (132), unverified taxonomy (143); missing metadata alone is NOT a disqualifier (158 excludes it) (searched: jobRowBuilder.js whole file).
Claim: score<85 or any disqualifier -> draft. jobRowBuilder.js:255,261-263,266-267.
Claim: primary reason foreign_location -> archived regardless of score. jobRowBuilder.js:258-260. Exception: unreachable_link precedes foreign_location in precedence (24-31, loop 165-170) so both -> draft/unreachable_link. Foreign only flagged when no German region/"Germany"/region id match (108-115).
Claim: score components. jobRowBuilder.js:41-72 (0 if title <=2 chars or apply link not http/https; 30 base; +10 company, +10 type, +10 work mode, +8 experience, +7 function not other, +15/+5 link shape, +10 http not failing; caps 75 talent pool, 80 portal fallback, 80 unverified taxonomy, 83 function other). Adapters set candidate.confidence_score via calculateConfidenceScore (e.g. greenhouse.js:56); buildJobRows uses given score if defined (242-244).
Claim: demotion guard: a stored live row with same apply_link stays live, draft_reason cleared. jobWriter.js:77-93 (row-by-link), 129-135 (composite collision). Exception: only if lookup works (try/catch 83-85).
Claim: later archiving. (a) reconciler: live job missing from company's latest scan -> consecutive_missing_scans+1, archived when >=2 (jobDeltaReconciler.js:319-326); only runs when company scan returned >=1 candidate and not dryRun (adapters.js:124-131); relink instead if same title+region has new URL (219-226). (b) lifecycle guard run after ingestion unless !runLifecycle/dryRun/quotaExhausted/timedOut (run-job-ingestion.js:505-507): checks status=live jobs not checked in 3 days (lifecycleGuard.js:327-337, 381-392), batch = max(25, ceil(n/3)) capped at n (307-313); archives: no apply link (97-106), posted_at >180 days (44, 109-122), 404/410 (144-154), soft-404 phrase on 2xx page (172-187), 5xx or other non-2xx (e.g. 403) on 2nd consecutive failure (maxServerFailures=2, 157-168, 201-212); network error/timeout keeps status (213-228).
Exceptions found: drafts are not touched by reconciler/lifecycle (both select status=live: jobDeltaReconciler.js:185, lifecycleGuard.js:384). (searched: all `status:` writes, grep in src/api/scripts.)

## Q2 the 10 points
Claim: +10 when `job.is_http_200 !== false`. jobRowBuilder.js:66. Applies when: apply link already valid http/https (55: else score 0) and title >2 chars (41). Exceptions: caps 67-70 can lower the total; explicit `false` removes the 10 and also makes draft reason unreachable_link (99).
Claim: nothing in the ingestion code sets it false; only `true` set (deel.js:70, heavenhr.js:99,120, teamtailor.js:123,194) or left unset. (searched: grep is_http_200 over src, scripts, api, excluding tests: only reads at jobRowBuilder.js:66,99 and backfill-draft-reasons.js:102 reads a stored column; no `false` assignment.) So the link is not fetched at ingestion; later lifecycle guard checks it.
Other link points (not the 10): valid link counted in 30 base (57 comment, 15), +15 direct-looking URL else +5 (64-65).

## Q3 classifyJobFunction (classifierRules.js)
Claim: title weight 1.5x, dept 0.5x -> dept is one third. classifierRules.js:134-144 (15 vs 5, 7.5 vs 2.5, 3.75 vs 1.25).
Claim: dept only counts for a tier when title did not match that same tier of that category (else-if, 135,139,143).
Claim: inhibitor -15 if title OR dept matches (147-150) equal weight.
Claim: best score <4 -> 'other' (167). Talent pool title -> undefined whatever dept (117-123).
Claim: dept actually passed in by: ashby.js:60, join.js:89 (category name), personio.js:90, recruitee.js:84, workable.js:53 (department + function), domSelector.js:246, gemini.js:351. NOT passed (title only): greenhouse.js:50, deel.js:58, heavenhr.js:96,110, hibob.js:115, talentstorm.js:115, teamtailor.js:114,187. (searched: grep mapTaxonomy.jobFunction in src/api/scripts.)
Derived: dept alone: tier1 5 (>=4 ok), tier2 2.5, tier3 1.25 (<4 -> other) unless several tiers add to >=4.

## Q4 work mode / seniority / job type
Claim: each ATS adapter reads feed fields when present, else keyword rules on title (taxonomy.js mapTaxonomy 28-216). Lines: ashby.js:42-43,57,59; greenhouse.js:33,47,49; personio.js:70-73,87,89; recruitee.js:65,81,83; workable.js:35-37,50,52; join.js:63-71,86,88; gemini.js:333,347-348 (AI-extracted field first, then title); domSelector.js:220-223,240,243; hibob.js:91-93,112-114; talentstorm.js:97,112-114.
Claim: defaults when nothing found: jobRowBuilder.js:278-280 stored as experienced / full_time / hybrid. Exception: draft diagnostics and score look at raw candidate (jobRowBuilder.js:148-152 missing fields; 59-61 points) so the default does not earn points; but some adapters fill defaults themselves (heavenhr.js:62,74-76; deel.js:55-57; teamtailor.js:97,111,170,184; recruitee.js:92-96 and domSelector.js:267-271 only for scoring).
Seniority tiers: taxonomy.js:55 CANONICAL_TIERS six values.

## Q5 60-second AI pause
Claim: pause = QuotaTracker.record429(60) set in GeminiFlashAdapter on a 429 reply (or any reply whose body mentions "quota"), then adapter returns [] for that call. adapters/gemini.js:258-262. Fixed 60, not the server's Retry-After (rateLimiter.js:83 default 60; gemini.js:96 header read only for the pool result).
Claim: what it blocks: that adapter's own extractJobs and extractFromHtml return [] while paused. gemini.js:191-193,201,207-209. Nothing else (other ATS adapters, DOM selector, key pool not consulted).
Claim: in nightly run, new adapter (new GeminiFlashAdapter -> new QuotaTracker, gemini.js:184) per company: adapters.js:119 getAdapterForCompany -> :91-95 `new GeminiFlashAdapter()` / `new FallbackEngine()` (fallbackEngine.js:34 new GeminiFlashAdapter). So pause is not carried to next company. FallbackEngine calls gemini once per company (fallbackEngine.js:65). The skip-other-companies logic is only in runFallbackIngestion (fallbackEngine.js:172-175) which the nightly script does not call (searched: grep runFallbackIngestion whole repo excl tests: only defined/exported adapters.js:30,57). Nightly 429 breaker (adapters.js:145-162, run-job-ingestion.js:450) needs a thrown error; the Gemini adapter returns [] instead (gemini.js:260-261; defaultCallGemini catches 121-129) so this path does not trigger it.
What does carry over: key pool cooldown (shared defaultKeyPool singleton, keyPool.js:287; gemini.js:23,42) - that is Q6.

## Q6 key switching (keyPool.js)
Claim: every call picks eligible primary key with lowest use count, ties -> least recently used (getKey 118-141), so keys rotate even without errors. Eligible = not in cooldown (118-121).
Claim: on 429 (result status 429 at 231-233, or thrown error with status/statusCode 429 or text 429/RESOURCE_EXHAUSTED 248-255) key put in cooldown 60 s (DEFAULT_COOLDOWN_MS line 6, markRateLimited 178-182) and request retried with next key if attempts left (234-238, 256-260).
Claim: attempts per request = min(total keys, 4 with paid key else 3) (207).
Exceptions: timeouts (504) and other errors do not switch (gemini.js:88-90,104; keyPool 246,266). Paid key: see Q7. When every key cooling, picks soonest-to-recover (155-160).

## Q7 paid key
Claim: getKey uses paid key only when no primary is eligible (142-151) and paid key not itself cooling (145). Cap: maxAttempts = min(6,4)=4 (207), so one request with five failing free keys uses 4 free keys, never reaches paid. Paid reached when all five free are inside a 60 s cooldown at the moment of picking (from earlier 429s, possibly earlier requests), e.g. request 2 within a minute: fifth free key, then paid on next attempt. Reserve key env names parseKeysFromEnv 19-20. Test: keyPool.test.js:70-76 (all primaries cooling -> paid).
Also: repeated-key guard 213-226 can pick paid if no untried eligible free key.
Exceptions: paid key itself in cooldown -> falls to free key with earliest recovery (153-160). Simulation derived by hand from lines 109-161, 191-245 (not run).

## Q8 directory search
Claim: client-side over loaded companies: useCompanyDirectory.js:47-55; search.js:4-5 split on commas, trim, lowercase, drop empties; search.js:8-10 matches when ANY term is contained (substring, case-insensitive) in ANY field; empty terms -> all (9). Fields: name, tags, city, sector label (useCompanyDirectory.js:50-55). Combined with filters by AND (73-79). Description is not searched. Placeholder text DirView.jsx:251. Sector label from sector definitions else SECTORS constants (54; constants.js:4-11).
Exceptions: none found (searched: grep matchesTerms/parseSearchTerms in src; used also by JobView? not needed).

## Q9 Submission in Review banner
Claim: SubmitBasicInfo.jsx:28 isDraft = existingCompany && existingCompany.is_draft; 109 renders banner. existingCompany set only in handleEnrich (useSubmitForm.js:183-187), from /api/enrich response `existing_company`; cleared to null when the response has none (185). Failed enrich (429/!ok) returns early (139-146) leaving old value.
Claim: existing_company built by findExistingCompany (enrichDb.js:51-98): first company (limit 1, :72) whose website contains the domain; is_draft = status==='draft' (91); returns null with no DB credentials, error, or 3 s timeout (67,80,82,94-97).
Claim: cached replay: enrichPipeline.js:275-277 returns cached first (before lookup at :102 only reached when not cached); cached profile includes existing_company saved at 364/376-377; enrichmentCache.js:122 spreads profile; TTL 90 days (saveEnrichmentCache 163 ttl param, enrichPipeline 377 passes 90). Not saved when partial (enrichPipeline.js:376, enrichmentCache.js:167).
Exceptions: live match -> different banner "Already Registered" (SubmitBasicInfo.jsx:27,90) and submit opens contact modal (useSubmitForm.js:264-267). Cache banner only when neither (121).
Not tied to pressing submit.

## Q10 test gate (src/scripts/test_gate.py)
Claim: check() runs as pre-commit hook (hook_body 187-203; install 206-221; installed only if no other pre-commit/core.hooksPath, optional per stratosphere-setup SKILL.md:223). Looks at staged changes vs HEAD (160-163): adds/mods/deletions, no rename detection.
Claim: skipped: UNGATED patterns (40-41): *.md, *.mdx, *.txt, *.rst, docs/*, .memory/*, .agents/*, .claude/*, .github/*, LICENSE*, .gitignore, .gitattributes, png/jpg/jpeg/gif/svg/webp/ico; pattern without "/" matches the file name at any depth (53-55), patterns with "/" match the full path from root; symlinks/submodules skipped (42,167).
Claim: every other staged file must be in .tmp/test-gate.json with identical blob hash from a passing `record` run, deletions recorded as gone (168-171, save_record 79-92); else exit 1 and commit blocked (172-180). `record` records every changed path in working tree (git status), not only related ones (81-87), only if the test command exited 0 (65-76).
Exceptions: none besides above. (searched: whole file)

## Q11 removed assertions (floor_guard.py)
Claim: test files = TEST_RX (28): dir tests/test/__tests__/spec(s)/, test_*, *_test.x, *.test.x, *.spec.x, Test(s).java. Assertion line = ASSERT_RX (41). Counts added vs removed lines per test file (160); flags only if SUM over all changed test files of (added-removed) < 0 (161); then reports each test file where removed > added (162-163). Edited line = 1 removed + 1 added (diff -U0, 179; parse_diff 96-101).
Diff = merge base with default branch -> working tree incl. untracked (175-181, untracked 103-111: skips >1 MB, binary, symlink).
Exception: row `tests-removed <glob> — reason` under "## Floor exceptions" in ARCHITECTURE.md at default-branch tip (55,184-188). Exit 1 block.
Entry points: 3d-implement-issue.md:69, 3z-afk-loop.md:59, 4a-verify-and-ship.md:24.

## Q12 thresholds (floor_guard.py)
Claim: THRESHOLDS 47-54. fail_under / --cov-fail-under / --max-warnings|maxWarnings in CONFIG files (pytest.ini, pyproject.toml, setup.cfg, tox.ini, .coveragerc, package.json, .github/workflows/*) (43); lines/branches/functions/statements in jest/vitest config.* or package.json (44); codecov target lowered / threshold raised (45). Coverage minimums looser = lower; max-warnings and codecov threshold looser = higher.
Condition: a removed line carrying the key must exist (136-137 `if not sides["rem"]: continue`); flagged if the added value is looser than removed (lowest vs lowest for min, highest vs highest for max) or no added value (138-140). Grouped by key across all files (134) not per file. New threshold with nothing removed: silent. Tightening silent.
Exception: `threshold <glob>` row (55,186-188).

## Q13 higher version? (build/validate.py)
Claim: validate.py:295-296: error only if sha256 differs from fork-point manifest AND version string is equal. Different (even lower) passes. Only for paths already in the baseline manifest (`path in prev`); baseline = merge-base with origin default (249-258); no baseline manifest -> nothing compared (279-285). Version must match x.y.z (292-293). sha256 from build.py:273 body_hash of built file.
Claim: separate bump_guard.py (CI on PRs only: build-guard.yml:36-38): if manifest or shipped scripts differ from last release tag then plugin VERSION must be higher than the tag's (bump_guard.py:81-98); this one does demand strictly higher but for the plugin VERSION, not per document.

## Q14 date line only
Claim: body_hash (_versioning.py:32-40) drops only frontmatter lines whose key is `version` or `timestamp` (line key = text before first colon, stripped). So editing `timestamp:` alone leaves sha256 unchanged -> validate.py:295 does not flag (e.g. src/rules/okf-protocol.md:10, src/workflows/3d-implement-issue.md:10 carry timestamp).
Exception: manifest also stores `timestamp` (build.py:273; read_version _versioning.py:21-27) so manifest differs -> bump_guard.py:81 still sees a change (needs plugin VERSION above last tag, 96). `generated:` block date (`at:` nested line, e.g. src/memory-templates/ARCHITECTURE.md:5-7): key is `at` not stripped -> counts as content. A date written in body counts. Needs frontmatter at start of file (split_frontmatter 11-16); no frontmatter -> nothing stripped.

## Self-check pass
Re-opened each cited line above while composing; adjustments made: Q2 narrowed to "unless known to fail"; Q5 narrowed to adapter instance + not in nightly script; Q7 says "can only" for the all-five-cooling case; Q13 says "different", not "higher"; Q14 splits timestamp vs generated.at.
