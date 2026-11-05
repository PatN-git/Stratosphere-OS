"""B6 Part A, scripted (no model, no gh, no GitHub): finished-unit merge-flow checks against the bt221 worktree code.

    python run_parta.py            # builds C:\\t\\pa6-1, writes C:\\t\\pa6-driver\\out\\{assertions,trace}.md and results.json
"""
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
WT = Path(r"C:\Users\patri\Dev\Stratosphere-OS\.claude\worktrees\bt221")
ISSUES = str(WT / "src/scripts/issues.py")
RECON = str(WT / "src/scripts/reconcile.py")
ROOT = Path(r"C:\t\pa6-1")
DRV = Path(r"C:\t\pa6-driver")
OUT = DRV / "out"
BARE = ROOT / "pa6.git"
PROJ = ROOT / "project"
ARCH = ".memory/ARCHITECTURE.md"
TRACKER_REF = "pa6/issues"

UNITS = {
    "U1": dict(epic="Slugify helper", slice="Implement slugify", dep="Document slugify", mod="slugify", slug="slugify",
               code='import re\n\n\ndef slugify(text):\n    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")\n',
               test='from slugify import slugify\n\n\ndef test_basic():\n    assert slugify("Hello, World!") == "hello-world"\n'),
    "U2": dict(epic="Word counter", slice="Count words", dep="Document the word counter", mod="wordcount", slug="words",
               code='def count_words(text):\n    return len(text.split())\n',
               test='from wordcount import count_words\n\n\ndef test_basic():\n    assert count_words("a b  c") == 3\n'),
    "U3": dict(epic="Title caser", slice="Title-case a string", dep="Document the title caser", mod="titlecase", slug="title",
               code='def title_case(text):\n    return " ".join(w[:1].upper() + w[1:].lower() for w in text.split())\n',
               test='from titlecase import title_case\n\n\ndef test_basic():\n    assert title_case("hello wORLD") == "Hello World"\n'),
    "U4": dict(epic="Clamp helper", slice="Clamp a number", dep="Document the clamp helper", mod="clamp", slug="clamp",
               code='def clamp(x, lo, hi):\n    return max(lo, min(x, hi))\n',
               test='from clamp import clamp\n\n\ndef test_outside():\n    assert clamp(-1, 0, 10) == 0\n'),
}

TRACE = []      # (label, cmd, rc, out)
RESULTS = []    # (name, ok, detail)
ALL_MERGED_OUT = []
ENV = {**os.environ, "HOME": str(ROOT / "home"), "USERPROFILE": str(ROOT / "home"),
       "GIT_CONFIG_GLOBAL": str(ROOT / "gitconfig"), "TMP": r"C:\t", "TEMP": r"C:\t",
       "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8", "GIT_TERMINAL_PROMPT": "0", "GIT_EDITOR": "true"}
ARGV_LOG = []


def _rm_ro(func, path, exc):
    os.chmod(path, stat.S_IWRITE)
    func(path)


def sh(cwd, *argv, trace=None, check=True):
    """Run one program; (rc, combined stdout+stderr stripped). `trace` = label to record in the command trace."""
    ARGV_LOG.append(argv[0])
    r = subprocess.run([str(a) for a in argv], cwd=str(cwd), env=ENV, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    out = (r.stdout + (("\n" + r.stderr) if r.stderr.strip() else "")).strip()
    if trace:
        shown = " ".join(("issues.py" if str(a) == ISSUES else "reconcile.py" if str(a) == RECON else str(a))
                         for a in argv if str(a) not in ("python", "--arch", ARCH))
        TRACE.append((trace, shown, r.returncode, out))
    if check and r.returncode:
        raise SystemExit(f"FAILED {argv} rc={r.returncode}\n{out}")
    return r.returncode, out


def iss(*args, label=None, check=True):
    return sh(PROJ, "python", ISSUES, "--arch", ARCH, *args, trace=label, check=check)


def recon(*args, label=None, check=False):
    return sh(PROJ, "python", RECON, "--arch", ARCH, *args, trace=label, check=check)


def git(*args, label=None, cwd=None, check=True):
    return sh(cwd or PROJ, "git", *args, trace=label, check=check)


def get(bt):
    return json.loads(iss("get", bt)[1])


def tracker_files():
    return set(git("ls-tree", "-r", "--name-only", TRACKER_REF, "--", "docs/issues", label=None)[1].split())


def tracker_head():
    return git("rev-parse", TRACKER_REF)[1]


def assert_(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail and not ok else ""))


