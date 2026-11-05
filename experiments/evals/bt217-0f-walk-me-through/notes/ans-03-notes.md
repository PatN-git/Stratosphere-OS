# Runner 03 notes (claims -> file:line, re-checked)

CTH = C:\Users\patri\Dev\CleanTechHub @26b46f7 ; SOS = C:\t\b217 @bdce919

Entry point (CTH nightly): .github/workflows/job-ingestion-cron.yml:5 cron '0 2 * * *' -> `node scripts/run-job-ingestion.js` (:57); env passes only GEMINI_API_KEY (:51), no GEMINI_API_KEYS/GEMINI_BACKUP_KEY.
run-job-ingestion.js:422 runAtsIngestionBatch -> adapters.js:119 getAdapterForCompany (new adapter per company, :63-97; default/custom -> new FallbackEngine :95) -> adapter.extractJobs -> upsertJobCandidates (supabaseClient.js:41-45 -> buildJobRows + writeJobRows).

## Q1 live / draft / archived
- Score: jobRowBuilder.js:41 title <=2 chars -> 0; :55 invalid http(s) link -> 0; :57 base 30; :58-66 points; :67-70 caps (talent pool 75, portal 80, unverified taxonomy 80, function other 83).
- Adapters compute confidence_score (e.g. ashby.js:67); buildJobRows uses it if present (jobRowBuilder.js:242-244).
- Disqualifiers :99 unreachable, :113-116 foreign (only if no affirmative German match :108-111), :123-125 talent pool, :132 portal, :140-142 unverified taxonomy; :158 hasDisqualifier.
- :162 primaryReason null only if score>=85 and no disqualifier. Precedence :24-31 unreachable first, then foreign.
- Status :255-268: live if score>=85 & no reason; foreign_location primary -> 'archived'; any other reason -> draft.
- Override: jobWriter.js:217-245 demotion guard: if a stored row with the same apply_link is 'live', the written status is forced 'live' (no exception for archived).
- Later archive: jobDeltaReconciler.js:182-185 only live jobs of that company; :319-326 missing from scan -> counter+1, archived at >=2; only called when the company returned >=1 candidate (adapters.js:124-131) and not dry run (:128).
- Lifecycle guard (run-job-ingestion.js:505 skipped on --skip-lifecycle/dry run/quota exhausted/timeout): lifecycleGuard.js:109-121 posted_at >180 days -> archived; :144 404/410 -> archived; :157-159 5xx -> archived at 2nd consecutive failure; :176-186 soft-404 text -> archived; :202-203 other non-2xx same 2-failure rule; :224 network error keeps status.

## Q2 apply-link 10 points
- jobRowBuilder.js:66 `if (job.is_http_200 !== false) score += 10;` -> given unless explicitly marked false.
- Prereq :41, :55 (else score 0). Grep over non-test code: is_http_200 only ever set `true` (teamtailor.js:123,194; heavenhr.js:99,120; deel.js:70); no code sets false.
- If false: :99 also unreachable -> draft (precedence top).

## Q3 department vs title
- classifierRules.js:135-144: tier1 title 15 / dept 5; tier2 7.5 / 2.5; tier3 3.75 / 1.25 -> dept = one third; `else if` -> dept counts for a tier only when title missed it.
- :147-150 inhibitor in title OR dept -> -15 (same weight).
- :162 title-only score is 2nd tie-breaker; :167 best < 4 -> 'other'.
- Callers passing a department: ashby.js:60, gemini.js:351, join.js:89 (category), recruitee.js:84, personio.js:90, workable.js:53 (dept + function), domSelector.js:246. Title only: greenhouse.js:50, hibob.js:115, heavenhr.js:96, teamtailor.js:114, talentstorm.js:115, deel.js:58.

## Q4 work mode / seniority / job type
- taxonomy.js:41-51 workMode keywords; :53-211 experience; :26-39 employmentType.
- Adapters: ashby.js:42-43 (workplaceType, then title, then isRemote), :57 employmentType||title, :59 experience(title); greenhouse.js:33 (location, then title), :47 title, :49 title; personio.js:70-72, :87, :89 (title+seniority+yearsOfExperience); recruitee.js:65 remote flag, :81, :83 experience_code||title; workable.js:35, :50, :52; talentstorm.js:97 (title only), :112, :114 seniority then title; gemini.js:333 AI field then title, :347-348.
- Fill-in defaults at write: jobRowBuilder.js:278-280 experienced / full_time / hybrid.
- Some adapters default earlier: deel.js:55-57, heavenhr.js:62, teamtailor.js:97,111.

