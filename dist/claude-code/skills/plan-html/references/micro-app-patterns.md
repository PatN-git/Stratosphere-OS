---
name: micro-app-patterns
description: Protocol and patterns for interactive round-trip editing micro-apps.
version: "1.1.0"
timestamp: 2026-06-24
---

# Micro-App Protocol & Patterns

Use Micro-Apps when the user needs to configure data, adjust parameters, or perform visual adjustments that produce config schemas/states to be fed back into code.

## Flow
1. **Emit Micro-App**: The agent generates the HTML with input controls (sliders, forms, checkboxes, draggable cards).
2. **Interactive Selection / Editing**: The user runs the HTML in their browser, interacts with the controls, and performs modifications.
3. **Copy Output**: User clicks "Copy JSON State" or "Copy Change Payload" and pastes it back into the terminal/editor or prompt.
4. **Apply Changes**: The agent parses the state or change payload, applies it back to the codebase source files, and verifies.

---

## Pattern 1: Configuration Editor
```html
<section class="config-app">
  <h2>Rules Configuration Editor</h2>
  <div class="control-group">
    <label for="threshold">Match Threshold (<span id="threshold-val">0.8</span>)</label>
    <input type="range" id="threshold" min="0" max="1" step="0.05" value="0.8" oninput="updateVal('threshold', this.value); updateConfig()">
  </div>
  <div class="control-group">
    <label><input type="checkbox" id="strict" onchange="updateConfig()"> Strict Validation Mode</label>
  </div>
  <div class="state-output">
    <h3>Resulting JSON Config</h3>
    <pre><code id="json-preview">{}</code></pre>
  </div>
</section>
<style>
  .control-group { margin-bottom: 1rem; }
  .control-group label { display: block; font-weight: bold; margin-bottom: 0.25rem; }
  input[type="range"] { width: 100%; }
  .state-output { margin-top: 1.5rem; }
  pre { background: var(--card-bg); border: 1px solid var(--border); padding: 1rem; border-radius: 0.375rem; overflow-x: auto; }
</style>
<script>
  function updateVal(id, val) {
    document.getElementById(id + '-val').textContent = val;
  }
  function updateConfig() {
    const config = {
      threshold: parseFloat(document.getElementById('threshold').value),
      strictMode: document.getElementById('strict').checked
    };
    document.getElementById('plan-data').textContent = JSON.stringify(config, null, 2);
    document.getElementById('json-preview').textContent = JSON.stringify(config, null, 2);
  }
  updateConfig();
</script>
```

---

## Pattern 2: Generic Board Editor (F1)
A domain-agnostic layout for cards moving between columns. Extremely useful for roadmap prioritization, sprint planning, and backlog triage.

### 1. Seam Schema
- **Input State (`plan-data`)**:
  ```json
  {
    "columns": [
      { "id": "col-1", "label": "Backlog" },
      { "id": "col-2", "label": "In Progress" }
    ],
    "cards": [
      { "id": "card-001", "label": "Setup database migrations", "column": "col-1", "meta": { "priority": "high" } },
      { "id": "card-002", "label": "Write E2E tests", "column": "col-2", "meta": { "priority": "medium" } }
    ]
  }
  ```

- **Output Change Payload**:
  Emits a line-delimited change payload showing moves. Each line has the format:
  `<card_id> -> <new_column_id>`
  Example:
  ```
  card-001 -> col-2
  card-002 -> col-1
  ```

### 2. Constraints & Seam Rules
- **Domain Agnostic**: The board template itself must contain zero domain-specific words (like "release", "milestone", "sprint"). It only understands `columns` and `cards`.
- **Ephemeral Editor**: The HTML board is an editor only, not a datastore. The source of truth remains the codebase files (like BACKLOG_MAP.md or task.md). The agent reads the source files, projects them onto columns/cards, writes the HTML, receives the pasted change payload, and maps the moves back to rewrite the source files.
- **Copy-Paste Only**: Works offline/hermetically in both Claude Code and Antigravity.
- **Robust Parser**: The parser on the agent side must validate each change line, reject malformed rows, and ignore lines with no changes.
