# Notes ans-04 (quotes first, then claims). CTH = C:\Users\patri\Dev\CleanTechHub, SOS = C:\t\b217

## Entry point (CTH nightly)
- .github/workflows/job-ingestion-cron.yml: `cron: '0 2 * * *'` ... `run: node scripts/run-job-ingestion.js`
- scripts/run-job-ingestion.js:422 `ingestionSummary = await runAtsIngestionBatch(client, companies, {`
- scripts/run-job-ingestion.js:505-509 `const skipLifecycleGuard = !runLifecycle || dryRun || ingestionSummary.quotaExhausted || timedOut;` ... `lifecycleSummary = await runLifecycleGuard(client, {`
- src/lib/ingestion/adapters.js:118-123 `const company = companies[i]; const adapter = getAdapterForCompany(company); ... const candidates = await adapter.extractJobs(company, { robotsGuard: guard });`
- adapters.js:197 `upsertJobCandidates(supabaseClient, allCandidates)`; supabaseClient.js:43 `deduplicateJobRows(scanned.flatMap(buildJobRows))`; :44 `writeJobRows(...)`
- adapters.js:128-131 `if (company.id && !dryRun) { ... reconcileCompanyJobDelta(...)` inside `if (Array.isArray(candidates) && candidates.length > 0)` (124)

## Q1 live / draft / archived
- jobRowBuilder.js:255 `let status = score >= 85 ? 'live' : 'draft';`
- :258-263 `if (primaryReason === 'foreign_location') { status = 'archived'; ...} else if (primaryReason) { status = 'draft'; draft_reason = primaryReason;`
- :158 `const hasDisqualifier = isUnreachable || isForeign || isGenericTalentPool || isPortalFallback || isTaxonomyUnverified;`
- :162-163 `if (score >= 85 && !hasDisqualifier) { primaryReason = null;` else loop over DRAFT_REASON_PRECEDENCE
- :24-31 precedence: unreachable_link, foreign_location, generic_talent_pool, portal_fallback, unverified_taxonomy, missing_metadata
- :99 `isUnreachable = candidate.is_http_200 === false || candidate.is_unreachable === true || !applyUrlValid`
- :108-115 foreign only when `!hasAffirmativeGermanMatch && (isForeignLocation(locInput) || candidate.is_foreign === true)`
- jobWriter.js:17-18 `Demotion guard: an automated re-scan or upsert never demotes a stored status = 'live' row.`; :90-93 `if (liveLinks.has(clean.apply_link)) { clean.status = 'live'; clean.draft_reason = null;`
- jobDeltaReconciler.js:319-326 `nextMissing = (job.consecutive_missing_scans || 0) + 1; ... if (nextMissing >= 2) { updatePayload.status = 'archived';` (only for existing status 'live' jobs, :185; only if not present in scan :218)
- lifecycleGuard.js:15 `MAX_JOB_AGE_MS = 180 * 24 * 60 * 60 * 1000`; :81-96 no apply_link -> archived; :99-113 posted_at older than max -> archived `exceeded_max_lifespan_180d`; :134 `status === 404 || status === 410` archived; :147-148 5xx `failures >= maxServerFailures ? 'archived' : (job.status || 'live')`, maxServerFailures default 2 (:79); :162-176 2xx soft-404 text -> archived; :194-198 other non-2xx same 2-failure rule; :213-223 network error `next_status: job.status || 'live'`
- lifecycleGuard.js:343-344 `.eq('status', 'live')` + :348 recency filter `last_checked_at.is.null,last_checked_at.lt.${cutoffIso}` (minAgeDays 3)

## Q2 apply-link 10 points
- jobRowBuilder.js:55 `if (!applyUrlValid) return 0;` (valid = http: or https: URL, :47-54)
- :64-65 `isDirectJobUrl = !isPortalFallback && /(\/jobs?|\/careers?|...)/i.test(job.apply_link); score += isDirectJobUrl ? 15 : 5;`
- :66 `if (job.is_http_200 !== false) score += 10;`
- :68 `if (isPortalFallback) score = Math.min(score, 80);`
- grep non-test src/api/scripts: is_http_200 only ever set `true` (deel.js:70, heavenhr.js:99,120, teamtailor.js:123,194, scripts/ingest-tier4.js:231); never `false`. Other adapters (ashby.js:67, greenhouse.js:56 ...) do not set it -> undefined !== false.
- calculateConfidenceScore body has no fetch (jobRowBuilder.js:40-73).

