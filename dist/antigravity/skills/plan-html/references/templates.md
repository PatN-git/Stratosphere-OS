# plan-html Templates

## 1. Implementation Plan
Use when mapping out multi-phase plans requiring timeline visualization and status/progress tracking.

```html
<section class="milestones">
  <h2>Project Roadmap</h2>
  <div class="progress-container">
    <div class="progress-bar" style="width: 33%">33% Complete</div>
  </div>
  <div class="timeline">
    <details class="phase-card" open>
      <summary><span class="status status-done">Done</span> Phase 1: Core Setup</summary>
      <div class="phase-details">
        <ul>
          <li>Configure database schema</li>
          <li>Initialize project configurations</li>
        </ul>
      </div>
    </details>
    <details class="phase-card" open>
      <summary><span class="status status-progress">In Progress</span> Phase 2: Core Logic</summary>
      <div class="phase-details">
        <ul>
          <li>Build core engines and controllers</li>
        </ul>
      </div>
    </details>
  </div>
</section>
<style>
  .status { display: inline-block; padding: 0.125rem 0.375rem; border-radius: 0.25rem; font-size: 0.75rem; font-weight: bold; margin-right: 0.5rem; text-transform: uppercase; }
  .status-done { background-color: #d1fae5; color: #065f46; }
  .status-progress { background-color: #fef3c7; color: #92400e; }
  .phase-card { border: 1px solid var(--border); border-radius: 0.5rem; margin-top: 1rem; background-color: var(--card-bg); }
  .phase-details { padding: 1rem; border-top: 1px solid var(--border); }
  .phase-details ul { padding-left: 1.25rem; }
</style>
```

---

## 2. Trade-Off Matrix
Use for side-by-side comparison of multiple design options across several criteria.

```html
<section class="matrix-section">
  <h2>Option Matrix</h2>
  <div class="table-wrapper">
    <table>
      <thead>
        <tr>
          <th>Criterion</th>
          <th>Option A: Serverless</th>
          <th>Option B: Dedicated Node</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>Cost</strong></td>
          <td><span class="badge badge-pos">Low ($0-$10/mo)</span></td>
          <td><span class="badge badge-neg">High ($40+/mo)</span></td>
        </tr>
        <tr>
          <td><strong>Complexity</strong></td>
          <td><span class="badge badge-neg">High (Cold starts)</span></td>
          <td><span class="badge badge-pos">Low (Deterministic)</span></td>
        </tr>
      </tbody>
    </table>
  </div>
</section>
<style>
  .table-wrapper { overflow-x: auto; margin-top: 1rem; }
  table { width: 100%; border-collapse: collapse; text-align: left; }
  th, td { padding: 0.75rem 1rem; border: 1px solid var(--border); }
  th { background-color: var(--card-bg); font-weight: bold; }
  .badge { display: inline-block; padding: 0.25rem 0.5rem; border-radius: 0.375rem; font-size: 0.825rem; font-weight: 500; }
  .badge-pos { background-color: #d1fae5; color: #065f46; }
  .badge-neg { background-color: #fee2e2; color: #991b1b; }
</style>
```

---

## 3. Annotated Flowchart
Use to illustrate execution flows, state transitions, or processes with interactive step highlights.

```html
<section class="flowchart-section">
  <h2>Interactive Process Flow</h2>
  <div class="flow-layout">
    <div class="flow-step active" id="step-1" onclick="highlightStep('step-1')">
      <div class="step-num">1</div>
      <div class="step-title">Ingest Prompt</div>
    </div>
    <div class="flow-arrow">➔</div>
    <div class="flow-step" id="step-2" onclick="highlightStep('step-2')">
      <div class="step-num">2</div>
      <div class="step-title">Apply Gates</div>
    </div>
    <div class="flow-arrow">➔</div>
    <div class="flow-step" id="step-3" onclick="highlightStep('step-3')">
      <div class="step-num">3</div>
      <div class="step-title">Emit Output</div>
    </div>
  </div>
  <div class="step-info" id="step-info-box">
    Click a step above to see detailed annotations.
  </div>
</section>
<style>
  .flow-layout { display: flex; align-items: center; justify-content: space-between; gap: 0.5rem; margin: 1.5rem 0; }
  .flow-step { flex: 1; text-align: center; padding: 1rem; border: 2px solid var(--border); border-radius: 0.5rem; background: var(--card-bg); cursor: pointer; transition: all 0.2s ease; }
  .flow-step.active { border-color: var(--accent); background: var(--accent-muted); color: var(--text); }
  .flow-arrow { font-size: 1.5rem; color: var(--border); }
  .step-num { font-size: 1.25rem; font-weight: 800; color: var(--accent); margin-bottom: 0.25rem; }
  .step-info { padding: 1rem; border: 1px solid var(--border); border-radius: 0.5rem; background: var(--card-bg); font-style: italic; }
</style>
<script>
  const stepData = {
    'step-1': 'Prompt Ingestion: Read input from user to capture context.',
    'step-2': 'Apply Gates: Evaluates 4-scenario framework to check suitability.',
    'step-3': 'Emit Output: Serializes to Markdown or HTML depending on results.'
  };
  function highlightStep(stepId) {
    document.querySelectorAll('.flow-step').forEach(el => el.classList.remove('active'));
    document.getElementById(stepId).classList.add('active');
    document.getElementById('step-info-box').textContent = stepData[stepId];
    document.getElementById('step-info-box').style.fontStyle = 'normal';
  }
</script>
```
