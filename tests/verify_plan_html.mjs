import fs from 'fs';
import path from 'path';
import vm from 'vm';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, '..');

console.log('=== plan-html Behavioral Verification Harness ===\n');

let failed = false;

function assert(label, condition) {
  if (condition) {
    console.log(`  PASS  ${label}`);
  } else {
    console.log(`  FAIL  ${label}`);
    failed = true;
  }
}

// Helper to walk object leaves
function getLeafValues(obj, pathList = []) {
  let values = [];
  if (obj === null || obj === undefined) return values;
  
  if (typeof obj === 'string' || typeof obj === 'number') {
    const lastKey = pathList[pathList.length - 1];
    const excludedKeys = ['id', 'status', 'trend', 'good', 'severity', 'kind', 'done', 'type', 'column'];
    if (!excludedKeys.includes(lastKey)) {
      values.push(String(obj));
    }
    return values;
  }
  
  if (Array.isArray(obj)) {
    obj.forEach((item, index) => {
      values = values.concat(getLeafValues(item, [...pathList, index]));
    });
    return values;
  }
  
  if (typeof obj === 'object') {
    Object.keys(obj).forEach(key => {
      values = values.concat(getLeafValues(obj[key], [...pathList, key]));
    });
    return values;
  }
  
  return values;
}

// Stack-based basic HTML parser for mock DOM
function parseHTML(html) {
  const root = new MockElement('root');
  const stack = [root];
  const tagRegex = /<(\/?)([a-z0-9-]+)([^>]*?)(\/?)>/gi;
  let lastIndex = 0;
  let match;
  while ((match = tagRegex.exec(html)) !== null) {
    const [fullTag, isClose, tagName, attrStr, isSelfClose] = match;
    const textBefore = html.slice(lastIndex, match.index).trim();
    if (textBefore && stack.length > 0) {
      stack[stack.length - 1].textContent += (stack[stack.length - 1].textContent ? ' ' : '') + textBefore;
    }
    lastIndex = tagRegex.lastIndex;

    if (isClose) {
      if (stack.length > 1) {
        stack.pop();
      }
    } else {
      const attrs = {};
      const classMatch = attrStr.match(/class=["']([^"']+)["']/);
      if (classMatch) attrs.class = classMatch[1];
      const idMatch = attrStr.match(/id=["']([^"']+)["']/);
      if (idMatch) attrs.id = idMatch[1];
      const hrefMatch = attrStr.match(/href=["']([^"']+)["']/);
      if (hrefMatch) attrs.href = hrefMatch[1];
      const titleMatch = attrStr.match(/title=["']([^"']+)["']/);
      if (titleMatch) attrs.title = titleMatch[1];

      const el = new MockElement(tagName.toLowerCase(), attrs);
      if (stack.length > 0) {
        stack[stack.length - 1].children.push(el);
      }
      if (!isSelfClose && !['img', 'input', 'br', 'hr', 'meta', 'link'].includes(tagName.toLowerCase())) {
        stack.push(el);
      }
    }
  }
  const textAfter = html.slice(lastIndex).trim();
  if (textAfter && stack.length > 0) {
    stack[stack.length - 1].textContent += (stack[stack.length - 1].textContent ? ' ' : '') + textAfter;
  }
  return root.children;
}

// Custom lightweight DOM mockup for VM
class MockElement {
  constructor(tagName = 'div', attrs = {}) {
    this.tagName = tagName;
    this.attrs = attrs;
    this.children = [];
    this.textContent = '';
    this._innerHTML = '';
    this.className = attrs.class || '';
    this.style = {};
    this.classList = {
      add: (c) => {
        const classes = this.className.split(/\s+/).filter(Boolean);
        if (!classes.includes(c)) {
          classes.push(c);
          this.className = classes.join(' ');
        }
      },
      remove: (c) => {
        const classes = this.className.split(/\s+/).filter(Boolean);
        this.className = classes.filter(x => x !== c).join(' ');
      },
      contains: (c) => {
        return this.className.split(/\s+/).includes(c);
      }
    };
  }

  setAttribute(name, val) {
    this.attrs[name] = val;
    if (name === 'class') this.className = val;
  }
  getAttribute(name) {
    if (name === 'class') return this.className;
    return this.attrs[name] || null;
  }
  addEventListener(event, callback) {}

  set innerHTML(val) {
    this._innerHTML = '';
    this.children = parseHTML(val);
  }

