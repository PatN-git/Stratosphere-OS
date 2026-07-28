import os
import sys
import subprocess
from pathlib import Path

def test_validate_memory():
    print("--- Testing validate_memory.py ---")
    tmp_mem = Path(".tmp/dummy_memory")
    tmp_mem.mkdir(parents=True, exist_ok=True)
    # Write a fake memory file with a secret
    (tmp_mem / "fake.md").write_text("Hello\nSecret: sk-123456789012345678901234567890123456789012345678\nWorld", encoding="utf-8")
    
    # Run validate_memory.py from dist/antigravity/scripts/
    result = subprocess.run([sys.executable, "dist/antigravity/scripts/validate_memory.py", "--path", str(tmp_mem)], capture_output=True, text=True)
    print("Exit code:", result.returncode)
    if result.returncode == 1 and "Secret detected" in result.stdout:
        print("validate_memory test passed!")
        return True
    else:
        print("validate_memory test failed! Output:\n", result.stdout, result.stderr)
        return False

def test_validate_memory_backlog():
    print("\n--- Testing validate_memory.py Backlog checks ---")
    tmp_mem = Path(".tmp/dummy_memory_backlog")
    if tmp_mem.exists():
        shutil.rmtree(tmp_mem, ignore_errors=True)
    tmp_mem.mkdir(parents=True, exist_ok=True)
    
    backlog_content = """---
type: backlog
title: Backlog Map
description: Test
timestamp: 2026-06-18
version: "1.1.1"
---
# BACKLOG MAP

## Rules
- Dummy rule

## Label Registry
- **Primary Type (`type:<class>`)**: `type:feature`
- **Execution Mode (`mode:<mode>`)**: `mode:HITL`, `mode:AFK`
- **Tier (`tier:<tier>`)**: `tier:epic`, `tier:slice`

## Backlog

| ID | Title | Status | Labels | Milestone | Dependencies | ICE | Ref |
|:---|:---|:---|:---|:---|:---|:---|:---|
| BT-059-01 | Hierarchical | planned | type:feature, mode:HITL | v1.0.0 | — | — | — |
| BT-060 | Missing primary type | in progress | mode:HITL, tier:slice, size:medium | v1.0.0 | — | — | — |
| BT-061 | Missing execution mode | in progress | type:feature, tier:slice, size:medium | v1.0.0 | — | — | — |
| BT-062 | Fully valid slice | in progress | type:feature, mode:HITL, tier:slice, size:medium | v1.0.0 | — | — | — |
| BT-063 | Parent feature is ignored | in progress | type:feature, tier:epic | v1.0.0 | — | — | — |
| BT-064 | Needs spec row exempt | needs_spec | size:medium | v1.0.0 | — | — | — |
| BT-065 | Planned row exempt | planned | size:medium | v1.0.0 | — | — | — |
| BT-066 | Leftover needs_spec invalid primary | in progress | type:NEEDS_SPEC, mode:AFK, tier:slice, size:medium | v1.0.0 | — | — | — |
| BT-067 | Epic with size | in progress | type:feature, tier:epic, size:large | v1.0.0 | — | — | — |
| BT-068 | Leaf with legacy type:AFK | in progress | type:feature, type:AFK, tier:slice, size:medium | v1.0.0 | — | — | — |
| BT-069 | Active concept map | in progress | concept:map, status:in progress | v1.0.0 | — | — | — |
"""
    (tmp_mem / "BACKLOG_MAP.md").write_text(backlog_content, encoding="utf-8")
    
    result = subprocess.run([sys.executable, "dist/antigravity/scripts/validate_memory.py", "--path", str(tmp_mem)], capture_output=True, text=True)
    print("Exit code:", result.returncode)
    
    # Assertions
    passed = True
    if result.returncode != 1:
        print("Error: Expected exit code 1, got", result.returncode)
        passed = False
        
    expected_errors = [
        "Invalid Backlog ID format 'BT-059-01'",
        "Slice 'BT-060'",
        "is missing a Primary Type label",
        "Slice 'BT-061'",
        "is missing an Execution Mode label",
        "Slice 'BT-066'",
        "is missing a Primary Type label",
        "Epic 'BT-067'",
        "must not carry size: labels",
        "Slice 'BT-068'",
        "is missing an Execution Mode label"
    ]
    
    for err in expected_errors:
        if err not in result.stdout:
            print(f"Error: Expected to find '{err}' in output, but did not. Output:\n", result.stdout)
            passed = False
            
    unexpected_errors = [
        "BT-062",
        "BT-063",
        "BT-064",
        "BT-065",
        "BT-069"
    ]
    for uerr in unexpected_errors:
        if uerr in result.stdout and ("missing" in result.stdout or "Invalid" in result.stdout or "must not" in result.stdout) and f"'{uerr}'" in result.stdout:
            print(f"Error: Unexpected error reported for '{uerr}'. Output:\n", result.stdout)
            passed = False
            
    if passed:
        print("validate_memory backlog checks passed!")
    return passed

