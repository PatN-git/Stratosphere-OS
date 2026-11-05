# Notes for runner 12 (quotes verbatim, file:line; CTH = C:\Users\patri\Dev\CleanTechHub, SOS = C:\t\b217)

## Q1 (CTH) live / draft / archived
Entry: scripts/run-job-ingestion.js:422 `ingestionSummary = await runAtsIngestionBatch(client, companies, {` ; cron .github/workflows/job-ingestion-cron.yml `cron: '0 2 * * *'`
- src/lib/ingestion/adapters.js:197 `const { committedCount, failures, duplicates } = await upsertJobCandidates(supabaseClient, allCandidates);`
- src/lib/ingestion/supabaseClient.js:43 `const rowsToUpsert = deduplicateJobRows(scanned.flatMap(buildJobRows));`
- jobRowBuilder.js:242-245 `const rawScore = candidate.confidence_score !== undefined ? candidate.confidence_score : calculateConfidenceScore({ ...candidate, title: cleanTitle }); const score = Math.round(Math.min(100, Math.max(0, rawScore)));`
- jobRowBuilder.js:253 `const { primaryReason, diagnostics } = evaluateDraftDiagnostics({ ...candidate, title: cleanTitle }, score);`
- jobRowBuilder.js:255-268 `let status = score >= 85 ? 'live' : 'draft';` ... `if (primaryReason === 'foreign_location') { status = 'archived'; draft_reason = 'foreign_location'; } else if (primaryReason) { status = 'draft'; draft_reason = primaryReason; } else if (status === 'live') { draft_reason = null; } else { draft_reason = 'missing_metadata'; }`
- jobRowBuilder.js:158 `const hasDisqualifier = isUnreachable || isForeign || isGenericTalentPool || isPortalFallback || isTaxonomyUnverified;`
- jobRowBuilder.js:162-164 `if (score >= 85 && !hasDisqualifier) { primaryReason = null; } else { for (const reason of DRAFT_REASON_PRECEDENCE) {`
- jobRowBuilder.js:24-31 precedence: unreachable_link, foreign_location, generic_talent_pool, portal_fallback, unverified_taxonomy, missing_metadata
- jobRowBuilder.js:99 `const isUnreachable = candidate.is_http_200 === false || candidate.is_unreachable === true || !applyUrlValid;`
- jobRowBuilder.js:113-116 `const isForeign = !hasAffirmativeGermanMatch && ( isForeignLocation(locInput) || candidate.is_foreign === true );`
- jobRowBuilder.js:67-70 caps: `if (isGenericTalentPool) score = Math.min(score, 75); if (isPortalFallback) score = Math.min(score, 80); if (job.taxonomy_verified === false || job.company_taxonomy_verified === false) score = Math.min(score, 80); if (job.job_function === 'other') score = Math.min(score, 83);`
- jobWriter.js:17 `Demotion guard: an automated re-scan or upsert never demotes a stored `status = 'live'` row.` ; 88-93 `if (liveLinks.has(clean.apply_link)) { clean.status = 'live'; clean.draft_reason = null; }`
- (note: jobWriter.js:145 archived stored row revived with sibling row status; only for composite-title collision)
Archive after ingest:
- adapters.js:124-130 `if (Array.isArray(candidates) && candidates.length > 0) { ... if (company.id && !dryRun) { ... const delta = await reconcileCompanyJobDelta(`
- jobDeltaReconciler.js:182-185 `.eq('company_id', companyId) .eq('status', 'live');`
- jobDeltaReconciler.js:319-326 `const nextMissing = (job.consecutive_missing_scans || 0) + 1; ... if (nextMissing >= 2) { updatePayload.status = 'archived'; }`
- jobDeltaReconciler.js:225 refreshed link for same title+region -> relink instead of counting missing
- run-job-ingestion.js:505 `const skipLifecycleGuard = !runLifecycle || dryRun || ingestionSummary.quotaExhausted || timedOut;`
- lifecycleGuard.js:44 `const MAX_JOB_AGE_MS = 180 * 24 * 60 * 60 * 1000;` ; 111 `if (!isNaN(postedTime) && Date.now() - postedTime > MAX_JOB_AGE_MS) {` -> next_status 'archived'
- lifecycleGuard.js:97-107 no apply_link -> archived ; 144 `if (status === 404 || status === 410) {` -> archived ; 157-159 `if (status >= 500) { const failures = (job.check_failures || 0) + 1; const next_status = failures >= maxServerFailures ? 'archived' : (job.status || 'live');` ; 94 `const maxServerFailures = options.maxServerFailures || 2;` ; 176-186 soft-404 text -> archived ; 202-203 other non-2xx same failures>=max rule ; 224 `next_status: job.status || 'live', // Invariant: status preserved on network partition`
- lifecycleGuard.js:383-384 `.select('id, apply_link, status, check_failures, posted_at') .eq('status', 'live');` ; 336-338 recency `last_checked_at.is.null,last_checked_at.lt.${cutoffIso}` minAgeDays 3

