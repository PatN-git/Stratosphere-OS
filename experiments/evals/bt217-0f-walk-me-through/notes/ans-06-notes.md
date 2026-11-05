# Notes runner 06 (claims, scope ledger, self-check)
CTH = C:\Users\patri\Dev\CleanTechHub (HEAD 26b46f7). SOS = C:\t\b217 (HEAD bdce919; src/scripts == .agents/scripts verified by diff for floor_guard/test_gate).
Entry points traced: cron .github/workflows/job-ingestion-cron.yml -> scripts/run-job-ingestion.js:269 runJobIngestionPipeline -> adapters.js:99 runAtsIngestionBatch -> reconcileCompanyJobDelta + upsertJobCandidates (supabaseClient.js:41) -> buildJobRows -> writeJobRows; then runLifecycleGuard (run-job-ingestion.js:509).

## Q1
- Claim: stored status = live iff score>=85 and no disqualifier. jobRowBuilder.js:255 (`score>=85 ? live : draft`), :158-163 (primaryReason null only if score>=85 && !hasDisqualifier), :158 disqualifiers = unreachable (is_http_200===false / is_unreachable / invalid http(s) link :99), foreign, generic talent pool (:123-129), portal fallback (:132), unverified taxonomy (:139-145).
  Applies when: row built at ingest. Exceptions found: foreign -> archived (:258-260); unreachable outranks foreign (precedence :24-31, loop :165-190) so foreign+dead link = draft/unreachable_link; foreign only if no affirmative German match (:108-115) (searched: jobRowBuilder.js whole file). Score<85 without disqualifier -> draft, reason missing_metadata (:191-196, :267).
- Claim: label of draft = highest-ranked reason, order unreachable, foreign, talent pool, portal, unverified taxonomy, missing metadata (:24-31).
- Claim: already-live row with same apply_link stays live, draft_reason null even if new row says draft/archived. jobWriter.js:67-95 (liveLinks, :90-93). Exceptions: lookup failure ignored (:83-85) (searched: jobWriter.js; upsert path :99-108,:161-186 uses guarded chunk). DB trigger also clears draft_reason on live (migration_bt252 trigger) - not stated.
- Claim: live job archived when absent from company's scan twice: jobDeltaReconciler.js:319-326 (nextMissing>=2 -> archived); only status live jobs (:182-185); only when scan returned >=1 candidate and not dry run (adapters.js:124-130); relinked instead if same title+region has a new link (:219-226, relink :307); counter resets when job seen again (:341-348). Exception: companies whose scan returns zero jobs never reach reconcile (adapters.js:124).
- Claim: daily lifecycle guard archives live jobs: no apply link (lifecycleGuard.js:97-107), posted_at >180d (:44,:109-122), HTTP 404/410 (:144-154), soft-404 text on 2xx (:172-187), 5xx or other non-2xx when failure count reaches 2 (:157-169, :201-212; maxServerFailures default 2 :94; not overridden in run-job-ingestion.js:509-512), network error keeps status (:213-228). Applies to status live rows with last_checked_at null or older than 3 days (:384-388, minAgeDays :378), batch limit ceil(n/3) min 25 (:307-313). Skipped when --skip-lifecycle/RUN_LIFECYCLE=false, dry run, quota exhausted, timed out (run-job-ingestion.js:505). Draft rows not touched (eq status live :384) (searched: lifecycleGuard.js, jobDeltaReconciler.js).
  Not claimed: new scan of an existing draft/archived link re-upserts status (not re-verified by test), so omitted.

## Q2
- Claim: +10 if is_http_200 !== false. jobRowBuilder.js:66. Applies: score computed in adapters (e.g. gemini.js:374) or buildJobRows (:242-244). Exceptions: invalid/non-http(s) link returns 0 before this (:46-55). Searched `is_http_200` in src scripts api tests docs/database: set true in deel.js:70, heavenhr.js:99/120, teamtailor.js:123/194, ingest-tier4.js:231, benchmarkHelpers.js:297; set false only in tests (jobRowBuilder.test.js:107,180); read in jobRowBuilder.js:66,99 and backfill-draft-reasons.js:102. So nothing in ingestion sets false.
- Claim: other link points: 30 base includes valid link (:57 comment "valid title (15) + valid apply_link (15)"); +15 direct-looking URL else +5 (:64-65). is_http_200 false also forces draft reason unreachable_link (:99).

