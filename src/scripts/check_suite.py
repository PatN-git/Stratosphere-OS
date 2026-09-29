#!/usr/bin/env python3
"""Deterministic integrity checks run by stratosphere-setup and stratosphere-update.

  check_suite.py suite       [--skills-dir DIR]   all 22 lifecycle skills present + uncorrupted
  check_suite.py visibility  [--project P] [--host claude|agents|auto]   system pack visible to the host
  check_suite.py legacy      [--project P] [--apply]   stale pre-canonical-bundle paths

Exit 0 = clean, 1 = problems found (a non-fatal halt: the caller prints the report and stops).
Never invoked by 0a-start-session (zero-session-overhead invariant).
"""
import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent  # <skills dir>/stratosphere-setup

# The 22 Layer 1 skills (`stratos.layer: lifecycle`). A test guards this against the bundle.
LIFECYCLE_SKILLS = [
    "0a-start-session", "0b-stop-session", "0c-handoff", "0d-nightly-consolidation",
    "1a-research", "1b-concept-framing", "1c-concept-map",
    "2a-write-prd", "2b-interface-design", "2c-reconcile-specs",
    "3a-version-planning", "3b-create-issue", "3c-sprint-planning", "3d-implement-issue",
    "3x-jules-dispatch", "3z-afk-loop",
    "4a-verify-and-ship", "4b-audit-architecture-drift", "4c-codebase-health-audit",
    "stratosphere-setup", "stratosphere-update", "sync-skills",
]

SUITE_REMEDIATION = "npx skills add PatN-git/Stratosphere-OS/dist/skills -a <agent> --copy -y"

# Mirrors build/build.py REF_CITE: relative and absolute reference citations.
REF_CITE = re.compile(
    r'\.agents/skills/[a-z0-9-]+/references/([A-Za-z0-9_.-]+\.md)'
    r'|(?<![\w/.])references/([A-Za-z0-9_.-]+\.md)')


def cited_refs(text):
    return {a or b for a, b in REF_CITE.findall(text)}


def frontmatter(text):
    m = re.match(r"^---\r?\n(.*?)\r?\n---", text, re.S)
    return m.group(1) if m else ""


def skill_problems(skill_dir: Path):
    """Reasons an installed skill directory is corrupt; empty list = healthy."""
    md = skill_dir / "SKILL.md"
    if not md.is_file():
        return ["SKILL.md missing"]
    text = md.read_text(encoding="utf-8")
    fm = frontmatter(text)
    problems = []
    if not re.search(rf'^name:\s*["\']?{re.escape(skill_dir.name)}["\']?\s*$', fm, re.M):
        problems.append(f"frontmatter name != directory '{skill_dir.name}'")
    if not re.search(r'^disable-model-invocation:\s*true\s*$', fm, re.M):
        problems.append("frontmatter disable-model-invocation: true missing")
    if not re.search(r'^triggers:\s*\[\s*["\']user["\']\s*\]', fm, re.M):
        problems.append('frontmatter triggers: ["user"] missing')
    sidecar = skill_dir / "agents" / "openai.yaml"
    if not sidecar.is_file() or not re.search(r'allow_implicit_invocation:\s*false', sidecar.read_text(encoding="utf-8")):
        problems.append("agents/openai.yaml sidecar missing or not allow_implicit_invocation: false")
    # Transitive closure, as build.py copies it: a reference may itself cite further references.
    seen, queue = set(), sorted(cited_refs(text))
    while queue:
        name = queue.pop()
        if name in seen:
            continue
        seen.add(name)
        ref = skill_dir / "references" / name
        if not ref.is_file():
            problems.append(f"references/{name} missing")
            continue
        queue.extend(cited_refs(ref.read_text(encoding="utf-8")) - seen)
    return problems


def check_suite(skills_dir: Path):
    missing, corrupt = [], {}
    for name in LIFECYCLE_SKILLS:
        d = skills_dir / name
        if not d.is_dir():
            missing.append(name)
        elif (p := skill_problems(d)):
            corrupt[name] = p
    return missing, corrupt


def cmd_suite(args):
    skills_dir = Path(args.skills_dir) if args.skills_dir else PLUGIN_ROOT.parent
    missing, corrupt = check_suite(skills_dir)
    present = len(LIFECYCLE_SKILLS) - len(missing)
    if not missing and not corrupt:
        print(f"[SUITE OK] {present}/{len(LIFECYCLE_SKILLS)} lifecycle skills present and intact in {skills_dir}")
        return 0
    print(f"[SUITE INCOMPLETE] {present}/{len(LIFECYCLE_SKILLS)} lifecycle skills present in {skills_dir}")
    if missing:
        print(f"Missing ({len(missing)}): " + ", ".join(missing))
    for name, reasons in corrupt.items():
        print(f"Corrupt: {name} - " + "; ".join(reasons))
    print(f"Remediation: {SUITE_REMEDIATION}")
    return 1


