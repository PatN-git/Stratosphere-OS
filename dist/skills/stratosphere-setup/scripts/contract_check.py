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
  [CONTRACT-AMBIGUOUS <col>: <t1>, <t2>]                     advisory, printed before the verdict line; exit code unchanged
  [CONTRACT-SKIP] no schema declared                         exit 0
  [CONTRACT-OK] <n> reference(s) checked                     exit 0
A reference must resolve in EVERY given source; <source> names the one it is missing from.

--parity compares the schema sources with each other instead of reading docs (no --docs):
  [CONTRACT-DRIFT] <table>.<col> (documented in <a>, missing from <b>)   one per column, every source pair
  [CONTRACT-DRIFT] <table> (documented in <a>, missing from <b>)         a whole table; its columns are not repeated
  [CONTRACT-OK] parity: <n> table(s) compared                            exit 0
Drift exits 1. Fewer than two non-template sources (no --sql, absent or template-only md) -> no output, exit 0.
Tables and columns only (enums are not compared). Known limit: a table that a source reaches only through
`ALTER TABLE ... ADD COLUMN` (its CREATE TABLE lives in another file) reports as if it held just those columns.

What is checked (backticked spans and fenced code lines only; prose is never read):
  - `x.y`  where `x` is a known table  -> `y` must be a column of `x`   (kind: column; kind: table
                                          when `x` is known to one source but absent from another)
  - an enum literal, only when bound on the same span to a known enum type or to a column
    of that type (`employment_type = 'v'`, `jobs.status: 'v'`, `status IN ('a','b')`)
    -> the value must be a label of that enum                            (kind: enum-value)
    A bare column name binds only when every table declaring it has the same enum type; if the tables disagree
    (`jobs.status` enum, `notes.status` text) the value check is skipped and one [CONTRACT-AMBIGUOUS] line names them.
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
SQL_ALTER_RE = re.compile(  # table, then the comma-separated clause list up to the `;` (quoted `;` kept)
    r"ALTER\s+TABLE\s+(?:IF\s+EXISTS\s+)?(?:ONLY\s+)?(?:\w+\.)?(\w+)\s+((?:'[^']*'|[^;'])*)", re.I)
SQL_ADD_CLAUSE_RE = re.compile(r'ADD\s+(COLUMN\s+)?(?:IF\s+NOT\s+EXISTS\s+)?"?(\w+)"?\s+"?(\w+)', re.I)
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
        self.endpoints = set()

    def add_enum(self, typ, labels):
        known = self.enums.get(typ)
        if labels is None:
            self.enums.setdefault(typ, None)
        else:
            self.enums[typ] = (known or set()) | set(labels)

    def declares_tables(self):
        return bool(set(self.tables) - {PLACEHOLDER_TABLE})

    def bare_column_types(self, col):
        """(tables declaring `col`, their enum types or None) for a bare column name."""
        owners = sorted(t for t, cols in self.tables.items() if col in cols)
        return owners, {self.col_enum.get((t, col)) for t in owners}

    def enum_for(self, table, col):
        """Enum type bound by `[table.]col` (or `col` naming an enum type itself), else None.
        A bare `col` binds only when every table declaring it agrees on one enum type."""
        if table:
            return self.col_enum.get((table, col))
        if col in self.enums:
            return col
        _, types = self.bare_column_types(col)
        return types.pop() if len(types) == 1 else None

    def ambiguous_owners(self, table, col):
        """Tables that make a bare enum-typed `col` ambiguous (mixed enum/non-enum or different enums), else []."""
        if table or col in self.enums:
            return []
        owners, types = self.bare_column_types(col)
        return owners if len(types) > 1 else []


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
    """Drop `--` and nestable (Postgres) `/* */` comments; single-quoted literals are copied verbatim."""
    out, i, in_q = [], 0, False
    while i < len(text):
        c = text[i]
        if in_q:
            in_q = c != "'"
        elif c == "'":
            in_q = True
        elif text.startswith("--", i):
            while i < len(text) and text[i] != "\n":
                i += 1
            continue
        elif text.startswith("/*", i):
            depth = 0
            while i < len(text):
                if text.startswith("/*", i):
                    depth, i = depth + 1, i + 2
                elif text.startswith("*/", i):
                    depth, i = depth - 1, i + 2
                    if not depth:
                        break
                else:
                    i += 1
            out.append(" ")  # a comment still separates tokens
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
            head = re.split(r"[\s(]", item.strip(), maxsplit=1)[0].lower()  # `UNIQUE(` / `CHECK(` need no space
            if len(tok) >= 2 and head not in SQL_NON_COLUMN:
                cols.add(tok[0].strip('"'))
                src.col_enum[(m.group(1), tok[0].strip('"'))] = tok[1].strip('"')
    for m in SQL_ALTER_RE.finditer(text):
        for clause in split_top_level(m.group(2)):
            c = SQL_ADD_CLAUSE_RE.match(clause.strip())
            # without COLUMN, `ADD <keyword> ...` is a constraint/index, not a column
            if c and (c.group(1) or c.group(2).lower() not in SQL_NON_COLUMN | {"index", "key"}):
                src.tables.setdefault(m.group(1), set()).add(c.group(2))
                src.col_enum[(m.group(1), c.group(2))] = c.group(3)
    # keep only the column->type bindings whose type is an enum
    src.col_enum = {k: t for k, t in src.col_enum.items() if t in src.enums}
    return src