def closed_fully(bt, expect_closed=True):
    """(ok, detail): done, completed, closed date set, archived path, claimed_by cleared."""
    i = get(bt)
    files = tracker_files()
    arch = f"docs/issues/archive/{bt}.md" in files and f"docs/issues/{bt}.md" not in files
    ok = (i["status"] == "done" and i["close_reason"] == "completed" and i["closed"] and i["state"] == "CLOSED"
          and arch and i["claimed_by"] is None)
    return ok, f"status={i['status']} reason={i['close_reason']} state={i['state']} archived={arch} claimed_by={i['claimed_by']}"


def still_open_in_review(bt):
    i = get(bt)
    files = tracker_files()
    ok = (i["status"] == "in review" and i["state"] == "OPEN" and not i["closed"] and f"docs/issues/{bt}.md" in files)
    return ok, f"status={i['status']} state={i['state']}"


def merged_out(*args, label):
    rc, out = iss("merged", *args, label=label)
    ALL_MERGED_OUT.append(out)
    return out


def edges(label):
    """{(dep, blk): ('CLEAR'|'KEEP', cmd|None)} of `reconcile.py --edges dependents --all-open`."""
    rc, out = recon("--edges", "dependents", "--all-open", label=label)
    res, last = {}, None
    for line in out.splitlines():
        m = re.match(r"\[(CLEAR|KEEP) (\S+) <- (\S+)\]", line)
        if m:
            last = (m.group(2), m.group(3))
            res[last] = [m.group(1), None]
        elif line.strip().startswith("cmd:") and last:
            res[last][1] = line.split("cmd:", 1)[1].strip()
    return res


def apply_clear(res):
    for (dep, blk), (verdict, cmd) in res.items():
        if verdict == "CLEAR":
            m = re.fullmatch(r"python \.agents/scripts/issues\.py set (\S+) --remove-blocker (\S+)", cmd or "")
            assert m, f"unexpected clear cmd {cmd}"
            iss("set", m.group(1), "--remove-blocker", m.group(2), label="apply the printed [CLEAR] cmd")


