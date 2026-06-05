#!/usr/bin/env python3
"""Fetch StratosphereOS external skills on demand from external-skills.json.

external-skills.json (shipped at the plugin root) is the SINGLE source of truth
for third-party skills. This script only downloads + surgically extracts the
selected skills into the project at each entry's targetPath. It never rewrites
the registry and never audits local skills — that keeps it safe to run inside
the installer.

Run from the project root:
  python sync_skills.py --list
  python sync_skills.py --default                  # system skills (default: true)
  python sync_skills.py --category database web     # everything in those categories
  python sync_skills.py --only supabase impeccable  # exact names
  python sync_skills.py --all
Add --dry-run to preview without downloading.
"""
import argparse
import json
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

PLACEHOLDER_URLS = {"", "TODO", "PENDING", "N/A"}


def load_registry(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    # Accept either {"skills": [...]} or a bare list.
    return data.get("skills", []) if isinstance(data, dict) else data


def select(skills, args):
    chosen = []
    if args.all:
        chosen = list(skills)
    else:
        if args.default:
            chosen += [s for s in skills if s.get("default")]
        if args.category:
            cats = set(args.category)
            chosen += [s for s in skills if s.get("category") in cats]
        if args.only:
            names = set(args.only)
            chosen += [s for s in skills if s.get("name") in names]
    seen, out = set(), []
    for s in chosen:
        if s.get("name") not in seen:
            seen.add(s.get("name"))
            out.append(s)
    return out


def fetch(entry, root, dry):
    name = entry.get("name")
    url = entry.get("repoZipUrl")
    sub = entry.get("subPath", "")
    target = entry.get("targetPath")
    if not url or url in PLACEHOLDER_URLS:
        return "skip", f"{name}: no valid repoZipUrl ({url!r}) — fix the registry entry"
    if not target:
        return "skip", f"{name}: no targetPath in registry"
    if dry:
        return "dry", f"{name}: would pull {url} [{sub}] -> {target}"

    target_dir = Path(root) / target
    try:
        with urllib.request.urlopen(url) as resp:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
                shutil.copyfileobj(resp, tmp)
                zip_path = tmp.name
        count = 0
        with zipfile.ZipFile(zip_path) as z:
            for member in z.infolist():
                if not member.filename.startswith(sub):
                    continue
                rel = member.filename[len(sub):]
                if not rel or member.is_dir():
                    continue
                dest = target_dir / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                with z.open(member) as srcf, open(dest, "wb") as dstf:
                    shutil.copyfileobj(srcf, dstf)
                count += 1
        Path(zip_path).unlink(missing_ok=True)
        if count == 0:
            return "warn", f"{name}: 0 files matched subPath {sub!r} — check the path"
        return "ok", f"{name}: {count} files -> {target}"
    except Exception as exc:  # noqa: BLE001 - report any network/zip error to the user
        return "fail", f"{name}: {exc}"


def main():
    here = Path(__file__).resolve().parent
    default_registry = here.parent / "external-skills.json"
    ap = argparse.ArgumentParser(description="Fetch external StratosphereOS skills from external-skills.json")
    ap.add_argument("--registry", default=str(default_registry),
                    help="path to external-skills.json (default: sibling of scripts/)")
    ap.add_argument("--list", action="store_true", help="list registry entries and exit")
    ap.add_argument("--default", action="store_true", help="select entries marked default: true")
    ap.add_argument("--category", nargs="*", help="select by category (database web mobile design system)")
    ap.add_argument("--only", nargs="*", help="select by exact name")
    ap.add_argument("--all", action="store_true", help="select every entry")
    ap.add_argument("--dry-run", action="store_true", help="preview without downloading")
    args = ap.parse_args()

    skills = load_registry(args.registry)

    if args.list:
        for s in skills:
            flag = "*" if s.get("default") else " "
            print(f" {flag} {s.get('name',''):<34} [{s.get('category','-'):<8}] {s.get('description','')}")
        print("\n(* = installed by default)")
        return

    chosen = select(skills, args)
    if not chosen:
        print("Nothing selected. Use --default / --category / --only / --all, or --list to see options.")
        return

    root = Path.cwd()
    results = {}
    for entry in chosen:
        status, msg = fetch(entry, root, args.dry_run)
        results.setdefault(status, []).append(msg)
        print(f"[{status.upper()}] {msg}")

    if results.get("fail"):
        sys.exit(1)


if __name__ == "__main__":
    main()
