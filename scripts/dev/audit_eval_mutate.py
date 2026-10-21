#!/usr/bin/env python3
"""audit_eval_mutate.py: dev-only. Seeded defects for the 4a audit test corpus.

Takes a clean slice (the state after its audit fixes, or a control), clones its repo into a scratch folder, applies ONE
scripted mutation as a commit, and builds the packet and snapshot from the mutant, so the gap is labeled by construction.

  audit_eval_mutate.py --out DIR [--mutants docs/research/4a-audit-eval/mutants.json] [--id ID]...

Mutations: delete_test (a slice test is removed), weaken_assertion (a pinned assertion becomes an existence check),
remove_literal (a literal the AC names is swapped for a near miss), delete_step (a workflow line that runs a script is removed).
Writes DIR/<mutant id>/{packet.md, snapshot/, issue.md, labels.json, mutation.json}. Never touches the source repos.
"""
import argparse
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("audit_eval_build", HERE / "audit_eval_build.py")
build = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build)

ROOT = HERE.parents[1]
DATA = ROOT / "docs" / "research" / "4a-audit-eval"
STOP = {"test", "tests", "that", "with", "when", "from", "into", "only", "does", "have", "this", "then", "than", "each"}


def _words(text, limit=5):
    seen = []
    for w in re.split(r"[^A-Za-z0-9]+", text):
        if len(w) >= 4 and w.lower() not in STOP and w.lower() not in seen:
            seen.append(w.lower())
    return seen[:limit]


def _indent(line):
    return len(line) - len(line.lstrip())


def _py_blocks(lines):
    out = []
    for i, line in enumerate(lines):
        m = re.match(r"^([ \t]*)def (test_\w+)\(", line)
        if not m:
            continue
        ind, start, end = len(m.group(1)), i, i + 1
        while start > 0 and lines[start - 1].lstrip().startswith("@") and _indent(lines[start - 1]) == ind:
            start -= 1
        while end < len(lines) and (not lines[end].strip() or _indent(lines[end]) > ind):
            end += 1
        while end > i + 1 and not lines[end - 1].strip():
            end -= 1
        out.append((start, end, m.group(2), sum("assert " in x for x in lines[i:end])))
    return out


def _js_blocks(lines):
    out = []
    for i, line in enumerate(lines):
        m = re.match(r"^(\s*)(?:it|test)\((['\"`])(.+?)\2", line)
        if not m:
            continue
        close = re.compile(r"^" + re.escape(m.group(1)) + r"\}(?:,\s*\d+)?\)\s*;?\s*$")
        end = next((j for j in range(i + 1, len(lines)) if close.match(lines[j])), None)
        if end is not None:
            out.append((i, end + 1, m.group(3), sum("expect(" in x for x in lines[i:end + 1])))
    return out


def _blocks(lines, path):
    return _py_blocks(lines) if path.endswith(".py") else _js_blocks(lines) if re.search(r"\.[jt]sx?$", path) else []


def _enclosing_name(lines, idx, path):
    for start, end, name, _ in _blocks(lines, path):
        if start <= idx < end:
            return name
    return ""


def delete_test(text, path, allow=None):
    """Remove the test with the most assertions (only among names `allow` accepts); the AC it covered is no longer proven."""
    lines = text.splitlines(keepends=True)
    blocks = [b for b in _blocks(lines, path) if allow is None or allow(b[2])]
    if not blocks:
        return None
    start, end, name, _ = max(blocks, key=lambda b: b[3])
    blanks = 0
    while end < len(lines) and not lines[end].strip() and blanks < 2:
        end += 1
        blanks += 1
    new = "".join(lines[:start] + lines[end:])
    return new, {"cls": "missing-test", "name": name, "terms": _words(name), "file": path,
                 "desc": f"The test '{name}' in {path} was removed, so the behavior it asserted is no longer proven by any test."}


def weaken_assertion(text, path, allow_line=None):
    """Turn the first pinned-value assertion (a line `allow_line` accepts) into an existence check."""
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if allow_line is not None and not allow_line(line.strip()):
            continue
        if path.endswith(".py"):
            m = re.match(r"^(\s*)assert (.+?) == (.+?)(\s*)$", line)
            if m and "returncode" not in m.group(2):
                lines[i] = f"{m.group(1)}assert {m.group(2)} is not None\n"
                lhs = m.group(2)
            else:
                continue
        else:
            m = re.search(r"expect\((.+?)\)\.(?:toBe|toEqual|toStrictEqual)\((.+?)\);", line)
            if not m:
                continue
            lines[i] = line.replace(m.group(0), f"expect({m.group(1)}).toBeDefined();")
            lhs = m.group(1)
        name = _enclosing_name(text.splitlines(keepends=True), i, path)
        return "".join(lines), {"cls": "unpinned-case", "name": name, "terms": _words(name + " " + lhs), "file": path,
                                "desc": f"In '{name}' of {path} the assertion on `{lhs}` was weakened to an existence check, so a wrong value would pass."}
    return None


def remove_literal(text, literal, allow=None):
    """Swap the first occurrence of a literal an AC names for a near miss (brackets and case dropped)."""
    idx = text.find(literal)
    if idx < 0 or (allow is not None and not allow(literal)):
        return None
    near = re.sub(r"[\[\]`]", "", literal).lower()
    near = near if near != literal else literal + " (see docs)"
    return text[:idx] + near + text[idx + len(literal):], {
        "cls": "text-absent", "terms": [literal.lower()], "file": "",
        "desc": f"The literal `{literal}` named by an acceptance criterion no longer appears in the implementation (changed to `{near}`)."}


