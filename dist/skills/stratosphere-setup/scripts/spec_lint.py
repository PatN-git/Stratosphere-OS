#!/usr/bin/env python3
"""spec_lint.py: deterministic lint for the structural checklist items of a PRD and a discovery brief. Read-only.

  spec_lint.py <doc> [<doc> ...]

The doc kind comes from the frontmatter `type:` (`prd` | `discovery-brief`). Judgment items (outcome-oriented goals,
solution-free problem, specific actor, observable success state, quality of any rationale) are never checked here.
Precision over recall: a shape the parser cannot classify with certainty is ignored. Fenced blocks are never read as
sections, bullets or markers.

Output (stdout):
  [SPEC-LINT] <doc>:<line> <rule-id> <detail>   one per finding, never the source line; exit 1
  [SPEC-OK] <n> doc(s), <m> check(s)             exit 0
A named doc with a missing file or another type prints [SPEC-ERROR] on stderr and exits 2 (never a pass).

PRD rules: prd-sections, prd-nongoals, prd-s7-clean, prd-deferred-mirror, prd-no-slices, prd-open-in-s10,
prd-boundaries. Brief rules: brief-sections, brief-rat, brief-followups, brief-facts, brief-decisions, brief-next-step.
Stdlib only.
"""
import re
import sys
from pathlib import Path

# Section numbers and titles of src/references/PRD-template.md (a test pins them to the template).
PRD_SECTIONS = {1: "Problem", 2: "Solution (user view)", 3: "Goals", 4: "Non-Goals", 5: "Success Signals",
                6: "User Stories", 7: "Constraints & Direction", 8: "Definition of Done", 9: "Out of Scope",
                10: "Open Questions", 11: "Further Notes", 12: "Viability & Cost"}
PRD_MAY_BE_EMPTY = {10, 11}
# Brief sections that must be present and non-empty (src/references/discovery_brief_template.md; a test pins them).
BRIEF_REQUIRED = ("ask", "vocabulary", "actor", "problem", "chosen framing", "success state", "riskiest assumption",
                  "recommended next step")
RAT_STATUSES = ("untested", "running", "survived", "failed")
CODE_EXTS = {"py", "js", "mjs", "cjs", "ts", "tsx", "jsx", "json", "md", "sql", "yml", "yaml", "css", "html", "sh", "toml", "txt"}

FENCE_RX = re.compile(r"^\s*(```|~~~)")
H2_RX = re.compile(r"^#{1,2}\s")
PRD_H2_RX = re.compile(r"^##\s+(\d+)\.")
BULLET_RX = re.compile(r"^[-*]\s+(.*)")
SPAN_RX = re.compile(r"`([^`]+)`")
BOLD_LABEL_RX = re.compile(r"^\*\*[^*]+\*\*[\s:—–-]*")
DEFERRED_RX = re.compile(r"^\s*(\d+)\.\s+.*\[DEFERRED\]")
OPEN_RX = re.compile(r"^\s*>\s*open:", re.I)
SLICE_HEAD_RX = re.compile(r"^#{1,6}\s.*\bslices?\b", re.I)
SLICE_LINE_RX = re.compile(r"^\s*(?:[-*]|\d+\.)?\s*\**slice\s*\d+", re.I)
PATH_REL_RX = re.compile(r"^(?:\.{1,2}/|~/)")
PATH_DOTDIR_RX = re.compile(r"^\.\w[\w.-]*/")
PATH_FILE_RX = re.compile(r"^[\w.-]+(?:/[\w.-]+)+\.(\w{1,5})$")
TIERS = ("Always", "Ask first", "Never")
H2_TEXT_RX = re.compile(r"^##\s+(.*?)\s*$")
AS_OF_RX = re.compile(r"\(as of \d{4}-\d{2}-\d{2}\)")
EXISTING_RX = re.compile(r"existing:\s*(?:BT-|#)\d+", re.I)
CHECKED_RX = re.compile(r"^\s*[-*]\s+\[[xX]\]")