## Q3
- Claim: dept hit worth 5/2.5/1.25 vs title 15/7.5/3.75 (classifierRules.js:135-144) = 1/3. Dept counted for a tier only if title did NOT match that tier (else-if, :136,:140,:144). Inhibitor -15 applies from title OR dept, same size (:147-150). Result 'other' if best score <4 (:167); tie-breakers :157-165. Talent-pool titles return undefined (:117-123).
- Adapters passing department: ashby.js:60, gemini.js:351, domSelector.js:246, join.js:89 (category name), personio.js:90, recruitee.js:84, workable.js:53. Title only: deel.js:58, greenhouse.js:50, heavenhr.js:96/110, hibob.js:115, talentstorm.js:115, teamtailor.js:114/187. (searched grep `jobFunction(` src scripts api)
- Dept-only tier1 = 5 >= 4 (qualifies), tier2 alone 2.5 <4, tier3 alone 1.25 <4 (arithmetic from lines above).

## Q4
- Work mode/job type/seniority ("experience"): per-adapter, feed field first then keyword mapper on title (taxonomy.js:26-211). Examples read: ashby.js:42-59 (workplaceType, isRemote, employmentType; experience from title), personio.js:70-89 (experience from name+seniority+yearsOfExperience), recruitee.js:65-83 (remote flag, codes), workable.js:35-52, talentstorm.js:112-114 (seniority field), hibob.js:91-114, greenhouse.js:33-49 (title/location only), gemini.js:333-348 (AI-read job.work_mode etc. then title), domSelector.js:220-243.
- Defaults: buildJobRows jobRowBuilder.js:278-280 (experienced / full_time / hybrid); some adapters default themselves: deel.js:55-57, heavenhr.js:62,74-76, teamtailor.js:97,111, domSelector.js:269-271, recruitee.js:92-94.
- Seniority from feed field only in: personio (:89), recruitee (:83 experience_code), talentstorm (:114), workable (:52), gemini (:347); all other adapters title only.

## Q5
- Claim: pause = QuotaTracker.record429(60) in GeminiFlashAdapter.extractFromHtml gemini.js:259-261 when Gemini result status 429 OR body text contains "quota"; then returns []. While paused: extractJobs/extractFromHtml return [] without calling (gemini.js:201,207). rateLimiter.js:83-96 (60s default; expires on read).
- Claim: nightly creates a NEW adapter per company: adapters.js:119 getAdapterForCompany -> new GeminiFlashAdapter (:92) or new FallbackEngine (:95; fallbackEngine.js:34 new GeminiFlashAdapter) each loop iteration; QuotaTracker per adapter (gemini.js:184). So pause is not shared across companies in nightly. runFallbackIngestion (shared engine, fallbackEngine.js:163-175) is not called by run-job-ingestion (searched grep runFallbackIngestion src scripts api: only defined/re-exported adapters.js:30,57). Within one company only one Gemini extraction call per extractJobs.
- Claim: return [] not throw -> does not trip run-level stop; that stop is adapters.js:145-163 only on a thrown 429/RESOURCE_EXHAUSTED error. defaultCallGemini catches (gemini.js:121-131).
- Fixed 60, Retry-After header not used for it (gemini.js:260). Key pool has own separate 60 s per-key cooldown (keyPool.js:6,178).

## Q6
- keyPool.js getKey :109-170: primary keys not cooling (rateLimitedUntil<=now :118-121), choose lowest usageCount, tie -> oldest lastUsedAt (:126-141), usage recorded (:163-167). executeWithRetry :191-281: on result status 429 (:231) or thrown error with status/statusCode 429 or message /429|RESOURCE_EXHAUSTED/ (:248-251) -> markRateLimited(key) default 60000 (:178, :6) and retry with another key; maxAttempts = min(total keys, backup?4:3) (:207). Non-429 thrown errors rethrown (:266); non-429 failed results returned (:246). Applies in-process memory only (keyStats Map :60). Test tests/unit/geminiKeyPool.test.js:136 "does not retry on non-429".
- Exceptions: last attempt 429 -> throws 429 with Retry-After 60 (:240-244).

## Q7
- Paid key = backupKey. getKey :142-150: only when no eligible primary (all in cooldown) and backup not cooling. executeWithRetry :213-226: if getKey returns an already-tried key, use untried non-cooling primary, else backup if untried. maxAttempts :207 = min(5+1, 4) = 4 (arithmetic). So single request with 5 healthy free keys: 4 attempts all free (each 429 -> cooldown :233), paid not reached; paid reached if >=2 free keys already cooling from earlier calls (arithmetic; labelled "would"). If all cooling and paid cooling too: pick primary with earliest rateLimitedUntil (:153-161). Test geminiKeyPool.test.js:326-339 (all 5 cooling -> paid), :311-324 (never while healthy).
- Reserve key env: GEMINI_BACKUP_KEY / GEMINI_PAID_KEY / GEMINI_API_KEY_BACKUP (keyPool.js:19-20). Cron workflow env passes only GEMINI_API_KEY (job-ingestion-cron.yml env block).

## Q8
- search.js:4-11; useCompanyDirectory.js:49-55: terms split on commas, trimmed, lowercased; matches if ANY term is contained (substring includes) in company name, any tag, city, or sector label (sectorDefs label else SECTORS label). Combined (AND) with other filters (:73-79). No whole-word, no fuzzy, no description field (fields list :50-55). Placeholder DirView.jsx:251.

