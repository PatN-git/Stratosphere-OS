# Jules API contract (v1alpha) — as pinned for jules-dispatch

Source: https://developers.google.com/jules/api (v1alpha, **alpha — may change**).
Confirm the exact shapes on the first live run (guarded by `JulesError`).

- **Base URL:** `https://jules.googleapis.com/v1alpha`
- **Auth header:** `X-Goog-Api-Key: <JULES_API_KEY>` (env var `JULES_API_KEY`, from `.env.local`).

## Endpoints used
| Purpose | Method | Path |
|---|---|---|
| List connected sources | GET | `/sources` |
| Create session | POST | `/sessions` |
| Get session | GET | `/sessions/{id}` |
| List activities (poll) | GET | `/sessions/{id}/activities?pageSize=&createTime=` |

## Session resource (relevant fields)
```
name, id, prompt,
sourceContext: { source, githubRepoContext: { startingBranch } },
title, requirePlanApproval (bool), automationMode (enum),
createTime, updateTime, state (enum), url,
outputs: [ { pullRequest: { url, title, description } } ]
```

- **`automationMode`** enum: `AUTOMATION_MODE_UNSPECIFIED`, `AUTO_CREATE_PR`.
- **`state`** enum: `STATE_UNSPECIFIED`, `QUEUED`, `PLANNING`, `AWAITING_PLAN_APPROVAL`,
  `AWAITING_USER_FEEDBACK`, `IN_PROGRESS`, `PAUSED`, `FAILED`, `COMPLETED`.

## PR URL location (authoritative for `find_pr_url`)
**`outputs[].pullRequest.url`** on the **Session** resource (via `GET /sessions/{id}`).
The activities stream is progress/plan detail; the PR lands on `session.outputs`.

## Create-session request body
```json
{
  "prompt": "<issue title/body/acceptance-criteria only>",
  "sourceContext": { "source": "<source name>", "githubRepoContext": { "startingBranch": "main" } },
  "title": "<slice id>",
  "requirePlanApproval": true,
  "automationMode": "AUTO_CREATE_PR"
}
```

## Identifying a Jules PR (verified live 2026-07-16)
- **Authoritative:** the session's **`outputs[].pullRequest.url`** (what `find_pr_url` uses).
- **Reliable corroboration:** commit author **`google-labs-jules[bot]`**.
- **Branch name is NOT a fixed `jules-*` prefix** — Jules follows the target repo's
  `AGENTS.md` branch conventions. Observed: PR #77 used `jules-<digits>-<hash>`, but the
  live E2E on cleantech_jobs produced `feature/<slug>-<sessionId>`. **Do not match on the
  branch prefix.**
