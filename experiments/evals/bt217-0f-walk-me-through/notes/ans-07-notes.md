# Notes runner 07 (claims with file:line, re-read against source before answering)

CTH = C:\Users\patri\Dev\CleanTechHub ; SOS = C:\t\b217

## Q1 (CTH) live / draft / archived
- jobRowBuilder.js:255 status = score >= 85 ? 'live' : 'draft'; :162 score>=85 && !hasDisqualifier -> primaryReason null (live); :158 hasDisqualifier = unreachable|foreign|talent pool|portal fallback|taxonomy unverified
- :258-263 primaryReason foreign_location -> status archived; other primaryReason -> draft
- :24-31 precedence unreachable_link, foreign_location, generic_talent_pool, portal_fallback, unverified_taxonomy, missing_metadata (unreachable outranks foreign)
- :99 unreachable = is_http_200===false || is_unreachable || invalid http(s) link; :113-118 foreign only if no German match; :139-142 unverified = function not in canonical list or company taxonomy flag false
- :67-70 caps: talent pool 75, portal 80, unverified 80, function 'other' 83 (all < 85)
- adapters never set is_http_200:false/is_foreign/taxonomy flags (grep src+scripts) - only read in backfill script
- jobWriter.js:88-94 demotion guard: stored live row stays live on upsert
- jobDeltaReconciler.js:182-185 only company's live jobs; :319-326 missing from scan -> consecutive_missing_scans+1, >=2 -> archived; :225 refreshed link for same title/region relinked instead
- lifecycleGuard.js:144-154 404/410 archived; :157-168 5xx archived at failures>=maxServerFailures(:94 default 2); :172-187 soft-404 text archived; :109-122 posted_at older than 180d archived; :201-211 other non-2xx same 2-failure rule
- run-job-ingestion.js:505-516 lifecycle guard runs after ingestion unless skipped/dryRun/quota/timeout

## Q2 (CTH) the 10 points
- jobRowBuilder.js:66 `if (job.is_http_200 !== false) score += 10` -> 10 pts unless flagged as failing; no other 10-pt apply link item
- :55 invalid/missing http(s) link -> score 0; :57 base 30 (title+link valid); :64-65 direct-looking link +15 else +5; isDirect requires !portal fallback
- is_http_200 set true in deel.js:70, heavenhr.js:99,120, teamtailor.js:123,194; never false in nightly adapters

## Q3 (CTH) department vs title
- classifierRules.js:135-144 title tier1/2/3 = 15/7.5/3.75; dept (only if title did not match that tier, else-if) = 5/2.5/1.25 -> title 3x
- :147-150 inhibitor -15 if title OR dept matches
- :167 best score < 4 -> 'other'
- adapters passing department: ashby:60, domSelector:246, gemini:351, join:89, personio:90, recruitee:84, workable:53; title only: greenhouse:50, deel:58, heavenhr:96/110, hibob:115, talentstorm:115, teamtailor:114/187

## Q4 (CTH) work mode, seniority, job type
- taxonomy.js:41-51 workMode keywords: remote/telecommut/homeoffice -> remote, then hybrid, then on-site words; :26-39 employmentType keywords; :53-211 experience from title keywords, else undefined
- adapters feed title plus source fields: e.g. greenhouse.js:33,47-49; ashby.js:42-43,57-59 (isRemote flag); workable.js:35-36 (telecommuting); recruitee.js:65 offer.remote
- jobRowBuilder.js:278-280 defaults experience 'experienced', employment_type 'full_time', work_mode 'hybrid' when missing
- some sources default earlier: deel.js:55-57, heavenhr.js:62, teamtailor.js:97,111

## Q5 (CTH) 60-second AI pause
- gemini.js(adapter):258-261 on status 429 or body containing 'quota' -> quotaTracker.record429(60); return []
- rateLimiter.js:83-86 sets flag, cooldownUntil = now + 60*1000; :88-96 expires; no sleep/wait
- gemini.js:201,207 extractJobs/extractFromHtml return [] while exhausted
- adapters.js:119 getAdapterForCompany per company -> :95 new FallbackEngine; fallbackEngine.js:34 new GeminiFlashAdapter -> new QuotaTracker (gemini.js:184) per company
- runFallbackIngestion (shared engine, fallbackEngine.js:172) not called from nightly (grep: no caller)
- adapters.js:145-163 nightly quota stop only on thrown error with 429; Gemini path returns [] not throw (gemini.js:261)
- keyPool.js:6,178-182 separate per-key 60 s cooldown, defaultKeyPool singleton shared (gemini.js adapter:185)

