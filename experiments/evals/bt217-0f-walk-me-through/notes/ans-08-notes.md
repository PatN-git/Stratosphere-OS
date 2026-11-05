# Runner 08 notes — claims with file:line (self-checked)

CTH = C:\Users\patri\Dev\CleanTechHub @26b46f7 ; SOS = C:\t\b217 @bdce919

## Entry points
- Nightly: .github/workflows/job-ingestion-cron.yml:5 (cron 02:00), :51 only GEMINI_API_KEY passed, :56 runs scripts/run-job-ingestion.js
- run-job-ingestion.js:422 runAtsIngestionBatch; :505 lifecycle skipped if !runLifecycle||dryRun||quotaExhausted||timedOut; :509 runLifecycleGuard
- adapters.js:119 getAdapterForCompany per company (inside loop); :95 default -> new FallbackEngine(); :92 'gemini' -> new GeminiFlashAdapter()
- adapters.js:130 reconcileCompanyJobDelta only when candidates.length>0 (:124) and !dryRun
- adapters.js:197 upsertJobCandidates -> supabaseClient.js:43 buildJobRows + dedupe -> jobWriter.writeJobRows

## Q1 live/draft/archived
- jobRowBuilder.js:41 title<=2 chars -> 0; :55 invalid http(s) link -> 0
- :255 status = score>=85 ? live : draft; :162 primaryReason null only if score>=85 && !hasDisqualifier
- :158 disqualifiers: unreachable, foreign, talent pool, portal fallback, taxonomy unverified (missing_metadata is not one)
- :99 unreachable = is_http_200===false || is_unreachable || invalid URL
- :108-116 foreign only if no affirmative German match
- :139-142 unverified = job_function not canonical OR taxonomy_verified/company_taxonomy_verified === false
- :24-31 precedence unreachable > foreign > talent pool > portal > taxonomy > missing_metadata
- :258-260 primaryReason foreign_location -> archived
- adapters drop non-remote foreign jobs before scoring: ashby.js:46, gemini.js:336, greenhouse.js:36 etc. (deel has none)
- jobWriter.js:77-93 demotion guard: stored live link -> status live, draft_reason null (overrides draft AND archived)
- jobDeltaReconciler.js:185 only live jobs of that company; :216 present check; :223-225 same title+region with new link -> relink; :282-288 colliding active -> displaced archived; :319-326 nextMissing>=2 -> archived
- lifecycleGuard.js:384,387 only live, last_checked null or older than 3 days (:328/:378); :97 no link -> archived; :109-121 posted_at >180 days -> archived; :144 404/410 -> archived; :157-159 5xx failures>=2 (maxServerFailures default 2 :94); :176 soft-404 -> archived; :196 healthy resets 0; :202-203 other non-2xx failures>=2; :219-224 network error keeps status but +1
- schema.sql:214 posted_at DEFAULT CURRENT_DATE

## Q2 10 points
- jobRowBuilder.js:66 `if (job.is_http_200 !== false) score += 10;`
- :41,:55 preconditions; :64-65 separate 15/5 direct-URL points; caps :67 75, :68 80, :69 80, :70 83
- grep: is_http_200 set only to true (deel.js:70, heavenhr.js:99/120, teamtailor.js:123/194); never false in src
- adapters precompute confidence_score; buildJobRows :242 uses it if defined

## Q3 department vs title
- classifierRules.js:135 tier1 title 15 / :136 dept 5 (else-if); :139/:140 7.5/2.5; :143/:144 3.75/1.25 -> dept = 1/3 of title
- :147-149 inhibitor -15 from title or dept equally; :12 data_ai inhibitors include sales
- :157-165 ties: tier1 count, then title-only score, then canonical order; :167 <4 -> other
- callers with department: ashby.js:60, personio.js:90, recruitee.js:84, workable.js:53 (dept+function), join.js:89 (category), domSelector.js:246, gemini.js:351; without: greenhouse, deel, heavenhr, hibob, talentstorm, teamtailor

## Q4 work mode / seniority / job type
- taxonomy.js:41-51 workMode keywords (remote/telecommut/homeoffice/home office; hybrid; on-site/onsite/vor ort/\boffice\b)
- taxonomy.js:26-39 employmentType (student/werkstudent/intern/praktik -> working_student first)
- taxonomy.js:53-211 experience; :100-113 director/vp/chief... -> senior_management unless assistant
- per adapter fields: greenhouse.js:33,47,49; gemini.js:333,347,348; ashby.js:42-43,57,59; personio.js:70-72,87,89; workable.js:35-36,50,52; recruitee.js:65,81,83; hibob.js:91-93,112,114; talentstorm.js:97,112,114; join.js:63-68,86,88
- defaults in adapter: deel.js:55-57 (all three); heavenhr.js:62,71-76 (work mode, emp type); teamtailor.js:97,111 / 170,184 (work mode, emp type)
- score-with-defaults: recruitee.js:90-95; domSelector.js:267-272
- jobRowBuilder.js:278-280 stored defaults experienced/full_time/hybrid; :59-61 points 10/10/8