  get innerHTML() {
    if (this._innerHTML) return this._innerHTML;
    return this.children.map(c => {
      const attrsStr = Object.entries(c.attrs).map(([k, v]) => ` ${k}="${v}"`).join('');
      const tag = c.tagName;
      if (['img', 'input', 'br', 'hr', 'meta', 'link'].includes(tag)) {
        return `<${tag}${attrsStr}/>`;
      }
      return `<${tag}${attrsStr}>${c.innerHTML || c.textContent}</${tag}>`;
    }).join('');
  }

  querySelector(selector) {
    return this.querySelectorAll(selector)[0] || null;
  }

  querySelectorAll(selector) {
    let results = [];
    const matches = (el) => {
      if (selector.startsWith('#')) {
        return el.getAttribute('id') === selector.slice(1);
      }
      if (selector.startsWith('.')) {
        const classes = selector.slice(1).split('.');
        return classes.every(c => el.classList.contains(c));
      }
      if (selector.includes('[href=')) {
        const hrefVal = selector.match(/href=["']?([^"']+)["']?/)[1];
        return el.getAttribute('href') === hrefVal;
      }
      return el.tagName.toLowerCase() === selector.toLowerCase();
    };

    const dfs = (el) => {
      if (matches(el)) results.push(el);
      (el.children || []).forEach(child => dfs(child));
    };

    (this.children || []).forEach(child => dfs(child));
    return results;
  }
}

// Helper to determine the template type from data
function detectTemplateType(data) {
  if (data.columns && data.cards) return 'board';
  if (data.criteria && data.options && data.ratings) return 'trade-off-matrix';
  if (data.events) return 'incident-timeline';
  if (data.context && data.options && data.decision) return 'decision-record';
  if (data.lenses && data.options) return 'wireframe-compare';
  if (data.kpis && data.sections) return 'status-report';
  if (data.sections && data.toc) return 'plan-document';
  if (data.tabs) return 'custom-composition';
  return 'unknown';
}

// ─── 1. Lossless Export & Render Validation ────────────────────────────────
console.log('[1] Lossless Export & Render Validation');

const outputDir = path.join(rootDir, 'src/skills/plan-html/test/output');
const mockFiles = fs.readdirSync(outputDir).filter(file => file.endsWith('.html'));