def system_pack(registry: Path):
    return sorted(e["name"] for e in json.loads(registry.read_text(encoding="utf-8"))["skills"] if e.get("category") == "system")


def host_skill_dirs(host: str, project: Path, home: Path):
    """Skill directories the running host actually reads. Claude Code does not read `.agents/skills/`."""
    if host == "claude":
        return [project / ".claude" / "skills", home / ".claude" / "skills"]
    return [project / ".agents" / "skills", home / ".agents" / "skills", home / ".gemini" / "config" / "skills"]


def cmd_visibility(args):
    project, home = Path(args.project).resolve(), Path(args.home).expanduser()
    host = args.host if args.host != "auto" else ("claude" if os.environ.get("CLAUDECODE") else "agents")
    visible_dirs = host_skill_dirs(host, project, home)
    invisible = [n for n in system_pack(Path(args.registry)) if not any((d / n / "SKILL.md").is_file() for d in visible_dirs)]
    if not invisible:
        print(f"[VISIBILITY OK] system pack visible to the {host} host")
        return 0
    print(f"[SYSTEM PACK INVISIBLE to {host} host] {', '.join(invisible)}")
    # Present on disk in another host's skills dir? Then a copy fixes it; otherwise fetch it.
    other_dirs = host_skill_dirs("agents" if host == "claude" else "claude", project, home)
    dest_root = visible_dirs[0]  # the project-level skills dir of the running host
    fetch = []
    for name in invisible:
        src = next((d / name for d in other_dirs if (d / name / "SKILL.md").is_file()), None)
        if src is None:
            fetch.append(name)
            continue
        print(f"Remediation ({name}):")
        print(f'  bash:       cp -r "{src}" "{dest_root / name}"')
        print(f'  PowerShell: Copy-Item -Recurse "{src}" "{dest_root / name}"')
    if fetch:
        print(f"Not found on disk: {', '.join(fetch)}. Remediation: run /sync-skills (system pack), then re-run this check.")
    return 1


def legacy_roots(project: Path, home: Path):
    """The project, plus old (pre-canonical-bundle) plugin install roots where stale paths lived."""
    plugin_roots = [project / ".claude" / "plugins" / "stratosphere-os", project / ".agents" / "plugins" / "stratosphere-os",
                    home / ".claude" / "plugins" / "stratosphere-os", home / ".gemini" / "config" / "plugins" / "stratosphere-os"]
    return [project] + [r for r in plugin_roots if r.is_dir()]


def stale_command_files(commands: Path):
    """Old per-lifecycle command/workflow files (`0a_start-session.md` or `0a-start-session.md`); user files never match."""
    return [f for f in sorted(commands.iterdir())
            if f.is_file() and f.suffix == ".md" and f.stem.replace("_", "-") in LIFECYCLE_SKILLS]


def find_legacy(project: Path, home: Path):
    """[(path, files_or_None)]: None = remove the whole directory, else remove only those files."""
    found = []
    for root in legacy_roots(project, home):
        if (root / "dist" / "claude-code").is_dir():
            found.append((root / "dist" / "claude-code", None))
        anti = root / "dist" / "antigravity"  # the current one holds only plugin.json; a payload means the old duplicate tree
        if anti.is_dir() and any((anti / sub).exists() for sub in ("skills", "scripts", "assets")):
            found.append((anti, None))
        if (root / "commands").is_dir() and (files := stale_command_files(root / "commands")):
            found.append((root / "commands", files))
    return found


def cmd_legacy(args):
    found = find_legacy(Path(args.project).resolve(), Path(args.home).expanduser())
    if not found:
        print("[LEGACY OK] no pre-canonical-bundle paths found")
        return 0
    print(f"[LEGACY PATHS FOUND] {len(found)}")
    for path, files in found:
        print(f"  {path}" + (f"  (files: {', '.join(f.name for f in files)})" if files else ""))
    if not args.apply:
        print("Nothing deleted. After the user confirms, re-run with --apply.")
        return 1
    for path, files in found:
        if files is None:
            shutil.rmtree(path)
        else:
            for f in files:
                f.unlink()
            if not any(path.iterdir()):
                path.rmdir()
        print(f"Removed: {path}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    location = argparse.ArgumentParser(add_help=False)
    location.add_argument("--project", default=".")
    location.add_argument("--home", default="~")
    p = sub.add_parser("suite")
    p.add_argument("--skills-dir", help="skills directory to check (default: the one holding this script's skill)")
    p.set_defaults(fn=cmd_suite)
    p = sub.add_parser("visibility", parents=[location])
    p.add_argument("--host", choices=["claude", "agents", "auto"], default="auto")
    p.add_argument("--registry", default=str(PLUGIN_ROOT / "external-skills.json"))
    p.set_defaults(fn=cmd_visibility)
    p = sub.add_parser("legacy", parents=[location])
    p.add_argument("--apply", action="store_true", help="delete what was found (only after user confirmation)")
    p.set_defaults(fn=cmd_legacy)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
