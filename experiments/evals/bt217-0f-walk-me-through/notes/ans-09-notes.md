# Notes runner 09 (quotes + claims; CTH=26b46f7 working tree, SOS=bdce919)

## Q1 CTH job live/draft/archived
Entry: scripts/run-job-ingestion.js:422 runAtsIngestionBatch -> adapters.js:197 upsertJobCandidates -> supabaseClient.js:43 buildJobRows.
- jobRowBuilder.js:255 `let status = score >= 85 ? 'live' : 'draft';`
- :258-263 `if (primaryReason === 'foreign_location') { status = 'archived'; ...} else if (primaryReason) { status = 'draft'; draft_reason = primaryReason; }`
- :158 `const hasDisqualifier = isUnreachable || isForeign || isGenericTalentPool || isPortalFallback || isTaxonomyUnverified;`
- :162 `if (score >= 85 && !hasDisqualifier) { primaryReason = null; } else { for (const reason of DRAFT_REASON_PRECEDENCE) ...`
- :24-31 precedence: unreachable_link, foreign_location, generic_talent_pool, portal_fallback, unverified_taxonomy, missing_metadata
- :99 `isUnreachable = candidate.is_http_200 === false || candidate.is_unreachable === true || !applyUrlValid;`
- :108-115 affirmative German match: germanRegions.length>0 || germany|deutschland in text || region_id && != 'unassigned' || region_ids non-empty; isForeign = !match && (isForeignLocation(locInput) || candidate.is_foreign === true)
- :139-142 unverified taxonomy: job_function present and not canonical, or taxonomy_verified===false / company_taxonomy_verified===false
- :67-70 caps: talent pool 75, portal fallback 80, taxonomy unverified 80, job_function other 83 (all < 85)
- jobWriter.js:17 `Demotion guard: an automated re-scan or upsert never demotes a stored status = 'live' row.`; :90-93 `if (liveLinks.has(clean.apply_link)) { clean.status = 'live'; clean.draft_reason = null; }`
- jobDeltaReconciler.js:182-185 only existing `.eq('status','live')`; :319-326 `nextMissing = (job.consecutive_missing_scans||0)+1; ... if (nextMissing >= 2) updatePayload.status = 'archived'`
- adapters.js:124-131 delta only `if (Array.isArray(candidates) && candidates.length > 0)` ... `if (company.id && !dryRun)`
- lifecycleGuard.js: :16 MAX_JOB_AGE_MS 180 d; :92-ish no apply_link -> archived; 404/410 archived; >=500 and other non-2xx: failures>=maxServerFailures(2) archived; soft-404 pattern archived; healthy 2xx live + check_failures 0; network error keeps status, failures+1.
- run-job-ingestion.js:505 `skipLifecycleGuard = !runLifecycle || dryRun || ingestionSummary.quotaExhausted || timedOut;`
- lifecycleGuard.js:380-ish runLifecycleGuard selects `.eq('status','live')`, last_checked_at null or older than 3 days (minAgeDays 3), oldest first.

## Q2 10 points apply link
- jobRowBuilder.js:41 `if (!job.title || ... job.title.trim().length <= 2) return 0;`
- :55 `if (!applyUrlValid) return 0;` (valid = new URL() ok, protocol http: or https:)
- :57 `let score = 30; // valid title (15) + valid apply_link (15)`
- :64-65 direct job URL pattern +15 else +5
- :66 `if (job.is_http_200 !== false) score += 10;`
- grep is_http_200: set `true` in ingest-tier4.js:231, deel.js:70, heavenhr.js:99/120, teamtailor.js:123/194; no non-test source sets false; other adapters leave unset; backfill-draft-reasons.js:102 reads column from DB.

