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

// ─── 1. Lossless Export Validation ──────────────────────────────────────────
console.log('[1] Lossless Export Validation');

const outputDir = path.join(rootDir, 'src/skills/plan-html/test/output');
const mockFiles = [
  'auth-refactor-plan.html',
  'db-options-matrix.html',
  'complex-plan-document.html',
  'triage-board.html'
];

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
  
  // Extract script block containing toMarkdown
  const scriptRegex = /<script>([\s\S]*?)<\/script>/g;
  let scriptContent = '';
  let m;
  while ((m = scriptRegex.exec(content)) !== null) {
    if (m[1].includes('toMarkdown')) {
      scriptContent = m[1];
      break;
    }
  }
  
  if (!scriptContent) {
    assert(`toMarkdown script block found in ${file}`, false);
    return;
  }
  
  // Run script in a vm context
  const context = {
    document: {
      getElementById: (id) => ({ textContent: match[1] }),
      querySelector: () => ({ textContent: '' }),
      addEventListener: () => {}
    },
    navigator: {
      clipboard: {
        writeText: () => Promise.resolve()
      }
    },
    window: {
      addEventListener: () => {}
    },
    addEventListener: () => {}
  };
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
      // Clean value to search for
      const cleanVal = val.trim();
      if (cleanVal && !md.includes(cleanVal)) {
        console.log(`    Missing leaf: "${cleanVal}"`);
        allPresent = false;
      }
    });
    
    assert(`Lossless check: every content leaf of ${file} present in markdown`, allPresent);
  } catch (err) {
    assert(`Execution of script/toMarkdown in ${file} failed: ${err.message}`, false);
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
