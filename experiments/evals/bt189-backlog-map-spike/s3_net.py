"""BT-189 A3 item 5: net text estimate from s2_counts.json (sentence-level CORE/GATE chars) + s2 site kinds + s1 survivors."""
import json, collections, io
cnt = {r['file']: r for r in json.load(open('s2_counts.json'))}
rows = [l.split('|') for l in io.open('s2-inventory.md', encoding='utf-8').read().split('\n')[6:170]
        if l.startswith('| ') and l.split('|')[1].strip().isdigit()]
kinds = collections.defaultdict(collections.Counter)
for r in rows:
    f = r[2].strip().strip('`').split(':')[0]
    kinds[f.split('/')[-1]][r[3].strip()] += 1
# survivors (sentence-level, 0.6 x full-line chars of surviving call-site lines; invariant doc 3.09/34.15 of 4152 = 377)
SURV = {'workflows/0b-stop-session.md': 295, 'workflows/3c-sprint-planning.md': 104, 'workflows/4a-verify-and-ship.md': 883,
        'workflows/3z-afk-loop.md': 517, 'references/terminal-sync-invariant.md': 377}
# slimmer gate: extra prose per terminal phase
GATE = {'workflows/3a-version-planning.md': 220, 'workflows/3b-create-issue.md': 260, 'workflows/3c-sprint-planning.md': 260,
        'workflows/4a-verify-and-ship.md': 200, 'workflows/0b-stop-session.md': 120}
# scoped-query prose (C only)
SCOPED = {'skills/load-memory/SKILL.md': 200, 'workflows/3c-sprint-planning.md': 700, 'workflows/3d-implement-issue.md': 250,
          'workflows/4a-verify-and-ship.md': 200, 'workflows/3z-afk-loop.md': 250, 'workflows/0a-start-session.md': 150,
          'workflows/3a-version-planning.md': 250, 'workflows/1b-concept-framing.md': 100, 'workflows/2a-write-prd.md': 100}
# B: freshness sentence per reading workflow
FRESH = {k: 110 for k in ('workflows/0a-start-session.md', 'workflows/1b-concept-framing.md', 'workflows/2a-write-prd.md',
         'workflows/3a-version-planning.md', 'workflows/3c-sprint-planning.md', 'workflows/3z-afk-loop.md',
         'skills/load-memory/SKILL.md', 'workflows/3d-implement-issue.md', 'workflows/4b-audit-architecture-drift.md')}
FRESH['memory-templates/BACKLOG_MAP.md'] = 500   # generated-file header + read-only note
ADAPTER = {'references/tracker-verbs.md (new)': 2200 + 1000}  # verb adapter doc + offline-backend notes (C only)
out = []
tot = collections.Counter()
for f, r in sorted(cnt.items(), key=lambda kv: -kv[1]['all_sent']):
    cg = r['all_sent']; core = r['core_sent']
    k = kinds.get(f.split('/')[-1], collections.Counter()); n = sum(k.values()) or 1
    reads = core * k['read'] / n
    s = SURV.get(f, 0)
    delC = max(0, cg - s)
    delB = max(0, cg - reads - s)
    addB = FRESH.get(f, 0) + GATE.get(f, 0)
    addC = SCOPED.get(f, 0) + GATE.get(f, 0)
    out.append((f, cg, delB, addB, delB - addB, delC, addC, delC - addC))
    for key, v in zip(('cg', 'delB', 'addB', 'netB', 'delC', 'addC', 'netC'), out[-1][1:]): tot[key] += v
for f, v in ADAPTER.items():
    out.append((f, 0, 0, 0, 0, 0, v, -v)); tot['addC'] += v; tot['netC'] -= v
print('| file | CORE+GATE now | B deleted | B added | B net | C deleted | C added | C net |\n|:--|--:|--:|--:|--:|--:|--:|--:|')
for o in out:
    print('| ' + ' | '.join(str(round(x)) if not isinstance(x, str) else x for x in o) + ' |')
print('| **total** | ' + ' | '.join(str(round(tot[k])) for k in ('cg', 'delB', 'addB', 'netB', 'delC', 'addC', 'netC')) + ' |')
# workflows-only
wf = [o for o in out if o[0].startswith('workflows/')]
print('workflows only: B net', round(sum(o[4] for o in wf)), 'C net', round(sum(o[7] for o in wf)))
