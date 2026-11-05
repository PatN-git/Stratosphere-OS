# Notes ans-11 (claims with file:line; each re-opened and confirmed)

CTH = C:\Users\patri\Dev\CleanTechHub, SOS = C:\t\b217

## Q1 (entry: .github/workflows/job-ingestion-cron.yml cron 0 2 * * * -> scripts/run-job-ingestion.js -> runAtsIngestionBatch adapters.js:99 -> upsertJobCandidates supabaseClient.js:41-44 -> buildJobRows)
- live iff score>=85 and no disqualifier: jobRowBuilder.js:162 (primaryReason null), :255 status live
- disqualifiers: unreachable (is_http_200===false / is_unreachable / invalid link) :99; foreign :113; talent pool :123; portal fallback :132; unverified taxonomy :139-142; hasDisqualifier :158
- precedence unreachable > foreign > talent pool > portal > taxonomy > missing metadata: :24-31, loop :165-190
- archived only when primaryReason === foreign_location :258-260 (so unreachable link wins -> draft)
- other reason -> draft :261-263; score<85 w/o reason -> missing_metadata draft :191-196, :266-267
- foreign check skipped when affirmative German match :104-115
- demotion guard: stored live row (same apply_link) forced to live, reason cleared: jobWriter.js:88-95 (and :129-135 collision path)
- several adapters drop non-German on-site jobs before the builder unless remote: greenhouse.js:36, ashby.js:46, personio.js:76, gemini.js:336
- missing from scans: live jobs of company not in scan; counter +1; >=2 archived: jobDeltaReconciler.js:319-326; only when company returned >=1 candidates adapters.js:124, not dryRun :128; relink if same title+region new link :223-317
- lifecycle guard (runs after ingestion unless skipped run-job-ingestion.js:505): only status live rows (lifecycleGuard.js:384), not checked within 3 days (:378, :386); archives: no link :97-106, posted_at >180d :44,:109-122, 404/410 :144, soft-404 on 2xx :172-187, 5xx :157-168 and other non-2xx :201-212 once failures>=2 (:94), network error keeps status :219-228; 200 healthy -> live, reset :190-197

## Q2
- invalid/missing http(s) link or title <=2 chars -> score 0: jobRowBuilder.js:41, :55
- base 30 :57; +10 when is_http_200 !== false :66; direct-job-URL pattern 15 else 5 :64-65 (not for portal fallback)
- grep non-test src/scripts/api: no `is_http_200: false`; only `true` in deel/heavenhr/teamtailor/ingest-tier4/benchmarkHelpers; backfill reads DB column scripts/backfill-draft-reasons.js:102
- adapters call calculateConfidenceScore (e.g. greenhouse.js:56)

## Q3
- classifierRules.js:134-144 tier1 title 15 / dept 5, tier2 7.5/2.5, tier3 3.75/1.25; dept only if title missed that tier (else if); inhibitor -15 either title or dept :146-150; winner <4 -> 'other' :167
- department passed: ashby.js:60, domSelector.js:246, gemini.js:351, join.js:89 (category), personio.js:90, recruitee.js:84, workable.js:53; title only: deel.js:58, greenhouse.js:50, heavenhr.js:96/110, hibob.js:115, talentstorm.js:115, teamtailor.js:114/187

## Q4
- taxonomy.js:26-216 mapTaxonomy.employmentType/workMode/experience keyword rules
- greenhouse.js:34-35,:60-62 (location/title); ashby.js:42-43 workplaceType then title then isRemote; :61 employmentType||title; personio.js:68-71,:92-94 (employmentType+schedule+title; seniority+years); gemini.js:329,:347-348 AI field then title
- defaults when nothing found: jobRowBuilder.js:278-280 (experienced, full_time, hybrid); score computed before defaults on the candidate (:242-244; points only if truthy :58-62)

