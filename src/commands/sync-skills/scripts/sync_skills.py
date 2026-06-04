import os
import json
import argparse
import tempfile
import zipfile
import urllib.request
import shutil
from datetime import datetime
from pathlib import Path

def get_skill_metadata(skill_path):
    """Deterministic parsing of SKILL.md and folder structure without external dependencies."""
    metadata = {
        "id": os.path.basename(skill_path),
        "name": os.path.basename(skill_path),
        "description": "",
        "lastUpdated": datetime.fromtimestamp(os.path.getmtime(skill_path)).isoformat()
    }
     
def sync_external_skill(entry, workspace_root):
    """Download and surgically extract an external skill from GitHub."""
    name = entry.get("name")
    url = entry.get("repoZipUrl")
    sub_path = entry.get("subPath")
    target_rel = entry.get("targetPath")
    
    if not url or url == "PENDING" or url == "N/A":
        return False, "No valid repoZipUrl provided."

    target_dir = Path(workspace_root) / target_rel
    print(f"  -> Pulling {name} from {url}...")
    
    try:
        # 1. Download to temp file
        with urllib.request.urlopen(url) as response:
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                shutil.copyfileobj(response, tmp_file)
                temp_zip_path = tmp_file.name

        # 2. Extract surgically
        with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
            for member in zip_ref.infolist():
                if member.filename.startswith(sub_path):
                    # Get relative path within the skill folder
                    rel_filename = member.filename[len(sub_path):]
                    if not rel_filename: continue
                    
                    target_file = target_dir / rel_filename
                    
                    # Create parent directories
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Extract file
                    if not member.is_dir():
                        with zip_ref.open(member) as source, open(target_file, "wb") as target:
                            shutil.copyfileobj(source, target)
        
        os.unlink(temp_zip_path)
        return True, "Success"
    except Exception as e:
        return False, str(e)

def atomic_write_json(file_path, data):
    """Atomically write JSON to prevent corruption."""
    temp_fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(file_path), text=True)
    try:
        with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        os.replace(temp_path, file_path)
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise e

