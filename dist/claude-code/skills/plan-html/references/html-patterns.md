---
name: html-patterns
description: html-patterns
version: "1.0.1"
timestamp: 2026-06-17
---

# Reusable Patterns for plan-html

## Accordion / Collapsible Section
```html
<details class="accordion-item" open>
  <summary>Phase 1: Foundation</summary>
  <div class="content">
    <p>Details about this phase.</p>
  </div>
</details>
<style>
  details { border: 1px solid var(--border); border-radius: 0.375rem; margin-bottom: 0.75rem; background: var(--card-bg); }
  summary { padding: 0.75rem 1rem; font-weight: 600; cursor: pointer; user-select: none; }
  .content { padding: 0.75rem 1rem; border-top: 1px solid var(--border); }
</style>
```

## Tabs Layout
```html
<div class="tabs">
  <div class="tab-list">
    <button class="tab-btn active" onclick="switchTab(event, 'tab-1')">Tab 1</button>
    <button class="tab-btn" onclick="switchTab(event, 'tab-2')">Tab 2</button>
  </div>
  <div id="tab-1" class="tab-panel active">Panel 1 Content</div>
  <div id="tab-2" class="tab-panel">Panel 2 Content</div>
</div>
<style>
  .tab-list { display: flex; gap: 0.25rem; border-bottom: 1px solid var(--border); margin-bottom: 1rem; }
  .tab-btn { background: none; border: none; border-bottom: 2px solid transparent; padding: 0.5rem 1rem; cursor: pointer; }
  .tab-btn.active { border-bottom-color: var(--accent); color: var(--accent); font-weight: bold; }
  .tab-panel { display: none; }
  .tab-panel.active { display: block; }
</style>
<script>
  function switchTab(e, id) {
    const parent = e.target.closest('.tabs');
    parent.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    parent.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    e.target.classList.add('active');
    parent.querySelector('#' + id).classList.add('active');
  }
</script>
```

## Progress Bar
```html
<div class="progress-container">
  <div class="progress-bar" style="width: 65%;">65%</div>
</div>
<style>
  .progress-container { background: var(--border); border-radius: 9999px; height: 1.25rem; overflow: hidden; width: 100%; }
  .progress-bar { background: var(--accent); color: white; text-align: right; padding-right: 0.5rem; font-size: 0.75rem; font-weight: bold; line-height: 1.25rem; }
</style>
```