## Q2 (CTH) 10 points apply link
- jobRowBuilder.js:55 `if (!applyUrlValid) return 0;` ; 47-53 valid = parsed.protocol http: or https:
- jobRowBuilder.js:66 `if (job.is_http_200 !== false) score += 10;`
- grep over src/scripts/api (non-test): is_http_200 set only as `true` (deel.js:70, heavenhr.js:99,120, teamtailor.js:123,194, ingest-tier4.js:231); never set false; gemini.js candidate (lines 79-93 of file, i.e. 361-372) has no is_http_200.
- jobRowBuilder.js:64-65 separate: `score += isDirectJobUrl ? 15 : 5;` ; 57 `let score = 30; // valid title (15) + valid apply_link (15)`
- caps after (67-70) can lower total.

## Q3 (CTH) department vs title
- classifierRules.js:135-136 `if (rules.tier1.test(normTitle)) { score += 15; tScore += 15; t1++; } else if (normDept && rules.tier1.test(normDept)) { score += 5; t1++; }`
- :139-140 `score += 7.5` title / `score += 2.5` dept (else-if) ; :143-144 `3.75` title / `1.25` dept (else-if)
- :147-150 `if (rules.inhibitors.test(normTitle) || (normDept && rules.inhibitors.test(normDept))) { score -= 15;`
- :167 `if (sorted[0][1] < 4) return 'other';`
- :117-123 talent pool guard returns undefined
- Callers passing department: ashby.js:60 `mapTaxonomy.jobFunction(title, job.department || '')`, domSelector.js:246, gemini.js:351, join.js:89 (categoryName), personio.js:90, recruitee.js:84, workable.js:53; title only: deel.js:58, greenhouse.js:50, heavenhr.js:96,110, hibob.js:115, talentstorm.js:115, teamtailor.js:114,187.
- taxonomy.js:213-215 `jobFunction(title = '', department = '') { return classifyJobFunction(title, department); }`

## Q4 (CTH) work mode / seniority / job type
- taxonomy.js:26-51 employmentType()/workMode() keyword matchers; :53-210 experience() keyword tiers (returns undefined if none).
- work mode sources: ashby.js:42-43 `let workMode = mapTaxonomy.workMode(job.workplaceType || '') || mapTaxonomy.workMode(title); if (!workMode && job.isRemote) workMode = 'remote';` ; gemini.js:333 `mapTaxonomy.workMode(job.work_mode) || mapTaxonomy.workMode(title)` ; greenhouse.js:33 locationName||title ; recruitee.js:65 `offer.remote ? 'remote' : (...)` ; hibob.js:91-93 ; personio.js:70-72 ; deel.js:55 `|| 'hybrid'` ; heavenhr.js:62 `|| 'hybrid'`; teamtailor.js:97 `|| 'hybrid'` ; talentstorm.js:97 title only.
- employment type: ashby.js:57 `job.employmentType || title`; personio.js:87; join.js:86; recruitee.js:81 `offer.employment_type_code || title`; workable.js:50 `job.type || title`; gemini.js:348 `job.employment_type || title`; greenhouse.js:47 title only; deel.js:56 `|| 'full_time'`.
- experience: workable.js:52 `job.experience || title`; recruitee.js:83 `offer.experience_code || title`; talentstorm.js:114 `item.seniority` then title; personio.js:89 name+seniority+yearsOfExperience; gemini.js:347 `job.experience` then title; greenhouse.js:49 title; deel.js:57 `|| 'experienced'`.
- jobRowBuilder.js:278-280 `experience: candidate.experience || 'experienced', employment_type: candidate.employment_type || 'full_time', work_mode: candidate.work_mode || 'hybrid',`
- jobRowBuilder.js:60-61 `if (job.work_mode) score += 10; if (job.experience) score += 8;` (employment_type :59 += 10)
- domSelector.js:268-272 / recruitee.js:90-94 score computed with defaults applied.