## Q5 60-second pause
- gemini.js:258-261 on status 429 or body containing "quota": quotaTracker.record429(60); return [] (cascade stops).
- rateLimiter.js:83-86 cooldown = now + 60 s; :88-96 auto-clears.
- Tracker per adapter instance gemini.js:184; checked at :201, :207 (same instance only).
- adapters.js:119 new adapter per company; fallbackEngine.js:34 new GeminiFlashAdapter per FallbackEngine -> pause never reaches next company.
- adapters.js:145-163 circuit breaker only on thrown error; Gemini returns [] (fallbackEngine.js:64-71) -> no batch stop.
- Separate: keyPool.js:6 DEFAULT_COOLDOWN_MS 60000; :233/:255 markRateLimited on 429; :287 defaultKeyPool singleton shared (gemini.js:42,185) -> key cooldown does carry across companies in the same run.
- runFallbackIngestion (fallbackEngine.js:172 skips companies while paused) is not called by the nightly entry (grep: only exported).

## Q6 key switch
- keyPool.js:109-170 getKey every call: least-used non-cooling primary, tie = oldest lastUsedAt (:127-141).
- :231-238 returned 429 -> markRateLimited(60 s) and retry next key; :248-260 thrown 429/RESOURCE_EXHAUSTED same.
- :207 maxAttempts = min(keys incl. backup, 4 with backup / 3 without); :240-244, :262-264 then throws 429.
- :246 other results returned, :266 other errors thrown -> no switch.
- :153-161 all cooling & no usable backup -> free key whose cooldown ends first.

## Q7 paid key
- keyPool.js:142-151 paid chosen only when no primary key is out of cooldown and paid not cooling.
- :213-226 if pick was already tried this request and no untried non-cooling free key -> paid key if untried.
- :207 with 5 free + paid -> 4 attempts; a single request starting with 5 fresh free keys stops after 4 free keys (each pick prefers eligible primary) -> paid not reached.
- Cooldown 60 s :6/:180. Nightly workflow passes no reserve key var (job-ingestion-cron.yml:51; parse :18-20).

## Q8 directory search
- search.js:4-5 split on commas, trim, lowercase; :8-11 any term substring-in any field, lowercase.
- useCompanyDirectory.js:49-55 fields: name, tags, city, sector label; :73-79 AND with other filters.
- DirView.jsx:251 search box input; supabase.js:33 description loaded but not searched.
- Spaces not split (only commas). Example "SolarX" is illustrative.

## Q9 banner
- SubmitBasicInfo.jsx:28 isDraft = existingCompany.is_draft; :109-118 banner.
- useSubmitForm.js:133-146 after AI Auto-fill (needs website, not rate-limited/failed); :183-187 sets existingCompany from response.
- enrichDb.js:72 first company whose website contains the domain (case-insensitive, limit 1); :80 3 s timeout; :91 is_draft = status==='draft'; errors -> null.
- enrichPipeline.js:95-98 cache hit returns before lookup (:102); cached profile carries whatever existing_company was saved (:364, cache 90 days enrichmentCache.js / pipeline :319).
- Non-draft match -> "Already Registered" instead (:27,:89).

## Q10 test gate
- test_gate.py:160-171 check: staged files vs HEAD (or empty tree first commit), --cached.
- :167 skip UNGATED (:40-41) and symlinks/submodules (:42).
- :53-55 pattern without "/" matches file name any depth; with "/" matches full path from repo root.
- :169-170 blocked unless record holds same blob (deleted -> must be recorded deleted).
- Runs as pre-commit hook (:187-200) once installed.

## Q11 assertions removed
- floor_guard.py:6 diff base = merge base with default branch (or --base) to working tree incl. untracked (:179-184).
- :28 TEST_RX test file paths; :41 ASSERT_RX; :159-162 net sum across test files < 0 -> flag each test file with removed > added.
- :188 exception rows `tests-removed <glob>` on default-branch tip skip; :189 row added on branch = violation.
- Exit 1 (:195).

## Q12 thresholds
- :47-54 keys & files: fail_under, --cov-fail-under (pytest.ini, pyproject.toml, setup.cfg, tox.ini, .coveragerc, package.json, .github/workflows/*); lines/branches/functions/statements (jest/vitest config, package.json); codecov target (min) threshold (max); --max-warnings/maxWarnings (CONFIG files only).
- :135-141 needs a removed line; old = min/max of removed; new = min/max of added; flagged if lower (min keys) / higher (max keys) or removed with none added; pooled per key across files.
- Tightening silent; new threshold with no removed line not checked (:136).
- Exceptions :188 `threshold <glob>`.

## Q13 version bump
- validate.py:295-296 error when sha256 differs from baseline and version string is equal -> requires a different version, not higher (no ordering).
- :292-293 must be x.y.z (_versioning.py:4).
- :249-264 baseline merge-base with origin/<default> or default, else last v* tag, else HEAD.
- :295 only paths present at baseline; manifest = .md files in dist/skills bundle (build.py:263-273).
- bump_guard.py:95-101 separate PR-only check (build-guard.yml:33-37): plugin VERSION must be higher than last release tag when shipped content changed.

## Q14 date line
- _versioning.py:32-41 body_hash strips only frontmatter lines whose key is `version` or `timestamp`.
- `timestamp:` date edit -> same hash -> not a change.
- `generated:` / `at:` date (OKF v0.2, :25-26) is hashed -> counts as change; e.g. dist/skills/2a-write-prd/references/PRD-template.md uses generated.
- Any date in the body counts.
