# Notes runner 02 (claims -> file:line, re-checked against the lines read)

CTH = C:\Users\patri\Dev\CleanTechHub (HEAD 26b46f7). SOS = C:\t\b217 (HEAD bdce919).
Entry point CTH nightly: .github/workflows/job-ingestion-cron.yml (cron 0 2 * * *) -> scripts/run-job-ingestion.js -> runAtsIngestionBatch (adapters.js:99) -> adapter.extractJobs -> upsertJobCandidates (supabaseClient.js:41) -> buildJobRows (jobRowBuilder.js:240) -> writeJobRows (jobWriter.js:59).

## Q1
- score >= 85 -> 'live' else 'draft': jobRowBuilder.js:255; primaryReason set -> draft (261-263); foreign_location -> archived (258-260).
- primaryReason null only if score>=85 && no disqualifier: jobRowBuilder.js:158,162. Disqualifiers: unreachable, foreign, generic talent pool, portal fallback, unverified taxonomy (158). Missing fields are NOT a disqualifier (158) -> live if score>=85.
- Precedence unreachable_link > foreign_location > generic_talent_pool > portal_fallback > unverified_taxonomy > missing_metadata: jobRowBuilder.js:24-31, loop 165-190. So foreign only archives when link not unreachable.
- Caps: talent pool 75, portal fallback 80, unverified taxonomy 80, job_function 'other' 83: jobRowBuilder.js:67-70. Score 0 if title <=2 chars or link not http(s): 41,55.
- foreign: jobRowBuilder.js:105-116 (no German region match, no Germany/Deutschland text, no region_id other than 'unassigned', no region_ids; AND isForeignLocation or is_foreign===true). Adapters set region_ids to company.region if no location match and company.region != 'unassigned' (greenhouse.js:~39-40).
- Adapters drop foreign non-remote openings before building: greenhouse.js:35-37.
- Stored live row never demoted by re-scan: jobWriter.js:88-95 (liveLinks -> status live), 129-131.
- Later archiving: reconciler 2 consecutive missing scans jobDeltaReconciler.js:319-326; lifecycle guard lifecycleGuard.js: 404/410 144, soft-404 176-186, 5xx/other non-2xx archived when check_failures>=2 (maxServerFailures 2) 157-159, 201-203, older than 180 days 44,109-122, network error keeps status 224. Guard runs on status live only, skipped on dry run/quota/timeout: run-job-ingestion.js:505, lifecycleGuard.js:384.

## Q2
- `if (job.is_http_200 !== false) score += 10;` jobRowBuilder.js:66. Whole score 0 if link not valid http/https: 46-55. Base 30 incl. valid link 15 (57). Direct-looking link +15 else +5 (64-65).
- Non-test code sets is_http_200 only to true (deel.js:70, heavenhr.js:99,120, teamtailor.js:123,194, ingest-tier4.js:231, benchmarkHelpers.js:297); others leave it unset. No non-test false found (grep).

## Q3
- classifierRules.js:134-144 weights: tier1 title 15 / dept 5; tier2 7.5 / 2.5; tier3 3.75 / 1.25; dept counts per tier only when title missed that tier (else-if). Inhibitor -15 title or dept (147-150). Winner must score >=4 else 'other' (167). Talent-pool title -> undefined (117-123).
- Department passed in by: ashby.js:60, domSelector.js:246, gemini.js:351, join.js:89 (category), personio.js:90, recruitee.js:84, workable.js:53 (dept + function). Title only: greenhouse.js:50, deel.js:58, heavenhr.js:96,110, hibob.js:115, talentstorm.js:115, teamtailor.js:114,187.
- Dept alone: tier1 5 >= 4 OK; tier2 + tier3 = 3.75 < 4 (arithmetic from 140,144).

## Q4
- taxonomy.js:26-51 employmentType, workMode; 53-211 experience (seniority); keyword rules over text. Inputs vary by connector: greenhouse.js:34,46-49 (location name/title); ashby.js:41,53-56 (workplaceType, isRemote, employmentType, title); personio.js:68-71,92-94; gemini.js:~336-348 (model-extracted fields, then title).
- Defaults when nothing recognised: experience 'experienced', employment_type 'full_time', work_mode 'hybrid': jobRowBuilder.js:278-280. Score credits only values the connector found (59-61).

## Q5
- Pause: QuotaTracker.record429(60) gemini.js:260; rateLimiter.js:83-86 (cooldownUntil = now + 60 s), isQuotaExhausted 88-96. Tracker is per adapter instance: gemini.js:184 (new QuotaTracker()).
- Nightly creates a fresh adapter per company: adapters.js:90-97 (new GeminiFlashAdapter()/new FallbackEngine() -> fallbackEngine.js:34 new GeminiFlashAdapter), called in loop adapters.js:110-117.
- While paused, that instance returns [] : gemini.js:201,207. Fixed 60, not Retry-After: gemini.js:260.
- Nightly uses runAtsIngestionBatch, not runFallbackIngestion (run-job-ingestion.js:21; grep); runFallbackIngestion is the one that defers other companies on isQuotaExhausted (fallbackEngine.js:172).
- Run-level quota stop reacts to errors escaping the extractor matching 429/RESOURCE_EXHAUSTED: adapters.js:126-136; Tier-4 errors are caught in fallbackEngine.js:66-72.
- Key pool cooldown is separate, shared singleton: keyPool.js:6,178-181,287.