## Q5 (CTH) 60-second AI pause
- gemini.js:258-262 `// If 429 Quota exhausted, record cooldown and abort cascade immediately` `if (geminiRes && (geminiRes.status === 429 || JSON.stringify(geminiRes.body || '').includes('quota'))) { this.quotaTracker.record429(60); return []; }`
- rateLimiter.js:83-86 `record429(retryAfterSeconds = 60) { this.quotaExhausted = true; this.cooldownUntil = Date.now() + retryAfterSeconds * 1000;`
- rateLimiter.js:88-95 isQuotaExhausted() true until Date.now() >= cooldownUntil.
- gemini.js:184 `this.quotaTracker = options.quotaTracker || new QuotaTracker();` ; :201 `if (this.isQuotaExhausted()) return [];` ; :207-209 same in extractFromHtml
- adapters.js:118-123 inside the per-company loop: `const company = companies[i]; const adapter = getAdapterForCompany(company); ... const candidates = await adapter.extractJobs(company, { robotsGuard: guard });`
- adapters.js:91-95 `case 'gemini': return new GeminiFlashAdapter(); case 'custom': default: return new FallbackEngine();` ; fallbackEngine.js:34 `this.gemini = options.gemini || new GeminiFlashAdapter(options.geminiOptions);`
- fallbackEngine.js:172 `if (engine.gemini.isQuotaExhausted()) { deferredCount++; continue;` is in runFallbackIngestion, which is not called by scripts/run-job-ingestion.js (grep: only runAtsIngestionBatch imported, line 21).
- adapters.js:145-163 batch's own stop: `const is429 = err?.status === 429 || err?.statusCode === 429 || /429|RESOURCE_EXHAUSTED/i.test(err?.message || '');` inside `catch (err)`; Gemini adapter returns [] (gemini.js:261) so it does not throw here.
- atsUtils.js:261 one `adapterInstance.extractFromHtml(...)` per company fetch.

## Q6 (CTH) key switch
- keyPool.js:6 `export const DEFAULT_COOLDOWN_MS = 60000;`
- :118-121 eligiblePrimary = keys where `!stats || stats.rateLimitedUntil <= now`
- :125-141 least-used (usageCount), tie -> oldest lastUsedAt
- :178-182 markRateLimited sets rateLimitedUntil = Date.now() + cooldownMs
- :207 `const maxAttempts = Math.min(allKeys.length, this.backupKey ? 4 : 3);`
- :231-239 `if (result && result.ok === false && result.status === 429) { lastResult = result; this.markRateLimited(key); if (attempt < maxAttempts - 1) { ... continue; }` then throw
- :248-266 catch: is429 (status/statusCode 429 or message /429|RESOURCE_EXHAUSTED/) -> markRateLimited + rotate; other errors `throw err;`
- :246 `return result;` any other non-429 result returned as is
- gemini.js:70 `return await pool.executeWithRetry(async (key) => {` ; gemini.js:95 `if (res.status === 429) {` returns ok false status 429; non-429 errors returned as results (104).
- defaultKeyPool singleton keyPool.js:287.

## Q7 (CTH) paid key
- keyPool.js:142-150 `} else if (this.backupKey) { // All primary keys are cooling down! ... if (!backupStats || backupStats.rateLimitedUntil <= now) { ... chosenKey = this.backupKey; }` (only when eligiblePrimary.length == 0)
- :207 maxAttempts = min(allKeys.length, 4 with backup) -> with 5 free + 1 paid = min(6,4)=4
- :234-244 last attempt (attempt == maxAttempts-1) with 429 -> throws, no further key.
- :213-226 duplicate-key branch: untried primary first, then `this.backupKey && !attemptedKeys.has(this.backupKey)`.
- :153-161 if backup also cooling -> falls to key with earliest rateLimitedUntil among free keys
- trace: fresh pool, all 429: attempts 0-3 use four free keys (each getKey picks an eligible free key), attempt 3 throws; paid not reached in that request. Next request: 5th free key (still eligible) tried, then getKey finds all 5 cooling -> paid.
- tests/unit/geminiKeyPool.test.js:326-338 test that getKey returns backup when all 5 free marked rate-limited.
- cron workflow passes only GEMINI_API_KEY env (no backup env).