TS_INTERFACE_RE = re.compile(
    r'(?:export\s+)?interface\s+([A-Za-z0-9_]+)(?:<[^>]+>)?(?:\s+extends\s+[^{]+)?\s*\{([^}]*)\}',
    re.DOTALL
)
TS_TYPE_OBJ_RE = re.compile(
    r'(?:export\s+)?type\s+([A-Za-z0-9_]+)(?:<[^>]+>)?\s*=\s*\{([^}]*)\}',
    re.DOTALL
)
TS_TYPE_UNION_RE = re.compile(
    r"""(?:export\s+)?type\s+([A-Za-z0-9_]+)\s*=\s*((?:['"][^'"]+['"]\s*\|\s*)*['"][^'"]+['"])\s*;""",
    re.M
)
TS_FIELD_RE = re.compile(
    r'(?:^|[\n;,])\s*([A-Za-z0-9_]+|["\'][^"\']+["\'])(\?)?\s*:\s*([^;,\n]+)',
    re.M
)
ENDPOINT_ROUTE_RE = re.compile(r'^(?:(GET|POST|PUT|PATCH|DELETE)\s+)?(/[\w\-./:]+)$')
DEFERRED_RE = re.compile(r'^\s*(?:\d+\.|\*|-)\s*(?:\*\*\[DEFERRED\]\*\*|\[DEFERRED\])\s*(.*)', re.I)
ODI_RE = re.compile(r'\(ODI:.*?\)', re.I)


def strip_ts_comments(text):
    """Strip // and /* */ comments from TypeScript code, preserving quoted strings."""
    out, i = [], 0
    in_single_q = False
    in_double_q = False
    in_backtick = False
    while i < len(text):
        c = text[i]
        if in_single_q:
            if c == "'" and (i == 0 or text[i - 1] != "\\"):
                in_single_q = False
            out.append(c)
            i += 1
        elif in_double_q:
            if c == '"' and (i == 0 or text[i - 1] != "\\"):
                in_double_q = False
            out.append(c)
            i += 1
        elif in_backtick:
            if c == '`' and (i == 0 or text[i - 1] != "\\"):
                in_backtick = False
            out.append(c)
            i += 1
        elif c == "'":
            in_single_q = True
            out.append(c)
            i += 1
        elif c == '"':
            in_double_q = True
            out.append(c)
            i += 1
        elif c == '`':
            in_backtick = True
            out.append(c)
            i += 1
        elif text.startswith("//", i):
            while i < len(text) and text[i] != "\n":
                i += 1
        elif text.startswith("/*", i):
            i += 2
            while i < len(text) and not text.startswith("*/", i):
                i += 1
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def parse_ts(path):
    src = Source(Path(path).name)
    src.endpoints = getattr(src, "endpoints", set())
    text = strip_ts_comments(Path(path).read_text(encoding="utf-8-sig"))

    # 1. Parse string literal union types (enums)
    for m in TS_TYPE_UNION_RE.finditer(text):
        type_name = m.group(1)
        labels = QUOTED_RE.findall(m.group(2))
        src.add_enum(type_name, labels)

    # 2. Parse interfaces and type objects
    for m in list(TS_INTERFACE_RE.finditer(text)) + list(TS_TYPE_OBJ_RE.finditer(text)):
        name = m.group(1)
        body = m.group(2)
        cols = src.tables.setdefault(name, set())
        for fm in TS_FIELD_RE.finditer(body):
            raw_field = fm.group(1).strip()
            field_name = raw_field.strip("'\"")
            cols.add(field_name)

            # Check if field name is an endpoint route (e.g. "/api/v1/..." or "GET /api/v1/...")
            ep_m = ENDPOINT_ROUTE_RE.match(field_name)
            if ep_m:
                src.endpoints.add(field_name)

            field_type = fm.group(3).strip()
            # If field_type is string literal union (e.g. 'a' | 'b')
            if "'" in field_type or '"' in field_type:
                labels = QUOTED_RE.findall(field_type)
                if labels and "|" in field_type:
                    anon_type = f"{name}_{field_name}"
                    src.add_enum(anon_type, labels)
                    src.col_enum[(name, field_name)] = anon_type
            elif field_type in src.enums:
                src.col_enum[(name, field_name)] = field_type

    return src