## Q3 title vs department
- classifierRules.js:135-136 `if (rules.tier1.test(normTitle)) { score += 15; ...} else if (normDept && rules.tier1.test(normDept)) { score += 5;`
- :139-140 tier2 7.5 title / else-if dept 2.5; :143-144 tier3 3.75 / 1.25
- :147-150 `if (rules.inhibitors.test(normTitle) || (normDept && rules.inhibitors.test(normDept))) { score -= 15;`
- :167 `if (sorted[0][1] < 4) return 'other';`
- :118-123 talent pool title -> `return undefined`
- taxonomy.js:213-215 `jobFunction(title = '', department = '') { return classifyJobFunction(title, department);`
- callers pass department: ashby.js:60 (job.department), domSelector.js:246, gemini.js:351, join.js:89 (categoryName), personio.js:90, recruitee.js:84, workable.js:53 (department + function). Title only: deel.js:58, greenhouse.js:50, heavenhr.js:96,110, hibob.js:115, talentstorm.js:115, teamtailor.js:114,187.

## Q4 work mode / seniority / job type
- taxonomy.js:41-51 workMode keyword match on text ('remote','hybrid','on-site','vor ort', word office); :26-39 employmentType keywords; :53-... experience keywords incl. exact canonical tiers (:58)
- ashby.js:42 `workMode = mapTaxonomy.workMode(job.workplaceType || '') || mapTaxonomy.workMode(title)`; :57 `employment_type: mapTaxonomy.employmentType(job.employmentType || title)`; :59 `experience: mapTaxonomy.experience(title)`
- greenhouse.js:33 workMode from location name else title; :47 employmentType(title); :49 experience(title)
- gemini.js:333 `mapTaxonomy.workMode(job.work_mode) || mapTaxonomy.workMode(title)`; :347 experience(job.experience)||experience(title); :348 employmentType(job.employment_type || title)
- deel.js:55-57 `|| 'hybrid'`, `|| 'full_time'`, `|| 'experienced'`
- jobRowBuilder.js:278-280 `experience: candidate.experience || 'experienced', employment_type: candidate.employment_type || 'full_time', work_mode: candidate.work_mode || 'hybrid'`
- score computed before defaults: adapters set confidence_score from candidate (ashby.js:67) and buildJobRows uses it when defined (jobRowBuilder.js:242-244); :58-61 points only `if (job.employment_type)` etc.

## Q5 60 s AI pause
- gemini.js:258-262 `// If 429 Quota exhausted, record cooldown and abort cascade immediately` `if (geminiRes && (geminiRes.status === 429 || JSON.stringify(geminiRes.body || '').includes('quota'))) { this.quotaTracker.record429(60); return [];`
- gemini.js:184 `this.quotaTracker = options.quotaTracker || new QuotaTracker();` (per adapter instance); :201 `if (this.isQuotaExhausted()) return [];`; :207-209 same in extractFromHtml
- rateLimiter.js:83-86 record429: `quotaExhausted = true; cooldownUntil = Date.now() + retryAfterSeconds * 1000`; :88-95 isQuotaExhausted clears after cooldownUntil
- adapters.js:119 new adapter per company inside the loop (getAdapterForCompany :63-97; :91-92 'gemini' -> new GeminiFlashAdapter(); :95 default -> new FallbackEngine()); fallbackEngine.js:34 `this.gemini = options.gemini || new GeminiFlashAdapter(options.geminiOptions)`
- gemini.js returns [] on 429 (no throw); batch circuit breaker adapters.js:145-163 triggers only on a thrown error with 429.
- fallbackEngine.js:171-175 `if (engine.gemini.isQuotaExhausted()) { deferredCount++; continue;` is inside runFallbackIngestion; grep: runFallbackIngestion not called by scripts/run-job-ingestion.js (only exported in adapters.js:57, defined fallbackEngine.js:163).
- keyPool defaultKeyPool is module-level singleton (keyPool.js:287), 60000 ms per-key cooldown (:6) - separate mechanism.