## Q8 (CTH) directory search
- src/lib/search.js:4-5 `parseSearchTerms = (query) => query.split(",").map(t => t.trim().toLowerCase()).filter(Boolean);`
- :8-11 `matchesTerms = (terms, fields) => !terms.length || terms.some(term => fields.flat().some(f => typeof f === "string" && f.toLowerCase().includes(term)));`
- useCompanyDirectory.js:49-55 `const terms = parseSearchTerms(searchInputValue); const matchesSearch = c => matchesTerms(terms, [ c.name, c.tags ?? [], c.city, (sectorDefs && sectorDefs[c.sector]?.label) || SECTORS[c.sector]?.label, ]);`
- :73-79 `matchesTaxonomy(c) && (teamSize...) && (funding...) && (!hiringNowFilter || c.total_live_jobs > 0) && matchesSearch(c)`
- DirView.jsx:65 `} = useCompanyDirectory(companies, effectiveSectorDefs);` ; :251 `<Search value={searchInputValue} ... placeholder="Search companies, tags, cities..."`

## Q9 (CTH) banner
- SubmitBasicInfo.jsx:28 `const isDraft = Boolean(existingCompany && existingCompany.is_draft);` ; :108-112 `{isDraft && (` ... `Submission in Review:` ... `has already been submitted and is currently in review.`
- useSubmitForm.js:183-187 `if (d.existing_company) { setExistingCompany(d.existing_company); } else { setExistingCompany(null); }` inside handleEnrich (:133 `const handleEnrich = async () => { if (!wb || enrichLoading) return;`) after `if (status === 429) {...return;} if (!ok) {...return;}` (:139-146)
- enrichDb.js:72 `.../rest/v1/companies?website=ilike.*${encodeURIComponent(domain)}*&select=id,slug,name,city,status&limit=1`; :91 `is_draft: r.status === 'draft',` ; :67 `if (!supabaseUrl || !serviceKey || !domain) return null;` ; :80 `signal: AbortSignal.timeout(3000)` ; :94-97 catch -> null; :82 `if (!res.ok) return null;`
- enrichPipeline.js:96-99 `const cached = ... getEnrichmentCache(...); if (cached) { return cached; }` BEFORE :102 `findExistingCompany(domain, options)` ; :364 `...(existingCompany ? { existing_company: existingCompany } : {}),` ; :379 `await saveEnrichmentCache(domain, websiteStr, finalPayload, crawlMeta, 90, options);` ; enrichmentCache.js:122-124 `return { ...profile,` (so a cached hit carries the stored existing_company from caching time; 90-day ttl line 379)
- SubmitView.jsx:221 `existingCompany={existingCompany}` passed to SubmitBasicInfo.
- the live variant: SubmitBasicInfo.jsx:27 `isLive = Boolean(existingCompany && !existingCompany.is_draft)` -> "Already Registered" banner instead.

## Q10 (SOS) test gate
- src/scripts/test_gate.py:160-179 check(): `raw = git("diff", "--cached", "--raw", "-z", "--no-renames", "--no-abbrev", base)` ; `if ungated(path) or new_mode in SKIP_MODES: continue` ; `staged = None if status == "D" or new_sha == ZERO else new_sha` ; `if path not in files or files[path] != staged: untested.append(path)`
- :161 base = HEAD else EMPTY_TREE
- :40-41 UNGATED = ("*.md", "*.mdx", "*.txt", "*.rst", "docs/*", ".memory/*", ".agents/*", ".claude/*", ".github/*", "LICENSE*", ".gitignore", ".gitattributes", "*.png", "*.jpg", "*.jpeg", "*.gif", "*.svg", "*.webp", "*.ico")
- :38-39 comment `A pattern without "/" matches the file name at any depth.` ; :53-55 ungated() uses fnmatch on full path if "/" in pat else last path component
- :42 SKIP_MODES = ("120000", "160000")  # symlinks, submodules
- :79-93 save_record records every changed file (git status porcelain incl. untracked) by blob hash after a passing run; :73-75 failing run records nothing.
- :187-200 hook body runs `.agents/scripts/test_gate.py check`; :203-218 install writes hook, only if no foreign hook / no core.hooksPath. Gate only active when hook installed.

## Q11 (SOS) removed assertions
- floor_guard.py:28 TEST_RX = `(^|/)(tests?|__tests__|specs?)/|(^|/)test_[^/]*$|_test\.\w+$|\.(test|spec)\.\w+$|Tests?\.java$`
- :41 ASSERT_RX = `\bassert\w*|\bexpect\s*\(|\.should\b|\bt\.(?:Error|Fatal)f?\(|\brequire\.|\braises\(|\btoThrow\b`
- :159-162 `count = lambda lines: sum(1 for l in lines if ASSERT_RX.search(l))` ; `tests = {p: (count(t for _, t in a), count(r)) for p, (a, r) in files.items() if TEST_RX.search(p)}` ; `if sum(a - r for a, r in tests.values()) < 0:` ; `out += [("tests-removed", p, 0, f"{r - a} net assertion lines removed") for p, (a, r) in tests.items() if r > a]`
- :6 diff = merge base with default branch -> working tree (committed, staged, unstaged, untracked)
- :179-180 `git diff -U0 -M ... base` ; :184 untracked(files) adds untracked as added lines
- :188 `found = [f for f in find(files) if not any(f[0] == r and rx.match(f[1]) for r, rx in allowed)]` ; :55 EXC_RULES includes "tests-removed"; :11 exceptions rows read from default-branch tip only
- :77-90 parse_diff: deleted files take old path, removed lines counted.
- Callers: 3d-implement-issue.md:69, 4a-verify-and-ship.md:24, 3z-afk-loop.md:59 `python .agents/scripts/floor_guard.py`; exit 1 = violation.

