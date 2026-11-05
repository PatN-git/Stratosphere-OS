# Notes runner 10 (CTH 26b46f7, SOS bdce919)

Entry points: CTH nightly = .github/workflows/job-ingestion-cron.yml (cron 0 2 * * *) -> scripts/run-job-ingestion.js:269 runJobIngestionPipeline -> adapters.js:99 runAtsIngestionBatch -> getAdapterForCompany (adapters.js:63, new adapter per company per loop at :119) -> upsertJobCandidates (supabaseClient.js:41) -> buildJobRows -> writeJobRows. Lifecycle guard: run-job-ingestion.js:505-509.

## Q1 ledger (Claim / Applies when / Exceptions found (searched))
- Live needs score>=85 AND no disqualifier. jobRowBuilder.js:162 (primaryReason null only if score>=85 && !hasDisqualifier), :255 status = score>=85?live:draft, :264-268. Applies: every row built in nightly (supabaseClient.js:42). Exceptions: demotion guard (jobWriter.js:88-94) keeps stored-live live; searched grep "status" in src/lib/ingestion.
- Disqualifiers = unreachable/invalid link (:99), foreign location (:113), generic talent pool (:123-125), portal fallback (:132), unverified taxonomy (:140-143). Score also capped: talent pool 75, portal 80, unverified 80, job_function other 83 (:67-70) -> all <85.
- Else draft with highest-priority reason (DRAFT_REASON_PRECEDENCE :24-31; loop :165-196; buildJobRows :261-263). Exception: foreign_location primary -> status archived (:258-260). Unreachable outranks foreign (precedence :25-26) so unreachable+foreign = draft. Foreign only when no German region match (:108-113). Several adapters drop foreign on-site jobs before this (ashby.js:44-46, gemini.js ~L338) unless remote.
- Stored live row is never demoted by re-scan: jobWriter.js:17, 67-95 (matches by apply_link); composite collision path :129-135.
- Archive via reconcile: live job of company absent from scan; nextMissing>=2 -> archived (jobDeltaReconciler.js:319-326); reset to 0 when seen (:341-348); only status=live jobs of that company (:182-185); only runs when company's extraction returned >=1 candidate and not dryRun (adapters.js:124-131). Exception: if a candidate with same sanitized title+region has a new link, job is relinked not counted missing (:219-226, 307-312); collision with active row archives displaced job (:283-290).
- Archive via lifecycle guard: only status live, last_checked_at null or older than 3 days (lifecycleGuard.js:381-388, 329-338), batch limit rolling 3-day cycle min 25 (:307-313). Rules: no link (:97-107); posted_at older than 180d (:44, 109-123); 404/410 (:144-154); soft-404 text on 2xx (:172-186); 5xx or other non-2xx (e.g. 403): archived when failures>=2 (maxServerFailures default 2 :94; :157-169, :201-212); network error/timeout: status unchanged (:213-228); healthy 2xx resets failures (:189-198). Guard skipped on dryRun, runLifecycle false, quotaExhausted, timedOut (run-job-ingestion.js:505).

## Q2
- Claim: +10 if job.is_http_200 !== false (jobRowBuilder.js:66). Applies: any scored candidate with a valid http(s) link; invalid link -> score 0 (:55). Exceptions: searched is_http_200 across api src scripts: only set to `true` (deel:70, heavenhr:99,120, teamtailor:123,194, ingest-tier4:231), never false -> others unset => counts as pass. Also +15 for link looking like job page (not portal fallback) else +5 (:64-65); valid link is 15 of base 30 (:57 comment).