def collect_ts_files(paths):
    files = []
    for p in paths:
        pt = Path(p)
        if pt.is_file():
            files.append(pt)
        elif pt.is_dir():
            for item in sorted(pt.rglob("*")):
                if item.is_file() and (item.name.endswith(".ts") or item.name.endswith(".d.ts")):
                    if not (item.name.endswith(".test.ts") or item.name.endswith(".spec.ts")):
                        parts = set(item.parts)
                        if "node_modules" not in parts and ".git" not in parts:
                            files.append(item)
    return files


def ep_norm(ep):
    parts = ep.strip().split()
    return parts[-1] if len(parts) > 1 else parts[0]


def is_prd_doc(path):
    try:
        text = Path(path).read_text(encoding="utf-8-sig", errors="replace")[:1000]
        return "type: prd" in text or "# PRD" in text or "## 6. User Stories" in text
    except OSError:
        return False


def check_prd_contracts(prd_path, sources):
    """Verify PRD-specific invariants:
    1. 100% mirroring: Every [DEFERRED] story in §6 must be mirrored in §9 Out of Scope.
    2. Backticked HTTP endpoints must resolve against declared endpoints in sources.
    Returns a list of finding strings.
    """
    findings = []
    lines = Path(prd_path).read_text(encoding="utf-8-sig").splitlines()

    sec6_lines = []
    sec9_lines = []
    cur_sec = None

    for no, line in enumerate(lines, 1):
        if line.startswith("## "):
            header = line[3:].strip().lower()
            if header.startswith("6.") or "user stories" in header:
                cur_sec = 6
            elif header.startswith("9.") or "out of scope" in header:
                cur_sec = 9
            else:
                cur_sec = None
        elif cur_sec == 6:
            sec6_lines.append((no, line))
        elif cur_sec == 9:
            sec9_lines.append((no, line))

    sec9_text = " ".join(t for _, t in sec9_lines).lower()

    # 1. Mirroring check: §6 [DEFERRED] -> §9
    for no, line in sec6_lines:
        m = DEFERRED_RE.match(line)
        if m:
            raw_story = m.group(1).strip()
            # Strip (ODI: ...) first per Safeguard 4
            clean_story = ODI_RE.sub("", raw_story).strip()
            title_display = clean_story.split(":", 1)[0].strip() if ":" in clean_story else clean_story
            title_key = title_display.strip("*_ \t").lower()

            match_phrase = title_key
            matched = match_phrase in sec9_text or (len(match_phrase) > 5 and any(w in sec9_text for w in match_phrase.split() if len(w) > 4))
            if not matched:
                findings.append(f"[CONTRACT-MISSING] {Path(prd_path).as_posix()}:{no} [DEFERRED] story \"{title_display}\" missing from §9 Out of Scope")

    # 2. Endpoint resolution check (Safeguards 5)
    known_endpoints = {ep for s in sources for ep in getattr(s, "endpoints", set())}
    if known_endpoints:
        known_paths = {ep_norm(ep) for ep in known_endpoints}
        source_names = ", ".join(sorted({s.name for s in sources if getattr(s, "endpoints", None)}))
        for no, span, fenced in spans(prd_path):
            ep_m = ENDPOINT_ROUTE_RE.match(span.strip())
            if ep_m:
                ep_token = span.strip()
                norm_p = ep_norm(ep_token)
                if ep_token not in known_endpoints and norm_p not in known_paths:
                    findings.append(f"[CONTRACT-MISSING] {Path(prd_path).as_posix()}:{no} {ep_token} (endpoint, {source_names})")

    return findings


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
    """Yield (ref, kind, source_name) for every unresolved reference in one span; kind "ambiguous" carries the tables instead."""
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
                owners = s.ambiguous_owners(table, col)
                if owners:
                    yield col, "ambiguous", ", ".join(owners)
                continue
            for v in values:
                if v not in labels:
                    yield f"{col}='{v}'", "enum-value", s.name