## Q6 key switch
- keyPool.js:118-121 eligiblePrimary filter `stats.rateLimitedUntil <= now`; :125-141 least-used, tie oldest lastUsedAt
- :178-181 markRateLimited(key, cooldownMs = DEFAULT_COOLDOWN_MS) ; :6 `DEFAULT_COOLDOWN_MS = 60000`
- :207 `const maxAttempts = Math.min(allKeys.length, this.backupKey ? 4 : 3);`
- :231-238 `if (result && result.ok === false && result.status === 429) { lastResult = result; this.markRateLimited(key); if (attempt < maxAttempts - 1) { ... continue;`
- :248-259 thrown err 429 / RESOURCE_EXHAUSTED same; :266 other errors `throw err`; :246 other results `return result`
- gemini.js:94-103 res.status 429 -> returns {ok:false,status:429}; timeouts -> 504 (:88-90) returned as non-429.
- keys from env :18 `GEMINI_API_KEYS || GEMINI_API_KEY` comma split.

## Q7 paid key
- keyPool.js:142-151 `else if (this.backupKey) { ... if (!backupStats || backupStats.rateLimitedUntil <= now) { ... chosenKey = this.backupKey;` only reached when eligiblePrimary.length === 0 (:125)
- :153-161 if no key chosen: sort primaries by earliest rateLimitedUntil, `chosenKey = sorted[0] || this.backupKey`
- :207 maxAttempts = min(5+1, 4) = 4 ; :209-210 `for attempt ... let key = this.getKey();` :234 `if (attempt < maxAttempts - 1) continue` else throw (:240-244)
- :213-226 attemptedKeys branch: untried eligible primary else `if (this.backupKey && !attemptedKeys.has(this.backupKey))` backup
- backup env :19-20 GEMINI_BACKUP_KEY || GEMINI_PAID_KEY || GEMINI_API_KEY_BACKUP
- trace: fresh 5 keys all 429 in one request: attempts 0-3 use 4 distinct primaries (each cooled by :233), attempt 3 throws (:240) -> paid key not reached, 5th primary untried. Next request within 60 s: 4 cooling, 5th eligible chosen; if it 429s, attempt 1 getKey sees 0 eligible primary -> backup.

## Q8 directory search
- search.js:4-5 `query.split(",").map(t => t.trim().toLowerCase()).filter(Boolean)`; :8-11 `!terms.length || terms.some(term => fields.flat().some(f => typeof f === "string" && f.toLowerCase().includes(term)))`
- useCompanyDirectory.js:49-55 fields: c.name, c.tags ?? [], c.city, sector label `(sectorDefs && sectorDefs[c.sector]?.label) || SECTORS[c.sector]?.label`
- :73-79 `matchesTaxonomy(c) && ... && matchesSearch(c)` ; DirView.jsx:65 `useCompanyDirectory(companies, effectiveSectorDefs)`, :251 `<Search value={searchInputValue} onChange={setSearchInputValue}`; Search.jsx:9 onChange per keystroke.

## Q9 banner
- SubmitBasicInfo.jsx:28 `const isDraft = Boolean(existingCompany && existingCompany.is_draft);` :109 `{isDraft && (` ... "Submission in Review:"
- SubmitView.jsx:221 `existingCompany={existingCompany}`; useSubmitForm.js:183-187 `if (d.existing_company) { setExistingCompany(d.existing_company); } else { setExistingCompany(null);` inside handleEnrich (:133 `if (!wb || enrichLoading) return;`), after `if (status === 429) ... return;` (:139-142) and `if (!ok) ... return;` (:143-146); runs before `if (changed.length)` (:193)
- only setExistingCompany call: useSubmitForm.js:184,186.
- enrichDb.js:72 `companies?website=ilike.*${domain}*&select=id,slug,name,city,status&limit=1`; :91 `is_draft: r.status === 'draft'`
- enrichPipeline.js:95-99 cache returned early `if (cached) { return cached; }` (before findExistingCompany at :102); :364 `...(existingCompany ? { existing_company: existingCompany } : {})` in finalPayload; :377-378 finalPayload saved to cache when `!isPartial`; enrichmentCache.js:122-123 returned `...profile`; TTL 90 days (:11, enrichPipeline.js:378 saveEnrichmentCache(..., 90, ...)).
- enrich.js:22 handler calls enrichCompanyProfile.

