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
import hashlib
import json
import os
import shutil
import stat
import sys
import tempfile
import time
import urllib.request
from urllib.request import Request
import zipfile
from pathlib import Path

PLACEHOLDER_URLS = {"", "TODO", "PENDING", "N/A"}

# Global caching dictionary for zip files
zip_cache = {}


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


def get_file_sha256(path):
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def force_rmtree(path: Path):
    if not path.exists():
        return
    
    def remove_readonly(func, p, excinfo):
        try:
            os.chmod(p, stat.S_IWRITE)
            func(p)
        except Exception:
            pass

    # Clear read-only flags recursively including the directory itself
    try:
        path.chmod(stat.S_IWRITE)
    except Exception:
        pass
    for p in list(path.rglob("*")):
        try:
            p.chmod(stat.S_IWRITE)
        except Exception:
            pass

    # Retry rmtree a few times to handle Windows lock delays
    for attempt in range(5):
        try:
            shutil.rmtree(path, onerror=remove_readonly)
            if not path.exists():
                return
        except Exception:
            pass
        time.sleep(0.2)
    # If still exists, throw the original error by calling it once more
    shutil.rmtree(path, onerror=remove_readonly)


def check_lockfile(root, chosen_skills, lockfile_path, force):
    if force or not lockfile_path.exists():
        return True, []

    try:
        lock_data = json.loads(lockfile_path.read_text(encoding="utf-8"))
    except Exception:
        return True, []

    lock_skills = lock_data.get("skills", {})
    modified_files = []

    for entry in chosen_skills:
        name = entry.get("name")
        target = entry.get("targetPath")
        if not target:
            continue
        
        target_dir = Path(root) / target
        if not target_dir.exists():
            continue
        
        skill_lock = lock_skills.get(name)
        if not skill_lock:
            # If target_dir exists but is not tracked by the lockfile,
            # list its files to prevent accidental overwriting.
            for p in target_dir.rglob("*"):
                if p.is_file():
                    rel = p.relative_to(target_dir).as_posix()
                    modified_files.append(f"{target}/{rel} (untracked)")
            continue

        lock_files = skill_lock.get("files", {})
        for rel_path, expected_hash in lock_files.items():
            full_path = target_dir / rel_path
            if not full_path.exists():
                modified_files.append(f"{target}/{rel_path} (deleted)")
            else:
                current_hash = get_file_sha256(full_path)
                if current_hash != expected_hash:
                    modified_files.append(f"{target}/{rel_path} (modified)")

    if modified_files:
        return False, modified_files
    return True, []


def update_lockfile(root, entry, lockfile_path, ref):
    name = entry.get("name")
    target = entry.get("targetPath")
    target_dir = Path(root) / target
    
    files_hashes = {}
    if target_dir.exists():
        for p in target_dir.rglob("*"):
            if p.is_file():
                rel = p.relative_to(target_dir).as_posix()
                h = get_file_sha256(p)
                if h:
                    files_hashes[rel] = h

    lock_data = {"skills": {}}
    if lockfile_path.exists():
        try:
            lock_data = json.loads(lockfile_path.read_text(encoding="utf-8"))
            if "skills" not in lock_data:
                lock_data["skills"] = {}
        except Exception:
            pass

    lock_data["skills"][name] = {
        "ref": ref or "",
        "files": files_hashes
    }

    lockfile_path.parent.mkdir(parents=True, exist_ok=True)
    lockfile_path.write_text(json.dumps(lock_data, indent=2), encoding="utf-8")


def download_url(url, retries=2, delay=2):
    req = Request(
        url,
        headers={"User-Agent": "stratosphere-os"}
    )
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read()
        except Exception as exc:
            if attempt == retries - 1:
                raise exc
            time.sleep(delay * (2 ** attempt))


def get_cached_zip(url):
    if url in zip_cache:
        return zip_cache[url]
    
    data = download_url(url)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
        tmp.write(data)
        zip_path = tmp.name
    
    zip_cache[url] = zip_path
    return zip_path