## Q12 (SOS) threshold / max-warnings
- floor_guard.py:43 CONFIG = `(?:pytest\.ini|pyproject\.toml|setup\.cfg|tox\.ini|\.coveragerc|package\.json|\.github/workflows/.*)` ; :44 JS_CONFIG `(?:(?:jest|vitest)\.config\.\w+|package\.json)` ; :45 CODECOV
- :47-54 THRESHOLDS: fail_under (CONFIG, min); --cov-fail-under (CONFIG, min); lines|branches|functions|statements (JS_CONFIG, min); target (CODECOV, min); threshold (CODECOV, max); `(?P<k>--max-warnings|maxWarnings)[=\s\"':]+(?P<v>\d+)` (CONFIG, "max")
- :125-141 threshold_changes: `if not re.search(rf"(^|/){scope}$", path): continue` ; `if not sides["rem"]: continue` ; `old = (min if loosens == "min" else max)(v for _, v in sides["rem"])` ; `new = (min if loosens == "min" else max)((v for _, v in sides["add"]), default=None)` ; `if new is None or (new < old if loosens == "min" else new > old): yield ...`
- :163 `out += [("threshold", p, 0, token) for p, token in threshold_changes(files)]` ; :55 EXC_RULES has "threshold"
- docstring :7-8 `loosened coverage/lint thresholds ... Tightening is silent.`

## Q13 (SOS) validator version bump
- build/validate.py:295-296 `if path in prev and meta["sha256"] != prev[path]["sha256"] and meta["version"] == prev[path]["version"]: errs.append(f"{SETUP}/{path}: content changed but version not bumped (still {meta['version']})")`
- :292 `if not _versioning.SEMVER.match(v):` -> error not semver x.y.z ; _versioning.py:4 SEMVER `^\d+\.\d+\.\d+$`
- :246-248 comment baseline = PR fork point (merge-base with default branch), falls back to last release tag, then HEAD ; :253-264
- :281-288 prev loaded from `git show {bump_baseline}:{git_path}`; if none, prev = {} (no checks)
- build.py:259-273 manifest over BUNDLE.rglob("*.md"): `artifacts[key] = {"version": v, "sha256": _versioning.body_hash(text), "timestamp": ts}`
- .github/workflows/build-guard.yml `run: python build/validate.py .`
- bump_guard.py:95-96 `if semver(cur_v) <= semver(tag_v):` error (plugin VERSION vs last tag, separate guard, PR only, :31 FRAMEWORK_PATHS + manifest diff)

## Q14 (SOS) date line
- src/scripts/_versioning.py:32-41 body_hash: `fm = "\n".join(l for l in fm.split("\n") if l.split(":", 1)[0].strip() not in ("version", "timestamp"))` ; `return hashlib.sha256(text.encode("utf-8")).hexdigest()` ; :33 comment `remove ONLY this file's plugin-version metadata so a version bump alone never changes the hash.` ; :6-9 normalize: BOM stripped, CRLF -> LF
- _versioning.py:25-26 reader treats `timestamp:` and `generated:` `at:` as timestamp for the manifest field, but only version/timestamp lines are stripped from hash.
- src/workflows/4a-verify-and-ship.md:9-10 `version: "1.8.0"` / `timestamp: 2026-10-22` (frontmatter timestamp line). dist template STATUS.md frontmatter `generated:\n  by: stratosphere-setup\n  at: 2026-10-27` (the `at:` key is not stripped).
- Only frontmatter (fm) lines filtered; body text untouched.

## Self-check
Re-opened each cited line while drafting (all quotes copied from the tool output above). Dropped: claim about "consecutive" 5xx (check_failures also increments on network errors and resets only on healthy 2xx; phrased as "failure count reaches 2"); did not state any value not read.