## Q3 department vs title
- classifierRules.js:135 tier1 title +15 / `else if (normDept && rules.tier1.test(normDept)) score += 5`
- :139 tier2 title 7.5 / dept 2.5 ; :143 tier3 title 3.75 / dept 1.25 ; comments "1.5x title ... 0.5x dept"
- :147 inhibitor: `rules.inhibitors.test(normTitle) || (normDept && ...test(normDept))` -> -15 once
- :167 `if (sorted[0][1] < 4) return 'other';`
- callers pass dept: ashby.js:60, domSelector.js:246, gemini.js:351, join.js:89, personio.js:90, recruitee.js:84, workable.js:53. No dept: greenhouse.js:50, deel.js:58, heavenhr.js:96, hibob.js:115, talentstorm.js:115, teamtailor.js:114/187.

## Q4 work mode / seniority / job type
- taxonomy.js:41 workMode(input) keywords remote/hybrid/on-site/vor ort/office; :53 experience(input); :26 employmentType(input)
- greenhouse.js:33 workMode(location)||workMode(title); :47 employmentType(title); :49 experience(title)
- ashby.js:42-43 workMode(job.workplaceType)||workMode(title); `if (!workMode && job.isRemote) workMode='remote'`; employmentType(job.employmentType || title)
- gemini.js:333,347,348 (model output fields then title)
- personio.js:70,87,89 ; workable.js:35,50,52 ; recruitee.js:65 offer.remote
- jobRowBuilder.js:278-280 `experience: candidate.experience || 'experienced', employment_type: ... || 'full_time', work_mode: ... || 'hybrid'`
- adapter-level defaults: deel.js:55-57, heavenhr.js:62, teamtailor.js:97/111

## Q5 60-second AI pause
- gemini.js:259-262 `if (geminiRes && (geminiRes.status === 429 || JSON.stringify(geminiRes.body || '').includes('quota'))) { this.quotaTracker.record429(60); return []; }`
- gemini.js:184 `this.quotaTracker = options.quotaTracker || new QuotaTracker();` (per adapter instance); :201 and :207 `if (this.isQuotaExhausted()) return [];`
- rateLimiter.js:83-86 record429(retryAfterSeconds=60): cooldownUntil = now + seconds*1000; :88-96 clears after expiry
- adapters.js:119 `const adapter = getAdapterForCompany(company);` inside per-company loop; :91-92 `case 'gemini': return new GeminiFlashAdapter();` default `new FallbackEngine()` -> fallbackEngine.js:34 `new GeminiFlashAdapter(...)`
- adapters.js:145-162 run-level stop only when an error is THROWN with status 429 / 429|RESOURCE_EXHAUSTED text -> quotaExhausted, break; the adapter returns [] instead of throwing.
- gemini.js:122-129 defaultCallGemini converts a 429 into a returned {ok:false,status:429}, not a throw.
- runFallbackIngestion (fallbackEngine.js:172) shares one engine but is not called by the nightly script (grep: only run-job-ingestion.js -> runAtsIngestionBatch).

## Q6 key switch
- keyPool.js:6 DEFAULT_COOLDOWN_MS = 60000
- :118-141 getKey: eligiblePrimary = keys whose rateLimitedUntil <= now; picks lowest usageCount, tie oldest lastUsedAt
- :207 `maxAttempts = Math.min(allKeys.length, this.backupKey ? 4 : 3)`
- :231-238 `result.ok === false && result.status === 429` -> markRateLimited(key); `if (attempt < maxAttempts - 1) continue;` else throw 429
- :248-258 thrown error with status 429 / statusCode 429 / /429|RESOURCE_EXHAUSTED/ message -> same; else :266 `throw err`; non-429 result returned at :246.

## Q7 paid key
- keyPool.js:142-151 `else if (this.backupKey) { ... if (!backupStats || backupStats.rateLimitedUntil <= now) { ... chosenKey = this.backupKey; } }` only when eligiblePrimary.length === 0
- :6/:178 cooldown 60 s per key; :207 5 free + paid = 6 keys -> min(6,4)=4 attempts.
- :1-4 header "Engaged ONLY when all primary free-tier keys are rate-limited".

## Q8 directory search
- DirView.jsx:65 useCompanyDirectory; :251 Search placeholder "Search companies, tags, cities..."
- useCompanyDirectory.js:49-55 terms = parseSearchTerms(searchInputValue); matchesTerms(terms,[c.name, c.tags ?? [], c.city, sector label])
- search.js:4-5 split on "," , trim, lowercase, drop empty; :8-11 `!terms.length || terms.some(term => fields.flat().some(f => typeof f === "string" && f.toLowerCase().includes(term)))`
- :73-79 combined with other filters by &&.