def test_sync_skills():
    print("\n--- Testing sync_skills.py ---")
    # Run sync_skills.py from dist/antigravity/scripts/
    result = subprocess.run([sys.executable, "dist/antigravity/scripts/sync_skills.py", "--list"], capture_output=True, text=True)
    print("Exit code:", result.returncode)
    if result.returncode == 0:
        print("sync_skills.py test passed!")
        return True
    else:
        print("sync_skills.py test failed! Output:\n", result.stderr)
        return False

def test_scaffold():
    print("\n--- Testing scaffold.py ---")
    # Run scaffold.py from dist/antigravity/scripts/
    result = subprocess.run([sys.executable, "dist/antigravity/scripts/scaffold.py", "--dry-run"], capture_output=True, text=True)
    print("Exit code:", result.returncode)
    if result.returncode == 0:
        print("scaffold.py test passed!")
        return True
    else:
        print("scaffold.py test failed! Output:\n", result.stderr)
        return False

import shutil

def test_scaffold_repair_lock():
    print("\n--- Testing scaffold.py --repair-lock ---")
    repo_root = Path(__file__).resolve().parent.parent
    scaffold_script = repo_root / "dist" / "antigravity" / "scripts" / "scaffold.py"
    
    # Create temp directory inside repo's .tmp/ for testing
    tmp_project = repo_root / ".tmp" / "repair_lock_test_project"
    if tmp_project.exists():
        shutil.rmtree(tmp_project, ignore_errors=True)
    tmp_project.mkdir(parents=True, exist_ok=True)
    
    try:
        # Step 1: Run normal scaffolding first to set up files
        scaffold_res = subprocess.run(
            [sys.executable, str(scaffold_script)],
            cwd=str(tmp_project),
            capture_output=True,
            text=True
        )
        print("Scaffold install exit code:", scaffold_res.returncode)
        if scaffold_res.returncode != 0:
            print("scaffold.py install failed! Output:\n", scaffold_res.stderr)
            return False
            
        # Step 2: Run repair-lock dry-run
        repair_res = subprocess.run(
            [sys.executable, str(scaffold_script), "--repair-lock", "--dry-run"],
            cwd=str(tmp_project),
            capture_output=True,
            text=True
        )
        print("Repair dry-run exit code:", repair_res.returncode)
        if repair_res.stdout:
            print("Stdout snippet:", repair_res.stdout.strip().splitlines()[-1])
        
        if repair_res.returncode != 0:
            print("scaffold.py --repair-lock failed! Output:\n", repair_res.stderr)
            return False
            
        # Step 3: Assertions
        if "artifacts" not in repair_res.stdout:
            print("scaffold.py --repair-lock output did not mention 'artifacts'. Output:\n", repair_res.stdout)
            return False
            
        if " 0 artifacts" in repair_res.stdout:
            print("scaffold.py --repair-lock processed 0 artifacts! It should have matched the scaffolded project files. Output:\n", repair_res.stdout)
            return False
            
        print("scaffold.py --repair-lock test passed!")
        return True
    finally:
        # Clean up temp project directory
        if tmp_project.exists():
            shutil.rmtree(tmp_project, ignore_errors=True)

