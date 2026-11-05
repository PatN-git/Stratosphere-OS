# Notes — runner 05 (brief V0)

Repos: CTH = C:\Users\patri\Dev\CleanTechHub @26b46f7; SOS = C:\t\b217 @bdce919. Read-only throughout.

## Entry points traced
- Nightly: .github/workflows/job-ingestion-cron.yml (cron '0 2 * * *', env GEMINI_API_KEY only, no backup-key var) -> scripts/run-job-ingestion.js:422 runAtsIngestionBatch -> src/lib/ingestion/adapters.js:99-210 -> getAdapterForCompany (adapters.js:63-97, new adapter per company, line 119) -> upsertJobCandidates supabaseClient.js:41-45 -> buildJobRows jobRowBuilder.js:240 -> writeJobRows jobWriter.js:59. Lifecycle guard run-job-ingestion.js:505-516 -> lifecycleGuard.js:367.
- Directory: src/pages/DirView.jsx uses src/hooks/useCompanyDirectory.js.
- Submit: SubmitView.jsx:212-221 -> SubmitBasicInfo.jsx; existingCompany set in useSubmitForm.js:183-186 from /api/enrich (api/enrich.js:22-29 -> api/_lib/enrichPipeline.js).
- SOS: test_gate.py check (pre-commit hook body, test_gate.py:187-200); floor_guard.py main; build-guard.yml runs build.py, validate.py, bump_guard.py (PRs only).

## Claims with file:line (self-checked: each line re-read)

### Q1
- score>=85 -> live else draft: jobRowBuilder.js:255. Score from adapter's confidence_score if set (jobRowBuilder.js:242-244; adapters set it, e.g. gemini.js:374).
- primaryReason null only if score>=85 && !hasDisqualifier: :158,162. Disqualifiers = unreachable, foreign, talent pool, portal fallback, unverified taxonomy (:158). missing_metadata alone is not a disqualifier.
- foreign_location primary -> archived: :258-260; precedence unreachable_link before foreign_location: :24-31 -> unreachable+foreign => draft.
- foreign only when no affirmative German match: :108-116.
- Demotion guard: stored row with same apply_link live -> forced live, draft_reason null: jobWriter.js:67-95 (lines 90-93).
- Missing from feed: live jobs only (jobDeltaReconciler.js:182-185), nextMissing>=2 -> archived (:319-326); runs only if company returned >=1 candidate (adapters.js:124-131).
- Lifecycle: 404/410 archive (lifecycleGuard.js:144-153); 5xx or other non-2xx archive when failures>=2 (:157-159, :202-203; maxServerFailures default 2 :94); soft-404 text archive (:176-186); posted_at >180d archive (:44, :109-121); network error keeps status (:213-228). Only live jobs checked (:381-384). Skipped on dry run/quota/timeout (run-job-ingestion.js:505).

### Q2
- +10 if is_http_200 !== false: jobRowBuilder.js:66. Preconditions: title >2 chars (:41) and valid http/https apply_link (:46-55) else 0. Caps after: :67-70 (75/80/80/83).
- Separate direct-URL 15 vs 5: :64-65.
- grep is_http_200 in src/scripts/api: only `true` assignments (deel.js:70, heavenhr.js:99/120, teamtailor.js:123/194, ingest-tier4.js:231, benchmarkHelpers.js:297). Nothing sets false.

### Q3
- classifierRules.js:134-144: tier1 title 15 / dept 5; tier2 7.5 / 2.5; tier3 3.75 / 1.25; dept only via else-if (only if title missed that tier).
- inhibitors -15 if in title OR dept: :147-150.
- <4 -> 'other': :167. Ties: tier1 count, then title-only score, then canonical order: :157-165.
- Dept not passed by greenhouse.js:50, heavenhr.js:96/110, hibob.js:115, talentstorm.js:115, teamtailor.js:114/187, deel.js:58. Passed: ashby.js:60, personio.js:90, recruitee.js:84, workable.js:53 (dept+function), join.js:89 (category), gemini.js:351, domSelector.js:246.

### Q4
- mapTaxonomy taxonomy.js:25-216: employmentType :26-39, workMode :41-51 (remote > hybrid > on-site order), experience :53-211.
- Adapters: feed field then title, e.g. greenhouse.js:33 (location then title), ashby.js:42-43 (workplaceType, title, isRemote), workable.js:35-36, personio.js:70-72,87,89; gemini.js:333,347-348 (AI answer then title).
- Defaults before scoring in deel.js:55-57 (hybrid/full_time/experienced), heavenhr.js:62 (hybrid), teamtailor.js:97,111 (hybrid, full_time).
- Row fallback defaults experienced/full_time/hybrid: jobRowBuilder.js:278-280; score uses candidate values (adapters compute before), missing ones -> missing_fields :148-156, no points :59-61.