class Doc:
    def __init__(self, path):
        self.label = Path(path).as_posix()
        self.lines = Path(path).read_text(encoding="utf-8-sig").splitlines()
        self.fenced = []
        inside = False
        for line in self.lines:
            if FENCE_RX.match(line):
                self.fenced.append(True)
                inside = not inside
            else:
                self.fenced.append(inside)
        self.type, self.body = self._frontmatter()

    def _frontmatter(self):
        if not self.lines or self.lines[0].strip() != "---":
            return None, 0
        for i in range(1, len(self.lines)):
            if self.lines[i].strip() == "---":
                for line in self.lines[1:i]:
                    m = re.match(r"type:\s*(\S+)", line)
                    if m:
                        return m.group(1).strip("\"'"), i + 1
                return None, i + 1
        return None, 0

    def sections(self, number_rx):
        """{key: (heading_idx, end_idx)} for non-fenced `##` headings whose key `number_rx` returns; the section
        ends at the next non-fenced heading of level 1-2. Index = 0-based line."""
        heads = [(i, number_rx(self.lines[i])) for i in range(self.body, len(self.lines))
                 if not self.fenced[i] and H2_RX.match(self.lines[i])]
        out = {}
        for n, (i, key) in enumerate(heads):
            end = heads[n + 1][0] if n + 1 < len(heads) else len(self.lines)
            if key is not None and key not in out:
                out[key] = (i, end)
        return out

    def content(self, span, include_fenced=False):
        """Yield (idx, line) of a section's lines after its heading."""
        for i in range(span[0] + 1, span[1]):
            if include_fenced or not self.fenced[i]:
                yield i, self.lines[i]

    def bullets(self, span):
        """Top-level bullets of a section as (idx, text), text joined with its continuation lines (a bullet ends at a
        blank line or the next top-level bullet)."""
        out = []
        cur = None
        for i, line in self.content(span):
            m = BULLET_RX.match(line)
            if m:
                cur = [i, m.group(1)]
                out.append(cur)
            elif not line.strip() or not line[:1].isspace():
                cur = None
            elif cur:
                cur[1] += " " + line.strip()
        return [tuple(b) for b in out]


def prd_key(line):
    m = PRD_H2_RX.match(line)
    return int(m.group(1)) if m else None


def heading_key(text):
    """Lowercased `##` heading text without a trailing parenthetical: `Ask (verbatim)` -> `ask`."""
    return re.sub(r"\s*\(.*\)\s*$", "", text).strip().lower()


def brief_key(line):
    m = H2_TEXT_RX.match(line)
    return heading_key(m.group(1)) if m else None


def non_blank(doc, span):
    return any(line.strip() and not line.strip().startswith("<!--") for _, line in doc.content(span, include_fenced=True))


def norm(text):
    return re.sub(r"\s+", " ", re.sub(r"[*`_]", "", text)).strip().lower()


def check_prd_sections(doc, secs):
    for n, title in PRD_SECTIONS.items():
        if n not in secs:
            yield 0, f"missing section {n} ({title})"
        elif n not in PRD_MAY_BE_EMPTY and not non_blank(doc, secs[n]):
            yield secs[n][0], f"section {n} ({title}) is empty"


def check_prd_nongoals(doc, secs):
    if 4 not in secs:
        return
    items = doc.bullets(secs[4])
    if len(items) < 3:
        yield secs[4][0], f"{len(items)} non-goal bullet(s), need at least 3"
    for i, text in items:
        if not BOLD_LABEL_RX.sub("", text, count=1).strip(" :—–-*_"):
            yield i, "non-goal has no rationale"


def span_kind(span):
    s = span.strip()
    if "://" in s or s.startswith("/") or " " in s:
        return None
    if PATH_REL_RX.match(s):
        return "relative path"
    if PATH_DOTDIR_RX.match(s):
        return "dot-directory path"
    if s.endswith("/"):
        return "directory path"
    m = PATH_FILE_RX.match(s)
    if m and m.group(1).lower() in CODE_EXTS:
        return "file path"
    return None


def check_prd_s7_clean(doc, secs):
    if 7 not in secs:
        return
    for i in range(secs[7][0] + 1, secs[7][1]):
        if doc.fenced[i]:
            if not doc.fenced[i - 1]:
                yield i, "fenced code block in section 7"
            continue
        for m in SPAN_RX.finditer(doc.lines[i]):
            kind = span_kind(m.group(1))
            if kind:
                yield i, f"{kind} in a backtick span"