def delete_step(text, path):
    """Drop the first workflow line that runs a script (or carries a HALT tag)."""
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        m = re.search(r"python \S*scripts/(\w+)\.py", line) or re.search(r"HALT.*?\[([A-Z][A-Z-]{2,})\]", line)
        if m:
            term = m.group(1)
            return "".join(lines[:i] + lines[i + 1:]), {
                "cls": "wiring-omission", "terms": [term], "file": path,
                "desc": f"The step in {path} that runs or halts on `{term}` was deleted, so the workflow no longer wires it in."}
    return None


def make_label(mutant_id, info):
    terms = info["terms"][:5]
    return {"id": "g1", "ac": info["desc"][:120], "desc": info["desc"], "cls": info["cls"], "key_terms": terms,
            "min_terms": 2 if len(terms) >= 2 else 1, "evidence": f"seeded {mutant_id} {info.get('file', '')}".strip(),
            "label_confidence": "high"}


def _git(repo, *args):
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout.strip()


def _ac_literals(body):
    ac = re.search(r"### Acceptance Criteria.*?(?=\n### |\Z)", body, re.S)
    lits = re.findall(r"`([^`\n]{6,60})`", ac.group(0) if ac else "")
    return [l for l in dict.fromkeys(lits) if not re.match(r"^(npm|npx|python3?|pytest|git|gh|bash|node|cd)\s", l) and "/" not in l
            and len(l) >= 8 and re.search(r"[^a-z]", l) and not re.search(r"\.\w{1,4}$", l)]


def apply(kind, repo, paths, issue_body, added=None):
    """Return (path, new_text, info) for the first path the mutation applies to, else None.

    `added` = {path: set of stripped lines the slice added}; a mutation only touches what the slice added, so the packet's net diff never shows a deletion."""
    added = added or {}
    tests = [p for p in paths if build.TEST.search(p)]
    srcs = [p for p in paths if not build.TEST.search(p) and not p.endswith((".md", ".json", ".yml", ".yaml"))]
    mds = [p for p in paths if p.endswith(".md") and "workflows/" in p]
    for p in {"delete_test": tests, "weaken_assertion": tests, "delete_step": mds, "remove_literal": srcs}[kind]:
        f = Path(repo) / p
        if not f.is_file():
            continue
        text = f.read_text(encoding="utf-8")
        if kind == "remove_literal":
            for lit in _ac_literals(issue_body):
                res = remove_literal(text, lit, allow=(lambda l, a=added.get(p): a is None or any(l in x for x in a)))
                if res:
                    return p, res[0], {**res[1], "file": p}
            continue
        a = added.get(p)
        if kind == "delete_test":
            res = delete_test(text, p, allow=None if a is None else (lambda n: any(n in x for x in a)))
        elif kind == "weaken_assertion":
            res = weaken_assertion(text, p, allow_line=None if a is None else (lambda s: s in a))
        else:
            res = delete_step(text, p)
        if res:
            return p, res[0], res[1]
    return None


def make_mutant(entry, manifest, out_dir):
    case = next(c for c in manifest["cases"] if c["id"] == entry["case"])
    src = manifest["repos"][case["repo"]]
    commits = build.slice_commits(src["path"], case["slice"], case["fix"][-1] if case["fix"] else "last")
    post = _git(src["path"], "rev-parse", commits[-1])
    clone = out_dir / "_clones" / entry["id"]
    if not clone.exists():
        subprocess.run(["git", "clone", "--shared", "--no-checkout", src["path"], str(clone)], check=True, capture_output=True)
    _git(clone, "checkout", "--detach", post)
    paths = build.changed_paths(clone, commits)
    body = subprocess.run(["gh", "issue", "view", str(case["issue"]), "-R", src["gh"], "--json", "body", "-q", ".body"],
                          capture_output=True, text=True, encoding="utf-8").stdout
    base = _git(clone, "rev-parse", f"{commits[0]}^")
    added = {}
    for p in paths:
        diff = subprocess.run(["git", "-C", str(clone), "diff", base, post, "--", p], capture_output=True, text=True, encoding="utf-8").stdout
        added[p] = {l[1:].strip() for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")}
    res = apply(entry["mutation"], clone, paths, body, added)
    if not res:
        return None
    path, new_text, info = res
    (clone / path).write_text(new_text, encoding="utf-8", newline="")
    _git(clone, "-c", "user.name=mutant", "-c", "user.email=m@example.com", "commit", "-q", "-am", f"test({case['slice']}): seeded mutant {entry['id']}")
    mutant = {**case, "id": entry["id"], "pre": _git(clone, "rev-parse", "HEAD"), "fix": [], "kind": "mutant"}
    repos = {case["repo"]: {"path": str(clone), "gh": src["gh"]}}
    info = build.build_case(mutant, repos, out_dir)
    d = out_dir / entry["id"]
    (d / "labels.json").write_text(json.dumps({"case": entry["id"], "labels": [make_label(entry["id"], res[2])]}, indent=1), encoding="utf-8")
    (d / "mutation.json").write_text(json.dumps({**entry, "file": path, "cls": res[2]["cls"], "desc": res[2]["desc"]}, indent=1), encoding="utf-8")
    return d


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--out", required=True)
    ap.add_argument("--manifest", default=str(DATA / "cases.json"))
    ap.add_argument("--mutants", default=str(DATA / "mutants.json"))
    ap.add_argument("--id", action="append", default=[])
    a = ap.parse_args(argv)
    manifest = json.loads(Path(a.manifest).read_text(encoding="utf-8"))
    for entry in json.loads(Path(a.mutants).read_text(encoding="utf-8")):
        if a.id and entry["id"] not in a.id:
            continue
        d = make_mutant(entry, manifest, Path(a.out))
        print(entry["id"], "->", d if d else "NOT APPLICABLE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