def get_real_subpath(zip_file_obj, sub_path):
    namelist = zip_file_obj.namelist()
    if not namelist:
        return sub_path
    
    first_member = namelist[0]
    zip_root = first_member.split('/')[0] + '/'
    
    sub_path_parts = sub_path.strip("/").split("/")
    if len(sub_path_parts) > 1:
        real_sub = zip_root + "/".join(sub_path_parts[1:]) + "/"
    else:
        real_sub = zip_root
    return real_sub


def fetch(entry, root, dry, lockfile_path):
    name = entry.get("name")
    url = entry.get("repoZipUrl")
    ref = entry.get("ref")
    sub = entry.get("subPath", "")
    target = entry.get("targetPath")
    
    if not url or url in PLACEHOLDER_URLS:
        return "skip", f"{name}: no valid repoZipUrl ({url!r}) — fix the registry entry"
    if not target:
        return "skip", f"{name}: no targetPath in registry"

    if ref:
        if "/archive/" in url:
            base = url.split("/archive/")[0]
            url = f"{base}/archive/{ref}.zip"

    if dry:
        return "dry", f"{name}: would pull {url} [{sub}] -> {target}"

    target_dir = Path(root) / target
    try:
        zip_path = get_cached_zip(url)
        
        with zipfile.ZipFile(zip_path) as z:
            real_sub = get_real_subpath(z, sub)
            
            with tempfile.TemporaryDirectory() as tmpdir:
                temp_target = Path(tmpdir) / "extracted"
                temp_target.mkdir(parents=True, exist_ok=True)
                
                count = 0
                for member in z.infolist():
                    if not member.filename.startswith(real_sub):
                        continue
                    rel = member.filename[len(real_sub):]
                    if not rel or member.is_dir():
                        continue
                    dest = temp_target / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    with z.open(member) as srcf, open(dest, "wb") as dstf:
                        shutil.copyfileobj(srcf, dstf)
                    count += 1
                
                if count == 0:
                    return "warn", f"{name}: 0 files matched subPath {sub!r} (resolved as {real_sub!r}) — check the path"
                
                target_dir.parent.mkdir(parents=True, exist_ok=True)
                if target_dir.exists():
                    force_rmtree(target_dir)
                for attempt in range(5):
                    try:
                        shutil.move(str(temp_target), str(target_dir))
                        break
                    except Exception as exc:
                        if attempt == 4:
                            raise exc
                        time.sleep(0.2)
                
        update_lockfile(root, entry, lockfile_path, ref)
        return "ok", f"{name}: {count} files -> {target}"
    except Exception as exc:
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
    ap.add_argument("--project-root", default=str(Path.cwd()), help="path to project root directory")
    ap.add_argument("--force", action="store_true", help="force overwrite even if files are modified locally")
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

    project_root = Path(args.project_root).resolve()
    skills_base = project_root / ".agents" / "skills"
    
    print(f"Project root: {project_root}")
    print(f"Skills destination directory: {skills_base}")
    
    try:
        skills_base.mkdir(parents=True, exist_ok=True)
        # Test write access
        dummy = skills_base / ".write_test"
        dummy.write_text("test", encoding="utf-8")
        dummy.unlink()
    except Exception as exc:
        print(f"Error: Target directory {skills_base} is not writable or cannot be created: {exc}")
        sys.exit(1)

    lockfile_path = skills_base / ".lock.json"
    ok, modified = check_lockfile(project_root, chosen, lockfile_path, args.force)
    if not ok:
        print("Error: The following files have been modified locally. Use --force to overwrite:")
        for m in modified:
            print(f"  {m}")
        sys.exit(1)

    results = {}
    try:
        for entry in chosen:
            status, msg = fetch(entry, project_root, args.dry_run, lockfile_path)
            results.setdefault(status, []).append(msg)
            print(f"[{status.upper()}] {msg}")
    finally:
        # Clean up temp files
        for path in zip_cache.values():
            try:
                Path(path).unlink(missing_ok=True)
            except Exception:
                pass

    if results.get("fail"):
        sys.exit(1)


if __name__ == "__main__":
    main()