## Q9
- Banner: SubmitBasicInfo.jsx:28,109-118 shows when existingCompany && existingCompany.is_draft. Only setter: useSubmitForm.js:183-187 inside handleEnrich (AI Auto-fill) from response d.existing_company; set null otherwise. Server: enrichPipeline.js:102 findExistingCompany(domain) ; enrichDb.js:72 `website=ilike.*domain*&limit=1`, is_draft = status==='draft' (:91), 3 s timeout (:80), non-ok/error -> null (:82,:94-96), needs supabase url+key (:67). Live (non-draft) match -> "Already Registered" banner instead (SubmitBasicInfo.jsx:27,90-106). Cache: enrichPipeline.js:77-80 returns cached before lookup; payload saved includes existing_company (:364) with 90 d TTL (saveEnrichmentCache(...,90) in pipeline; cache read enrichmentCache.js:~120-140 spreads profile). Cache path = stale existing_company.
- Not claimed: pre-filled content details.

## Q10
- test_gate.py check :160-179: staged diff vs HEAD (EMPTY_TREE if none) `git diff --cached --raw --no-renames`; skip if ungated(path) or mode 120000/160000 (:167); else path must be in record with same blob sha (deleted: None) (:169-171). UNGATED :40-41 (patterns w/o "/" match basename at any depth :54). Hook only if installed (:203-218), `install` never over foreign hook/core.hooksPath. Record = every changed file at passing run (:79-93). Exceptions: none beyond ungated (searched: test_gate.py all).

## Q11
- floor_guard.py: diff = merge-base with default branch -> working tree incl. untracked (docstring :6; :179-184; untracked() :103-111). tests dict only for paths matching TEST_RX (:28,:160): counts ASSERT_RX lines added vs removed per file (:41,:159-160). Flag only if sum(added-removed) over all changed test files < 0 (:161); then each test file with removed>added reported `tests-removed` (:162). Moved between files nets zero -> silent (test_floor_guard.py:110-111). Deleted test file flagged (test :81). Exception row `tests-removed <glob> — reason` from default branch tip only (:55,:185-188; docstring :11-12). Exit 1 = violation (:195).
- Line-based: a rewritten assertion line counts -1/+1.

## Q12
- threshold_changes :125-141 + THRESHOLDS :47-54. fail_under / --cov-fail-under in CONFIG files (pytest.ini, pyproject.toml, setup.cfg, tox.ini, .coveragerc, package.json, .github/workflows/*) min-type; lines|branches|functions|statements in jest/vitest.config.* and package.json min-type; codecov target min-type, threshold max-type; --max-warnings|maxWarnings in CONFIG files max-type. Flag only if a removed line with that key exists (:136-137); old = min (or max) of removed values, new = min/max of added values; flag if new lower (min-type) / higher (max-type) or no added (:138-141). Brand-new limit (no removed) silent (test :104); moved between files silent (test :108-109); raised silent. Exception row `threshold <glob>` on default tip (:55,:185-188).

## Q13
- validate.py:269-298 `_check_manifest_bumps`: for each artifact in built dist manifest (versions.json) that also exists in baseline manifest: error if sha256 differs AND version == previous version (:295-296). Version only needs to be semver x.y.z (:292-293). Baseline = merge-base with origin/<default> or default; else last tag; else HEAD (:249-264). New artifacts (not in prev) not checked (`path in prev`). Manifest covers .md files in dist bundle only (build.py:262-275). Not "higher": only "not equal".
- bump_guard.py:89-105 separate: plugin VERSION must be > last tag when manifest or shipped src/scripts etc. changed (semver(cur)<=semver(tag) error :98). CI runs both (.github/workflows/build-guard.yml:31,38).

## Q14
- _versioning.py:32-41 body_hash strips frontmatter lines whose key (text before first ':', stripped) is `version` or `timestamp`; normalizes BOM/CRLF (:6-9). `generated:` / nested `at:` NOT stripped. Verified with scratch script (hash06.py outside repo, -B): timestamp-only change same hash True; version-only True; generated.at-only False. Real files: dist/skills/0a-start-session/SKILL.md has `timestamp: 2026-10-22`; dist/.../templates/memory/STATUS.md has `generated:\n  by:\n  at: 2026-10-27`. Body-text dates count (whole body hashed).

## Self-check
Re-read each cited line range while drafting (all ranges above were read in full in this session). Conditions kept: "unless known to fail" (Q2), "only when all primary cooling" (Q7), 2-in-a-row (Q1), net-negative across files (Q11), removed-line requirement (Q12), "same version, not lower" (Q13), key-name-specific (Q14). Q7 "four attempts" is arithmetic from :207; labelled as such.
