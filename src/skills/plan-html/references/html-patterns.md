---
name: html-patterns
description: Reusable HTML, CSS, and JS patterns for interactive, complex plan documents and spatial components.
version: "1.1.0"
timestamp: 2026-06-24
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

## Reading Progress Bar
Renders a thin bar at the top of the viewport indicating how far down the document the user has scrolled.
```html
<div id="reading-progress" class="reading-progress"></div>
<style>
  .reading-progress { position: fixed; top: 0; left: 0; height: 4px; background: var(--accent); width: 0%; z-index: 1001; transition: width 0.1s ease; }
</style>
<script>
  window.addEventListener('scroll', () => {
    const winScroll = document.body.scrollTop || document.documentElement.scrollTop;
    const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
    const scrolled = height > 0 ? (winScroll / height) * 100 : 0;
    document.getElementById('reading-progress').style.width = scrolled + '%';
  });
</script>
```

## Sticky Table of Contents (TOC) & Scroll-Spy
Generates a side navigation list that highlights sections dynamically as they enter the viewport.
```html
<div class="layout">
  <aside class="sidebar">
    <nav class="toc" aria-label="Table of Contents">
      <ul id="toc-list">
        <!-- Dynamically generated list items:
             <li><a href="#section-id" class="toc-link">Section Title</a></li>
        -->
      </ul>
    </nav>
  </aside>
  <main class="content">
    <section id="section-1" class="spy-section">Content 1</section>
    <section id="section-2" class="spy-section">Content 2</section>
  </main>
</div>
<style>
  .layout { display: grid; grid-template-columns: 260px 1fr; gap: 2rem; }
  .sidebar { position: sticky; top: 2rem; height: calc(100vh - 4rem); overflow-y: auto; }
  .toc ul { list-style: none; padding: 0; }
  .toc li { margin-bottom: 0.5rem; }
  .toc-link { text-decoration: none; color: var(--text); opacity: 0.6; font-size: 0.9rem; transition: opacity 0.2s; }
  .toc-link:hover { opacity: 1; }
  .toc-link.active { opacity: 1; color: var(--accent); font-weight: 600; }
  @media (max-width: 768px) {
    .layout { grid-template-columns: 1fr; }
    .sidebar { position: static; height: auto; margin-bottom: 1.5rem; }
  }
</style>
<script>
  // Scroll-Spy using IntersectionObserver
  const observerOptions = { root: null, rootMargin: '0px 0px -60% 0px', threshold: 0 };
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const id = entry.target.getAttribute('id');
        document.querySelectorAll('.toc-link').forEach(link => {
          if (link.getAttribute('href') === '#' + id) {
            link.classList.add('active');
          } else {
            link.classList.remove('active');
          }
        });
      }
    });
  }, observerOptions);
  document.querySelectorAll('.spy-section').forEach(sec => observer.observe(sec));
</script>
```

## Knowledge Explorer (Client-Side Search/Filter)
Enables filtering sections in real-time by entering query keywords.
```html
<div class="search-box">
  <input type="text" id="search-input" placeholder="Filter sections..." oninput="filterContent(this.value)">
</div>
<script>
  function filterContent(query) {
    const q = query.toLowerCase().trim();
    document.querySelectorAll('.spy-section').forEach(sec => {
      const text = sec.textContent.toLowerCase();
      const match = !q || text.includes(q);
      sec.style.display = match ? 'block' : 'none';
      
      // Update corresponding TOC link visibility
      const id = sec.getAttribute('id');
      const tocLink = document.querySelector(`.toc-link[href="#${id}"]`);
      if (tocLink) {
        tocLink.parentElement.style.display = match ? 'block' : 'none';
      }
    });
  }
</script>
```

## Diagram Components (Inline SVG)
Zero-dependency diagrams representing decision gates, branching options, and loops.

### 1. Decision Node
```html
<svg viewBox="0 0 400 120" class="svg-diagram">
  <!-- Diamond Shape -->
  <polygon points="200,10 280,60 200,110 120,60" fill="var(--card-bg)" stroke="var(--accent)" stroke-width="2"/>
  <text x="200" y="65" text-anchor="middle" font-weight="bold" fill="var(--text)">Is Complex?</text>
  <!-- Yes/No Outputs -->
  <path d="M 280 60 L 350 60" stroke="var(--border)" stroke-width="2" marker-end="url(#arrow)"/>
  <text x="315" y="50" text-anchor="middle" font-size="12" fill="var(--text)">Yes</text>
  <path d="M 120 60 L 50 60" stroke="var(--border)" stroke-width="2" marker-end="url(#arrow)"/>
  <text x="85" y="50" text-anchor="middle" font-size="12" fill="var(--text)">No</text>
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--border)" />
    </marker>
  </defs>
</svg>
```

### 2. Branching Options
```html
<svg viewBox="0 0 400 180" class="svg-diagram">
  <!-- Root node -->
  <rect x="150" y="10" width="100" height="40" rx="5" fill="var(--card-bg)" stroke="var(--border)" stroke-width="2"/>
  <text x="200" y="35" text-anchor="middle" fill="var(--text)">Start</text>
  
  <!-- Branch Arrows -->
  <path d="M 200 50 L 200 80 Q 200 90 110 90 L 80 90 L 80 110" fill="none" stroke="var(--border)" stroke-width="2" marker-end="url(#arrow)"/>
  <path d="M 200 50 L 200 80 Q 200 90 290 90 L 320 90 L 320 110" fill="none" stroke="var(--border)" stroke-width="2" marker-end="url(#arrow)"/>
  
  <!-- Branch A -->
  <rect x="30" y="110" width="100" height="40" rx="5" fill="var(--card-bg)" stroke="var(--accent)" stroke-width="2"/>
  <text x="80" y="135" text-anchor="middle" fill="var(--text)">Branch A</text>
  
  <!-- Branch B -->
  <rect x="270" y="110" width="100" height="40" rx="5" fill="var(--card-bg)" stroke="var(--accent)" stroke-width="2"/>
  <text x="320" y="135" text-anchor="middle" fill="var(--text)">Branch B</text>
</svg>
```

### 3. Loop Block
```html
<svg viewBox="0 0 400 160" class="svg-diagram">
  <!-- Iteration box -->
  <rect x="140" y="20" width="120" height="40" rx="5" fill="var(--card-bg)" stroke="var(--accent)" stroke-width="2"/>
  <text x="200" y="45" text-anchor="middle" fill="var(--text)">Execute Work</text>
  
  <!-- Forward Arrow -->
  <path d="M 200 60 L 200 100" stroke="var(--border)" stroke-width="2" marker-end="url(#arrow)"/>
  
  <!-- Evaluation Diamond -->
  <polygon points="200,100 240,120 200,140 160,120" fill="var(--card-bg)" stroke="var(--border)" stroke-width="1.5"/>
  <text x="200" y="124" text-anchor="middle" font-size="10" fill="var(--text)">Done?</text>
  
  <!-- Loopback Arrow (eval -> back to iteration box) -->
  <path d="M 160 120 L 80 120 Q 70 120 70 80 Q 70 40 80 40 L 140 40" fill="none" stroke="var(--border)" stroke-width="2" marker-end="url(#arrow)"/>
  <text x="100" y="110" text-anchor="middle" font-size="10" fill="var(--text)">No</text>
</svg>
```
