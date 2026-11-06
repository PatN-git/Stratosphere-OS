"""S1 helper: item-weighted class of every D-item / [DRIFT] line in the CleanTechHub nightly reports (read-only)."""
import re
from collections import Counter, defaultdict
from pathlib import Path

D = Path(r"C:\Users\patri\Dev\CleanTechHub\docs\nightly")
M, G, A = "map-only", "gh-post-condition", "ambiguous"


def classify(text):
    t = text
    if t.startswith("closed on GitHub"):
        return M, "closed on GitHub, map lagging (GH correct)"
    if t.startswith("milestone"):
        return M, "milestone differs, GH migrated/assigned, map stale"
    if t.startswith("labels"):
        mo = re.search(r"map_only=\[(.*?)\] gh_only=\[(.*?)\]", t)
        mo_s, go_s = (mo.group(1), mo.group(2)) if mo else ("", "")
        if "size:" in go_s:
            return A, "size:* all became medium on GH, cause unknown"
        if re.fullmatch(r"(['\"]?(scope:baseline|status:[a-z _]+|size:[a-z]+)['\"]?,? ?)*", mo_s) and "priority" not in go_s and "size" not in go_s:
            return M, "status:* in map labels = reconcile false positive (F1)"
        if "priority:" in go_s:
            return M, "priority:* never populated in map"
        return M, "label cell differs, map stale"
    if t.startswith("parent"):
        if "map=None" in t:
            return M, "parent never populated in map"
        return A, "map has parent, GH has none (missing addSubIssue or map stale)"
    if t.startswith("blocked_by"):
        mo = re.search(r"map=\[(.*?)\] gh=\[(.*?)\]", t)
        m_s, g_s = mo.group(1), mo.group(2)
        if m_s == "" and g_s:
            return G, "GH keeps blockedBy edge the map cleared (missing removeBlockedBy)"
        if m_s and g_s:
            gs = set(re.findall(r"BT-\d+", g_s)); ms = set(re.findall(r"BT-\d+", m_s))
            return (G, "GH keeps an extra stale edge") if gs - ms else (M, "map keeps edge GH dropped")
        return M, "map keeps edge GH cleared (map stale)"
    if t.startswith("status"):
        return A, "status map vs gh disagree, direction unknown"
    if t.startswith("pr-link"):
        return G, "PR-link comment missing on GH"
    if t.startswith("stale blocker"):
        return G, "stale blocker edge"
    return A, "other"


tot = defaultdict(Counter)
detail = defaultdict(Counter)
for f in sorted(D.glob("nightly-*.md")):
    txt = f.read_text(encoding="utf-8")
    items = re.findall(r"\[(?:MIRROR-)?DRIFT[ -]?(?:BT-\d+)?:? ?([^\]\n]*(?:\[[^\]\n]*\][^\]\n]*)*)\]", txt)
    # D-n lines (10-09 onwards) and `[DRIFT] BT-x: text` lines (07-25 .. 10-05)
    seen = []
    for m in re.finditer(r"^- \*\*D-\d+:\*\* `\[MIRROR-DRIFT BT-\d+: ([^`]*)`", txt, re.M):
        seen.append(m.group(1))
    for m in re.finditer(r"^\s*- `\[DRIFT\] BT-\d+: (.*?)`", txt, re.M):
        seen.append(m.group(1).replace("stale blocker `BT-055` should be cleared (already `status:done`)", "stale blocker"))
    if not seen:
        continue
    for s in seen:
        s = s.strip()
        if s.count("]") > s.count("["):
            s = s[:-1]
        c, why = classify(s)
        tot[f.stem][c] += 1
        detail[(c, why)][f.stem] += 1
grand = Counter()
for k, v in tot.items():
    print(k, dict(v), "n=", sum(v.values()))
    grand.update(v)
print("TOTAL item-instances", dict(grand), sum(grand.values()))
for (c, why), v in sorted(detail.items()):
    print(c, "|", why, "|", dict(v), "=", sum(v.values()))
