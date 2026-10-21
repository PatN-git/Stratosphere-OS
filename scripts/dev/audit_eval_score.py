#!/usr/bin/env python3
"""audit_eval_score.py: dev-only. Score auditor result files against the corpus labels.

  audit_eval_score.py --eval-dir DIR [--arm A]... [--min-label-confidence low|medium|high]

DIR/<case>/labels.json   {"case", "labels": [{id, ac, desc, cls, key_terms, min_terms, label_confidence}]}
DIR/results/<case>__<arm>__<k>.json   {"findings": [{"ac", "conf", "text"}], "files_read": n}   (k = repeat number)
DIR/results/tokens.csv   case,arm,k,tokens   (optional)

A finding matches a label when at least `min_terms` of the label's key terms appear in its `ac` plus `text` (case
insensitive). A label is `found` when a matching finding has confidence >= 80, `watch` when the best match is 60-79,
else `missed`. Matching is mechanical, never an LLM judge.
"""
import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

FOUND, WATCH_FLOOR = 80, 60
RANK = {"low": 0, "medium": 1, "high": 2}


def loads_lenient(text):
    """json.loads that tolerates the stray backslashes (`\\_`, `\\d`) a model leaves in its own JSON; valid escapes are kept."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return json.loads(re.sub(r"\\(.)", lambda m: m.group(0) if m.group(1) in '"\\/bfnrtu' else "\\\\" + m.group(1), text, flags=re.S))


def matches(label, f):
    text = f"{f.get('ac', '')} {f.get('text', '')}".lower()
    hits = sum(1 for t in label["key_terms"] if t.lower() in text)
    return hits >= min(label.get("min_terms", 1), len(label["key_terms"]))


def classify(label, findings):
    best = max((f["conf"] for f in findings if matches(label, f)), default=-1)
    return "found" if best >= FOUND else "watch" if best >= WATCH_FLOOR else "missed"


def score_run(labels, findings):
    status = {l["id"]: classify(l, findings) for l in labels}
    n = len(labels)
    unmatched = [f for f in findings if not any(matches(l, f) for l in labels)]
    matched = [f for f in findings if any(matches(l, f) for l in labels)]
    return {
        "status": status,
        "matched80": sum(f["conf"] >= FOUND for f in matched),
        "matched_watch": sum(WATCH_FLOOR <= f["conf"] < FOUND for f in matched),
        "recall80": (sum(s == "found" for s in status.values()) / n) if n else None,
        "recall60": (sum(s != "missed" for s in status.values()) / n) if n else None,
        "unmatched80": sum(f["conf"] >= FOUND for f in unmatched),
        "unmatched_watch": sum(WATCH_FLOOR <= f["conf"] < FOUND for f in unmatched),
    }


def triage_outcome(labels, watch, verdicts):
    """What a cheap second look does to a run's watch items. `watch` = the 60-79 findings, `verdicts` = {index: confirmed|refuted|unclear}.

    promoted_labels: labels a confirmed watch item matches; lost_labels: labels whose matching watch items were all refuted or
    unclear; noise_removed: unmatched items refuted; unlabeled_confirmed: unmatched items confirmed (real but unlabeled, or wrong)."""
    promoted, lost = [], []
    for l in labels:
        idx = [i for i, f in enumerate(watch) if matches(l, f)]
        if not idx:
            continue
        (promoted if any(verdicts.get(i) == "confirmed" for i in idx) else lost).append(l["id"])
    unmatched = [i for i, f in enumerate(watch) if not any(matches(l, f) for l in labels)]
    return {"promoted_labels": promoted, "lost_labels": lost,
            "noise_removed": sum(verdicts.get(i) == "refuted" for i in unmatched),
            "unlabeled_confirmed": sum(verdicts.get(i) == "confirmed" for i in unmatched),
            "unclear": sum(v == "unclear" for v in verdicts.values())}


def detection(runs):
    """{label id: share of runs in which it was `found`}."""
    ids = {i for r in runs for i in r["status"]}
    return {i: sum(r["status"].get(i) == "found" for r in runs) / len(runs) for i in sorted(ids)}


def flaky(p):
    return [i for i, v in p.items() if 0 < v < 1]


def stable(p):
    return [i for i, v in p.items() if v == 1]


COMMAND = re.compile(r"^(npm|npx|yarn|pnpm|python3?|pytest|git|gh|bash|sh|node|vitest|make|cd)\s")
FILE_NAME = re.compile(r"^[\w.-]+\.\w{1,5}$")


def absent_literals(ac_text, corpus, paths):
    """Backticked literals of the AC text that appear in none of the changed files (hint for a 'text absent' gap).

    Skipped: shell commands, prose fragments (a `;`, or 4+ words not starting with `[`), and path or file-name
    literals, which are checked against the changed paths instead of the file contents."""
    out = []
    for lit in dict.fromkeys(m.strip() for m in re.findall(r"`([^`\n]{3,80})`", ac_text)):
        if COMMAND.match(lit) or ";" in lit or (not lit.startswith("[") and len(lit.split()) >= 4):
            continue
        if "/" in lit or FILE_NAME.match(lit):
            present = any(p == lit or p.endswith("/" + lit) or p.endswith(lit) for p in paths) or lit in corpus
        else:
            present = lit in corpus
        if not present:
            out.append(lit)
    return out


def lint_catches(label, absent):
    """True when an absent literal holds at least `min_terms` of the label's key terms (a literal stands alone, so 1 is enough
    for a single-term hit); the lint is only a hint, so this is deliberately the generous reading."""
    need = 1
    return any(sum(t.lower() in lit.lower() for t in label["key_terms"]) >= need for lit in absent)


def lint_report(eval_dir):
    eval_dir = Path(eval_dir)
    lines, caught_all, caught_text, total, total_text, flags, linked = [], 0, 0, 0, 0, 0, 0
    for lf in sorted(eval_dir.glob("*/labels.json")):
        d = json.loads(lf.read_text(encoding="utf-8"))
        packet = (lf.parent / "packet.md").read_text(encoding="utf-8")
        ac = re.search(r"## Acceptance Criteria.*?(?=\n## )", packet, re.S).group(0)
        paths = re.findall(r"^- (\S+)$", re.search(r"## Changed paths\n(.*?)(?=\n## )", packet, re.S).group(1), re.M)
        corpus = "".join((lf.parent / "snapshot" / p).read_text(encoding="utf-8", errors="replace") + "\n" for p in paths if (lf.parent / "snapshot" / p).is_file())
        absent = absent_literals(ac, corpus, paths)
        hit = [l["id"] for l in d["labels"] if lint_catches(l, absent)]
        hit_text = [l["id"] for l in d["labels"] if l["cls"] == "text-absent" and l["id"] in hit]
        linked_lits = [a for a in absent if any(t.lower() in a.lower() for l in d["labels"] for t in l["key_terms"])]
        lines.append(f"{d['case']:12} absent={len(absent)} caught={hit} unlinked_flags={len(absent) - len(linked_lits)}  {absent[:4]}")
        caught_all += len(hit)
        caught_text += len(hit_text)
        total += len(d["labels"])
        total_text += sum(l["cls"] == "text-absent" for l in d["labels"])
        flags += len(absent)
        linked += len(linked_lits)
    lines.append(f"\nlint catches {caught_all}/{total} labels ({caught_text}/{total_text} of the text-absent class); "
                 f"{flags} flagged literals, {flags - linked} not tied to any label ({(flags - linked) / max(len(list(eval_dir.glob('*/labels.json'))), 1):.1f} per case)")
    return "\n".join(lines)


def load(eval_dir, arms, min_conf):
    eval_dir = Path(eval_dir)
    labels = {}
    for f in sorted(eval_dir.glob("*/labels.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        labels[d["case"]] = [dict(l, case=d["case"]) for l in d["labels"] if RANK[l.get("label_confidence", "low")] >= RANK[min_conf]]
    controls = {p.parent.name for p in eval_dir.glob("*/packet.md")} - set(labels)
    runs = defaultdict(list)
    for f in sorted((eval_dir / "results").glob("*__*__*.json")):
        case, arm, k = f.stem.split("__")
        if arms and arm not in arms:
            continue
        runs[(case, arm)].append(loads_lenient(f.read_text(encoding="utf-8")))
    tokens = defaultdict(list)
    tf = eval_dir / "results" / "tokens.csv"
    if tf.exists():
        for row in csv.DictReader(tf.open(encoding="utf-8")):
            tokens[(row["case"], row["arm"])].append(int(row["tokens"]))
    return labels, controls, runs, tokens


def report(eval_dir, arms, min_conf):
    labels, controls, runs, tokens = load(eval_dir, arms, min_conf)
    lines, by_arm = [], defaultdict(lambda: defaultdict(list))
    for (case, arm), rs in sorted(runs.items()):
        ls = labels.get(case, [])
        scored = [score_run(ls, r["findings"]) for r in rs]
        det = detection(scored) if ls else {}
        for l in ls:
            by_arm[arm]["labels"].append((case, l["id"], l["cls"], det[l["id"]], max(s["status"][l["id"]] == "watch" or s["status"][l["id"]] == "found" for s in scored)))
        by_arm[arm]["unmatched80"].append(sum(s["unmatched80"] for s in scored) / len(scored))
        by_arm[arm]["watch"].append(sum(s["unmatched_watch"] for s in scored) / len(scored))
        if ls:
            by_arm[arm]["matched_watch"].append(sum(s["matched_watch"] for s in scored) / len(scored))
            by_arm[arm]["watch_total"].append(sum(s["matched_watch"] + s["unmatched_watch"] for s in scored) / len(scored))
        else:
            by_arm[arm]["control_watch"].append(sum(s["unmatched_watch"] for s in scored) / len(scored))
            by_arm[arm]["control_fp80"].append(sum(s["unmatched80"] for s in scored) / len(scored))
        tk = tokens.get((case, arm), [])
        lines.append(f"{case:12} {arm:6} runs={len(rs)} labels={len(ls)} " + (f"detect={det} " if ls else "(control) ") +
                     f"unmatched80/run={by_arm[arm]['unmatched80'][-1]:.1f} watch/run={by_arm[arm]['watch'][-1]:.1f}" +
                     (f" tokens/run={sum(tk) // len(tk)}" if tk else ""))
    for arm, d in sorted(by_arm.items()):
        ls = d["labels"]
        if ls:
            lines.append(f"\n[{arm}] labels={len(ls)}  mean detection@80={sum(x[3] for x in ls) / len(ls):.2f}  "
                         f"ever seen at >=60={sum(x[4] for x in ls) / len(ls):.2f}  stable={sum(x[3] == 1 for x in ls)}  "
                         f"flaky={sum(0 < x[3] < 1 for x in ls)}  never_found={sum(x[3] == 0 for x in ls)}")
            by_cls = defaultdict(list)
            for x in ls:
                by_cls[x[2]].append(x[3])
            lines.append("  by class: " + ", ".join(f"{c}={sum(v) / len(v):.2f} (n={len(v)})" for c, v in sorted(by_cls.items())))
        lines.append(f"  unmatched findings >=80 per run (all cases): {sum(d['unmatched80']) / len(d['unmatched80']):.2f}; "
                     f"unmatched watch per run: {sum(d['watch']) / len(d['watch']):.2f}")
        if d["watch_total"]:
            lines.append(f"  watch items per labeled case run: {sum(d['watch_total']) / len(d['watch_total']):.2f}; matched to a label: "
                         f"{sum(d['matched_watch']) / max(sum(d['watch_total']), 1e-9):.0%} (unmatched is not necessarily false: labels cover only fixed gaps)")
        if d["control_watch"]:
            lines.append(f"  controls: {sum(d['control_watch']) / len(d['control_watch']):.2f} watch items and "
                         f"{sum(d['control_fp80']) / len(d['control_fp80']):.2f} findings >=80 per run")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--eval-dir", required=True)
    ap.add_argument("--arm", action="append", default=[])
    ap.add_argument("--min-label-confidence", default="low", choices=list(RANK))
    ap.add_argument("--lint", action="store_true", help="score the AC-literal lint instead of the result files")
    a = ap.parse_args(argv)
    print(lint_report(a.eval_dir) if a.lint else report(a.eval_dir, a.arm, a.min_label_confidence))
    return 0


if __name__ == "__main__":
    sys.exit(main())