## Q5
- gemini.js:259-261 429 or body includes 'quota' -> quotaTracker.record429(60) -> return []; rateLimiter.js:83-86 fixed 60 s; :88-96 isQuotaExhausted; gemini.js:201,:207 skip while paused
- Retry-After header is not used for pause (:96 only in result headers)
- per-instance tracker: gemini.js:184; new adapter per company adapters.js:119, getAdapterForCompany :63-97 (FallbackEngine builds its own GeminiFlashAdapter fallbackEngine.js:34)
- run's circuit breaker needs a thrown 429 adapters.js:145-163; Gemini path returns [] not throw
- runFallbackIngestion (shared engine) not used by nightly (grep) ; nightly = run-job-ingestion.js calls runAtsIngestionBatch :422
- key pool is process-wide singleton gemini.js:23,:185; keyPool.js:287

## Q6/Q7 (keyPool.js)
- getKey :109-170: least-used eligible primary :125-141; backup only if no eligible primary and backup not cooling :142-151; fallback :153-161
- 429 -> markRateLimited(key) 60000 ms :6,:178-181,:233,:255; rotate while attempt < maxAttempts-1 :234,:256
- maxAttempts = min(allKeys.length, backup?4:3) :207
- non-429 result returned as is :246; non-429 throw rethrown :266
- repeat-key branch :213-226
- cap exhaustion throws 429 :240-244

## Q8
- useCompanyDirectory.js:47-55,:78 matchesSearch(name, tags, city, sector label); search.js:4-11 split on comma, trim, lowercase, substring `includes`, any term in any field; combined AND with other filters :73-79; DirView.jsx:65 uses hook, :251 search box
- sector label from sectorDefs[c.sector].label else SECTORS label :54

## Q9
- SubmitBasicInfo.jsx:28 isDraft = existingCompany && existingCompany.is_draft; banner :109-118
- existingCompany set only in handleEnrich useSubmitForm.js:183-187 (from /api/enrich response, after AI Auto-fill; clears if absent)
- enrichPipeline.js:102 findExistingCompany(domain); :364 existing_company included when found; enrichDb.js:77 website ilike *domain*, limit 1 :70; :91 is_draft = status==='draft'
- cache: enrichPipeline.js:96-98 returns cached early; :379 saves finalPayload (includes existing_company); enrichmentCache.js:112-129 spreads profile -> cached match replayed (90 days TTL :11)

## Q10 (src/scripts/test_gate.py; .agents copy identical)
- check :160-179: staged diff vs HEAD (:162), skip ungated or symlink/submodule :167, SKIP_MODES :42; untested if path not in record or hash differs; deleted staged None :169
- UNGATED :40-41; matching rule :53-55 (pattern w/o "/" matches file name any depth; others anchored)
- hook installed only via install :203-218 (not over foreign hook/core.hooksPath); hook body :187-200
- record saves every changed file in `git status` after passing run :79-92

## Q11/Q12 (src/scripts/floor_guard.py)
- diff base merge-base default branch -> working tree + untracked :175-184
- TEST_RX :28; ASSERT_RX :41; tests-removed :159-162 (net across all test files <0, then lists files where removed>added)
- exceptions `tests-removed|threshold <glob> — reason` from default-branch tip :185-188, EXC_RULES :55, EXC_RE :57
- THRESHOLDS :47-54; CONFIG :43; JS_CONFIG :44; CODECOV :45; threshold_changes :125-141 (flag only if a removed line carried key :137; min-type: new<old or removed; max-type: new>old)
- findings exit 1 :192-195

## Q13/Q14
- validate.py:269-298 _check_manifest_bumps: error iff path in baseline and sha256 differs and version equal :295; semver format check :292; no ordering compare (grep)
- baseline :249-266 merge-base HEAD with origin/<default> or default, else last tag, else HEAD; baseline manifest read :283-290 (if unreadable prev empty -> nothing flagged)
- manifest = every .md under dist/skills, build.py:268-273; sha256 = _versioning.body_hash
- _versioning.py:29-39 body_hash: normalize BOM/CRLF; drop only frontmatter lines whose key is exactly version or timestamp; everything else (incl generated: / at:, body) hashed
- read_version :17-28 shows generated.at is a separate date form (legacy timestamp)
- examples read: src/commands/stratosphere-setup/SKILL.md `timestamp: 2026-10-22`; src/dev-skills/.../glossary.md `generated: at: 2026-09-15`
- build/bump_guard.py:78-100: separate PR-only check build-guard.yml (pull_request) on overall VERSION vs last tag