def count_refs(span, known_tables, fenced):
    return sum(1 for m in REF_RE.finditer(span) if m.group(1) in known_tables) + sum(1 for _ in bindings(span, fenced))


def load_sources(schema, sql_paths, ts_paths=None):
    """Parsed schema sources (md first, then each sql, then each ts); dropped if empty."""
    sources = [parse_sql(p) for p in sql_paths]
    if ts_paths:
        for p in collect_ts_files(ts_paths):
            sources.append(parse_ts(p))
    if Path(schema).is_file():
        sources.insert(0, parse_md(schema))
    return [s for s in sources if s.declares_tables() or bool(s.enums) or (hasattr(s, "endpoints") and bool(s.endpoints))]


def parity_drift(sources):
    """Yield (ref, present_in, absent_from) for every table/column one source has and another lacks."""
    for a in sources:
        for b in sources:
            if a is b:
                continue
            for table in sorted(set(a.tables) - {PLACEHOLDER_TABLE}):
                if table not in b.tables:
                    yield table, a.name, b.name
                    continue
                for col in sorted(a.tables[table] - b.tables[table]):
                    yield f"{table}.{col}", a.name, b.name


def run_parity(sources):
    if len(sources) < 2:
        return 0
    findings = [f"[CONTRACT-DRIFT] {ref} (documented in {a}, missing from {b})" for ref, a, b in parity_drift(sources)]
    if findings:
        print("\n".join(findings))
        return 1
    print(f"[CONTRACT-OK] parity: {len({t for s in sources for t in s.tables} - {PLACEHOLDER_TABLE})} table(s) compared")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Spec-to-schema contract check (detection only).")
    ap.add_argument("--docs", nargs="+", default=[], help="spec docs to check (PRD, design doc); not used with --parity")
    ap.add_argument("--prd", default=None, help="PRD document to check for contracts, endpoints, and deferred story mirroring")
    ap.add_argument("--schema", default=".memory/DATABASE_SCHEMA.md")
    ap.add_argument("--sql", nargs="+", default=[], help="schema.sql file(s); a reference must resolve in each")
    ap.add_argument("--ts", nargs="+", default=[], help="TypeScript file(s) or directories to parse interfaces and types from")
    ap.add_argument("--parity", action="store_true", help="flag tables/columns present in one schema source but not another")
    args = ap.parse_args(argv)
    if args.parity and (args.docs or args.prd):
        ap.error("--parity takes no --docs or --prd")
    if not args.parity and not args.docs and not args.prd:
        ap.error("at least one of --docs or --prd is required")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    all_inputs = [*args.docs, *([args.prd] if args.prd else []), *args.sql, *(args.ts or [])]
    missing = [p for p in all_inputs if not Path(p).exists()]
    if missing:
        print(f"[CONTRACT-ERROR] file not found: {', '.join(missing)}", file=sys.stderr)
        return 2

    sources = load_sources(args.schema, args.sql, ts_paths=args.ts)
    if args.parity:
        return run_parity(sources)

    all_docs = list(args.docs)
    if args.prd and args.prd not in all_docs:
        all_docs.append(args.prd)

    if not sources and not any(is_prd_doc(d) for d in all_docs):
        print("[CONTRACT-SKIP] no schema declared")
        return 0

    known_tables = {t for s in sources for t in s.tables} - {PLACEHOLDER_TABLE}
    findings, advisories, checked = [], [], 0

    if sources:
        for doc in all_docs:
            label = Path(doc).as_posix()
            for no, span, fenced in spans(doc):
                checked += count_refs(span, known_tables, fenced)
                for ref, kind, source in check_span(span, sources, known_tables, fenced):
                    if kind == "ambiguous":
                        line, bucket = f"[CONTRACT-AMBIGUOUS {ref}: {source}]", advisories
                    else:
                        line, bucket = f"[CONTRACT-MISSING] {label}:{no} {ref} ({kind}, {source})", findings
                    if line not in bucket:
                        bucket.append(line)

    for doc in all_docs:
        if doc == args.prd or is_prd_doc(doc):
            prd_findings = check_prd_contracts(doc, sources)
            for pf in prd_findings:
                if pf not in findings:
                    findings.append(pf)

    if advisories:
        print("\n".join(advisories))
    if findings:
        print("\n".join(findings))
        return 1
    if not sources and not findings:
        print("[CONTRACT-SKIP] no schema declared")
        return 0
    print(f"[CONTRACT-OK] {checked} reference(s) checked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
