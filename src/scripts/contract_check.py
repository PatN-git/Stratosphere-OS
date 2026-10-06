#!/usr/bin/env python3
"""contract_check.py — deterministic spec-to-schema contract check (detection only; never writes).

Flags references in spec docs (PRD, design doc) that the declared schema cannot satisfy,
so 2a/2b catch mechanical mismatches while authoring and 2c reasons only over the rest.
Precision over recall: anything the parser cannot classify with certainty is ignored.

Usage:
  python .agents/scripts/contract_check.py --docs <doc> [<doc> ...] \
      [--schema .memory/DATABASE_SCHEMA.md] [--sql schema.sql [...]]

Output (stdout):
  [CONTRACT-MISSING] <doc>:<line> <ref> (<kind>, <source>)   one per finding; exit 1
  [CONTRACT-SKIP] no schema declared                         exit 0
  [CONTRACT-OK] <n> reference(s) checked                     exit 0
A reference must resolve in EVERY given source; <source> names the one it is missing from.

What is checked (backticked spans and fenced code lines only; prose is never read):
  - `x.y`  where `x` is a known table  -> `y` must be a column of `x`   (kind: column; kind: table
                                          when `x` is known to one source but absent from another)
  - an enum literal, only when bound on the same span to a known enum type or to a column
    of that type (`employment_type = 'v'`, `jobs.status: 'v'`, `status IN ('a','b')`)
    -> the value must be a label of that enum                            (kind: enum-value)
    A quoted token followed by `:` is a key, never a value; in fenced lines only `=`-style and IN bind
    (a JSON/YAML `"status": "x"` example is not checked).
Not checked: bare words, free-floating literals, `x.y` with unknown `x` (`api/submit.js`),
`x.<ext>` file names, `x.y(` calls, views, and the reverse direction (schema columns no doc uses).
Known limit: a table with a genuinely missing column named like a file extension (`jobs.json`) is not
reported; a file name and a column cannot be told apart, and precision wins.

Schema formats (read from CleanTechHub, the reference consumer):
  .memory/DATABASE_SCHEMA.md
    ### `table` [LAW]                                       table heading (tag optional)
    - `col`: ...  /  - `a`, `b` (jsonb), `c` (Enum `t`; ...): ...   column bullets; names = the
        leading backticked run before the first `:`
    ... Enum `type` ... Labels `'a'`, `'b'`. **Not labels:** `'x'`   enum type bound to the column;
        labels = the quoted values after `Labels`/`confirmed`, up to the first `;` or `. `
        (so "Not labels" and "is not a label" values are never taken); older files list them
        straight after the type in parentheses; no such list -> values unknown
  schema.sql (--sql)
    CREATE TABLE [IF NOT EXISTS] t ( col type ..., CONSTRAINT/PRIMARY/UNIQUE/... )
    CREATE TYPE t AS ENUM ('a', 'b');  ALTER TABLE t ADD COLUMN c ...;  ALTER TYPE t ADD VALUE 'v';
  A template-only DATABASE_SCHEMA.md (just the `table_name` placeholder) declares nothing.
"""
import argparse
import re
import sys
from pathlib import Path

PLACEHOLDER_TABLE = "table_name"
FILE_EXTS = {"js", "mjs", "cjs", "ts", "tsx", "jsx", "json", "md", "sql", "csv", "yml", "yaml",
             "py", "html", "css", "txt", "toml", "sh", "env", "lock"}

HEADING_RE = re.compile(r"^###\s+`(\w+)`")
BULLET_NAMES_RE = re.compile(r"^-\s+((?:`\w+`(?:\s*\([^()]*\))?\s*,?\s*)+):")
NAME_RE = re.compile(r"`(\w+)`(?:\s*\(([^()]*)\))?")
ENUM_TYPE_RE = re.compile(r"\bEnum\s+`(\w+)`")
LABELS_RE = re.compile(r"(?<!Not )\b(?:Labels|confirmed)\b(.*)")
BARE_LABELS_RE = re.compile(r"\bEnum\s+`\w+`\s*\(([^()]*)\)")
QUOTED_RE = re.compile(r"""['"]([^'"\s]+)['"]""")

