---
name: 0e-plain-english
description: "Restate the agent's last message or question in plain, non-technical English with an offer to elaborate. Invoke only on explicit user request — never autonomously."
disable-model-invocation: true
triggers: ["user"]
metadata:
  stratos.layer: lifecycle
  stratos.mode: HITL
version: "1.0.0"
timestamp: 2026-10-20
---

Explain your previous message (or subject passed as arguments) to a non-technical reader, in first person. Read-only: no edits, commands, or answers on user's behalf.

Output ≤ 250 words, ≤ 140 if nothing is asked of the user. Short sentences, everyday words, in order:
1. **Verdict:** bold 1–2 sentences: what was said, decided, or done. Later sections never restate it.
2. **Picture:** one everyday analogy, reused through the answer, only where it makes an abstract mechanism concrete; omit for plain status.
3. **Needs from you:** every question, decision, or approval requested, secondary ones included, each as one plain question; `nothing` if none. Never drop or merge items. Under a question that offers choices, list every choice once, by its own label, in one sentence: what it is and what picking it costs, risks, or gains, from conversation context; if unknown, omit the cost rather than say you do not know it. Where the user must pick among named items (steps, files, tests), list each, glossed; never collapse them into a category.
4. **Recommendation:** only the pick and reason your message gave, in one line, naming the choice by label without restating it; none given: omit this section. Never invent one.
5. **Heads-up:** every action that changed anything (issue, PR, push, commit, message, file edit, delete, spend, publish), stated bluntly even if reversible, with commit and push status exactly as the input gives it. Outward-facing actions one line each; local file edits may share a line. Omit only if the input reports no action.
6. **Left out:** one line naming dropped categories (numbers, labels, links); omit if none.
7. Close: `Say "more" for details, or name the part to unpack.`

Over the cap, shorten Picture, then choice sentences, then Heads-up wording. Never drop a Need, an outward-facing action, a handle, a behavior change, or a reversibility statement.

Rules:
- State only what the input states, including the reasons it gives. Never add a reason, consequence, or reassurance it does not give; where it gives none, omit rather than pad. Quote marks only around character-for-character text.
- Replace commands, paths, IDs, and internal names with plain descriptions. Keep one short handle (ID or link) for anything created or changed, and a raw name the user must act on, once. Every git, CI, and tool word (commit, branch, PR, push, staged, validator, slice, step or phase names) is replaced or glossed in ≤ 5 words on first use. A technical term that must stay gets a ≤ 8-word definition.

On "more" or a follow-up: elaborate only the requested part, same rules, with a concrete example; offer "more" again only if detail remains.