## Q10 test-gate
- test_gate.py:162 `raw = git("diff", "--cached", "--raw", "-z", "--no-renames", "--no-abbrev", base)` (base HEAD or empty tree :161)
- :167 `if ungated(path) or new_mode in SKIP_MODES: continue` ; :42 `SKIP_MODES = ("120000", "160000")` symlinks, submodules
- :169-171 `staged = None if status == "D" or new_sha == ZERO else new_sha; if path not in files or files[path] != staged: untested.append(path)`
- :40-41 UNGATED list; :53-55 ungated(): pattern without "/" matches the file name at any depth, else the whole path via fnmatchcase
- :87-88 record stores hash of every file in `git status --porcelain` (incl. untracked) after a passing run (:73-76, :79-93); deleted -> None (:87)
- hook: :187-200 hook_body runs `test_gate.py check`; :203-218 install (not over core.hooksPath/foreign hook).

## Q11 removed assertions
- floor_guard.py:28 TEST_RX; :41 ASSERT_RX = `\bassert\w*|\bexpect\s*\(|\.should\b|\bt\.(?:Error|Fatal)f?\(|\brequire\.|\braises\(|\btoThrow\b`
- :159-162 `count = lambda lines: sum(1 for l in lines if ASSERT_RX.search(l)); tests = {p: (count(added), count(removed)) for ... if TEST_RX.search(p)}; if sum(a - r for a, r in tests.values()) < 0: out += [("tests-removed", p, 0, ...) for p, (a, r) in tests.items() if r > a]`
- :179-180 diff `-U0 -M ... base` ; :175 base = pr_body.resolve_base (merge-base with default branch, pr_body.py:95-102); :184 untracked files added (`untracked(files)`), deleted file path handled :86-87
- :185-188 exceptions `tests-removed <glob>` from default-branch tip only; :55 EXC_RULES; :189 row added elsewhere = violation.
- exit 1 on any finding (:192-195).

## Q12 thresholds
- floor_guard.py:47-54 THRESHOLDS: fail_under (CONFIG, "min"), --cov-fail-under (CONFIG, min), lines|branches|functions|statements (JS_CONFIG, min), codecov target (min), codecov threshold (max), `--max-warnings|maxWarnings` (CONFIG, "max")
- :43 CONFIG = pytest.ini|pyproject.toml|setup.cfg|tox.ini|.coveragerc|package.json|.github/workflows/.* ; :44 JS_CONFIG = (jest|vitest).config.*|package.json ; :45 CODECOV
- :129 `if not re.search(rf"(^|/){scope}$", path): continue`
- :136-141 `if not sides["rem"]: continue; old = (min if loosens == "min" else max)(removed values); new = (min|max)(added values, default=None); if new is None or (new < old if loosens == "min" else new > old): yield ...`
- :163 `out += [("threshold", p, 0, token) ...]` ; exceptions rule name "threshold" :55.

## Q13 version bump
- build/validate.py:249-266 baseline = merge-base HEAD with origin/<default> else default; else last v tag; else HEAD
- :295-296 `if path in prev and meta["sha256"] != prev[path]["sha256"] and meta["version"] == prev[path]["version"]: errs.append("... content changed but version not bumped")`
- :292-293 each version must match SEMVER x.y.z (_versioning.py:4 `^\d+\.\d+\.\d+$`)
- manifest built by build.py:259-275 over `BUNDLE.rglob("*.md")`, sha256 = body_hash; new path not in prev is not checked (`path in prev`)
- no comparison "higher": only `==`.
- build/bump_guard.py:95-96 `if semver(cur_v) <= semver(tag_v):` error - separate, plugin VERSION vs last release tag, when manifest changed or shipped framework files changed (:81-89); workflow build-guard.yml runs it on pull_request only.

## Q14 date line
- _versioning.py:32-41 body_hash: strips frontmatter lines whose key `l.split(":", 1)[0].strip() in ("version", "timestamp")`; rest of text hashed
- verified (in-memory, no write): src/workflows/3d-implement-issue.md `timestamp:` edit -> same hash True; src/memory-templates/STATUS.md `generated:\n  at:` edit -> hash differs.
- frontmatter examples: 3d-implement-issue.md:9-10 `version: "2.8.0"` / `timestamp: 2026-10-22`; STATUS.md uses `generated:\n  by:\n  at: 2026-10-27`.

## Self-check
- Re-opened lines for Q1 (writer demotion guard applies when stored row with same apply_link is live), Q5 (fresh adapter per company), Q7 trace, Q11 (net across ALL test files then per-file r > a), Q12 (new threshold with nothing removed ignored). Dropped: no claims about description in search, no unread values.
