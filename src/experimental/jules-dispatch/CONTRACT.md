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

## GitHub-handoff fingerprint (from cleantech_jobs PR #77)
Jules opens PRs from branches prefixed `jules-<digits>-<hash>`, commits authored by
`google-labs-jules[bot]`, body with `## Summary` / `## Changes`. Corroborating signal
alongside the session's own `outputs[].pullRequest.url`.