def check_prd_deferred_mirror(doc, secs):
    if 6 not in secs:
        return
    mirror = norm(" ".join(line for _, line in doc.content(secs[9]))) if 9 in secs else ""
    for i, line in doc.content(secs[6]):
        m = DEFERRED_RX.match(line)
        if not m:
            continue
        n = m.group(1)
        if re.search(rf"(?:story\s*#?|§6\s*#){n}\b", mirror):
            continue
        after = re.split(r"\bi want\b", norm(line), maxsplit=1)
        clause = re.split(r",|\bso that\b", after[1] if len(after) > 1 else norm(line.split("[DEFERRED]", 1)[1]))[0]
        words = clause.split()[:8]
        if words and " ".join(words) in mirror:
            continue
        yield i, f"deferred story {n} is not mirrored in section 9"


def check_prd_no_slices(doc, secs):
    for i in range(doc.body, len(doc.lines)):
        if doc.fenced[i]:
            continue
        line = doc.lines[i]
        if SLICE_HEAD_RX.match(line):
            yield i, "slice heading"
        elif SLICE_LINE_RX.match(line):
            yield i, "slice list line"


def check_prd_open_in_s10(doc, secs):
    lo, hi = (secs[10][0], secs[10][1]) if 10 in secs else (len(doc.lines), len(doc.lines))
    for i in range(doc.body, len(doc.lines)):
        if not doc.fenced[i] and not lo <= i < hi and OPEN_RX.match(doc.lines[i]):
            yield i, "`> open:` marker outside section 10"


def tier_value(doc, idx, text, block_end):
    """Text after a tier label, or the nested sub-bullet lines under it when the label line carries none."""
    val = re.sub(r"^\W*(?:always|ask first|never)\W*", "", text, flags=re.I).strip()
    if val:
        return val
    base = len(doc.lines[idx]) - len(doc.lines[idx].lstrip())
    parts = []
    for j in range(idx + 1, block_end):
        line = doc.lines[j]
        if line.strip() and len(line) - len(line.lstrip()) > base and not doc.fenced[j]:
            parts.append(line.strip().lstrip("-* ").strip())
        elif line.strip():
            break
    return " ".join(parts)


def check_prd_boundaries(doc, secs):
    if 7 not in secs:
        return
    start = next((i for i, line in doc.content(secs[7]) if re.search(r"\*\*Boundaries:?\*\*", line)), None)
    if start is None:
        yield secs[7][0], "no Boundaries entry in section 7"
        return
    base = len(doc.lines[start]) - len(doc.lines[start].lstrip())
    end = secs[7][1]
    for j in range(start + 1, secs[7][1]):
        line = doc.lines[j]
        if line.strip() and len(line) - len(line.lstrip()) <= base and BULLET_RX.match(line.lstrip()):
            end = j
            break
    for tier in TIERS:
        idx = next((j for j in range(start, end) if re.search(rf"\*\*{tier}:?\*\*|^\s*[-*]\s+{tier}:", doc.lines[j], re.I)), None)
        if idx is None:
            yield start, f"Boundaries has no '{tier}' line"
            continue
        val = tier_value(doc, idx, doc.lines[idx].lstrip(" -*").replace("**", ""), end)
        if not val:
            yield idx, f"Boundaries '{tier}' is empty"
        elif re.match(r"none\b", val, re.I) and not re.match(r"none\s*[—–-]+\s*\S", val, re.I):
            yield idx, f"Boundaries '{tier}' says none without a reason"


PRD_RULES = {"prd-sections": check_prd_sections, "prd-nongoals": check_prd_nongoals, "prd-s7-clean": check_prd_s7_clean,
             "prd-deferred-mirror": check_prd_deferred_mirror, "prd-no-slices": check_prd_no_slices,
             "prd-open-in-s10": check_prd_open_in_s10, "prd-boundaries": check_prd_boundaries}
def label_value(doc, span, label):
    """(idx, text) of a `**label:**` line's value (an indented or numbered continuation counts when the line is bare);
    (None, '') when the label is absent."""
    for i, line in doc.content(span):
        m = re.search(rf"\*\*{re.escape(label)}:?\*\*:?\s*(.*)", line)
        if m:
            val = m.group(1).strip()
            nxt = doc.lines[i + 1] if i + 1 < span[1] else ""
            if not val and nxt.strip() and (nxt[:1].isspace() or re.match(r"\d+\.", nxt)):
                val = nxt.strip()
            return i, val
    return None, ""