mockFiles.forEach(file => {
  const filePath = path.join(outputDir, file);
  if (!fs.existsSync(filePath)) {
    assert(`Mock file exists: ${file}`, false);
    return;
  }
  
  const content = fs.readFileSync(filePath, 'utf-8');
  
  // Extract JSON state
  const dataRegex = /<script\s+id="plan-data"\s+type="application\/json">([\s\S]*?)<\/script>/;
  const match = content.match(dataRegex);
  if (!match) {
    assert(`State script present in ${file}`, false);
    return;
  }
  
  let data;
  try {
    data = JSON.parse(match[1].trim());
    assert(`Parse JSON state in ${file}`, true);
  } catch (err) {
    assert(`Parse JSON state in ${file} (${err.message})`, false);
    return;
  }
  
  // Extract script block containing toMarkdown / renderBody
  const scriptRegex = /<script>([\s\S]*?)<\/script>/g;
  let scriptContent = '';
  let m;
  while ((m = scriptRegex.exec(content)) !== null) {
    if (m[1].includes('toMarkdown') || m[1].includes('renderBody')) {
      scriptContent = m[1];
      break;
    }
  }
  
  if (!scriptContent) {
    assert(`Script block found in ${file}`, false);
    return;
  }
  
  // Setup Mock DOM structure for execution context
  const bodyRoot = new MockElement('body');
  let wrap;
  if (file === 'custom-composition.html') {
    bodyRoot.children = parseHTML(content);
    wrap = bodyRoot.querySelector('.wrap') || bodyRoot;
  } else {
    wrap = new MockElement('div', { class: 'wrap' });
    const h1 = new MockElement('h1');
    const period = new MockElement('div', { class: 'period' });
    const meta = new MockElement('div', { class: 'meta' });
    const toolbar = new MockElement('div', { class: 'toolbar' });
    wrap.children.push(h1, period, meta, toolbar);
    bodyRoot.children.push(wrap);

    // Setup template specific components
    const triageBoard = new MockElement('div', { class: 'board-layout' });
    const matrixTable = new MockElement('table', { id: 'matrix' });
    const contextDiv = new MockElement('div', { id: 'context' });
    const optionsDiv = new MockElement('div', { id: 'options' });
    const decisionDiv = new MockElement('div', { id: 'decision' });
    const consequencesUl = new MockElement('ul', { id: 'consequences' });
    const timelineDiv = new MockElement('div', { id: 'timeline' });
    const kpisDiv = new MockElement('div', { id: 'kpis' });
    const sectionsDiv = new MockElement('div', { id: 'sections' });
    const compareGrid = new MockElement('div', { id: 'compare-grid' });
    const contentDiv = new MockElement('main', { id: 'content', class: 'content' });
    const tocList = new MockElement('ul', { id: 'toc-list' });
    const phasesDiv = new MockElement('div', { id: 'phases' });

    wrap.children.push(
      triageBoard, matrixTable, contextDiv, optionsDiv, decisionDiv,
      consequencesUl, timelineDiv, kpisDiv, sectionsDiv, compareGrid,
      contentDiv, tocList, phasesDiv
    );
  }

  const toast = new MockElement('div', { id: 'toast' });
  const progressLabel = new MockElement('div', { id: 'progress-label' });
  const progressBar = new MockElement('div', { id: 'progress-bar' });
  const readingProgress = new MockElement('div', { id: 'reading-progress' });
  bodyRoot.children.push(toast, progressLabel, progressBar, readingProgress);
  let domContentLoadedListener = null;

  // VM context definition
  const context = {
    document: {
      documentElement: bodyRoot,
      querySelector: (sel) => {
        if (sel === '.wrap') return wrap;
        return wrap.querySelector(sel) || bodyRoot.querySelector(sel);
      },
      querySelectorAll: (sel) => {
        const results = wrap.querySelectorAll(sel);
        return results.length > 0 ? results : bodyRoot.querySelectorAll(sel);
      },
      getElementById: (id) => {
        if (id === 'plan-data') return { textContent: match[1] };
        return bodyRoot.querySelector(`#${id}`);
      },
      addEventListener: (event, listener) => {
        if (event === 'DOMContentLoaded') {
          domContentLoadedListener = listener;
        }
      }
    },
    navigator: {
      clipboard: {
        writeText: () => Promise.resolve()
      }
    },
    window: {
      addEventListener: (event, listener) => {
        if (event === 'DOMContentLoaded') {
          domContentLoadedListener = listener;
        }
      },
      getComputedStyle: (el) => ({
        display: el.style.display || 'block'
      })
    },
    addEventListener: (event, listener) => {
      if (event === 'DOMContentLoaded') {
        domContentLoadedListener = listener;
      }
    },
    localStorage: {
      getItem: () => null,
      setItem: () => {}
    },
    originalColumns: {},
    console: {
      log: () => {},
      error: (...args) => console.error("VM error:", ...args)
    },
    IntersectionObserver: class {
      constructor() {}
      observe() {}
      unobserve() {}
      disconnect() {}
    }
  };
  bodyRoot.classList.remove = () => {};
  bodyRoot.classList.add = () => {};
  vm.createContext(context);
  
  try {
    vm.runInContext(scriptContent, context);
    if (typeof context.toMarkdown !== 'function') {
      assert(`toMarkdown defined in ${file}`, false);
      return;
    }
    
    // Call toMarkdown(data)
    const md = context.toMarkdown(data);
    assert(`toMarkdown executed without errors in ${file}`, typeof md === 'string');
    
    // Verify every content leaf scalar is in the output markdown
    const leaves = getLeafValues(data);
    let allPresent = true;
    leaves.forEach(val => {
      const cleanVal = val.trim();
      if (cleanVal && !md.includes(cleanVal)) {
        console.log(`    Missing leaf: "${cleanVal}"`);
        allPresent = false;
      }
    });
    
    assert(`Lossless check: every content leaf of ${file} present in markdown`, allPresent);

    // Call renderBody(data)
    if (typeof context.renderBody !== 'function') {
      assert(`renderBody defined in ${file}`, false);
      return;
    }

    if (domContentLoadedListener) {
      domContentLoadedListener();
    } else {
      context.renderBody(data);
      if (typeof context.afterRender === 'function') {
        context.afterRender(data);
      }
    }

    // (a) Content root non-empty after renderBody
    const hasRenderedContent = wrap.innerHTML || bodyRoot.innerHTML;
    assert(`Render check: ${file} content root is non-empty`, !!hasRenderedContent);

    // (b) Idempotent - blank the root, re-render, serialized DOM equals first render
    const firstRenderHTML = bodyRoot.innerHTML;
    // Reset DOM roots
    if (file === 'custom-composition.html') {
      // Just re-run renderBody to verify it updates idempotently
    } else {
      // Recreate wrap elements
      wrap.children = [];
      const h1 = new MockElement('h1');
      const period = new MockElement('div', { class: 'period' });
      const meta = new MockElement('div', { class: 'meta' });
      const toolbar = new MockElement('div', { class: 'toolbar' });
      wrap.children.push(h1, period, meta, toolbar);
      
      const triageBoard = new MockElement('div', { class: 'board-layout' });
      const matrixTable = new MockElement('table', { id: 'matrix' });
      const contextDiv = new MockElement('div', { id: 'context' });
      const optionsDiv = new MockElement('div', { id: 'options' });
      const decisionDiv = new MockElement('div', { id: 'decision' });
      const consequencesUl = new MockElement('ul', { id: 'consequences' });
      const timelineDiv = new MockElement('div', { id: 'timeline' });
      const kpisDiv = new MockElement('div', { id: 'kpis' });
      const sectionsDiv = new MockElement('div', { id: 'sections' });
      const compareGrid = new MockElement('div', { id: 'compare-grid' });
      const contentDiv = new MockElement('main', { id: 'content', class: 'content' });
      const tocList = new MockElement('ul', { id: 'toc-list' });
      const phasesDiv = new MockElement('div', { id: 'phases' });

      wrap.children.push(
        triageBoard, matrixTable, contextDiv, optionsDiv, decisionDiv,
        consequencesUl, timelineDiv, kpisDiv, sectionsDiv, compareGrid,
        contentDiv, tocList, phasesDiv
      );
    }
    toast.innerHTML = '';
    
    // Re-render
    context.renderBody(data);
    if (typeof context.afterRender === 'function') {
      context.afterRender(data);
    }
    const secondRenderHTML = bodyRoot.innerHTML;
    assert(`Render check: ${file} rendering is idempotent`, firstRenderHTML === secondRenderHTML);

    // (c) Invariants per type
    const templateType = detectTemplateType(data);
    if (templateType === 'plan-document') {
      const linksCount = bodyRoot.querySelectorAll('.toc-link').length;
      const sectionsCount = bodyRoot.querySelectorAll('.spy-section').length;
      assert(`Invariant: plan-document ${file} matches TOC links (${linksCount}) to sections (${sectionsCount})`, linksCount > 0 && linksCount === sectionsCount);
    } else if (templateType === 'board') {
      const cards = bodyRoot.querySelectorAll('.board-card');
      let allCardsInColumns = true;
      cards.forEach(card => {
        let inCol = false;
        const columns = bodyRoot.querySelectorAll('.board-column');
        columns.forEach(col => {
          if (col.innerHTML.includes(card.getAttribute('id'))) {
            inCol = true;
          }
        });
        if (!inCol) allCardsInColumns = false;
      });
      assert(`Invariant: board ${file} renders all cards (${cards.length}) inside columns`, cards.length > 0 && allCardsInColumns);
    } else if (templateType === 'trade-off-matrix') {
      const cells = bodyRoot.querySelectorAll('.cell-score');
      const expected = data.options.length * data.criteria.length;
      assert(`Invariant: trade-off-matrix ${file} has ratings cell count (${cells.length}) matching options*criteria (${expected})`, cells.length > 0 && cells.length === expected);
    } else if (templateType === 'decision-record') {
      const chosen = bodyRoot.querySelectorAll('.option-card.chosen');
      assert(`Invariant: decision-record ${file} has at least one chosen option card`, chosen.length > 0);
    } else if (templateType === 'incident-timeline') {
      const cards = bodyRoot.querySelectorAll('.event-card');
      assert(`Invariant: incident-timeline ${file} has matching event cards (${cards.length} vs expected ${data.events.length})`, cards.length > 0 && cards.length === data.events.length);
    } else if (templateType === 'status-report') {
      const kpis = bodyRoot.querySelectorAll('.kpi-card');
      const sections = bodyRoot.querySelectorAll('.section');
      assert(`Invariant: status-report ${file} has correct KPI (${kpis.length}) and Section (${sections.length}) counts`, kpis.length === data.kpis.length && sections.length === data.sections.length);
    } else if (templateType === 'wireframe-compare') {
      const badges = bodyRoot.querySelectorAll('.lens-badge');
      const expected = data.options.length * data.lenses.length;
      assert(`Invariant: wireframe-compare ${file} has badge count (${badges.length}) matching options*lenses (${expected})`, badges.length > 0 && badges.length === expected);
    } else if (templateType === 'custom-composition') {
      const tabBtns = bodyRoot.querySelectorAll('.tab-btn');
      assert(`Invariant: custom-composition ${file} has correct initial tab button count`, tabBtns.length > 0);
    }

  } catch (err) {
    assert(`Execution of script/renderBody in ${file} failed: ${err.stack}`, false);
  }
});