def main():
    parser = argparse.ArgumentParser(description="Reconcile installed skills with skills.json")
    parser.add_argument("--skills-dir", default=".agents/workflows", help="Directory containing installed skills")
    parser.add_argument("--config", default="", help="Path to skills.json (defaults to sibling of script)")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    parser.add_argument("--llm", action="store_true", help="Enable optional LLM assistance")
    parser.add_argument("--local", nargs="*", default=["sync-skills", "instantiation-memory"], help="Skills to treat as local-only (no repo sync)")
    parser.add_argument("--pull", action="store_true", help="Download external skills from GitHub")
    parser.add_argument("--summary", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    skills_dir = Path(args.skills_dir)
    # Default config path to sibling of script if not provided
    config_path = Path(args.config) if args.config else Path(__file__).parent.parent / "skills.json"
    local_only_names = set(args.local)
    workspace_root = Path(os.getcwd())

    # Greenfield: Create structures if missing
    if not skills_dir.exists():
        print(f"Greenfield: Creating {skills_dir}")
        if not args.dry_run:
            skills_dir.mkdir(parents=True, exist_ok=True)
            (skills_dir / "README.md").write_text("Installed skills repository.")

    if not config_path.exists():
        print(f"Greenfield: Creating {config_path}")
        if not args.dry_run:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            atomic_write_json(str(config_path), [])

    # Load existing config
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            skills_json = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        skills_json = []

    # Inventory disk
    disk_skills = {}
    if skills_dir.exists():
        for item in skills_dir.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                disk_skills[item.name] = get_skill_metadata(item)

    # Reconciliation logic
    summary = {
        "updated": [],
        "orphans": [],
        "missing": [],
        "flagged": []
    }

    new_config = []
    managed_ids = {} # map targetPath-basename to entry

    # 1. Process existing config
    for entry in skills_json:
        target_path = entry.get("targetPath", "")
        skill_id = os.path.basename(target_path) if target_path else entry.get("name")
        
        if not skill_id:
            summary["flagged"].append("Malformed entry (no name/targetPath)")
            continue

        if skill_id in managed_ids:
            summary["flagged"].append(f"Duplicate entry in JSON: {skill_id}")
            continue
            
        managed_ids[skill_id] = entry
        
        if skill_id in disk_skills:
            disk_meta = disk_skills[skill_id]
            
            # Update status if it's in the local-only list
            if skill_id in local_only_names:
                entry["status"] = "local"
                entry["repoZipUrl"] = "N/A"
                entry["subPath"] = "N/A"
            
            # Brownfield check: Out of sync?
            last_seen = entry.get("lastSeen")
            if last_seen and disk_meta["lastUpdated"] > last_seen:
                summary["flagged"].append(f"Skill '{skill_id}' has local changes (updated {disk_meta['lastUpdated']})")
            
            # Update metadata
            entry["lastSeen"] = disk_meta["lastUpdated"]
            if disk_meta["description"] and (not entry.get("description") or args.llm):
                entry["description"] = disk_meta["description"]
            
            # Naming convention check
            if not disk_meta["standard_name"]:
                summary["flagged"].append(f"Non-standard naming: {skill_id} (found SKILL.md, expected {disk_meta['correct_name']})")
                if not args.dry_run:
                    old_p = skills_dir / skill_id / "SKILL.md"
                    if old_p.exists():
                        new_p = skills_dir / skill_id / disk_meta["correct_name"]
                        print(f"  -> Renaming {old_p.name} to {new_p.name}...")
                        try:
                            old_p.rename(new_p)
                        except FileExistsError:
                            print(f"  [!] Note: {new_p.name} already exists. Removing redundant {old_p.name}...")
                            old_p.unlink()
                    else:
                        print(f"  [!] Warning: {skill_id} is non-standard but no SKILL.md found to rename.")

            new_config.append(entry)
            status_suffix = f" ({entry.get('status', 'managed')})"
            summary["updated"].append(f"{skill_id}{status_suffix}")
        else:
            summary["missing"].append(skill_id)
            entry["status"] = "missing_locally"
            new_config.append(entry)

    # 2. Find orphans
    for skill_id, meta in disk_skills.items():
        if skill_id not in managed_ids:
            # Naming convention check for orphans
            if not meta["standard_name"]:
                summary["flagged"].append(f"Non-standard naming: {skill_id} (found SKILL.md, expected {meta['correct_name']})")
                if not args.dry_run:
                    old_p = skills_dir / skill_id / "SKILL.md"
                    new_p = skills_dir / skill_id / meta["correct_name"]
                    print(f"  -> Renaming {old_p.name} to {new_p.name}...")
                    old_p.rename(new_p)

            is_local = skill_id in local_only_names
            if is_local:
                status = "local"
                summary["updated"].append(f"{skill_id} (local)")
            else:
                status = "orphan"
                summary["orphans"].append(skill_id)
                
            new_entry = {
                "name": meta["name"],
                "repoZipUrl": "N/A" if is_local else "PENDING",
                "subPath": "N/A" if is_local else f"repo-main/skills/{skill_id}/",
                "targetPath": f"{args.skills_dir}/{skill_id}",
                "lastSeen": meta["lastUpdated"],
                "status": status,
                "description": meta["description"]
            }
            new_config.append(new_entry)

    # Final Output
    if args.summary == "json":
        print(json.dumps({**summary, "config_path": str(config_path)}, indent=2))
    else:
        print("\n--- Skill Reconciliation Summary ---")
        print(f"Total Managed: {len(managed_ids)}")
        print(f"Updated:       {len(summary['updated'])}")
        print(f"Missing (Loc): {len(summary['missing'])}")
        print(f"Orphans (New): {len(summary['orphans'])}")
        print(f"Flagged:       {len(summary['flagged'])}")
        
        if summary["orphans"]:
            print("\n[!] NEW SKILLS FOUND ON DISK:")
            for o in summary["orphans"]: print(f"  - {o}")
            
        if summary["flagged"]:
            print("\n[!] ATTENTION REQUIRED:")
            for f in summary["flagged"]: print(f"  - {f}")
            
        if summary["missing"]:
            print("\n[?] MISSING LOCALLY (defined in JSON but not found):")
            for m in summary["missing"]: print(f"  - {m}")
        print("\n-----------------------------------\n")

    if args.pull:
        print("\n--- Pulling External Skills ---")
        for entry in new_config:
            if entry.get("status") != "local":
                if args.dry_run:
                    print(f"[DRY RUN] Would pull {entry.get('name')} from {entry.get('repoZipUrl')}")
                else:
                    success, msg = sync_external_skill(entry, workspace_root)
                    if not success:
                        print(f"  [!] Failed to pull {entry.get('name')}: {msg}")
                    else:
                        print(f"  [OK] Updated {entry.get('name')}")
        print("-------------------------------\n")

    if not args.dry_run:
        atomic_write_json(str(config_path), new_config)
        print(f"Successfully updated {config_path}")
    else:
        print("[DRY RUN] No files were modified.")

if __name__ == "__main__":
    main()