SQL_TABLE_RE = re.compile(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:\w+\.)?(\w+)\s*\(", re.I)
SQL_TYPE_RE = re.compile(r"CREATE\s+TYPE\s+(?:\w+\.)?(\w+)\s+AS\s+ENUM\s*\(([^)]*)\)", re.I)
SQL_ADD_COL_RE = re.compile(
    r"ALTER\s+TABLE\s+(?:IF\s+EXISTS\s+)?(?:ONLY\s+)?(?:\w+\.)?(\w+)\s+ADD\s+COLUMN\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)\s+(\w+)", re.I)
SQL_ADD_VALUE_RE = re.compile(
    r"ALTER\s+TYPE\s+(?:\w+\.)?(\w+)\s+ADD\s+VALUE\s+(?:IF\s+NOT\s+EXISTS\s+)?'([^']+)'", re.I)
SQL_NON_COLUMN = {"constraint", "primary", "unique", "foreign", "check", "exclude", "like"}

REF_RE = re.compile(r"(?<![\w./\\-])([A-Za-z_]\w*)\.([A-Za-z_]\w*)\b(?!\()")
BIND_RE = re.compile(
    r"""(?<![\w.])(?:(\w+)\.)?(\w+)["']?\s*(===?|!==?|<>|:|=|\bIN\b)\s*"""
    r"""(\(?\s*(?:['"][^'"\s]+['"](?!\s*:)\s*,?\s*)+\)?)""", re.I)  # a quoted token before `:` is a key, not a value


class Source:
    """One parsed schema source: tables -> columns, enum types -> labels (None = unknown), column -> enum type."""

    def __init__(self, name):
        self.name = name
        self.tables = {}
        self.enums = {}
        self.col_enum = {}

    def add_enum(self, typ, labels):
        known = self.enums.get(typ)
        if labels is None:
            self.enums.setdefault(typ, None)
        else:
            self.enums[typ] = (known or set()) | set(labels)

    def declares_tables(self):
        return bool(set(self.tables) - {PLACEHOLDER_TABLE})

    def enum_for(self, table, col):
        """Enum type bound by `[table.]col` (or `col` naming an enum type itself), else None."""
        if table:
            return self.col_enum.get((table, col))
        if col in self.enums:
            return col
        types = {t for (_, c), t in self.col_enum.items() if c == col}
        return types.pop() if len(types) == 1 else None


def parse_labels(text):
    m = LABELS_RE.search(text)
    if m:
        seg = re.split(r";|\.(?:\s|$)|\)", m.group(1), maxsplit=1)[0]
        return QUOTED_RE.findall(seg) or None
    m = BARE_LABELS_RE.search(text)
    return (QUOTED_RE.findall(m.group(1)) or None) if m else None


def parse_md(path):
    src = Source(Path(path).name)
    table = None
    for line in Path(path).read_text(encoding="utf-8-sig").splitlines():
        h = HEADING_RE.match(line)
        if h:
            table = h.group(1)
            src.tables.setdefault(table, set())
            continue
        if line.startswith("#"):
            table = None
        b = BULLET_NAMES_RE.match(line) if table else None
        if not b:
            continue
        names = NAME_RE.findall(b.group(1))
        rest = line[b.end():]
        for col, paren in names:
            src.tables[table].add(col)
            scope = paren if paren else (rest if len(names) == 1 else "")
            et = ENUM_TYPE_RE.search(scope)
            if et:
                src.col_enum[(table, col)] = et.group(1)
                src.add_enum(et.group(1), parse_labels(scope))
    return src


def strip_sql_comments(text):
    out, i, in_q = [], 0, False
    while i < len(text):
        c = text[i]
        if c == "'":
            in_q = not in_q
        if not in_q and text.startswith("--", i):
            while i < len(text) and text[i] != "\n":
                i += 1
            continue
        out.append(c)
        i += 1
    return "".join(out)


def split_top_level(body):
    parts, depth, cur, in_q = [], 0, [], False
    for c in body:
        if c == "'":
            in_q = not in_q
        if not in_q:
            depth += c == "("
            depth -= c == ")"
            if c == "," and depth == 0:
                parts.append("".join(cur))
                cur = []
                continue
        cur.append(c)
    parts.append("".join(cur))
    return parts


def parse_sql(path):
    src = Source(Path(path).name)
    text = strip_sql_comments(Path(path).read_text(encoding="utf-8-sig"))
    for m in SQL_TYPE_RE.finditer(text):
        src.add_enum(m.group(1), QUOTED_RE.findall(m.group(2)))
    for m in SQL_ADD_VALUE_RE.finditer(text):
        src.add_enum(m.group(1), [m.group(2)])
    for m in SQL_TABLE_RE.finditer(text):
        depth, i = 1, m.end()
        while i < len(text) and depth:
            depth += (text[i] == "(") - (text[i] == ")")
            i += 1
        cols = src.tables.setdefault(m.group(1), set())
        for item in split_top_level(text[m.end():i - 1]):
            tok = item.split()
            if len(tok) >= 2 and tok[0].lower() not in SQL_NON_COLUMN:
                cols.add(tok[0].strip('"'))
                src.col_enum[(m.group(1), tok[0].strip('"'))] = tok[1].strip('"')
    for m in SQL_ADD_COL_RE.finditer(text):
        src.tables.setdefault(m.group(1), set()).add(m.group(2))
        src.col_enum[(m.group(1), m.group(2))] = m.group(3)
    # keep only the column->type bindings whose type is an enum
    src.col_enum = {k: t for k, t in src.col_enum.items() if t in src.enums}
    return src


def spans(doc):
    """Yield (line_no, span_text, fenced) for inline backtick spans and every line inside a fenced block."""
    in_fence = False
    for no, line in enumerate(Path(doc).read_text(encoding="utf-8-sig").splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        elif in_fence:
            yield no, line, True
        else:
            for m in re.finditer(r"`([^`]+)`", line):
                yield no, m.group(1), False


def bindings(span, fenced):
    """Yield (table, col, vals) enum bindings; fenced code lines accept only `=`-style and IN (`:` is JSON/YAML)."""
    for m in BIND_RE.finditer(span):
        if not (fenced and m.group(3) == ":"):
            yield m.group(1), m.group(2), m.group(4)


def check_span(span, sources, known_tables, fenced):
    """Yield (ref, kind, source_name) for every unresolved reference in one span."""
    for m in REF_RE.finditer(span):
        x, y = m.groups()
        if x not in known_tables:
            continue
        ref = f"{x}.{y}"
        for s in sources:
            if x not in s.tables:
                yield ref, "table", s.name
            elif y not in s.tables[x] and y.lower() not in FILE_EXTS:
                yield ref, "column", s.name
    for table, col, vals in bindings(span, fenced):
        values = QUOTED_RE.findall(vals)
        for s in sources:
            typ = s.enum_for(table, col)
            labels = s.enums.get(typ) if typ else None
            if labels is None:
                continue
            for v in values:
                if v not in labels:
                    yield f"{col}='{v}'", "enum-value", s.name


def count_refs(span, known_tables, fenced):
    return sum(1 for m in REF_RE.finditer(span) if m.group(1) in known_tables) + sum(1 for _ in bindings(span, fenced))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Spec-to-schema contract check (detection only).")
    ap.add_argument("--docs", nargs="+", required=True, help="spec docs to check (PRD, design doc)")
    ap.add_argument("--schema", default=".memory/DATABASE_SCHEMA.md")
    ap.add_argument("--sql", nargs="+", default=[], help="schema.sql file(s); a reference must resolve in each")
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    missing = [p for p in (*args.docs, *args.sql) if not Path(p).is_file()]
    if missing:
        print(f"[CONTRACT-ERROR] file not found: {', '.join(missing)}", file=sys.stderr)
        return 2

    sources = [parse_sql(p) for p in args.sql]
    if Path(args.schema).is_file():
        sources.insert(0, parse_md(args.schema))
    sources = [s for s in sources if s.declares_tables()]  # a template-only schema declares nothing
    if not sources:
        print("[CONTRACT-SKIP] no schema declared")
        return 0

    known_tables = {t for s in sources for t in s.tables} - {PLACEHOLDER_TABLE}
    findings, checked = [], 0
    for doc in args.docs:
        label = Path(doc).as_posix()
        for no, span, fenced in spans(doc):
            checked += count_refs(span, known_tables, fenced)
            for ref, kind, source in check_span(span, sources, known_tables, fenced):
                line = f"[CONTRACT-MISSING] {label}:{no} {ref} ({kind}, {source})"
                if line not in findings:
                    findings.append(line)
    if findings:
        print("\n".join(findings))
        return 1
    print(f"[CONTRACT-OK] {checked} reference(s) checked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