def check_brief_sections(doc, secs):
    for key in BRIEF_REQUIRED:
        if key not in secs:
            yield 0, f"missing section '{key}'"
        elif not non_blank(doc, secs[key]):
            yield secs[key][0], f"section '{key}' is empty"
    if "vocabulary" in secs and non_blank(doc, secs["vocabulary"]):
        if not any(re.match(r"\*\*[^*]+\*\*", t) for _, t in doc.bullets(secs["vocabulary"])):
            yield secs["vocabulary"][0], "Vocabulary defines no `**Term:**` entry"


def check_brief_rat(doc, secs):
    span = secs.get("riskiest assumption")
    if not span:
        return
    for label in ("Riskiest Assumption", "Cheapest Test"):
        idx, val = label_value(doc, span, label)
        if not val:
            yield span[0] if idx is None else idx, f"Riskiest Assumption section has no '{label}' value"
    idx, val = label_value(doc, span, "Status")
    word = re.sub(r"[^a-z]", "", (val.split() or [""])[0].lower())
    if word not in RAT_STATUSES:
        yield span[0] if idx is None else idx, f"RAT status is not one of {'/'.join(RAT_STATUSES)}"


def check_brief_followups(doc, secs):
    if "decoupled follow-ups" not in secs:
        return
    for i, text in doc.bullets(secs["decoupled follow-ups"]):
        if norm(text).startswith("none"):
            continue
        if not (EXISTING_RX.search(text) or re.search(r"\bcandidate\b", text, re.I)):
            yield i, "follow-up is not marked `existing: BT-<n>` or `candidate`"


def check_brief_facts(doc, secs):
    span = secs.get("established facts")
    if not span:
        return
    if not AS_OF_RX.search(doc.lines[span[0]]):
        yield span[0], "Established Facts heading has no `(as of YYYY-MM-DD)` date"
    for i, text in doc.bullets(span):
        if not re.search(r"\b(?:source|probe):", text, re.I):
            yield i, "fact names no `source:` (or `probe:`)"


def check_brief_decisions(doc, secs):
    span = secs.get("constraints & settled decisions")
    if not span:
        return
    for i, text in doc.bullets(span):
        if not re.search(r"\bwhy:", text, re.I):
            yield i, "settled decision carries no `why:`"


def check_brief_next_step(doc, secs):
    span = secs.get("recommended next step")
    if not span:
        return
    n = sum(1 for _, line in doc.content(span) if CHECKED_RX.match(line))
    if n != 1:
        yield span[0], f"{n} next steps are checked, need exactly 1"


BRIEF_RULES = {"brief-sections": check_brief_sections, "brief-rat": check_brief_rat, "brief-followups": check_brief_followups,
               "brief-facts": check_brief_facts, "brief-decisions": check_brief_decisions, "brief-next-step": check_brief_next_step}
KINDS = {"prd": (prd_key, PRD_RULES), "discovery-brief": (brief_key, BRIEF_RULES)}


def lint(doc):
    """Return (findings, checks) for one doc: findings are (line_no_1_based, rule, detail)."""
    number_rx, rules = KINDS[doc.type]
    secs = doc.sections(number_rx) if number_rx else {}
    findings = set()
    for rule, fn in rules.items():
        for idx, detail in fn(doc, secs):
            findings.add((idx + 1, rule, detail))
    return sorted(findings), len(rules)


def main(argv=None):
    paths = sys.argv[1:] if argv is None else argv
    if not paths:
        print("[SPEC-ERROR] usage: spec_lint.py <doc> [<doc> ...]", file=sys.stderr)
        return 2
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    docs, errors = [], []
    for p in paths:
        if not Path(p).is_file():
            errors.append(f"[SPEC-ERROR] file not found: {Path(p).as_posix()}")
            continue
        doc = Doc(p)
        if doc.type not in KINDS:
            errors.append(f"[SPEC-ERROR] {doc.label}: not a lintable type (frontmatter type: prd | discovery-brief)")
        else:
            docs.append(doc)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 2
    out, checks = [], 0
    for doc in docs:
        found, n = lint(doc)
        checks += n
        out += [f"[SPEC-LINT] {doc.label}:{no} {rule} {detail}" for no, rule, detail in found]
    if out:
        print("\n".join(out))
        return 1
    print(f"[SPEC-OK] {len(docs)} doc(s), {checks} check(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
