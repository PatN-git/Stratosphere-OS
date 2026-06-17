---
name: micro-app-patterns
description: micro-app-patterns
version: "1.0.0"
updated: 2026-06-17
---

# Micro-App Protocol & Patterns

Use Micro-Apps when the user needs to configure data, adjust parameters, or perform visual adjustments that produce config schemas/states to be fed back into code.

## Flow
1. **Emit Micro-App**: The agent generates the HTML with input controls (sliders, forms, checkboxes).
2. **Interactive Selection**: The user runs the HTML, modifies inputs to match preference.
3. **Copy Output**: User clicks "Copy JSON State" and pastes it back into the terminal/editor.

## Pattern Example: Configuration Editor
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
    // Sync into base template state storage
    document.getElementById('plan-data').textContent = JSON.stringify(config, null, 2);
    // Sync to UI preview
    document.getElementById('json-preview').textContent = JSON.stringify(config, null, 2);
  }
  // Initialize
  updateConfig();
</script>
```