def main():
    if ROOT.exists():
        shutil.rmtree(ROOT, onerror=_rm_ro)
    OUT.mkdir(parents=True, exist_ok=True)
    (ROOT / "home").mkdir(parents=True)
    (ROOT / "gitconfig").write_text("[user]\n\tname = pa6\n\temail = pa6@example.test\n[init]\n\tdefaultBranch = master\n"
                                    "[core]\n\tautocrlf = false\n[commit]\n\tgpgsign = false\n[merge]\n\tff = true\n"
                                    "[safe]\n\tdirectory = *\n", encoding="utf-8")
    git("init", "-q", "--bare", "-b", "master", str(BARE), cwd=ROOT)
    PROJ.mkdir()
    git("init", "-q", "-b", "master", cwd=PROJ)
    (PROJ / ".gitignore").write_text(".tmp/\n", encoding="utf-8")
    (PROJ / "README.md").write_text("# pa6 sandbox\n", encoding="utf-8")
    (PROJ / ".memory").mkdir()
    (PROJ / ".memory" / "ARCHITECTURE.md").write_text("---\ntype: architecture\ntracker: local\n---\n# Architecture\n", encoding="utf-8")
    git("add", "-A")
    git("commit", "-q", "-m", "chore: init")
    git("remote", "add", "origin", BARE.as_posix())
    git("push", "-q", "-u", "origin", "master")
    git("fetch", "-q", "origin")
    git("remote", "set-head", "origin", "master")
    iss("init", label="init the tracker branch")

    # ---- build the four finished units (4a step 6 state) -------------------------------------------------------
    U = {}
    for key, u in UNITS.items():
        epic = iss("create", "--title", u["epic"], "--label", "type:feature,tier:epic", "--status", "in progress")[1]
        sl = iss("create", "--title", u["slice"], "--label", "type:feature,tier:slice,mode:HITL,size:small",
                 "--status", "planned", "--parent", epic)[1]
        dep = iss("create", "--title", u["dep"], "--label", "type:maintenance,tier:slice,mode:HITL,size:small",
                  "--status", "planned", "--blocked-by", sl)[1]
        branch = f"feature/{epic}-{u['slug']}"
        git("checkout", "-q", "-b", branch, "master")
        iss("claim", sl)
        (PROJ / f"{u['mod']}.py").write_text(u["code"], encoding="utf-8")
        (PROJ / "tests").mkdir(exist_ok=True)
        (PROJ / "tests" / f"test_{u['mod']}.py").write_text(u["test"], encoding="utf-8")
        git("add", f"{u['mod']}.py", f"tests/test_{u['mod']}.py")
        git("commit", "-q", "-m", f"feat({sl}): {u['slice'].lower()}")
        tip = git("rev-parse", "HEAD")[1]
        claimed = get(sl)["claimed_by"]
        git("push", "-q", "origin", branch)
        git("checkout", "-q", "master")
        U[key] = dict(epic=epic, slice=sl, dep=dep, branch=branch, tip=tip, claimed_before_ship=claimed)
    # 4a step 6 per unit: Shipped comment on the slice, slice closed, epic -> in review
    for key, d in U.items():
        iss("comment", d["slice"], "--body", f"Shipped on {d['branch']} @ {d['tip']}",
            label=f"{key} ship: Shipped comment")
        iss("set", d["slice"], "--status", "done", label=f"{key} ship: slice done")
        iss("close", d["slice"], label=f"{key} ship: slice close")
        iss("set", d["epic"], "--status", "in review", label=f"{key} ship: epic in review")
    git("push", "-q", "origin", TRACKER_REF)
    json.dump(U, open(OUT / "units.json", "w"), indent=1)

    # ---- A0: baseline -------------------------------------------------------------------------------------------
    assert_("A0.1 build: every slice was claimed on its unit branch before ship, cleared by ship",
            all(d["claimed_before_ship"] == d["branch"] and get(d["slice"])["claimed_by"] is None for d in U.values()),
            str({k: d["claimed_before_ship"] for k, d in U.items()}))
    assert_("A0.2 build: each slice carries a `Shipped on <branch> @ <sha>` comment with the full tip",
            all(any(f"Shipped on {d['branch']} @ {d['tip']}" in c for c in get(d["slice"])["comments"]) for d in U.values()))
    assert_("A0.3 build: four epics in review/open, four dependents blocked, `check` OK",
            all(still_open_in_review(d["epic"])[0] and get(d["dep"])["blocked_by"] == [d["slice"]] for d in U.values())
            and iss("check", label="check (baseline)")[1] == "[CHECK-OK 12 issue(s)]")
    out = merged_out(label="merged (baseline, nothing merged)")
    out2 = merged_out("--close", label="merged --close (baseline)")
    assert_("A0.4 baseline: `merged` and `merged --close` print [NO-MERGES]", out == "[NO-MERGES]" and out2 == "[NO-MERGES]", f"{out!r} {out2!r}")
    e = edges("reconcile --edges dependents --all-open (baseline)")
    assert_("A0.5 baseline: all four dependents KEEP, none CLEAR",
            len(e) == 4 and all(v[0] == "KEEP" for v in e.values()), str(e))

    # ---- A1: U1 merge commit ------------------------------------------------------------------------------------
    git("checkout", "-q", "master")
    git("merge", "-q", "--no-ff", U["U1"]["branch"], "-m", f"Merge branch '{U['U1']['branch']}'", label="HUMAN merge U1: merge commit")
    git("push", "-q", "origin", "master", label="HUMAN push master (U1)")
    out = merged_out(label="merged (after U1 merge commit)")
    assert_("A1.1 U1 merge commit: `merged` lists exactly [MERGED <U1 epic>]", out == f"[MERGED {U['U1']['epic']}]", out)
    assert_("A1.2 `merged` without --close writes nothing: U1 epic still in review/open", still_open_in_review(U["U1"]["epic"])[0])
    head0 = tracker_head()
    out = merged_out("--close", label="merged --close (after U1)")
    assert_("A1.3 `merged --close` prints [MERGED <U1 epic>] only", out == f"[MERGED {U['U1']['epic']}]", out)
    ok, det = closed_fully(U["U1"]["epic"])
    assert_("A1.4 U1 epic closed: done, completed, archived, claimed_by cleared", ok, det)
    ok, det = closed_fully(U["U1"]["slice"])
    assert_("A1.5 U1 slice closed: done, completed, archived, claimed_by cleared", ok, det)
    assert_("A1.6 U1 closed in exactly one tracker commit", git("rev-list", "--count", f"{head0}..{TRACKER_REF}")[1] == "1")
    assert_("A1.7 U2, U3, U4 epics untouched (in review/open)", all(still_open_in_review(U[k]["epic"])[0] for k in ("U2", "U3", "U4")))
    e = edges("reconcile --edges dependents --all-open (after U1)")
    k1 = (U["U1"]["dep"], U["U1"]["slice"])
    assert_("A1.8 U1 dependent [CLEAR]; U2/U3/U4 dependents [KEEP]",
            e.get(k1, [None])[0] == "CLEAR" and all(e[(U[k]["dep"], U[k]["slice"])][0] == "KEEP" for k in ("U2", "U3", "U4")), str(e))
    apply_clear(e)
    assert_("A1.9 applying the printed cmd clears U1 dependent's blocked_by; others stay blocked",
            get(U["U1"]["dep"])["blocked_by"] == []
            and all(get(U[k]["dep"])["blocked_by"] == [U[k]["slice"]] for k in ("U2", "U3", "U4")))

    # ---- A2: U2 squash ------------------------------------------------------------------------------------------
    git("merge", "-q", "--squash", U["U2"]["branch"], label="HUMAN merge U2: squash")
    git("commit", "-q", "-m", f"feature({U['U2']['epic']}): Word counter (#2)", label="HUMAN squash commit")
    sq = git("rev-parse", "--short", "HEAD")[1]
    git("push", "-q", "origin", "master", label="HUMAN push master (U2)")
    out = merged_out(label="merged (after U2 squash)")
    exp = f"[PROBABLY-MERGED {U['U2']['epic']}] (squash commit {sq} matches id in origin/master; confirm before close)"
    assert_("A2.1 U2 squash: `merged` reports exactly the advisory [PROBABLY-MERGED ... confirm before close]", out == exp, out)
    head1 = tracker_head()
    out = merged_out("--close", label="merged --close (after U2 squash)")
    assert_("A2.2 `merged --close` prints the advisory and does NOT close U2 epic",
            out == exp and still_open_in_review(U["U2"]["epic"])[0], out)
    assert_("A2.3 advisory-only `--close` wrote no tracker commit", tracker_head() == head1)
    out = merged_out("--close", label="merged --close (re-run, idempotent)")
    assert_("A2.4 re-run is stable (same advisory line, tracker head unchanged)", out == exp and tracker_head() == head1, out)
    e = edges("reconcile --edges dependents --all-open (after U2 squash)")
    assert_("A2.5 U2 dependent stays [KEEP] (squash is not an ancestor merge; advisory never frees it); U3/U4 KEEP",
            all(e[(U[k]["dep"], U[k]["slice"])][0] == "KEEP" for k in ("U2", "U3", "U4")) and (U["U1"]["dep"], U["U1"]["slice"]) not in e, str(e))

    # ---- A3: U4 merged on the remote only, branch deleted -------------------------------------------------------
    tmp = ROOT / "remote-merge"
    git("clone", "-q", BARE.as_posix(), str(tmp), cwd=ROOT)
    git("merge", "-q", "--no-ff", f"origin/{U['U4']['branch']}", "-m", f"Merge branch '{U['U4']['branch']}'", cwd=tmp, label="HUMAN merge U4 on the remote only (temp clone)")
    git("push", "-q", "origin", "master", cwd=tmp, label="HUMAN push (temp clone -> bare)")
    git("push", "-q", "origin", "--delete", U["U4"]["branch"], cwd=tmp, label="HUMAN delete U4 branch on the remote")
    shutil.rmtree(tmp, onerror=_rm_ro)
    git("branch", "-q", "-D", U["U4"]["branch"], label="delete U4 branch locally")
    git("update-ref", "-d", f"refs/remotes/origin/{U['U4']['branch']}", label="drop the U4 remote-tracking ref (fetch.prune equivalent)")
    stale = git("rev-parse", "origin/master")[1]
    bare_master = git("rev-parse", "master", cwd=BARE)[1]
    refs = git("for-each-ref", "--format=%(refname)", "refs/heads", "refs/remotes")[1]
    assert_("A3.0 setup: U4 branch gone locally and in remote-tracking refs; project origin/master is stale vs the bare master",
            U["U4"]["branch"] not in refs and stale != bare_master
            and git("merge-base", "--is-ancestor", U["U4"]["tip"], "origin/master", check=False)[0] != 0
            and git("merge-base", "--is-ancestor", U["U4"]["tip"], bare_master, cwd=BARE, check=False)[0] == 0,
            f"stale={stale[:7]} bare={bare_master[:7]}")
    out = merged_out(label="merged (U4 merged remotely, project NOT fetched)")
    out_c = merged_out("--close", label="merged --close (U4 not fetched)")
    assert_("A3.1 before fetch: U4 not detected by `merged` nor closed by `--close`",
            U["U4"]["epic"] not in out and U["U4"]["epic"] not in out_c and still_open_in_review(U["U4"]["epic"])[0], out)
    e = edges("reconcile --edges dependents --all-open (U4 before fetch)")
    assert_("A3.2 before fetch: U4 dependent stays [KEEP]", e[(U["U4"]["dep"], U["U4"]["slice"])][0] == "KEEP", str(e))
    git("fetch", "-q", "origin", label="git fetch -q origin")
    out = merged_out(label="merged (after fetch)")
    exp_lines = sorted([f"[MERGED {U['U4']['epic']}]", exp])
    assert_("A3.3 after fetch: U4 detected [MERGED] via the recorded tip SHA (branch is gone), U2 still advisory, U3 absent",
            sorted(out.splitlines()) == exp_lines
            and git("merge-base", "--is-ancestor", U["U4"]["tip"], "origin/master", check=False)[0] == 0
            and U["U4"]["branch"] not in git("for-each-ref", "--format=%(refname)", "refs/heads", "refs/remotes")[1], out)
    out = merged_out("--close", label="merged --close (after fetch)")
    assert_("A3.4 `--close` after fetch: same two lines", sorted(out.splitlines()) == exp_lines, out)
    ok, det = closed_fully(U["U4"]["epic"])
    assert_("A3.5 U4 epic closed: done, completed, archived, claimed_by cleared", ok, det)
    ok, det = closed_fully(U["U4"]["slice"])
    assert_("A3.6 U4 slice closed: done, completed, archived, claimed_by cleared", ok, det)
    e = edges("reconcile --edges dependents --all-open (after U4 fetch)")
    assert_("A3.7 U4 dependent [CLEAR]; U2 and U3 dependents [KEEP]",
            e[(U["U4"]["dep"], U["U4"]["slice"])][0] == "CLEAR"
            and e[(U["U2"]["dep"], U["U2"]["slice"])][0] == "KEEP" and e[(U["U3"]["dep"], U["U3"]["slice"])][0] == "KEEP", str(e))
    apply_clear(e)
    assert_("A3.8 applying the printed cmd clears U4 dependent; U2/U3 dependents stay blocked",
            get(U["U4"]["dep"])["blocked_by"] == []
            and all(get(U[k]["dep"])["blocked_by"] == [U[k]["slice"]] for k in ("U2", "U3")))

    # ---- A4: end state --------------------------------------------------------------------------------------------
    assert_("A4.1 U3 never merged: epic in review/open, never listed by any `merged` run",
            still_open_in_review(U["U3"]["epic"])[0] and not any(U["U3"]["epic"] in o or U["U3"]["slice"] in o for o in ALL_MERGED_OUT))
    assert_("A4.2 U2 squash epic still in review/open after every `--close` (never auto-closed)", still_open_in_review(U["U2"]["epic"])[0])
    assert_("A4.3 U1 + U4 slices and epics all closed; U2 slice closed, U3 slice closed (shipped)",
            all(closed_fully(U[k][r])[0] for k in ("U1", "U4") for r in ("epic", "slice"))
            and all(closed_fully(U[k]["slice"])[0] for k in ("U2", "U3")))
    rc, out = iss("check", label="check (final)")
    assert_("A4.4 `issues.py check` OK at the end", rc == 0 and out == "[CHECK-OK 12 issue(s)]", out)
    iss("list", "--all", label="list --all (final)")
    head_final = tracker_head()

    # ---- A5: views ------------------------------------------------------------------------------------------------
    (ROOT / "out").mkdir(exist_ok=True)
    md, html = ROOT / "out" / "board.md", ROOT / "out" / "board.html"
    rc, out = iss("board", "--md", str(md), label="board --md")
    text = md.read_text(encoding="utf-8") if md.exists() else ""
    assert_("A5.1 `board --md` writes the Markdown board with Done and In Review columns and the open dependents",
            rc == 0 and out.startswith("[BOARD] wrote") and "## Done (" in text and "## In Review (" in text
            and U["U3"]["epic"] in text and U["U3"]["dep"] in text and "blocked by" in text, out)
    rc, out = iss("board", "--web", "--out", str(html), label="board --web --out")
    page = html.read_text(encoding="utf-8") if html.exists() else ""
    assert_("A5.2 `board --web --out` writes an HTML page that names the units",
            rc == 0 and html.exists() and html.stat().st_size > 2000 and "<html" in page.lower()
            and U["U3"]["epic"] in page and U["U1"]["epic"] in page, f"rc={rc} size={html.stat().st_size if html.exists() else None} {out[:120]}")
    rc, out = iss("apply-moves", str(DRV / "moves-ok.txt"), "--dry-run", label="apply-moves --dry-run (one move)")
    assert_("A5.3 `apply-moves --dry-run` of one move reports it and writes nothing",
            rc == 0 and f"{U['U3']['dep']}: planned -> in progress" in out and "dry run: 1 move(s) would apply, nothing written" in out
            and tracker_head() == head_final and get(U["U3"]["dep"])["status"] == "planned", out)
    rc, out = iss("apply-moves", str(DRV / "moves-refused.txt"), "--dry-run", label="apply-moves --dry-run (drag unmerged epics to done)", check=False)
    assert_("A5.4 `apply-moves` refuses to drag the unmerged U3 epic and the advisory-only U2 epic to done",
            rc == 1 and out.count("in review and not merged") == 2 and tracker_head() == head_final, out)
    assert_("A5.5 no tracker write by any view (head unchanged)", tracker_head() == head_final)
    assert_("A5.6 no `gh` call anywhere in the run", "gh" not in ARGV_LOG, str(sorted(set(ARGV_LOG))))

    # ---- write fragments -----------------------------------------------------------------------------------------
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    lines = ["| # | Assertion | Verdict |", "|:--|:--|:--|"]
    for name, ok, det in RESULTS:
        num, _, rest = name.partition(" ")
        lines.append(f"| {num} | {rest.replace('|', '/')} | {'PASS' if ok else 'FAIL: ' + det.replace('|', '/')[:200]} |")
    lines.append("")
    lines.append(f"**{passed} PASS / {len(RESULTS) - passed} FAIL of {len(RESULTS)}**")
    (OUT / "assertions.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    tr = ["```"]
    for label, cmd, rc, out in TRACE:
        tr.append(f"## {label}")
        tr.append(f"$ {cmd}   (rc={rc})")
        body = out if len(out) <= 900 else out[:900] + " ..."
        tr += ([f"  {l}" for l in body.splitlines()] if body else [])
    tr.append("```")
    (OUT / "trace.md").write_text("\n".join(tr) + "\n", encoding="utf-8")
    json.dump([(n, ok, d) for n, ok, d in RESULTS], open(OUT / "results.json", "w"), indent=1)
    print(f"\n{passed} PASS / {len(RESULTS) - passed} FAIL of {len(RESULTS)}")


main()