// ─── 2. Gate Model Validation ───────────────────────────────────────────────
console.log('\n[2] Gate Model Validation');

function Gate(consumer, spatial, lineCount, diagramOnly) {
  // Human consumer check
  if (consumer !== 'human') {
    return 'markdown';
  }
  
  // If it's a diagram only, it doesn't trigger HTML
  if (diagramOnly) {
    return 'markdown';
  }
  
  // Trigger on scale (>= 100 lines) OR spatial
  if (lineCount >= 100 || spatial) {
    return 'html';
  }
  
  return 'markdown';
}

assert('human / non-spatial / 120 lines -> html', Gate('human', false, 120, false) === 'html');
assert('human / non-spatial / 40 lines -> markdown', Gate('human', false, 40, false) === 'markdown');
assert('human / diagramOnly / 120 lines -> markdown', Gate('human', true, 120, true) === 'markdown');
assert('agent / spatial / 120 lines -> markdown', Gate('agent', true, 120, false) === 'markdown');
assert('human / spatial / 20 lines -> html', Gate('human', true, 20, false) === 'html');
assert('human / non-spatial / 99 lines -> markdown', Gate('human', false, 99, false) === 'markdown');
assert('human / non-spatial / 100 lines -> html', Gate('human', false, 100, false) === 'html');