def test_update_flow():
    print("\n--- Testing in-place update E2E pipeline ---")
    repo_root = Path(__file__).resolve().parent.parent
    result = subprocess.run([sys.executable, "tests/test_update_flow.py"], cwd=str(repo_root), capture_output=True, text=True)
    print("Exit code:", result.returncode)
    sys.stdout.flush()
    if result.returncode == 0:
        print("Update E2E pipeline test passed!")
        return True
    else:
        print("Update E2E pipeline test failed! Output:\n", result.stdout, result.stderr)
        sys.stdout.flush()
        sys.stderr.flush()
        raise AssertionError(f"test_update_flow.py failed with exit code {result.returncode}.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")

def test_update_preflight():
    print("\n--- Testing update preflight instructions ---")
    repo_root = Path(__file__).resolve().parent.parent
    result = subprocess.run([sys.executable, "tests/test_update_preflight.py"], cwd=str(repo_root), capture_output=True, text=True)
    print("Exit code:", result.returncode)
    sys.stdout.flush()
    if result.returncode == 0:
        print("update_preflight instructions test passed!")
        return True
    else:
        print("update_preflight instructions test failed! Output:\n", result.stdout, result.stderr)
        return False

def test_orphan_guard():
    print("\n--- Testing Orphan-Guard Anti-Recurrence Check ---")
    repo_root = Path(__file__).resolve().parent.parent
    scaffold_script = repo_root / "dist" / "antigravity" / "scripts" / "scaffold.py"
    
    # 1. Add dist/antigravity/scripts to sys.path so we can import scaffold
    sys.path.insert(0, str(repo_root / "dist" / "antigravity" / "scripts"))
    import scaffold
    
    # Define EXCLUDE lists
    EXCLUDED_PLUGINS_METADATA = {
        "plugin.json",
        "versions.json",
        "external-skills.json",
    }
    
    # Helper to scan and map dist files
    dist_dir = repo_root / "dist" / "antigravity"
    
    # We will build two fixtures
    # Fixture 1: "no board"
    tmp_no_board = repo_root / ".tmp" / "fixture_no_board"
    if tmp_no_board.exists():
        shutil.rmtree(tmp_no_board, ignore_errors=True)
    tmp_no_board.mkdir(parents=True, exist_ok=True)
    
    # Fixture 2: "with board" (opted-in)
    tmp_with_board = repo_root / ".tmp" / "fixture_with_board"
    if tmp_with_board.exists():
        shutil.rmtree(tmp_with_board, ignore_errors=True)
    tmp_with_board.mkdir(parents=True, exist_ok=True)
    
    try:
        # Run normal scaffold on both
        sc1 = subprocess.run([sys.executable, str(scaffold_script)], cwd=str(tmp_no_board), capture_output=True, text=True)
        if sc1.returncode != 0:
            print("Scaffold on Fixture 1 failed:", sc1.stderr)
            return False
            
        sc2 = subprocess.run([sys.executable, str(scaffold_script)], cwd=str(tmp_with_board), capture_output=True, text=True)
        if sc2.returncode != 0:
            print("Scaffold on Fixture 2 failed:", sc2.stderr)
            return False
            
        # For Fixture 2, simulate setup's board step (conditional install of sync-labels Action)
        action_dst = tmp_with_board / ".github" / "workflows" / "sync-labels-to-project.yml"
        action_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(dist_dir / "assets" / "templates" / "github" / "sync-labels-to-project.yml", action_dst)
        
        # Run update on Fixture 2 so it is lockfile tracked/updated
        up2 = subprocess.run([sys.executable, str(scaffold_script), "--update"], cwd=str(tmp_with_board), capture_output=True, text=True)
        if up2.returncode != 0:
            print("Scaffold update on Fixture 2 failed:", up2.stderr)
            return False
            
        # Walk and check every file in dist/antigravity
        failures = []
        for p in dist_dir.rglob("*"):
            if not p.is_file():
                continue
            
            rel = p.relative_to(dist_dir)
            rel_str = rel.as_posix()
            
            # Check exclusions
            if "__pycache__" in rel.parts or rel_str.endswith(".pyc"):
                continue
            if rel_str == "scripts/sync_skills.py":
                # sync_skills.py is run within plugin scope by sync-skills command; never copied to project
                continue
            if rel_str.startswith("skills/"):
                # Skills are on-demand and third-party, gitignored. Documented exclude.
                continue
            if rel_str.startswith("scripts/_versioning.py") or rel_str.startswith("scripts/scaffold.py"):
                # Scaffold script itself lives in plugin/scripts, not copied to project root
                continue
            if rel_str in EXCLUDED_PLUGINS_METADATA:
                continue
                
            # Determine expected project destination
            proj_rel_path = None
            if rel_str.startswith("assets/templates/") or rel_str.startswith("workflows/") or rel_str.startswith("commands/"):
                proj_rel_path = scaffold.map_bundled_to_project(rel_str)
            elif rel_str == "scripts/validate_memory.py":
                proj_rel_path = ".agents/scripts/validate_memory.py"
            elif rel_str == "scripts/reconcile.py":
                proj_rel_path = ".agents/scripts/reconcile.py"
            elif rel_str == "scripts/okf_view.py":
                proj_rel_path = ".agents/scripts/okf_view.py"
            elif rel_str.startswith("scripts/design/"):
                if "test" in rel.parts:
                    continue # skip design tests
                proj_rel_path = f".agents/scripts/design/{rel.relative_to('scripts/design').as_posix()}"
            elif rel_str.startswith("scripts/okf_viewer/"):
                proj_rel_path = f".agents/scripts/okf_viewer/{rel.relative_to('scripts/okf_viewer').as_posix()}"
                
            if not proj_rel_path:
                failures.append(f"Bundled file '{rel_str}' has no mapping to the project root and is not excluded.")
                continue
                
            # Verify existence in the fixtures
            # 1. No Board Fixture
            p_no_board = tmp_no_board / proj_rel_path
            if proj_rel_path == ".github/workflows/sync-labels-to-project.yml":
                # Excluded on no-board fixture because not opted-in
                if p_no_board.exists():
                    failures.append(f"Optional action '{proj_rel_path}' exists in 'no board' project, but shouldn't.")
            else:
                if not p_no_board.exists():
                    failures.append(f"Bundled file '{rel_str}' (expected at '{proj_rel_path}') is missing from 'no board' project.")
                    
            # 2. With Board Fixture (opted-in)
            p_with_board = tmp_with_board / proj_rel_path
            if not p_with_board.exists():
                failures.append(f"Bundled file '{rel_str}' (expected at '{proj_rel_path}') is missing from 'with board' project.")
                
        # Verify gitignore/gitattributes reconciliation
        for fixture_path, name in [(tmp_no_board, "no board"), (tmp_with_board, "with board")]:
            gi_file = fixture_path / ".gitignore"
            if not gi_file.exists():
                failures.append(f".gitignore is missing from {name} project.")
            else:
                gi_content = gi_file.read_text(encoding="utf-8")
                if "*.work.md" not in gi_content:
                    failures.append(f"*.work.md missing from reconciled .gitignore in {name} project.")
                    
            ga_file = fixture_path / ".gitattributes"
            if not ga_file.exists():
                failures.append(f".gitattributes is missing from {name} project.")
            else:
                ga_content = ga_file.read_text(encoding="utf-8")
                if "docs/okf-view.html linguist-generated=true -diff" not in ga_content:
                    failures.append(f"Linguist attributes missing from reconciled .gitattributes in {name} project.")
                
        if failures:
            print("Orphan Guard failed! Unresolved / mismatched files:")
            for f in failures:
                print("  *", f)
            return False
            
        print("Orphan-Guard verification passed! No framework orphans found.")
        return True
        
    finally:
        # Cleanup
        shutil.rmtree(tmp_no_board, ignore_errors=True)
        shutil.rmtree(tmp_with_board, ignore_errors=True)

if __name__ == "__main__":
    success = True
    if not test_validate_memory():
        success = False
    if not test_validate_memory_backlog():
        success = False
    if not test_sync_skills():
        success = False
    if not test_scaffold():
        success = False
    if not test_scaffold_repair_lock():
        success = False
    if not test_update_preflight():
        success = False
    if not test_update_flow():
        success = False
    if not test_orphan_guard():
        success = False
        
    if success:
        print("\nAll script verification tests passed.")
        sys.exit(0)
    else:
        print("\nScript verification tests failed.")
        sys.exit(1)