## Q6 (CTH) key switch
- keyPool.js:118-141 getKey picks eligible free key with lowest usageCount, tie oldest lastUsedAt, every call
- :231-239, :253-259 on 429 (returned or thrown) markRateLimited(key) (60 s, :6,178) and retry next
- :207 maxAttempts = min(allKeys.length, backup ? 4 : 3)
- :246/:266 other results/errors returned/thrown, no switch (timeouts 504 returned in gemini.js adapter:88-90)

## Q7 (CTH) paid key
- keyPool.js:142-151 backup chosen only if no eligible primary (all cooling) and backup not cooling
- :207 with backup: maxAttempts=min(6,4)=4 -> one request tries at most 4 keys; attempt 3 throws (:234-244)
- :153-161 if backup also cooling -> free key with earliest rateLimitedUntil
- "would" scenario traced from code, not from a test (test keyPool.test.js:70-75 covers 2 free keys + backup)

## Q8 (CTH) search
- search.js:4-5 split on comma, trim, lowercase, drop empty; :8-11 any term, any field, includes (substring, case-insensitive)
- useCompanyDirectory.js:50-55 fields: name, tags, city, sector label; :73-79 AND with other filters
- DirView.jsx:65,251 wired to Search input

## Q9 (CTH) banner
- SubmitBasicInfo.jsx:28,109-112 isDraft = existingCompany && existingCompany.is_draft -> banner; :27,90 else Already Registered
- useSubmitForm.js:183-187 existingCompany set only in handleEnrich from d.existing_company (AI Auto-fill)
- enrichDb.js:72,91 lookup: companies website ilike *domain*, limit 1; is_draft = status==='draft'; 3 s timeout :80, failure -> null :94-97
- enrichPipeline.js:96-98 cache hit returns before lookup; :364 existing_company saved in payload; :379 cached 90 days -> cached reply replays stored match
- submit.js:179 new submissions stored status 'draft'

## Q10 (SOS) test gate
- test_gate.py:162 check: git diff --cached vs HEAD (staged only), --no-renames; :167 skip ungated or SKIP_MODES; :170 path must be in record with equal blob hash (deleted -> None)
- :40-41 UNGATED list; :53-55 pattern without "/" matches basename any depth, with "/" matches path from root; :42 modes 120000,160000
- :189-199 hook runs check; :203 install
- dist copy identical to src (diff)

## Q11 (SOS) tests removed
- floor_guard.py:28 TEST_RX; :41 ASSERT_RX; :159-162 per test file (added,removed) counts; flag only if sum(a-r) < 0, then every file with r > a
- :179-180,185-188 diff base merge base -> working tree incl untracked (:184); exceptions rows 'tests-removed <glob>' from default tip only (:55,185)
- deleted test file counted as removed: parse_diff :86-87

## Q12 (SOS) thresholds
- floor_guard.py:47-54 THRESHOLDS; :43-44 CONFIG/JS_CONFIG; :125-141 threshold_changes: only when a removed line carries the key; old=min/max removed, new=min/max added or None; flag if None or loosened
- tests/scripts/test_floor_guard.py:104 new threshold added without removed line stays clean; :82-86 lowered flagged

## Q13 (SOS) version bump
- validate.py:295-296 error if path in baseline manifest and sha256 differs and version == baseline version; only equality, no order check
- :266,249-264 baseline = merge-base with default branch (fallback tag, HEAD); :292 semver format only
- build.py:260-275 manifest = every .md in bundle: version + body_hash
- bump_guard.py:95-101 separate script: plugin VERSION must be > last tag when shipped content changed

## Q14 (SOS) date line
- _versioning.py:44-54 body_hash removes only frontmatter lines whose key is `version` or `timestamp`
- generated: {by, at} (glossary.md frontmatter; okf-protocol.md:32-38): `at:` line key is 'at' -> kept in hash
- okf-protocol.md:10,24 timestamp is a build field for out-of-scope files
- validate.py:295 mismatch -> needs different version

## Self-check
Re-opened each line above while writing (all reads in this session). Wording kept: conditions (unless known to fail; unreachable outranks foreign; net total across all test files; only when removed line carries key; equality not ordering; fresh adapter per company).