## Q3
- Title tier hit 15/7.5/3.75, department hit 5/2.5/1.25 (classifierRules.js:132-142, comments "1.5x"/"0.5x"). Dept considered for a tier only if title did not match that tier (else-if :132,136,140). Inhibitors -15 from title OR dept (:145-149). Winner score <4 -> 'other' (:166-170 region: `if (sorted[0][1] < 4) return 'other'`). Dept passed only by some adapters: ashby:60, domSelector:246, gemini:351, join:89 (category), personio:90, recruitee:84, workable:53; title only: greenhouse:50, heavenhr:96,110, hibob:115, deel:58, talentstorm:115, teamtailor:114,187. Searched: grep jobFunction( in adapters + fallbackEngine.

## Q4
- mapTaxonomy.workMode/experience/employmentType (taxonomy.js:23-60 etc) keyword rules on text. Inputs per adapter (grep): e.g. ashby.js:42,57,59 (workplaceType, employmentType, title); workable.js:35,50,52; personio.js:70,87,89; gemini.js:333,347-348 (model value then title); teamtailor:97,111,113 title and defaults. If no match undefined; buildJobRows defaults experience 'experienced', employment_type 'full_time', work_mode 'hybrid' (jobRowBuilder.js:278-280); score computed before defaults (:242-244) except deel/heavenhr/teamtailor default in adapter, recruitee:90-94 and domSelector:267-271 default only inside the score call.

## Q5
- gemini.js:258-262: on callGemini result status 429 or body containing 'quota' -> quotaTracker.record429(60), return []. 60 hard-coded (not Retry-After). rateLimiter.js:83-86. Tracker per adapter instance (gemini.js:184), new adapter instance per company (adapters.js:63-97 `new FallbackEngine()`/`new GeminiFlashAdapter()`; fallbackEngine.js:34 new GeminiFlashAdapter). Only consumers of isQuotaExhausted: gemini.js:201,207; fallbackEngine.js:172 (runFallbackIngestion, not used by cron: grep). Nightly run stops only if extractJobs throws 429 (adapters.js:145-162); Gemini path returns [] so no throw. Company still touched in normal completion (run-job-ingestion.js:465-474). Key pool cooldown separate (keyPool.js:6,178-182), defaultKeyPool shared singleton (gemini.js:23,185; keyPool.js:287).

## Q6
- keyPool.js:109-170 getKey: least used eligible free key, tie least recently used; 429 (result :231 or thrown :248-251) -> markRateLimited 60s (:178, :6) and retry with another key, maxAttempts = min(#keys, backup?4:3) (:207), last attempt throws 429 (:240-245,:262-264). Other errors rethrown (:266) / non-429 result returned (:246). Exceptions searched: executeWithRetry body.

## Q7
- Paid (backup) key: getKey :142-151 only when no free key eligible (all in cooldown) and backup not itself cooling; also :220-225 within a request. Max 4 attempts with a backup (:207) -> with 5 fresh free keys one request makes 4 free attempts and throws (:240-245), the paid key is not reached in that request; next request has 4 cooling, 5th tried, then paid. If paid also cooling -> picks free key with earliest cooldown end (:153-161). Workflow passes only GEMINI_API_KEY (job-ingestion-cron.yml env); backup env names keyPool.js:19-20.

## Q8
- search.js:4-11 parseSearchTerms/matchesTerms: comma split, lowercased, any term included (substring) in any field. useCompanyDirectory.js:49-55 fields: name, tags, city, sector label (sectorDefs label or SECTORS label). AND with other filters :73-79. DirView.jsx:65,222 uses filteredCompanies. constants.js:4-11 built-in labels (none contains "solar"). Not description (not in list).

## Q9
- SubmitBasicInfo.jsx:28,109: banner when existingCompany.is_draft. existingCompany set only at useSubmitForm.js:183-186 in handleEnrich (AI Auto-fill) from response d.existing_company. enrichDb.js:51-93: ilike website contains domain, limit 1, 3 s timeout, is_draft = status==='draft'; null if no creds/!ok/error (:67-68,:80,:96-99). enrichPipeline.js:102,276,364. Cache: returns cached payload early (:96-99) which includes saved existing_company (enrichmentCache.js:121-123; saved :379). Non-draft match -> "Already Registered" banner (SubmitBasicInfo.jsx:26,91). Submissions inserted status 'draft' (api/submit.js:179).

## Q10 (test_gate.py)
- check() :160-179: `git diff --cached` vs HEAD (or empty tree); skip ungated(path) or mode 120000/160000 (:167); blocked if path not in record or record blob != staged blob (None for deletes) (:169-170). UNGATED :40-41, matching :53-55 (no "/" pattern matches basename any depth; with "/" matches full path, fnmatch * crosses /). Hook is the pre-commit (:187-200), install refuses foreign hook or core.hooksPath (:203-212). Exceptions searched: whole file.

## Q11 (floor_guard.py)
- find() :159-162; TEST_RX :28; ASSERT_RX :41; diff base merge-base default branch -> working tree + untracked (:6, 175-184, untracked :103-111); flagged only if sum(added - removed) over all test files < 0, then each test file with removed>added (:160-162). Exceptions: `tests-removed <glob>` rows read from default-branch tip only (:11, 185-188); rows added elsewhere = violation (:189). Deleted test file counted via parse_diff (:86-87). Untracked >1MB or binary skipped (:106,109).

## Q12
- THRESHOLDS :47-54, CONFIG :43, JS_CONFIG :44, CODECOV :45; threshold_changes :125-141: only when a line of that key was removed (:136); loosened = new<old for min keys / new>old for max keys, or removed with none added (:138-141); path matched by file name scope at any depth (:129). Exception row `threshold` (EXC_RULES :55). Tightening/pure additions silent.

## Q13 (build/validate.py)
- :295 error only if sha256 differs AND version == baseline version; baseline = merge-base with default branch (:246-266), manifest dist/skills/stratosphere-setup/versions.json (:270,:283-286); only paths present in baseline manifest (`path in prev`); semver x.y.z format check :292. No ordering/greater-than comparison anywhere in validate.py (searched for compare: none). bump_guard.py:93-100 separate: plugin VERSION must be > last tag when shipped content changed.

## Q14
- _versioning.py:35-45 body_hash strips frontmatter lines whose key (before first ':') stripped is version or timestamp; everything else hashed incl. generated.at lines and body. Manifest built from *.md in dist bundle build.py:259-273 using body_hash. Examples read: dist/skills/3d-implement-issue/SKILL.md has timestamp: 2026-10-22; dist/.../memory/ARCHITECTURE.md has generated: at: 2026-09-29.

## Self-check
Re-opened lines above while reading; wording kept conditions: "unless explicitly false", "second consecutive", "net total", "only when removed line existed".