## Q9 banner
- SubmitBasicInfo.jsx:28 `isDraft = Boolean(existingCompany && existingCompany.is_draft)`; :109 `{isDraft && (` banner text "Submission in Review"
- useSubmitForm.js:130 handleEnrich (AI Auto-fill button) ; :183-187 setExistingCompany(d.existing_company) else null
- enrichPipeline.js:102 findExistingCompany(domain); :364 existing_company attached
- enrichDb.js:72 `companies?website=ilike.*domain*...&limit=1`; :91 `is_draft: r.status === 'draft'`; :67,:82 returns null if no config / not ok; :80 3000 ms timeout
- enrichPipeline.js:96-98 cache hit returns before lookup; enrichmentCache.js:122 spreads saved profile (finalPayload incl existing_company saved at :377).

## Q10 test-gate
- test_gate.py:160-179 check(): diff --cached --raw vs HEAD; skip `ungated(path) or new_mode in SKIP_MODES` (120000,160000); `if path not in files or files[path] != staged: untested.append(path)`; staged None if status D.
- :40-41 UNGATED list; :53-55 ungated(): pattern w/o "/" matches basename, else full path (fnmatchcase)
- :79-93 save_record records every path from `git status --porcelain` incl untracked after a passing run
- :187-199 hook runs `.agents/scripts/test_gate.py check`

## Q11 floor guard assertions
- floor_guard.py:28 TEST_RX; :41 ASSERT_RX; :159-162 `count = lambda lines: sum(1 for l in lines if ASSERT_RX.search(l)); tests = {p: (count(added), count(removed)) for ... if TEST_RX.search(p)}; if sum(a - r ...) < 0: out += [("tests-removed", p, 0, ...) for p,(a,r) in tests.items() if r > a]`
- :179 diff -U0 -M vs base (merge base with default branch) -> working tree; untracked added :184 (text files <=1 MB)
- :55,:188 exceptions "tests-removed <glob>" rows at default-branch tip suppress.

## Q12 thresholds
- floor_guard.py:47-54 THRESHOLDS; :43-45 CONFIG/JS_CONFIG/CODECOV scopes; :125-141 threshold_changes: `if not sides["rem"]: continue; old = (min if loosens=="min" else max)(removed); new = (...)(added, default None); if new is None or (new < old if min else new > old): yield`
- :163 -> rule "threshold"; exit 1 on any finding (:192-195).

## Q13 / Q14 validator
- validate.py:295 `if path in prev and meta["sha256"] != prev[path]["sha256"] and meta["version"] == prev[path]["version"]: errs.append(... content changed but version not bumped ...)`; :292 version must match SEMVER x.y.z
- :249-264 baseline = merge-base HEAD with origin/<default> or default, else last tag, else HEAD; :281-288 prev = {} if manifest unreadable at baseline
- build.py:263-273 manifest over every .md in dist/skills; sha256 = _versioning.body_hash(text)
- _versioning.py:32-41 body_hash: normalize (BOM, CRLF), then drops frontmatter lines whose `l.split(":",1)[0].strip() in ("version","timestamp")`; everything else hashed (body, other frontmatter lines incl `generated:` and nested `at:`).
- Data: src/references/audit-inputs.md:4 `timestamp: 2026-10-20` (stripped); src/memory-templates/ARCHITECTURE.md:5-7 `generated:\n  by: ..\n  at: 2026-09-29` (not stripped: key "at").
- bump_guard.py:96 `if semver(cur_v) <= semver(tag_v):` error — separate PR-only check (build-guard.yml PR step), plugin VERSION must exceed last release tag when shipped content changed.

## Self-check
Re-read numbered output of each file above during writing; wording below keeps conditions (85 threshold, unreachable outranks foreign, 2 missing scans, 180 d, 60 s, 4 attempts, etc.).