## Q6
- keyPool.js:109-170 getKey: eligible primary = not in cooldown (118-121), least used then oldest last use (125-141). 429 (result status 429 or thrown 429/RESOURCE_EXHAUSTED): markRateLimited 60 s (6, 178, 233, 255) then rotate if attempts left (234-238, 256-260). maxAttempts = min(total keys, backup ? 4 : 3) (207). After last attempt throws 429 (240-244, 262-264). Other errors rethrown (266); non-429 results returned (246). 504 timeout is returned as result gemini.js:84-86 (no rotation).

## Q7
- keyPool.js:142-150 backup only when no eligible primary and backup not in cooldown. If backup also cooling: free key with earliest cooldown end (153-161). Second path 213-226: key already tried, no untried eligible primary, backup untried -> backup. maxAttempts 4 with backup (207) -> with 5 free keys one request from all-healthy tries 4 free keys. Backup env: keyPool.js:19-20. Nightly workflow passes only GEMINI_API_KEY: job-ingestion-cron.yml:51.
- Reasoning: request 1 fails on 4 free keys (all cooling), 5th still eligible; request 2 uses 5th, on 429 next getKey has no eligible primary -> paid key. Stated as "would".

## Q8
- search.js:4-11 lowercase, comma split, trimmed, empty dropped; match if any term is substring (includes) of any field, case-insensitive; no terms -> everything. Fields: useCompanyDirectory.js:50-55 name, tags, city, sector label. Combined with other filters via && (73-79). DirView.jsx:65 uses hook, placeholder 251.

## Q9
- SubmitBasicInfo.jsx:28,110-120 banner iff existingCompany.is_draft truthy. existingCompany set from /api/enrich response d.existing_company in handleEnrich (useSubmitForm.js:183-187) -> only after AI Auto-fill click (needs website; 124-128); reset to null if response has none; not updated on failed request (129-137).
- enrichDb.js:79 lookup companies.website ilike *domain*, limit=1; is_draft: status === 'draft' (91); returns null on missing creds, error, or 3 s timeout (65, 100-102 area, 3000).
- Cached answers reuse saved payload incl. existing_company: enrichPipeline.js:94-99, 364, 377-379; enrichmentCache.js:121-135 (90 days DEFAULT_CACHE_TTL_DAYS 13).
- Not draft status match -> "Already Registered" banner instead: SubmitBasicInfo.jsx:27,90-92.

## Q10
- test_gate.py check 160-179: staged diff vs HEAD (diff --cached, no renames) 162; skip ungated (53-55, UNGATED 40-41) and modes 120000/160000 (42,167); file must be in .tmp/test-gate.json with same blob hash (169-170) (deletion needs recorded absence); record written only on passing run (73-76) and covers all changed files (79-91). Hook runs .agents/scripts/test_gate.py (identical copy of src, diff checked).

## Q11
- floor_guard.py:159-162, TEST_RX 28, ASSERT_RX 41. Net across all test files negative -> list files with removed > added. Diff base merge base w/ default branch to working tree incl. untracked (6, 175-184, 103-111). Exceptions: rule `tests-removed` glob row on default-branch tip (185-188, EXC_RULES 55). Unchanged-line moves net out (arithmetic).

## Q12
- floor_guard.py:47-54 THRESHOLDS, 125-141 threshold_changes: must have a removed line with the key (136); min-type (fail_under, --cov-fail-under, lines/branches/functions/statements, codecov target): flagged if lowered or removed; max-type (codecov threshold, --max-warnings/maxWarnings): flagged if raised or removed (138-141). Files: CONFIG 43, JS_CONFIG 44, CODECOV 45, path match 129. Exception rule `threshold` (55, 188). Tightening silent (doc line 8).

## Q13
- validate.py:269-298: compare sha256 in built versions.json vs merge-base baseline manifest (249-266, 281-288); error only when sha256 differs AND version equal (295-296); format x.y.z (292). Paths absent in baseline not checked (295 `path in prev`); baseline unreadable -> prev {} (281-288). Not "higher": equality only.
- Separate: bump_guard.py:95-101 plugin VERSION must exceed last release tag when shipped content changed (81-89).

## Q14
- _versioning.py:32-41 body_hash drops frontmatter lines whose key is `version` or `timestamp` only. build.py:273 uses it. Docs with `timestamp:` (155 files in dist/skills) -> date edit invisible. Docs with `generated:` block + nested `at:` (e.g. dist/skills/2a-write-prd/references/PRD-template.md; stratosphere-setup memory ARCHITECTURE.md) -> `at:` key not stripped -> counts.
