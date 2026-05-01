---
description: This skill ensures that the project's skill inventory is accurate, synchronized, and well-documented.
---

# Sync Skills Workflow

This skill ensures that the project's skill inventory is accurate, synchronized, and well-documented.

## Core Operations: Plan & Confirm

The skill's state is managed internally in [skills.json](./skills.json). **The user should not need to interact with this file directly.**

### Step 1: Generate Update Plan
Run the script with `--dry-run` to audit the repository state and generate a proposed plan.

```bash
python .agents/workflows/sync-skills/scripts/sync_skills.py --dry-run
```

### Step 2: Review and Resolve Ambiguities
Present the **Reconciliation Summary** to the user.
- **Orphans**: If the script flags orphans, ask the user: "I found new skills on disk. What are their GitHub URLs?"
- **Missing**: If skills are missing locally, ask: "Some skills in my config aren't on disk. Should I download them with --pull?"
- **Flagged**: Explain any local/remote conflicts (e.g., local changes since last sync).

**Interactive Management**: As the user provides information, you (the agent) are responsible for running the sync script to update the internal `skills.json` state.

### Step 3: Execute
Once the user confirms the plan or provides missing data, run the script to commit changes.

```bash
python .agents/workflows/sync-skills/scripts/sync_skills.py
```

## Configuration Flags
- `--dry-run`: Show what WOULD change without writing to disk.
- `--pull`: Download external skills from GitHub based on the config.
- `--local`: List of skills to treat as local-only (default: sync-skills, instantiation-memory).
- `--llm`: Enable this only if you need to refresh descriptions from SKILL.md files.

## LLM / Token Efficiency Rules
- **Prefer Deterministic Logic**: Always run the `sync_skills.py` script first to handle the heavy lifting.
- **Minimal Prompts**: Provide only the names and snippets of the flagged skills to the user.
- **Batch Decisions**: If multiple orphans are found, ask for all their URLs in a single turn.

## Greenfield Bootstrapping
If the project structure is missing, the script will automatically offer to create `.agents/workflows/` and the internal `skills.json`.