### Q5
- gemini.js:258-261: on 429 or body containing 'quota' -> quotaTracker.record429(60), return [] (stops model cascade).
- QuotaTracker per adapter instance: gemini.js:184 (constructor), rateLimiter.js:83-96 (60s window).
- New adapter per company: adapters.js:92, :119; FallbackEngine creates its own GeminiFlashAdapter fallbackEngine.js:34. runFallbackIngestion (shared engine, defers) not called by nightly (grep).
- Returned not thrown -> batch circuit breaker (adapters.js:145-163) not tripped: defaultCallGemini catches 429 -> returns object gemini.js:121-129.
- Key pool cooldown 60s: keyPool.js:6, :178-181; with one key and no backup, getKey still returns it: :153-161. Workflow env only GEMINI_API_KEY (cron yml); value contents (single vs comma list) not visible.

### Q6
- getKey least-used eligible primary, tie oldest lastUsedAt: keyPool.js:117-141.
- 429 -> markRateLimited 60s, continue to next attempt: :231-239 (returned 429), :247-261 (thrown status 429 or message /429|RESOURCE_EXHAUSTED/).
- maxAttempts = min(allKeys, backup?4:3): :207.
- Non-429 returned result returned (:246); thrown non-429 rethrown (:266). Timeout returned as 504: gemini.js:88-89.
- All benched: backup if not benched (:142-151); else earliest-ending free key (:153-161).

### Q7
- Backup chosen only when eligiblePrimary empty and backup not cooling: keyPool.js:125, :142-151.
- 5 keys + backup -> maxAttempts min(6,4)=4: :195, :207. Example derived (illustrative): fresh pool, all 429 -> 4 free keys tried, then throw (:240-244); next call within 60s -> 5th free key, then paid.
- Free keys preferred again after cooldown: eligibility check :118-121.

### Q8
- useCompanyDirectory.js:49-55: terms from parseSearchTerms; fields name, tags, city, sector label.
- search.js:4-5 split on comma, trim, lowercase; :8-11 any term substring (includes) in any field, case-insensitive; empty -> match all.
- AND with other filters: useCompanyDirectory.js:73-78.

### Q9
- Banner when existingCompany && existingCompany.is_draft: SubmitBasicInfo.jsx:28, :108-112; live variant :27, :93.
- existingCompany set from /api/enrich response on AI Auto-fill click: useSubmitForm.js:183-186 (inside handleEnrich, after ok and non-429 checks :138-149 region); button SubmitBasicInfo.jsx:39-51.
- Server: findExistingCompany enrichDb.js:51-97: website ilike *domain*, limit 1, is_draft = status==='draft' (:91); 3s timeout (:80); errors -> null.
- Domain normalized lowercase, www. stripped: enrichmentCache.js:21-30; enrichPipeline.js:80.
- Cache hit returns before lookup: enrichPipeline.js:95-99; payload incl. existing_company saved for 90 days: :364, :376-379; cache replays profile: enrichmentCache.js:122-139.

### Q10
- check(): staged diff vs HEAD (empty tree if none): test_gate.py:160-162; deletions included (:169).
- UNGATED list :40-41; matching rule :53-55 (no "/" -> file name any depth; with "/" -> path from repo root).
- SKIP_MODES symlinks/submodules :42, :167.
- Must equal recorded blob from passing run: :170; record = changed files after passing run :79-91.
- Hook runs check: :187-200 (only if installed).

### Q11
- Test file pattern TEST_RX :28; assertion-line pattern ASSERT_RX :41.
- Count lines added vs removed per test file; flag only if total net < 0, then each file with r > a: :159-162.
- Diff = merge base with default branch -> working tree, untracked added: :6, :179-184; -M renames :179.
- Exceptions: tip-of-default rows rule glob: :185-188.

### Q12
- THRESHOLDS :47-54; CONFIG files :43, JS_CONFIG :44, CODECOV :45.
- Only when a removed line had the key: :136-137; old/new min or max; flag if removed entirely or looser: :138-141. Tightening silent (:8).
- max-warnings: --max-warnings|maxWarnings, only in CONFIG files (pytest.ini, pyproject.toml, setup.cfg, tox.ini, .coveragerc, package.json, .github/workflows/*): :53, :43. Higher = looser ("max").
- Exception row `threshold <glob>` merged on default branch: :185-188.

### Q13
- validate.py:290-296 (in _check_manifest_bumps): error only if path in prev and sha differs and version == prev version. Different (even lower) version passes. New paths not checked. Semver format x.y.z :291-293.
- Baseline: merge-base with origin/default or default; else last v-tag; else HEAD: :249-264.
- Manifest built by build.py:259-275 (body_hash per .md).
- Higher required only for whole-plugin VERSION by bump_guard.py:81-101 (> last release tag if shipped content changed), PR-only in build-guard.yml.

### Q14
- body_hash _versioning.py:32-41: drops frontmatter lines whose key (text before first ':' stripped) is 'version' or 'timestamp'; normalizes BOM/CRLF (:6-9).
- `generated:` / `  at:` lines keep (key 'at'), so editing it changes hash. generated used by 18 src .md (grep), incl. shipped templates (dist grep). Body dates count.