// ─── 3. Round-Trip Parser Verification ──────────────────────────────────────
console.log('\n[3] Round-Trip Parser Verification');

function applyChanges(data, payloadStr) {
  const lines = payloadStr.split('\n');
  lines.forEach(line => {
    const trimmed = line.trim();
    if (!trimmed) return;
    const parts = trimmed.split('->');
    if (parts.length !== 2) {
      throw new Error(`Malformed line: ${trimmed}`);
    }
    const cardId = parts[0].trim();
    const newColId = parts[1].trim();
    
    // Validate card existence
    const card = data.cards.find(c => c.id === cardId);
    if (!card) {
      throw new Error(`Card not found: ${cardId}`);
    }
    
    // Validate column existence
    const col = data.columns.find(col => col.id === newColId);
    if (!col) {
      throw new Error(`Column not found: ${newColId}`);
    }
    
    card.column = newColId;
  });
  return data;
}

const boardFixturePath = path.join(outputDir, 'triage-board.html');
const boardContent = fs.readFileSync(boardFixturePath, 'utf-8');
const boardMatch = boardContent.match(/<script\s+id="plan-data"\s+type="application\/json">([\s\S]*?)<\/script>/);
const originalBoardData = JSON.parse(boardMatch[1].trim());

const payload = "issue-1 -> triage\nissue-2 -> archive";

try {
  const updatedData = applyChanges(JSON.parse(JSON.stringify(originalBoardData)), payload);
  
  assert('Parser: issue-1 updated to triage', updatedData.cards.find(c => c.id === 'issue-1').column === 'triage');
  assert('Parser: issue-2 updated to archive', updatedData.cards.find(c => c.id === 'issue-2').column === 'archive');
  
  const emitterChanges = [];
  updatedData.cards.forEach(c => {
    const originalCol = originalBoardData.cards.find(oc => oc.id === c.id).column;
    if (c.column !== originalCol) {
      emitterChanges.push(`${c.id} -> ${c.column}`);
    }
  });
  
  assert('Round-trip: reconstructed change payload matches original', emitterChanges.join('\n') === payload);
} catch (err) {
  assert(`Parser execution failed: ${err.message}`, false);
}

try {
  applyChanges(JSON.parse(JSON.stringify(originalBoardData)), "issue-1 - triage");
  assert('Parser: rejects malformed line (no ->) (Should have thrown)', false);
} catch (err) {
  assert('Parser: successfully rejects malformed line (no ->)', true);
}

try {
  applyChanges(JSON.parse(JSON.stringify(originalBoardData)), "issue-xyz -> triage");
  assert('Parser: rejects non-existent card (Should have thrown)', false);
} catch (err) {
  assert('Parser: successfully rejects non-existent card', true);
}

if (failed) {
  console.log('\n=== Behavioral Verification FAILED ===');
  process.exit(1);
} else {
  console.log('\n=== Behavioral Verification PASSED ===');
  process.exit(0);
}
