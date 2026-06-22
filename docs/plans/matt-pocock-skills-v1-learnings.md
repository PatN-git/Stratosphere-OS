# Matt Pocock Skills v1.0 Learnings & Recommendations

This document outlines the core learnings from Matt Pocock's Skills v1.0 release and provides recommendations on how to apply these concepts to the StratOS architecture to improve token efficiency and reduce cognitive load.

## 1. Core Learnings

### 1.1 Progressive Disclosure & `disable-model-invocation`
- **Concept:** By adding `disable-model-invocation: true` to the frontmatter of a skill or workflow, the agent is prevented from automatically loading its heavy description into the context window during every interaction.
- **Benefit:** This simple addition resulted in a **63% reduction in token cost** across typical sessions. It prevents context bloat for orchestrator workflows that the user will trigger manually anyway.
- **Industry Standard:** This approach is officially supported and recommended across major agent frameworks (Claude Code, GitHub Copilot, Zed) for commands that shouldn't be auto-triggered.

### 1.2 User-Invoked vs. Model-Invoked Taxonomy
- **User-Invoked Skills:** These act as *orchestrators*. They contain the high-level workflow steps and delegate to other skills. They should always have `disable-model-invocation: true`.
- **Model-Invoked Skills:** These are focused *disciplines* (like `micro-tdd`, `codebase-design`, `diagnosing-bugs`). They do not have the disable flag, meaning the agent can autonomously choose to invoke them when the current task demands it.

### 1.3 De-duplication of Workflows
- **Problem:** Previously, complex skills (like a "Grill with Docs" workflow) embedded both the interview loop and the domain modeling logic, leading to sprawl.
- **Solution:** Extract the reusable logic into small, Model-Invoked skills (e.g., `grilling` and `domain-modeling`). The User-Invoked orchestrator then becomes a thin shell that simply says "Run a `/grilling` session, using the `/domain-modeling` skill."

### 1.4 The Router Skill
- **Problem:** As the library of user-invoked orchestrators grows, users forget which skill to use when.
- **Solution:** A master router skill (`/ask-matt`) that serves as a single entry point. It briefly names all other skills, explains the lifecycle on-ramps, and guides the user on how to start their work.

### 1.5 Writing Great Skills
- **Vocabulary:** Skills should establish and utilize shared terminology (like "sprawl", "sediment", "premature completion") to compress complex concepts into dense "leading words" that the LLM already understands, further minimizing token consumption.

---

## 2. Recommendations for StratOS

Based on these learnings, the following architectural changes are recommended for StratOS. 

> **Note:** These changes are pending explicit user approval and have not yet been implemented.

### 2.1 Migrate to `disable-model-invocation`
- **Action:** Replace or supplement the StratOS-specific `trigger: User. Do not run autonomously.` with the industry-standard `disable-model-invocation: true` in all files under `src/workflows/`.
- **Reasoning:** While `trigger: User` communicates intent clearly, native AI agents may not use it to optimize the context window. Explicitly disabling model invocation aligns with how the underlying LLM interfaces compress context.

### 2.2 Realign the Taxonomy
- **User-Invoked (Orchestrators):** All files in `src/workflows/` (e.g., `0a_start-session.md`, `1a_research.md`, `3d_implement-issue.md`) are the orchestrators. They should be strictly user-invoked and hidden from the model's auto-context.
- **Model-Invoked (Primitives):** The skills in `src/skills/` (like `micro-tdd`) should remain model-invoked (no disable flag) so the agent can fall back to them natively during execution loops without explicit user commands.

### 2.3 Implement a StratOS Router Workflow
- **Action:** Create a new workflow, e.g., `src/workflows/00_router.md` or a `/ask-stratos` skill.
- **Reasoning:** This will act as the index for the 0a-4b lifecycle, answering the user's question "What do I run next?" and reducing the cognitive load of navigating the system.

### 2.4 Extract and De-duplicate Workflow Logic
- **Action:** Review the larger workflows (like `3d_implement-issue.md`) and extract standalone discipline logic (e.g., the rigorous RED-GREEN-REFACTOR TDD cycle) into smaller, model-invoked skills (which `micro-tdd` already partially serves). 
- **Reasoning:** The orchestrator should just point to the discipline skill, rather than spelling out the exact steps, keeping the workflow file extremely token-efficient.
