---
description: Scan matrix for 4c_codebase-health-audit. Defines what each of the six passes detects.
version: "1.0.0"
timestamp: 2026-07-27
---

# Health Audit — Scan Matrix

Reference for `4c_codebase-health-audit`. Each subagent receives only its assigned passes.

---

## Subagent A: Safety Auditor

### A1 — Security & Secrets

| Category | What to detect |
|:---|:---|
| **Hardcoded secrets** | API keys, tokens, passwords, private keys, connection strings in source. Patterns: assignment to `KEY`, `SECRET`, `TOKEN`, `PASSWORD`, `CREDENTIAL` vars with string literals; base64 blobs; `-----BEGIN` markers. |
| **SQL injection** | Raw string concatenation/interpolation in DB queries. Patterns: template literals in `.query()` / `.execute()` / `.raw()`; f-strings in SQL; `+` concatenation on query strings with variables. |
| **Unvalidated input** | `req.body`, `req.params`, `req.query`, URL params used in DB calls / file paths / shell commands without schema validation or sanitization. |
| **Permissive CORS** | `Access-Control-Allow-Origin: *` on non-public endpoints; `cors({ origin: '*' })` with `credentials: true`; wildcard origins on authenticated routes. |
| **Exposed debug** | Routes matching `/debug`, `/test`, `/__dev`; `console.log` outputting tokens or PII; `DEBUG=true` in committed env files; stack traces in API error responses. |
| **Missing auth** | Route handlers / API endpoints without auth middleware or session validation. Express/Fastify without `authenticate`/`requireAuth`; Next.js API routes without `getServerSession`/`auth()`; Supabase RPC without RLS. |
| **Insecure config** | Weak/deprecated crypto (`md5`, `sha1`, `des`); missing security headers (`helmet` absent, no CSP, no `X-Frame-Options`); `NODE_TLS_REJECT_UNAUTHORIZED=0`. |

### A2 — Dependency Health

Run native audit command based on lockfile:

```bash
npm audit --json      # package-lock.json
pnpm audit --json     # pnpm-lock.yaml
yarn audit --json     # yarn.lock
pip-audit --format json  # requirements.txt / pyproject.toml
cargo audit --json    # Cargo.lock
```

Also: `npm outdated --json` (or equivalent).

| Category | What to detect |
|:---|:---|
| **Known CVEs** | Dependencies flagged `moderate`, `high`, or `critical` by native audit. |
| **Outdated majors** | Dependencies >1 major version behind current release. |
| **Deprecated** | Packages marked deprecated in registry. |
| **Unmaintained** | No release in >24 months (heuristic; cap at 70 confidence). |

---

## Subagent B: Quality Auditor

### B1 — Reliability (Error Handling)

| Category | What to detect |
|:---|:---|
| **Empty catch** | `catch (e) {}`, `catch (_) {}`, `except: pass` — exception swallowed silently. |
| **Swallowed errors** | `catch` with logging but no rethrow, fallback, or error return — caller sees success. |
| **Missing propagation** | Service/data layer catches and returns `null`/`undefined`/`false` instead of rethrowing — caller cannot distinguish "not found" from "failed." |
| **Unhandled async** | Promise chains without `.catch()`; `async` functions with `await` but no `try/catch`; `EventEmitter` without `'error'` handler. |
| **Missing error boundaries** | React subtrees performing data fetching without `ErrorBoundary` wrapper. |
| **Generic catch-all** | `catch (e: Error)` or `except Exception` where specific subtypes need different handling. |
| **Missing cleanup** | Resources opened in try without `finally` cleanup or `using`/`async with` guard. |

### B2 — Correctness (Test Coverage)

For each source file, check for test counterpart (`*.test.*`, `*.spec.*`, `__tests__/*`).

| Category | What to detect |
|:---|:---|
| **Zero-test modules** | Source files with no test counterpart. Weight by file size. |
| **Critical untested paths** | Files in `auth/`, `billing/`, `payment/`, `security/` or containing `create*`, `delete*`, `update*`, `charge*`, `transfer*`, `verify*` — with no tests. High confidence. |
| **Skipped tests** | `.skip(`, `.todo(`, `xit(`, `xdescribe(`, `@pytest.mark.skip`, `@pytest.mark.xfail` in test files. |
| **Missing edge cases** | Functions with `| null`, `| undefined`, `?: T`, `Optional[T]` params — check if tests cover null/empty/boundary. Heuristic; cap 70 confidence. |
| **Thin test files** | Test file <20% line count of source file. Low impact signal. |

---

## Subagent C: Efficiency Auditor

### C1 — Maintainability (Duplication + Dead Code)

| Category | What to detect |
|:---|:---|
| **Duplicated blocks** | ≥10 contiguous lines of similar logic in 2+ files. Normalize whitespace and identifiers before comparing. Report both locations. |
| **Copy-paste patterns** | Functions with near-identical control flow differing only in entity/field names — candidates for a shared generic. |
| **Extractable utilities** | Repeated inline patterns across ≥3 call sites: validation, formatting, API boilerplate, date manipulation. |
| **Dead exports** | Exported symbols not imported anywhere. Exclude entrypoints (`index.*`, `main.*`, `app.*`) and public API files. |
| **Unreachable code** | Code after unconditional `return`/`throw`/`break`/`continue`; always-true/false branch conditions. |
| **Unused imports** | `import`/`require` for symbols not referenced in file body. |
| **Commented-out code** | ≥5 consecutive comment lines that are syntactically valid code. |
| **Orphaned files** | Source files not imported/referenced by any other file. Exclude entrypoints, configs, migrations. |

### C2 — Performance Anti-Patterns

| Category | What to detect |
|:---|:---|
| **N+1 queries** | DB/API calls inside `for`, `while`, `.forEach()`, `.map()`, `.reduce()` loops. |
| **Sync in async** | `fs.readFileSync`, `execSync`, `spawnSync` inside async handlers or event loops. |
| **Missing indexes** | `WHERE`/`ORDER BY` columns without matching index in migration files. Requires migrations in scope. |
| **Large bundle imports** | `import _ from 'lodash'`, `import * as Icons from 'react-icons'` — whole-library imports where only a subset is used. |
| **Unbounded queries** | `SELECT *` / `.from().select(*)` without `.limit()`, `.range()`, or pagination. |
| **Missing memoization** | React: large lists/expensive derivations without `React.memo`/`useMemo`/`useCallback`. Backend: repeated identical DB queries without caching. |
| **Unnecessary re-renders** | Inline object/array literals in JSX props; functions created in render body without `useCallback`; context providers with unstable value objects. |
| **Missing streaming** | Large file reads or dataset fetches loaded entirely into memory — candidates for streaming/chunking. |