## Q5 60-second AI pause
- gemini.js:259-261 status 429 OR body JSON includes 'quota' -> quotaTracker.record429(60); return []
- rateLimiter.js:83-86 cooldownUntil = now + 60s; :88-95 exhausted until then; :73-77 per-instance state
- gemini.js:184 new QuotaTracker per adapter instance; fallbackEngine.js:34 new GeminiFlashAdapter per engine; adapters.js:95/119 new per company
- gemini.js:201,207 paused adapter returns []
- Retry-After header ignored by record429(60) (gemini.js:260)
- adapters.js:134-163 429 breaker only on thrown error; gemini returns [] so no throw
- keyPool.js:287 shared singleton; :178-182 per-key 60s cooldown (DEFAULT_COOLDOWN_MS :6)
- runFallbackIngestion (fallbackEngine.js:172 defers on shared engine) not called by nightly (grep)

## Q6 key switching
- keyPool.js:109-141 getKey least-used eligible primary, tie oldest lastUsedAt; :117-121 skip cooling keys
- :142-151 all primary cooling -> backup if not cooling; :154-161 else soonest-ending primary
- :207 maxAttempts = min(allKeys, backup?4:3); :231-239 429 result -> markRateLimited, continue; :248-261 thrown 429/RESOURCE_EXHAUSTED same
- :246 any other result returned; :266 other errors rethrown -> no switch
- :213-226 already-tried key -> untried non-cooling primary, else backup

## Q7 paid key with five free
- maxAttempts min(6,4)=4 (:207); paid via getKey only when eligiblePrimary empty (:142)
- worked: k free keys cooling at start; paid reached at attempt i>=5-k, i<=3 -> k>=2
- keyPool.js:16-20 paid key vars GEMINI_BACKUP_KEY|GEMINI_PAID_KEY|GEMINI_API_KEY_BACKUP; cron yml:51 passes only GEMINI_API_KEY

## Q8 directory search
- search.js:4-5 split on comma, trim, lowercase; :8-11 any term, substring includes, case-insensitive
- useCompanyDirectory.js:50-55 fields name, tags, city, sector label; :73-79 ANDed with other filters
- DirView.jsx:65 uses the hook

## Q9 Submission in Review banner
- SubmitBasicInfo.jsx:28 isDraft = existingCompany && is_draft; :109-117 banner; :27/:90 live -> Already Registered
- useSubmitForm.js:133-201 handleEnrich (button only, SubmitBasicInfo.jsx:41); :139-146 429/!ok return before set; :183-187 set/clear
- enrichDb.js:72 website ilike *domain* limit 1; :91 is_draft = status==='draft'
- enrichPipeline.js:95-99 cache hit returns early; :102 lookup; :364 existing_company in payload; :378 saved to cache (90 days)
- enrichmentCache.js:97 expires_at > now; :121-123 profile spread (incl. existing_company)
- normalizeDomain lowercases, strips www (enrichmentCache.js:29-30)

## Q10 test gate
- test_gate.py:160-171 check: git diff --cached vs HEAD (empty tree first commit); untested if not recorded or hash differs; deleted -> must be recorded None
- :40-41 UNGATED list; :53-55 patterns without "/" match file name; fnmatchcase (case-sensitive)
- :42/:167 skip symlinks, submodules
- hook :195-196 runs check

## Q11 tests-removed
- floor_guard.py:179-184 diff merge-base(default branch) -> working tree, + untracked (:103-111)
- :41 ASSERT_RX; :159 counts lines; :160 test files via TEST_RX :28; :161 total net <0; :162 per-file r>a
- :185-188 exceptions from default-branch tip ARCHITECTURE.md Floor exceptions; pr_body.py:95-102 base

## Q12 thresholds
- floor_guard.py:43-54 keys/files/direction; :125-141 removed side required; old/new min or max; new None -> removed
- :188 exception rows

## Q13 version bump
- validate.py:295-296 error only if sha differs AND version equal -> different version required, not higher
- :291-293 semver x.y.z; :295 `path in prev` -> new docs not checked; :249-266 baseline merge-base, fallback v* tag, HEAD
- build-guard.yml:28 rebuild before :31 validate; bump_guard.py:95-101 plugin VERSION must exceed last tag (PRs only, yml:37)

## Q14 date line
- _versioning.py:32-41 body_hash strips only frontmatter lines keyed version/timestamp
- ARCHITECTURE.md memory template uses generated: at: (src/memory-templates/ARCHITECTURE.md:5-7); in manifest versions.json:18
- 79 src files have top-level timestamp:, 18 have generated:

## Self-check
Re-opened each cited line above; wording keeps conditions (e.g. "unless explicitly marked as failing", "version equal" not "not higher"). Dropped: claim that PRD-template uses generated-at (its own frontmatter uses timestamp:).
