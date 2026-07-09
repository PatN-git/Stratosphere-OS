#!/usr/bin/env python3
"""E2E/Integration tests for the StratosphereOS in-place update pipeline."""
import json
import os
import sys
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src" / "scripts"))
import _versioning
import scaffold

MIGRATION_SCRIPT = REPO_ROOT / "scripts" / "migrations" / "inject_markers.py"

def run_cmd(args, cwd, expect_code=0):
    res = subprocess.run(args, cwd=str(cwd), capture_output=True, text=True)
    print(f"RUNNING: {' '.join(args)}")
    print("STDOUT:\n", res.stdout)
    print("STDERR:\n", res.stderr)
    if res.returncode != expect_code:
        raise RuntimeError(f"Command failed: {args}")
    return res

def setup_mock_plugin(tmp_dir, backlog_template_content, version="1.1.4"):
    mock_plugin = tmp_dir / ".agents" / "plugins" / "stratosphere-os"
    if mock_plugin.exists():
        shutil.rmtree(mock_plugin)
    shutil.copytree(REPO_ROOT / "dist" / "antigravity", mock_plugin)
    
    # Write mock versions.json listing BACKLOG_MAP.md
    versions_data = {
        "artifacts": {
            "assets/templates/memory/BACKLOG_MAP.md": {
                "version": version,
                "timestamp": "2026-07-08",
                "sha256": "dummy"
            }
        }
    }
    (mock_plugin / "versions.json").write_text(json.dumps(versions_data, indent=2), encoding="utf-8")
    
    # Write mock template BACKLOG_MAP.md
    (mock_plugin / "assets" / "templates" / "memory" / "BACKLOG_MAP.md").write_text(backlog_template_content, encoding="utf-8")
    return mock_plugin / "scripts" / "scaffold.py"

def test_pristine_update():
    print("--- Test: Pristine Update ---")
    tmp = REPO_ROOT / ".tmp" / "test_pristine_update"
    if tmp.exists():
        shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True, exist_ok=True)
    
    # 1. Setup mock legacy project (simulate version 1.1.3 backlog_map)
    (tmp / ".memory").mkdir(parents=True, exist_ok=True)
    (tmp / ".agents").mkdir(parents=True, exist_ok=True)
    
    # Write lockfile
    lock_data = {
        "installed_plugin_version": "1.0.0",
        "artifacts": {
            ".memory/BACKLOG_MAP.md": {
                "version": "1.1.3",
                "sha256_at_install": "unknown"
            }
        }
    }
    (tmp / ".agents" / ".stratosphere-lock.json").write_text(json.dumps(lock_data, indent=2), encoding="utf-8")
    
    # Write legacy BACKLOG_MAP.md (v1.1.3 content without markers)
    legacy_rules = (
        "- **PRESERVATION RULE:** Do NOT delete or modify operational instructions under Rules (such as Label source of truth syncing rules) or the `Milestone` definition line under Label Registry during setup or backlog updates. They must remain permanently as operational guidance.\n"
        "- When writing the first entry, populate the Label Registry with all labels used in this GitHub project.\n"
        "- **BT-id padding & Atomic Minting:** The GitHub issue number must be zero-padded to 3 digits (e.g., #7 becomes BT-007). All references, links, and filenames must use this padded format. **CRITICAL:** Never predict or pre-allocate `BT-<n>` IDs offline by scanning existing entries and calculating `MAX(BT_ID) + 1`. Because GitHub shares sequence numbers across both Issues and Pull Requests, guessing numbers locally guarantees collisions. IDs must be atomically captured strictly upon executing `gh issue create`.\n"
        "- Update when GitHub issues are created, closed, or change status.\n"
        "- Include only ID, Title, Status, Labels, Milestone, Dependencies, ICE, Ref — nothing else.\n"
        "- Use the Label Registry; do not invent labels.\n"
        "- The `Ref` column links to learnings, architecture rules, design rules, or glossary terms (e.g., L-012, A-003, DR-020, G-005). Doc paths (PRD/design) live in the GitHub issue body, not in Ref.\n"
        "- **Label source of truth:** After installation (Checkpoint 6), the Label Registry here reflects the live GitHub label set.\n"
        "  - If a label appears in **GitHub but not the registry** → add it to the registry (with user confirmation).\n"
        "  - If a label appears in the **registry but not GitHub** → create it in GitHub before using it in any issue.\n"
        "  - Never use a label in the Backlog table that is not in both the registry and GitHub.\n"
        "- **Single Status Invariant:** An issue must always have exactly one `status:*` label. When transitioning an issue to a new status in GitHub or the Backlog table, always remove the prior `status:*` label first."
    )
    
    legacy_labels = (
        "- **Primary Type (`type:<class>`)**: `type:bug`, `type:content`, `type:feature`, `type:improvement`, `type:maintenance`, `type:research`\n"
        "- **Execution Mode (`type:<mode>`)**: `type:HITL` (Human-in-Loop required), `type:AFK` (Autonomous execution)\n"
        "- **Priority (`priority:xxx`)**: `priority:high` (Must have), `priority:medium` (Important), `priority:low` (Nice to have)\n"
        "- **Size (`size:xxx`)**: `size:large` (Architectural: Multi-feature/major schema), `size:medium` (Vertical: Standard Data/Logic/UI slice), `size:small` (Surgical: Local/Single-file)\n"
        "- **Scope (`scope:xxx`)**: `scope:baseline` (MVP end-to-end), `scope:differentiator` (differentiator to win), `scope:deferred` (out of scope/temporal deferral)\n"
        "- **Status (`status:xxx`)**: `status:planned`, `status:needs_spec`, `status:in progress`, `status:blocked`, `status:done`\n"
        "- **Milestone**: `vX.Y.Z` (`vMAJOR.MINOR.SPRINT`, e.g. `v1.2.3` = release 1.2, sprint 3). `MAJOR.MINOR` = the product release, owned by `/3a_version-planning`; `SPRINT` (Z) owned by `/3c_sprint-planning`. `vX.Y.0` = release planned, not yet sprinted. No leading zeros. Mirrors the GitHub milestone. This is the project's product-release tracker — not a tool/library version."
    )
    
    legacy_backlog = (
        "---\n"
        "type: backlog\n"
        "title: Backlog Map\n"
        "description: Authoritative registry and status mapping of all project issues.\n"
        "timestamp: 2026-07-02\n"
        "version: \"1.1.3\"\n"
        "---\n"
        "# BACKLOG MAP\n\n"
        "## Purpose\n"
        "Authoritative, high-density reference for project issues and their status.\n\n"
        "> Cross-reference rules → `.agents/rules/memory-protocol.md`.\n\n"
        "## Rules\n"
        f"{legacy_rules}\n\n"
        "## Label Registry\n"
        "- **Area (`area:xxx`)**: `area:BE-ai`, `area:BE-api`, `area:BE-auth`, `area:BE-data`, `area:BE-infrastructure`, `area:FE-<page_name>` (where `<page_name>` is replaced with the page's slug during audit or page creation, e.g., `area:FE-login`, `area:FE-dashboard`)\n"
        f"{legacy_labels}\n\n"
        "## Backlog\n\n"
        "| ID | Title | Status | Labels | Milestone | Dependencies | ICE | Ref |\n"
        "|:---|:---|:---|:---|:---|:---|:---|:---|\n"
        "| BT-001 | Test task | planned | area:FE-dashboard, type:feature | v1.0.3 | — | ICE: 0.27 (I: 2.0, C: 80%) | — |\n"
    )
    (tmp / ".memory" / "BACKLOG_MAP.md").write_text(legacy_backlog, encoding="utf-8")
    
    # 2. Run inject_markers.py to migrate legacy file to marked file
    run_cmd([sys.executable, str(MIGRATION_SCRIPT)], tmp)
    
    migrated_text = (tmp / ".memory" / "BACKLOG_MAP.md").read_text(encoding="utf-8")
    assert "SOS:BLOCK id=backlog-rules" in migrated_text
    
    # 3. Setup mock plugin with modified backlog-rules block at 1.1.4
    new_rules = legacy_rules + "\n- A new mock rules change to trigger pristine update."
    new_template = (
        "---\n"
        "type: backlog\n"
        "title: Backlog Map\n"
        "description: Authoritative registry\n"
        "timestamp: 2026-07-08\n"
        "version: \"1.1.4\"\n"
        "---\n"
        "# BACKLOG MAP\n\n"
        "## Rules\n"
        "<!-- SOS:BLOCK id=backlog-rules v=1.1.4 -->\n"
        f"{new_rules}\n"
        "<!-- SOS:/BLOCK id=backlog-rules -->\n\n"
        "## Label Registry\n"
        "- **Area (`area:xxx`)**: `area:BE-ai`\n"
        "<!-- SOS:BLOCK id=label-canonical v=1.1.4 -->\n"
        "- **Primary Type (`type:<class>`)**: `type:bug`\n"
        "- **Execution Mode (`type:<mode>`)**: `type:HITL`\n"
        "- **Priority (`priority:xxx`)**: `priority:high`\n"
        "- **Size (`size:xxx`)**: `size:large`\n"
        "- **Scope (`scope:xxx`)**: `scope:baseline`\n"
        "- **Status (`status:xxx`)**: `status:planned`\n"
        "- **Milestone**: `vX.Y.Z`\n"
        "<!-- SOS:/BLOCK id=label-canonical -->\n\n"
        "## Backlog\n\n"
        "<!-- SOS:BLOCK id=backlog-header v=1.1.4 -->\n"
        "| ID | Title | Status | Labels | Milestone | Dependencies | ICE | Ref |\n"
        "|:---|:---|:---|:---|:---|:---|:---|:---|\n"
        "<!-- SOS:/BLOCK id=backlog-header -->\n"
        "| BT-001 | Test task | planned | area:FE-dashboard, type:feature | v1.0.3 | — | ICE: 0.27 (I: 2.0, C: 80%) | — |\n"
    )
    scaffold_script = setup_mock_plugin(tmp, new_template)
    
    # 4. Dry-run update
    run_cmd([sys.executable, str(scaffold_script), "--update", "--dry-run"], tmp)
    
    # Assert dry-run staged the update to .stratosphere-new
    new_file = tmp / ".memory" / "BACKLOG_MAP.md.stratosphere-new"
    assert new_file.exists()
    new_text = new_file.read_text(encoding="utf-8")
    assert 'version: "1.1.3"' in new_text
    assert "SOS:BLOCK id=backlog-rules v=1.1.4" in new_text
    assert "A new mock rules change to trigger pristine update." in new_text
    
    # 5. Commit update
    run_cmd([sys.executable, str(scaffold_script), "--update"], tmp)
    
    # Assert original is updated and .stratosphere-new is deleted
    assert not new_file.exists()
    final_text = (tmp / ".memory" / "BACKLOG_MAP.md").read_text(encoding="utf-8")
    assert 'version: "1.1.3"' in final_text
    assert "A new mock rules change to trigger pristine update." in final_text
    
    # Check lockfile advanced
    lock_final = json.loads((tmp / ".agents" / ".stratosphere-lock.json").read_text(encoding="utf-8"))
    assert lock_final["artifacts"][".memory/BACKLOG_MAP.md"]["version"] == "1.1.4"
    
    shutil.rmtree(tmp, ignore_errors=True)
    print("Pristine Update E2E passed!")

def test_conflict_update():
    print("--- Test: Conflict Update & Merging ---")
    tmp = REPO_ROOT / ".tmp" / "test_conflict_update"
    if tmp.exists():
        shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True, exist_ok=True)
    
    # 1. Setup mock legacy project
    (tmp / ".memory").mkdir(parents=True, exist_ok=True)
    (tmp / ".agents").mkdir(parents=True, exist_ok=True)
    
    # Write a marked BACKLOG_MAP.md (v1.1.3)
    # The user has customized the rules block!
    legacy_marked = (
        "---\n"
        "type: backlog\n"
        "title: Backlog Map\n"
        "version: \"1.1.3\"\n"
        "---\n"
        "# BACKLOG MAP\n\n"
        "## Rules\n"
        "<!-- SOS:BLOCK id=backlog-rules v=1.1.3 -->\n"
        "- Operational rules\n"
        "- User custom rule!\n"
        "<!-- SOS:/BLOCK id=backlog-rules -->\n\n"
        "## Label Registry\n"
        "- **Area (`area:xxx`)**: area:FE-login\n"
        "<!-- SOS:BLOCK id=label-canonical v=1.1.3 -->\n"
        "- Labels\n"
        "<!-- SOS:/BLOCK id=label-canonical -->\n\n"
        "## Backlog\n"
        "<!-- SOS:BLOCK id=backlog-header v=1.1.3 -->\n"
        "| ID | Title | Status | Labels | Milestone | Dependencies | ICE | Ref |\n"
        "|:---|:---|:---|:---|:---|:---|:---|:---|\n"
        "<!-- SOS:/BLOCK id=backlog-header -->\n"
        "| BT-001 | Test task | planned | area:FE-dashboard | v1.0.3 | — | — | — |\n"
    )
    (tmp / ".memory" / "BACKLOG_MAP.md").write_text(legacy_marked, encoding="utf-8")
    
    # Lockfile has blocks map matching original v1.1.3 template block hashes
    # We mock a baseline hash that differs from H_user (since user edited the rules block)
    lock_data = {
        "installed_plugin_version": "1.0.0",
        "artifacts": {
            ".memory/BACKLOG_MAP.md": {
                "version": "1.1.3",
                "sha256_at_install": "unknown",
                "blocks": {
                    "backlog-rules": "mocked_old_base_hash_that_differs",
                    "label-canonical": _versioning.block_hash(legacy_marked, "label-canonical"),
                    "backlog-header": _versioning.block_hash(legacy_marked, "backlog-header")
                }
            }
        }
    }
    (tmp / ".agents" / ".stratosphere-lock.json").write_text(json.dumps(lock_data, indent=2), encoding="utf-8")
    
    # 2. Setup mock plugin where backlog-rules has changed
    new_template = (
        "---\n"
        "type: backlog\n"
        "title: Backlog Map\n"
        "version: \"1.1.4\"\n"
        "---\n"
        "# BACKLOG MAP\n\n"
        "## Rules\n"
        "<!-- SOS:BLOCK id=backlog-rules v=1.1.4 -->\n"
        "- Operational rules\n"
        "- Framework improvements!\n"
        "<!-- SOS:/BLOCK id=backlog-rules -->\n\n"
        "## Label Registry\n"
        "- **Area (`area:xxx`)**: area:FE-login\n"
        "<!-- SOS:BLOCK id=label-canonical v=1.1.4 -->\n"
        "- Labels\n"
        "<!-- SOS:/BLOCK id=label-canonical -->\n\n"
        "## Backlog\n"
        "<!-- SOS:BLOCK id=backlog-header v=1.1.4 -->\n"
        "| ID | Title | Status | Labels | Milestone | Dependencies | ICE | Ref |\n"
        "|:---|:---|:---|:---|:---|:---|:---|:---|\n"
        "<!-- SOS:/BLOCK id=backlog-header -->\n"
        "| BT-001 | Test task | planned | area:FE-dashboard | v1.0.3 | — | — | — |\n"
    )
    scaffold_script = setup_mock_plugin(tmp, new_template)
    
    # 3. Run update. It should report a conflict and exit code 1
    res = subprocess.run([sys.executable, str(scaffold_script), "--update"], cwd=str(tmp), capture_output=True, text=True)
    assert res.returncode == 1
    assert "needs merge/review" in res.stdout
    
    # 4. Simulate agent performing the merge and writing to .stratosphere-new
    merged_backlog = (
        "---\n"
        "type: backlog\n"
        "title: Backlog Map\n"
        "version: \"1.1.4\"\n"
        "---\n"
        "# BACKLOG MAP\n\n"
        "## Rules\n"
        "<!-- SOS:BLOCK id=backlog-rules v=1.1.4 -->\n"
        "- Operational rules\n"
        "- Framework improvements!\n"
        "- User custom rule!\n"
        "<!-- SOS:/BLOCK id=backlog-rules -->\n\n"
        "## Label Registry\n"
        "- **Area (`area:xxx`)**: area:FE-login\n"
        "<!-- SOS:BLOCK id=label-canonical v=1.1.3 -->\n"
        "- Labels\n"
        "<!-- SOS:/BLOCK id=label-canonical -->\n\n"
        "## Backlog\n"
        "<!-- SOS:BLOCK id=backlog-header v=1.1.3 -->\n"
        "| ID | Title | Status | Labels | Milestone | Dependencies | ICE | Ref |\n"
        "|:---|:---|:---|:---|:---|:---|:---|:---|\n"
        "<!-- SOS:/BLOCK id=backlog-header -->\n"
        "| BT-001 | Test task | planned | area:FE-dashboard | v1.0.3 | — | — | — |\n"
    )
    (tmp / ".memory" / "BACKLOG_MAP.md.stratosphere-new").write_text(merged_backlog, encoding="utf-8")
    
    # 5. Rerun update. It should verify invariants and succeed!
    run_cmd([sys.executable, str(scaffold_script), "--update"], tmp)
    
    # Verify original file updated and .stratosphere-new cleaned up
    assert not (tmp / ".memory" / "BACKLOG_MAP.md.stratosphere-new").exists()
    final_text = (tmp / ".memory" / "BACKLOG_MAP.md").read_text(encoding="utf-8")
    assert 'version: "1.1.4"' in final_text
    assert "- User custom rule!" in final_text
    assert "- Framework improvements!" in final_text
    
    shutil.rmtree(tmp, ignore_errors=True)
    print("Conflict Update E2E passed!")

def test_invariant_trips():
    print("--- Test: Invariant Trips ---")
    tmp = REPO_ROOT / ".tmp" / "test_invariant_trips"
    if tmp.exists():
        shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True, exist_ok=True)
    
    # Setup
    (tmp / ".memory").mkdir(parents=True, exist_ok=True)
    (tmp / ".agents").mkdir(parents=True, exist_ok=True)
    
    base_file = (
        "---\n"
        "type: backlog\n"
        "title: Backlog Map\n"
        "version: \"1.1.3\"\n"
        "---\n"
        "# BACKLOG MAP\n\n"
        "## Rules\n"
        "<!-- SOS:BLOCK id=backlog-rules v=1.1.3 -->\n"
        "- Operational rules\n"
        "<!-- SOS:/BLOCK id=backlog-rules -->\n\n"
        "## Label Registry\n"
        "- **Area (`area:xxx`)**: area:FE-login\n"
        "<!-- SOS:BLOCK id=label-canonical v=1.1.3 -->\n"
        "- Labels\n"
        "<!-- SOS:/BLOCK id=label-canonical -->\n\n"
        "## Backlog\n"
        "<!-- SOS:BLOCK id=backlog-header v=1.1.3 -->\n"
        "| ID | Title | Status | Labels | Milestone | Dependencies | ICE | Ref |\n"
        "|:---|:---|:---|:---|:---|:---|:---|:---|\n"
        "<!-- SOS:/BLOCK id=backlog-header -->\n"
        "| BT-001 | Test task | planned | area:FE-dashboard | v1.0.3 | — | — | — |\n"
    )
    p = tmp / ".memory" / "BACKLOG_MAP.md"
    p.write_text(base_file, encoding="utf-8")
    
    lock_data = {
        "installed_plugin_version": "1.0.0",
        "artifacts": {
            ".memory/BACKLOG_MAP.md": {
                "version": "1.1.3",
                "sha256_at_install": "unknown",
                "blocks": {
                    "backlog-rules": _versioning.block_hash(base_file, "backlog-rules"),
                    "label-canonical": _versioning.block_hash(base_file, "label-canonical"),
                    "backlog-header": _versioning.block_hash(base_file, "backlog-header")
                }
            }
        }
    }
    (tmp / ".agents" / ".stratosphere-lock.json").write_text(json.dumps(lock_data, indent=2), encoding="utf-8")
    
    # Build local mock plugin root to satisfy locate_plugin_root search
    mock_plugin = tmp / ".agents" / "plugins" / "stratosphere-os"
    shutil.copytree(REPO_ROOT / "dist" / "antigravity", mock_plugin)
    scaffold_script = mock_plugin / "scripts" / "scaffold.py"
    
    # Case A: Trip whole row count / IDs check
    # We drop BT-001 row
    tripped_a = base_file.replace('| BT-001 | Test task | planned | area:FE-dashboard | v1.0.3 | — | — | — |\n', '')
    p.with_suffix(".md.stratosphere-new").write_text(tripped_a, encoding="utf-8")
    res = subprocess.run([sys.executable, str(scaffold_script), "--update"], cwd=str(tmp), capture_output=True, text=True)
    if res.returncode != 1 or "Validation failed for '.memory/BACKLOG_MAP.md'" not in res.stdout:
        print("DEBUG Case A:")
        print("exit code:", res.returncode)
        print("stdout:\n", res.stdout)
        print("stderr:\n", res.stderr)
    assert res.returncode == 1
    assert "Validation failed for '.memory/BACKLOG_MAP.md'" in res.stdout
    
    # Case B: Trip raw out-of-block byte identity check
    # We edit "area:FE-login" to "area:FE-dashboard" outside the blocks
    tripped_b = base_file.replace('area:FE-login', 'area:FE-dashboard')
    p.with_suffix(".md.stratosphere-new").write_text(tripped_b, encoding="utf-8")
    res = subprocess.run([sys.executable, str(scaffold_script), "--update"], cwd=str(tmp), capture_output=True, text=True)
    assert res.returncode == 1
    assert "Raw out-of-block content changed" in res.stdout
    
    # Case C: Trip marker integrity check
    # We drop the backlog-rules close marker
    tripped_c = base_file.replace('<!-- SOS:/BLOCK id=backlog-rules -->', '')
    p.with_suffix(".md.stratosphere-new").write_text(tripped_c, encoding="utf-8")
    res = subprocess.run([sys.executable, str(scaffold_script), "--update"], cwd=str(tmp), capture_output=True, text=True)
    assert res.returncode == 1
    assert "Unterminated block markers" in res.stdout or "Orphan close marker" in res.stdout or "Validation failed" in res.stdout
    
    shutil.rmtree(tmp, ignore_errors=True)
    print("Invariant verification test passed!")

def test_crlf_bom_preservation():
    print("--- Test: CRLF & BOM Preservation ---")
    tmp = REPO_ROOT / ".tmp" / "test_crlf_bom"
    if tmp.exists():
        shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True, exist_ok=True)
    
    # Setup mock legacy project with BOM and CRLF
    (tmp / ".memory").mkdir(parents=True, exist_ok=True)
    (tmp / ".agents").mkdir(parents=True, exist_ok=True)
    
    lock_data = {
        "installed_plugin_version": "1.0.0",
        "artifacts": {
            ".memory/BACKLOG_MAP.md": {
                "version": "1.1.3",
                "sha256_at_install": "unknown"
            }
        }
    }
    (tmp / ".agents" / ".stratosphere-lock.json").write_text(json.dumps(lock_data, indent=2), encoding="utf-8")
    
    # Raw backlog map using CRLF line endings and starting with a UTF-8 BOM (\ufeff)
    sys.path.insert(0, str(REPO_ROOT / "scripts" / "migrations"))
    import inject_markers
    legacy_rules = inject_markers.OLD_BLOCKS["BACKLOG_MAP.md"]["backlog-rules"].replace("\n", "\r\n")
    legacy_labels = inject_markers.OLD_BLOCKS["BACKLOG_MAP.md"]["label-canonical"].replace("\n", "\r\n")
    
    legacy_backlog = (
        "\ufeff" # BOM
        "---\r\n"
        "type: backlog\r\n"
        "title: Backlog Map\r\n"
        "description: Authoritative registry and status mapping of all project issues.\r\n"
        "timestamp: 2026-07-02\r\n"
        "version: \"1.1.3\"\r\n"
        "---\r\n"
        "# BACKLOG MAP\r\n\r\n"
        "## Purpose\r\n"
        "Authoritative, high-density reference for project issues and their status.\r\n\r\n"
        "> Cross-reference rules → `.agents/rules/memory-protocol.md`.\r\n\r\n"
        "## Rules\r\n"
        f"{legacy_rules}\r\n\r\n"
        "## Label Registry\r\n"
        "- **Area (`area:xxx`)**: `area:BE-ai`, `area:BE-api`, `area:BE-auth`, `area:BE-data`, `area:BE-infrastructure`, `area:FE-<page_name>` (where `<page_name>` is replaced with the page's slug during audit or page creation, e.g., `area:FE-login`, `area:FE-dashboard`)\r\n"
        f"{legacy_labels}\r\n\r\n"
        "## Backlog\r\n\r\n"
        "| ID | Title | Status | Labels | Milestone | Dependencies | ICE | Ref |\r\n"
        "|:---|:---|:---|:---|:---|:---|:---|:---|\r\n"
        "| BT-001 | Test task | planned | area:FE-dashboard, type:feature | v1.0.3 | — | ICE: 0.27 (I: 2.0, C: 80%) | — |\r\n"
    )
    
    p = tmp / ".memory" / "BACKLOG_MAP.md"
    p.write_bytes(legacy_backlog.encode("utf-8"))
    
    # 1. Run migration. Assert EOL/BOM preserved
    res = subprocess.run([sys.executable, str(MIGRATION_SCRIPT)], cwd=str(tmp), capture_output=True, text=True)
    print("MIGRATION STDOUT:\n", res.stdout)
    print("MIGRATION STDERR:\n", res.stderr)
    migrated_text = p.read_bytes().decode("utf-8")
    assert migrated_text.startswith("\ufeff")
    assert "\r\n" in migrated_text
    assert "\n" not in migrated_text.replace("\r\n", "")
    
    # 2. Setup mock template with modified rules (v1.1.4)
    new_rules = legacy_rules.replace("\r\n", "\n") + "\n- A new mock rules change to trigger pristine update."
    new_template = (
        "---\n"
        "type: backlog\n"
        "title: Backlog Map\n"
        "description: Authoritative registry\n"
        "timestamp: 2026-07-08\n"
        "version: \"1.1.4\"\n"
        "---\n"
        "# BACKLOG MAP\n\n"
        "## Rules\n"
        "<!-- SOS:BLOCK id=backlog-rules v=1.1.4 -->\n"
        f"{new_rules}\n"
        "<!-- SOS:/BLOCK id=backlog-rules -->\n\n"
        "## Label Registry\n"
        "- **Area (`area:xxx`)**: `area:BE-ai`\n"
        "<!-- SOS:BLOCK id=label-canonical v=1.1.4 -->\n"
        "- **Primary Type (`type:<class>`)**: `type:bug`\n"
        "- **Execution Mode (`type:<mode>`)**: `type:HITL`\n"
        "- **Priority (`priority:xxx`)**: `priority:high`\n"
        "- **Size (`size:xxx`)**: `size:large`\n"
        "- **Scope (`scope:xxx`)**: `scope:baseline`\n"
        "- **Status (`status:xxx`)**: `status:planned`\n"
        "- **Milestone**: `vX.Y.Z`\n"
        "<!-- SOS:/BLOCK id=label-canonical -->\n\n"
        "## Backlog\n\n"
        "<!-- SOS:BLOCK id=backlog-header v=1.1.4 -->\n"
        "| ID | Title | Status | Labels | Milestone | Dependencies | ICE | Ref |\n"
        "|:---|:---|:---|:---|:---|:---|:---|:---|\n"
        "<!-- SOS:/BLOCK id=backlog-header -->\n"
        "| BT-001 | Test task | planned | area:FE-dashboard, type:feature | v1.0.3 | — | ICE: 0.27 (I: 2.0, C: 80%) | — |\n"
    )
    scaffold_script = setup_mock_plugin(tmp, new_template)
    
    # 3. Dry-run update. Assert staged new file retains BOM and CRLF
    run_cmd([sys.executable, str(scaffold_script), "--update", "--dry-run"], tmp)
    new_p = tmp / ".memory" / "BACKLOG_MAP.md.stratosphere-new"
    assert new_p.exists()
    new_text = new_p.read_bytes().decode("utf-8")
    assert new_text.startswith("\ufeff")
    assert "\r\n" in new_text
    
    # 4. Commit update. Assert committed file retains EOL/BOM
    run_cmd([sys.executable, str(scaffold_script), "--update"], tmp)
    assert not new_p.exists()
    final_text = p.read_bytes().decode("utf-8")
    assert final_text.startswith("\ufeff")
    assert "\r\n" in final_text
    assert "A new mock rules change to trigger pristine update." in final_text
    
    shutil.rmtree(tmp, ignore_errors=True)
    print("CRLF & BOM Preservation E2E passed!")

def test_unchanged_but_bumped():
    print("--- Test: Unchanged-but-bumped File ---")
    tmp = REPO_ROOT / ".tmp" / "test_unchanged_but_bumped"
    if tmp.exists():
        shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True, exist_ok=True)
    
    # Setup
    (tmp / ".memory").mkdir(parents=True, exist_ok=True)
    (tmp / ".agents").mkdir(parents=True, exist_ok=True)
    
    # Write lockfile
    lock_data = {
        "installed_plugin_version": "1.0.0",
        "artifacts": {
            ".memory/BACKLOG_MAP.md": {
                "version": "1.1.3",
                "sha256_at_install": "unknown",
                "blocks": {
                    "backlog-rules": "dummy_rules_hash",
                    "label-canonical": "dummy_labels_hash",
                    "backlog-header": "dummy_header_hash"
                }
            }
        }
    }
    (tmp / ".agents" / ".stratosphere-lock.json").write_text(json.dumps(lock_data, indent=2), encoding="utf-8")
    
    # Workspace file at 1.1.3
    user_file = (
        "---\n"
        "type: backlog\n"
        "title: Backlog Map\n"
        "version: \"1.1.3\"\n"
        "---\n"
        "# BACKLOG MAP\n\n"
        "## Rules\n"
        "<!-- SOS:BLOCK id=backlog-rules v=1.1.3 -->\n"
        "- Operational rules\n"
        "<!-- SOS:/BLOCK id=backlog-rules -->\n\n"
        "## Label Registry\n"
        "- **Area (`area:xxx`)**: area:FE-login\n"
        "<!-- SOS:BLOCK id=label-canonical v=1.1.3 -->\n"
        "- Labels\n"
        "<!-- SOS:/BLOCK id=label-canonical -->\n\n"
        "## Backlog\n"
        "<!-- SOS:BLOCK id=backlog-header v=1.1.3 -->\n"
        "| ID | Title | Status | Labels | Milestone | Dependencies | ICE | Ref |\n"
        "|:---|:---|:---|:---|:---|:---|:---|:---|\n"
        "<!-- SOS:/BLOCK id=backlog-header -->\n"
        "| BT-001 | Test task | planned | area:FE-dashboard | v1.0.3 | — | — | — |\n"
    )
    p = tmp / ".memory" / "BACKLOG_MAP.md"
    p.write_text(user_file, encoding="utf-8")
    
    # Mock lock hashes with the actual hashes of the file
    lock_data["artifacts"][".memory/BACKLOG_MAP.md"]["blocks"] = {
        "backlog-rules": _versioning.block_hash(user_file, "backlog-rules"),
        "label-canonical": _versioning.block_hash(user_file, "label-canonical"),
        "backlog-header": _versioning.block_hash(user_file, "backlog-header")
    }
    (tmp / ".agents" / ".stratosphere-lock.json").write_text(json.dumps(lock_data, indent=2), encoding="utf-8")
    
    # Template has identical block content, but version is bumped to 1.1.4
    new_template = (
        "---\n"
        "type: backlog\n"
        "title: Backlog Map\n"
        "version: \"1.1.4\"\n"
        "---\n"
        "# BACKLOG MAP\n\n"
        "## Rules\n"
        "<!-- SOS:BLOCK id=backlog-rules v=1.1.4 -->\n"
        "- Operational rules\n"
        "<!-- SOS:/BLOCK id=backlog-rules -->\n\n"
        "## Label Registry\n"
        "- **Area (`area:xxx`)**: area:FE-login\n"
        "<!-- SOS:BLOCK id=label-canonical v=1.1.4 -->\n"
        "- Labels\n"
        "<!-- SOS:/BLOCK id=label-canonical -->\n\n"
        "## Backlog\n"
        "<!-- SOS:BLOCK id=backlog-header v=1.1.4 -->\n"
        "| ID | Title | Status | Labels | Milestone | Dependencies | ICE | Ref |\n"
        "|:---|:---|:---|:---|:---|:---|:---|:---|\n"
        "<!-- SOS:/BLOCK id=backlog-header -->\n"
        "| BT-001 | Test task | planned | area:FE-dashboard | v1.0.3 | — | — | — |\n"
    )
    scaffold_script = setup_mock_plugin(tmp, new_template)
    
    import time
    mtime_before = p.stat().st_mtime
    time.sleep(0.02)
    
    # Run update. It should succeed, advance version, but leave block markers at 1.1.3 (no content change)
    run_cmd([sys.executable, str(scaffold_script), "--update"], tmp)
    
    mtime_after = p.stat().st_mtime
    assert mtime_before == mtime_after, "File was written to on-disk despite having zero content changes!"
    
    final_text = p.read_text(encoding="utf-8")
    assert 'version: "1.1.3"' in final_text
    # Blocks are untouched, so stamps are still v=1.1.3
    assert "SOS:BLOCK id=backlog-rules v=1.1.3" in final_text
    
    # Lockfile baseline is advanced
    lock_final = json.loads((tmp / ".agents" / ".stratosphere-lock.json").read_text(encoding="utf-8"))
    assert lock_final["artifacts"][".memory/BACKLOG_MAP.md"]["version"] == "1.1.4"
    
    shutil.rmtree(tmp, ignore_errors=True)
    print("Unchanged-but-bumped test passed!")

def test_atomicity_crash_recovery():
    print("--- Test: Atomicity and Crash Recovery ---")
    tmp = REPO_ROOT / ".tmp" / "test_atomicity_crash"
    if tmp.exists():
        shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True, exist_ok=True)
    
    # Setup
    (tmp / ".memory").mkdir(parents=True, exist_ok=True)
    (tmp / ".agents").mkdir(parents=True, exist_ok=True)
    
    lock_data = {
        "installed_plugin_version": "1.0.0",
        "artifacts": {
            ".memory/BACKLOG_MAP.md": {
                "version": "1.1.3",
                "sha256_at_install": "unknown",
                "blocks": {
                    "backlog-rules": "dummy_rules_hash",
                    "label-canonical": "dummy_labels_hash",
                    "backlog-header": "dummy_header_hash"
                }
            }
        }
    }
    (tmp / ".agents" / ".stratosphere-lock.json").write_text(json.dumps(lock_data, indent=2), encoding="utf-8")
    
    user_file = (
        "---\n"
        "type: backlog\n"
        "title: Backlog Map\n"
        "version: \"1.1.3\"\n"
        "---\n"
        "# BACKLOG MAP\n\n"
        "## Rules\n"
        "<!-- SOS:BLOCK id=backlog-rules v=1.1.3 -->\n"
        "- Operational rules\n"
        "<!-- SOS:/BLOCK id=backlog-rules -->\n\n"
        "## Label Registry\n"
        "- **Area (`area:xxx`)**: area:FE-login\n"
        "<!-- SOS:BLOCK id=label-canonical v=1.1.3 -->\n"
        "- Labels\n"
        "<!-- SOS:/BLOCK id=label-canonical -->\n\n"
        "## Backlog\n"
        "<!-- SOS:BLOCK id=backlog-header v=1.1.3 -->\n"
        "| ID | Title | Status | Labels | Milestone | Dependencies | ICE | Ref |\n"
        "|:---|:---|:---|:---|:---|:---|:---|:---|\n"
        "<!-- SOS:/BLOCK id=backlog-header -->\n"
        "| BT-001 | Test task | planned | area:FE-dashboard | v1.0.3 | — | — | — |\n"
    )
    p = tmp / ".memory" / "BACKLOG_MAP.md"
    p.write_text(user_file, encoding="utf-8")
    
    lock_data["artifacts"][".memory/BACKLOG_MAP.md"]["blocks"] = {
        "backlog-rules": _versioning.block_hash(user_file, "backlog-rules"),
        "label-canonical": _versioning.block_hash(user_file, "label-canonical"),
        "backlog-header": _versioning.block_hash(user_file, "backlog-header")
    }
    (tmp / ".agents" / ".stratosphere-lock.json").write_text(json.dumps(lock_data, indent=2), encoding="utf-8")
    
    new_template = (
        "---\n"
        "type: backlog\n"
        "title: Backlog Map\n"
        "version: \"1.1.4\"\n"
        "---\n"
        "# BACKLOG MAP\n\n"
        "## Rules\n"
        "<!-- SOS:BLOCK id=backlog-rules v=1.1.4 -->\n"
        "- Operational rules\n"
        "- Framework improvements!\n"
        "<!-- SOS:/BLOCK id=backlog-rules -->\n\n"
        "## Label Registry\n"
        "- **Area (`area:xxx`)**: area:FE-login\n"
        "<!-- SOS:BLOCK id=label-canonical v=1.1.4 -->\n"
        "- Labels\n"
        "<!-- SOS:/BLOCK id=label-canonical -->\n\n"
        "## Backlog\n"
        "<!-- SOS:BLOCK id=backlog-header v=1.1.4 -->\n"
        "| ID | Title | Status | Labels | Milestone | Dependencies | ICE | Ref |\n"
        "|:---|:---|:---|:---|:---|:---|:---|:---|\n"
        "<!-- SOS:/BLOCK id=backlog-header -->\n"
        "| BT-001 | Test task | planned | area:FE-dashboard | v1.0.3 | — | — | — |\n"
    )
    scaffold_script = setup_mock_plugin(tmp, new_template)
    
    # 1. Run dry-run to stage the proposed file
    run_cmd([sys.executable, str(scaffold_script), "--update", "--dry-run"], tmp)
    new_p = tmp / ".memory" / "BACKLOG_MAP.md.stratosphere-new"
    assert new_p.exists()
    
    # 2. Simulate a crash right after dry-run (so original BACKLOG_MAP.md is untouched,
    # lockfile is untouched, but .stratosphere-new file is left staged in project)
    assert 'version: "1.1.3"' in p.read_text(encoding="utf-8")
    assert json.loads((tmp / ".agents" / ".stratosphere-lock.json").read_text(encoding="utf-8"))["artifacts"][".memory/BACKLOG_MAP.md"]["version"] == "1.1.3"
    
    # 3. Rerun update (non-dry-run). It should find the staged file, verify it, apply it, and delete it
    run_cmd([sys.executable, str(scaffold_script), "--update"], tmp)
    assert not new_p.exists()
    assert 'version: "1.1.3"' in p.read_text(encoding="utf-8")
    assert "- Framework improvements!" in p.read_text(encoding="utf-8")
    assert json.loads((tmp / ".agents" / ".stratosphere-lock.json").read_text(encoding="utf-8"))["artifacts"][".memory/BACKLOG_MAP.md"]["version"] == "1.1.4"
    
    shutil.rmtree(tmp, ignore_errors=True)
    print("Atomicity and Crash Recovery test passed!")

def test_unmarked_file_skipped():
    print("--- Test: Unmarked File Skipped ---")
    tmp = REPO_ROOT / ".tmp" / "test_unmarked_skipped"
    if tmp.exists():
        shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True, exist_ok=True)
    
    # Setup
    (tmp / ".memory").mkdir(parents=True, exist_ok=True)
    (tmp / ".agents").mkdir(parents=True, exist_ok=True)
    
    # Write lockfile with BACKLOG_MAP locked at 1.1.3
    lock_data = {
        "installed_plugin_version": "1.0.0",
        "artifacts": {
            ".memory/BACKLOG_MAP.md": {
                "version": "1.1.3",
                "sha256_at_install": "unknown"
            }
        }
    }
    (tmp / ".agents" / ".stratosphere-lock.json").write_text(json.dumps(lock_data, indent=2), encoding="utf-8")
    
    # Write unmarked backlog map
    user_file = (
        "---\n"
        "type: backlog\n"
        "title: Backlog Map\n"
        "version: \"1.1.3\"\n"
        "---\n"
        "# BACKLOG MAP\n\n"
        "## Rules\n"
        "- Operational rules\n"
    )
    p = tmp / ".memory" / "BACKLOG_MAP.md"
    p.write_text(user_file, encoding="utf-8")
    
    new_template = (
        "---\n"
        "type: backlog\n"
        "title: Backlog Map\n"
        "version: \"1.1.4\"\n"
        "---\n"
        "# BACKLOG MAP\n\n"
        "## Rules\n"
        "<!-- SOS:BLOCK id=backlog-rules v=1.1.4 -->\n"
        "- Operational rules\n"
        "- Framework improvements!\n"
        "<!-- SOS:/BLOCK id=backlog-rules -->\n"
    )
    scaffold_script = setup_mock_plugin(tmp, new_template)
    
    # Run update. It should print the Notice, skip updating BACKLOG_MAP, and keep version in lockfile at 1.1.3
    res = subprocess.run([sys.executable, str(scaffold_script), "--update"], cwd=str(tmp), capture_output=True, text=True)
    assert res.returncode == 0
    assert "Notice: Unmarked framework file" in res.stdout
    assert "inject_markers.py" in res.stdout
    
    # File content remains unchanged
    assert p.read_text(encoding="utf-8") == user_file
    
    # Lockfile remains at 1.1.3
    lock_final = json.loads((tmp / ".agents" / ".stratosphere-lock.json").read_text(encoding="utf-8"))
    assert lock_final["artifacts"][".memory/BACKLOG_MAP.md"]["version"] == "1.1.3"
    
    shutil.rmtree(tmp, ignore_errors=True)
    print("Unmarked file skipped test passed!")

def test_project_version_preserved():
    print("--- Test: Project Version Preserved ---")
    tmp = REPO_ROOT / ".tmp" / "test_project_version_preserved"
    if tmp.exists():
        shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True, exist_ok=True)
    
    (tmp / ".memory").mkdir(parents=True, exist_ok=True)
    (tmp / ".agents").mkdir(parents=True, exist_ok=True)
    
    lock_data = {
        "installed_plugin_version": "1.0.0",
        "artifacts": {
            ".memory/BACKLOG_MAP.md": {
                "version": "1.1.3",
                "sha256_at_install": "unknown",
                "blocks": {
                    "backlog-rules": "dummy_rules_hash",
                    "label-canonical": "dummy_labels_hash",
                    "backlog-header": "dummy_header_hash"
                }
            }
        }
    }
    (tmp / ".agents" / ".stratosphere-lock.json").write_text(json.dumps(lock_data, indent=2), encoding="utf-8")
    
    # Project file at 1.3.0, but markers say 1.1.3
    user_file = (
        "---\n"
        "type: backlog\n"
        "title: Backlog Map\n"
        "version: \"1.3.0\"\n"
        "---\n"
        "# BACKLOG MAP\n\n"
        "## Rules\n"
        "<!-- SOS:BLOCK id=backlog-rules v=1.1.3 -->\n"
        "- Operational rules\n"
        "<!-- SOS:/BLOCK id=backlog-rules -->\n\n"
        "## Label Registry\n"
        "- **Area (`area:xxx`)**: area:FE-login\n"
        "<!-- SOS:BLOCK id=label-canonical v=1.1.3 -->\n"
        "- Labels\n"
        "<!-- SOS:/BLOCK id=label-canonical -->\n\n"
        "## Backlog\n"
        "<!-- SOS:BLOCK id=backlog-header v=1.1.3 -->\n"
        "| ID | Title | Status | Labels | Milestone | Dependencies | ICE | Ref |\n"
        "|:---|:---|:---|:---|:---|:---|:---|:---|\n"
        "<!-- SOS:/BLOCK id=backlog-header -->\n"
        "| BT-001 | Test task | planned | area:FE-dashboard | v1.0.3 | — | — | — |\n"
    )
    p = tmp / ".memory" / "BACKLOG_MAP.md"
    p.write_text(user_file, encoding="utf-8")
    
    # Update baseline hashes to match user_file
    lock_data["artifacts"][".memory/BACKLOG_MAP.md"]["blocks"] = {
        "backlog-rules": _versioning.block_hash(user_file, "backlog-rules"),
        "label-canonical": _versioning.block_hash(user_file, "label-canonical"),
        "backlog-header": _versioning.block_hash(user_file, "backlog-header")
    }
    (tmp / ".agents" / ".stratosphere-lock.json").write_text(json.dumps(lock_data, indent=2), encoding="utf-8")
    
    new_template = (
        "---\n"
        "type: backlog\n"
        "title: Backlog Map\n"
        "version: \"1.1.4\"\n"
        "---\n"
        "# BACKLOG MAP\n\n"
        "## Rules\n"
        "<!-- SOS:BLOCK id=backlog-rules v=1.1.4 -->\n"
        "- Operational rules\n"
        "- Framework improvements!\n"
        "<!-- SOS:/BLOCK id=backlog-rules -->\n\n"
        "## Label Registry\n"
        "- **Area (`area:xxx`)**: area:FE-login\n"
        "<!-- SOS:BLOCK id=label-canonical v=1.1.4 -->\n"
        "- Labels\n"
        "<!-- SOS:/BLOCK id=label-canonical -->\n\n"
        "## Backlog\n"
        "<!-- SOS:BLOCK id=backlog-header v=1.1.4 -->\n"
        "| ID | Title | Status | Labels | Milestone | Dependencies | ICE | Ref |\n"
        "|:---|:---|:---|:---|:---|:---|:---|:---|\n"
        "<!-- SOS:/BLOCK id=backlog-header -->\n"
        "| BT-001 | Test task | planned | area:FE-dashboard | v1.0.3 | — | — | — |\n"
    )
    scaffold_script = setup_mock_plugin(tmp, new_template)
    
    run_cmd([sys.executable, str(scaffold_script), "--update"], tmp)
    
    final_text = p.read_text(encoding="utf-8")
    # Assert project-local version 1.3.0 is preserved (not downgraded to 1.1.4)
    assert 'version: "1.3.0"' in final_text
    # Assert block updated, block marker version bumped to 1.1.4
    assert "- Framework improvements!" in final_text
    assert "SOS:BLOCK id=backlog-rules v=1.1.4" in final_text
    
    # Assert lockfile records template version 1.1.4
    lock_final = json.loads((tmp / ".agents" / ".stratosphere-lock.json").read_text(encoding="utf-8"))
    assert lock_final["artifacts"][".memory/BACKLOG_MAP.md"]["version"] == "1.1.4"
    
    shutil.rmtree(tmp, ignore_errors=True)
    print("Project version preserved test passed!")

def test_frontmatter_never_written_even_when_bundle_higher():
    print("--- Test: Frontmatter Never Written Even When Bundle Higher ---")
    tmp = REPO_ROOT / ".tmp" / "test_fm_never_written"
    if tmp.exists():
        shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True, exist_ok=True)
    
    (tmp / ".memory").mkdir(parents=True, exist_ok=True)
    (tmp / ".agents").mkdir(parents=True, exist_ok=True)
    
    lock_data = {
        "installed_plugin_version": "1.0.0",
        "artifacts": {
            ".memory/BACKLOG_MAP.md": {
                "version": "1.1.3",
                "sha256_at_install": "unknown",
                "blocks": {}
            }
        }
    }
    (tmp / ".agents" / ".stratosphere-lock.json").write_text(json.dumps(lock_data, indent=2), encoding="utf-8")
    
    user_file = (
        "---\n"
        "type: backlog\n"
        "title: Backlog Map\n"
        "version: \"1.1.3\"\n"
        "---\n"
        "# BACKLOG MAP\n\n"
        "## Rules\n"
        "<!-- SOS:BLOCK id=backlog-rules v=1.1.3 -->\n"
        "- Operational rules\n"
        "<!-- SOS:/BLOCK id=backlog-rules -->\n"
    )
    p = tmp / ".memory" / "BACKLOG_MAP.md"
    p.write_text(user_file, encoding="utf-8")
    
    lock_data["artifacts"][".memory/BACKLOG_MAP.md"]["blocks"] = {
        "backlog-rules": _versioning.block_hash(user_file, "backlog-rules")
    }
    (tmp / ".agents" / ".stratosphere-lock.json").write_text(json.dumps(lock_data, indent=2), encoding="utf-8")
    
    new_template = (
        "---\n"
        "type: backlog\n"
        "title: Backlog Map\n"
        "version: \"1.1.4\"\n"
        "---\n"
        "# BACKLOG MAP\n\n"
        "## Rules\n"
        "<!-- SOS:BLOCK id=backlog-rules v=1.1.4 -->\n"
        "- Operational rules\n"
        "- Framework improvements!\n"
        "<!-- SOS:/BLOCK id=backlog-rules -->\n"
    )
    scaffold_script = setup_mock_plugin(tmp, new_template)
    
    run_cmd([sys.executable, str(scaffold_script), "--update"], tmp)
    
    final_text = p.read_text(encoding="utf-8")
    # Frontmatter stays at 1.1.3 (Option B)
    assert 'version: "1.1.3"' in final_text
    
    # Lockfile advances to 1.1.4
    lock_final = json.loads((tmp / ".agents" / ".stratosphere-lock.json").read_text(encoding="utf-8"))
    assert lock_final["artifacts"][".memory/BACKLOG_MAP.md"]["version"] == "1.1.4"
    
    shutil.rmtree(tmp, ignore_errors=True)
    print("Frontmatter never written test passed!")

def test_content_based_scope_catches_stale_block_at_equal_version():
    print("--- Test: Content-Based Scope ---")
    tmp = REPO_ROOT / ".tmp" / "test_content_based_scope"
    if tmp.exists():
        shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True, exist_ok=True)
    
    (tmp / ".memory").mkdir(parents=True, exist_ok=True)
    (tmp / ".agents").mkdir(parents=True, exist_ok=True)
    
    user_file = (
        "---\n"
        "type: backlog\n"
        "title: Backlog Map\n"
        "version: \"1.1.4\"\n"
        "---\n"
        "# BACKLOG MAP\n\n"
        "## Rules\n"
        "<!-- SOS:BLOCK id=backlog-rules v=1.1.3 -->\n"
        "- Operational rules\n"
        "<!-- SOS:/BLOCK id=backlog-rules -->\n"
    )
    p = tmp / ".memory" / "BACKLOG_MAP.md"
    p.write_text(user_file, encoding="utf-8")
    
    # Lockfile claims we are at 1.1.4, matching bundle!
    lock_data = {
        "installed_plugin_version": "1.0.0",
        "artifacts": {
            ".memory/BACKLOG_MAP.md": {
                "version": "1.1.4",
                "sha256_at_install": "unknown",
                "blocks": {
                    "backlog-rules": _versioning.block_hash(user_file, "backlog-rules")
                }
            }
        }
    }
    (tmp / ".agents" / ".stratosphere-lock.json").write_text(json.dumps(lock_data, indent=2), encoding="utf-8")
    
    new_template = (
        "---\n"
        "type: backlog\n"
        "title: Backlog Map\n"
        "version: \"1.1.4\"\n"
        "---\n"
        "# BACKLOG MAP\n\n"
        "## Rules\n"
        "<!-- SOS:BLOCK id=backlog-rules v=1.1.4 -->\n"
        "- Operational rules\n"
        "- Framework improvements!\n"
        "<!-- SOS:/BLOCK id=backlog-rules -->\n"
    )
    scaffold_script = setup_mock_plugin(tmp, new_template)
    
    # Run update. Even though locked_version == b_version (1.1.4 == 1.1.4), the block hash differs.
    # Content-based scope must identify it as stale and update it!
    run_cmd([sys.executable, str(scaffold_script), "--update"], tmp)
    
    final_text = p.read_text(encoding="utf-8")
    assert "- Framework improvements!" in final_text
    
    shutil.rmtree(tmp, ignore_errors=True)
    print("Content-based scope test passed!")

def test_repair_lock_does_not_inflate_or_read_frontmatter():
    print("--- Test: Repair Lock does not Inflate/Read Frontmatter ---")
    tmp = REPO_ROOT / ".tmp" / "test_repair_lock_no_inflate"
    if tmp.exists():
        shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True, exist_ok=True)
    
    (tmp / ".memory").mkdir(parents=True, exist_ok=True)
    (tmp / ".agents").mkdir(parents=True, exist_ok=True)
    
    # Write a project file at 1.3.0 but markers at 1.1.3
    user_file = (
        "---\n"
        "type: backlog\n"
        "title: Backlog Map\n"
        "version: \"1.3.0\"\n"
        "---\n"
        "# BACKLOG MAP\n\n"
        "## Rules\n"
        "<!-- SOS:BLOCK id=backlog-rules v=1.1.3 -->\n"
        "- Operational rules\n"
        "<!-- SOS:/BLOCK id=backlog-rules -->\n"
    )
    p = tmp / ".memory" / "BACKLOG_MAP.md"
    p.write_text(user_file, encoding="utf-8")
    
    # No lockfile initially. We run --repair-lock
    new_template = (
        "---\n"
        "type: backlog\n"
        "title: Backlog Map\n"
        "version: \"1.1.5\"\n"
        "---\n"
        "# BACKLOG MAP\n\n"
        "## Rules\n"
        "<!-- SOS:BLOCK id=backlog-rules v=1.1.5 -->\n"
        "- Operational rules\n"
        "- Framework improvements!\n"
        "<!-- SOS:/BLOCK id=backlog-rules -->\n"
    )
    scaffold_script = setup_mock_plugin(tmp, new_template)
    
    run_cmd([sys.executable, str(scaffold_script), "--repair-lock"], tmp)
    
    # Assert lockfile version is derived from markers (1.1.3), NOT 1.3.0 and NOT the bundle (1.1.5)
    lock_final = json.loads((tmp / ".agents" / ".stratosphere-lock.json").read_text(encoding="utf-8"))
    assert lock_final["artifacts"][".memory/BACKLOG_MAP.md"]["version"] == "1.1.3"
    assert "backlog-rules" in lock_final["artifacts"][".memory/BACKLOG_MAP.md"]["blocks"]
    
    # Subsequent update (from 1.1.3 to 1.1.5 template) must be put in scope and succeed
    run_cmd([sys.executable, str(scaffold_script), "--update"], tmp)
    final_text = p.read_text(encoding="utf-8")
    assert "- Framework improvements!" in final_text
    
    shutil.rmtree(tmp, ignore_errors=True)
    print("Repair lock no-inflate test passed!")

def test_repair_then_update_pristine():
    print("--- Test: Repair then Update Pristine ---")
    tmp = REPO_ROOT / ".tmp" / "test_repair_then_update"
    if tmp.exists():
        shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True, exist_ok=True)
    
    (tmp / ".memory").mkdir(parents=True, exist_ok=True)
    (tmp / ".agents").mkdir(parents=True, exist_ok=True)
    
    user_file = (
        "---\n"
        "type: backlog\n"
        "title: Backlog Map\n"
        "version: \"1.1.3\"\n"
        "---\n"
        "# BACKLOG MAP\n\n"
        "## Rules\n"
        "<!-- SOS:BLOCK id=backlog-rules v=1.1.3 -->\n"
        "- Operational rules\n"
        "<!-- SOS:/BLOCK id=backlog-rules -->\n"
    )
    p = tmp / ".memory" / "BACKLOG_MAP.md"
    p.write_text(user_file, encoding="utf-8")
    
    new_template = (
        "---\n"
        "type: backlog\n"
        "title: Backlog Map\n"
        "version: \"1.1.4\"\n"
        "---\n"
        "# BACKLOG MAP\n\n"
        "## Rules\n"
        "<!-- SOS:BLOCK id=backlog-rules v=1.1.4 -->\n"
        "- Operational rules\n"
        "- Framework improvements!\n"
        "<!-- SOS:/BLOCK id=backlog-rules -->\n"
    )
    scaffold_script = setup_mock_plugin(tmp, new_template)
    
    # Run repair. Seeding base hashes matching user file (which matches template 1.1.3)
    run_cmd([sys.executable, str(scaffold_script), "--repair-lock"], tmp)
    
    # Subsequent update should classify block as pristine and update it (no conflict)
    run_cmd([sys.executable, str(scaffold_script), "--update"], tmp)
    final_text = p.read_text(encoding="utf-8")
    assert "- Framework improvements!" in final_text
    
    shutil.rmtree(tmp, ignore_errors=True)
    print("Repair then update pristine test passed!")

def test_customization_survives_second_update():
    print("--- Test: Customization Survives Second Update ---")
    tmp = REPO_ROOT / ".tmp" / "test_customization_survives"
    if tmp.exists():
        shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True, exist_ok=True)
    
    (tmp / ".memory").mkdir(parents=True, exist_ok=True)
    (tmp / ".agents").mkdir(parents=True, exist_ok=True)
    
    lock_data = {
        "installed_plugin_version": "1.0.0",
        "artifacts": {
            ".memory/BACKLOG_MAP.md": {
                "version": "1.1.3",
                "sha256_at_install": "unknown",
                "blocks": {}
            }
        }
    }
    (tmp / ".agents" / ".stratosphere-lock.json").write_text(json.dumps(lock_data, indent=2), encoding="utf-8")
    
    # File has block A (rules) unchanged, and block B (label-canonical) customized!
    user_file = (
        "---\n"
        "type: backlog\n"
        "title: Backlog Map\n"
        "version: \"1.1.3\"\n"
        "---\n"
        "# BACKLOG MAP\n\n"
        "## Rules\n"
        "<!-- SOS:BLOCK id=backlog-rules v=1.1.3 -->\n"
        "- Operational rules\n"
        "<!-- SOS:/BLOCK id=backlog-rules -->\n\n"
        "## Label Registry\n"
        "<!-- SOS:BLOCK id=label-canonical v=1.1.3 -->\n"
        "- Labels (user customized!)\n"
        "<!-- SOS:/BLOCK id=label-canonical -->\n"
    )
    p = tmp / ".memory" / "BACKLOG_MAP.md"
    p.write_text(user_file, encoding="utf-8")
    
    # The original baseline was standard 1.1.3 rules and 1.1.3 labels
    base_file_113 = (
        "---\n"
        "type: backlog\n"
        "title: Backlog Map\n"
        "version: \"1.1.3\"\n"
        "---\n"
        "# BACKLOG MAP\n\n"
        "## Rules\n"
        "<!-- SOS:BLOCK id=backlog-rules v=1.1.3 -->\n"
        "- Operational rules\n"
        "<!-- SOS:/BLOCK id=backlog-rules -->\n\n"
        "## Label Registry\n"
        "<!-- SOS:BLOCK id=label-canonical v=1.1.3 -->\n"
        "- Labels\n"
        "<!-- SOS:/BLOCK id=label-canonical -->\n"
    )
    
    lock_data["artifacts"][".memory/BACKLOG_MAP.md"]["blocks"] = {
        "backlog-rules": _versioning.block_hash(base_file_113, "backlog-rules"),
        "label-canonical": _versioning.block_hash(base_file_113, "label-canonical")
    }
    (tmp / ".agents" / ".stratosphere-lock.json").write_text(json.dumps(lock_data, indent=2), encoding="utf-8")
    
    # Template has new rules (1.1.4) but unchanged labels (1.1.3)
    new_template = (
        "---\n"
        "type: backlog\n"
        "title: Backlog Map\n"
        "version: \"1.1.4\"\n"
        "---\n"
        "# BACKLOG MAP\n\n"
        "## Rules\n"
        "<!-- SOS:BLOCK id=backlog-rules v=1.1.4 -->\n"
        "- Operational rules\n"
        "- Framework improvements!\n"
        "<!-- SOS:/BLOCK id=backlog-rules -->\n\n"
        "## Label Registry\n"
        "<!-- SOS:BLOCK id=label-canonical v=1.1.4 -->\n"
        "- Labels\n"
        "<!-- SOS:/BLOCK id=label-canonical -->\n"
    )
    scaffold_script = setup_mock_plugin(tmp, new_template)
    
    # First update: backlog-rules updates (pristine), label-canonical stays customized (unchanged classification)
    run_cmd([sys.executable, str(scaffold_script), "--update"], tmp)
    
    first_text = p.read_text(encoding="utf-8")
    assert "- Framework improvements!" in first_text
    assert "- Labels (user customized!)" in first_text
    
    # Assert lockfile advanced to 1.1.4 and block baseline is set to H_new of 1.1.4 template for both blocks
    lock_114 = json.loads((tmp / ".agents" / ".stratosphere-lock.json").read_text(encoding="utf-8"))
    assert lock_114["artifacts"][".memory/BACKLOG_MAP.md"]["version"] == "1.1.4"
    assert lock_114["artifacts"][".memory/BACKLOG_MAP.md"]["blocks"]["backlog-rules"] == _versioning.block_hash(new_template, "backlog-rules")
    assert lock_114["artifacts"][".memory/BACKLOG_MAP.md"]["blocks"]["label-canonical"] == _versioning.block_hash(new_template, "label-canonical")
    
    # Second update with the SAME bundle. The file should be out of scope, zero changes written
    # (especially, our customization must NOT be overwritten)
    p.write_text(first_text, encoding="utf-8") # refresh mod time
    res = subprocess.run([sys.executable, str(scaffold_script), "--update"], cwd=str(tmp), capture_output=True, text=True)
    assert res.returncode == 0
    assert "UPDATED" not in res.stdout
    
    second_text = p.read_text(encoding="utf-8")
    assert "- Framework improvements!" in second_text
    assert "- Labels (user customized!)" in second_text
    
    # ----------------------------------------------------
    # Conflict-Merge Variant E2E (Option B §4.1 item 6)
    # ----------------------------------------------------
    
    # 1. Bump template to 1.1.5 with rules changed again:
    template_115 = (
        "---\n"
        "type: backlog\n"
        "title: Backlog Map\n"
        "version: \"1.1.5\"\n"
        "---\n"
        "# BACKLOG MAP\n\n"
        "## Rules\n"
        "<!-- SOS:BLOCK id=backlog-rules v=1.1.5 -->\n"
        "- Operational rules\n"
        "- Framework improvements!\n"
        "- Version 1.1.5 framework improvements!\n"
        "<!-- SOS:/BLOCK id=backlog-rules -->\n\n"
        "## Label Registry\n"
        "<!-- SOS:BLOCK id=label-canonical v=1.1.5 -->\n"
        "- Labels\n"
        "<!-- SOS:/BLOCK id=label-canonical -->\n"
    )
    
    # 2. Modify backlog-rules block in the user's workspace so it's customized as well:
    user_file_custom = (
        "---\n"
        "type: backlog\n"
        "title: Backlog Map\n"
        "version: \"1.1.4\"\n"
        "---\n"
        "# BACKLOG MAP\n\n"
        "## Rules\n"
        "<!-- SOS:BLOCK id=backlog-rules v=1.1.4 -->\n"
        "- Operational rules\n"
        "- Framework improvements!\n"
        "- My custom local rule!\n"
        "<!-- SOS:/BLOCK id=backlog-rules -->\n\n"
        "## Label Registry\n"
        "<!-- SOS:BLOCK id=label-canonical v=1.1.4 -->\n"
        "- Labels (user customized!)\n"
        "<!-- SOS:/BLOCK id=label-canonical -->\n"
    )
    p.write_text(user_file_custom, encoding="utf-8")
    
    # Update mock plugin to 1.1.5
    scaffold_script_115 = setup_mock_plugin(tmp, template_115, version="1.1.5")
    
    # Running update. backlog-rules should conflict (both user and template changed)
    res = subprocess.run([sys.executable, str(scaffold_script_115), "--update"], cwd=str(tmp), capture_output=True, text=True)
    assert res.returncode != 0
    assert "BACKLOG_MAP.md needs merge/review" in res.stdout or "BACKLOG_MAP.md needs merge/review" in res.stderr
    
    # Simulate user committing conflict-merged file to .stratosphere-new:
    merged_text = (
        "---\n"
        "type: backlog\n"
        "title: Backlog Map\n"
        "version: \"1.1.4\"\n"
        "---\n"
        "# BACKLOG MAP\n\n"
        "## Rules\n"
        "<!-- SOS:BLOCK id=backlog-rules v=1.1.4 -->\n"
        "- Operational rules\n"
        "- Framework improvements!\n"
        "- Version 1.1.5 framework improvements!\n"
        "- My custom local rule!\n"
        "<!-- SOS:/BLOCK id=backlog-rules -->\n\n"
        "## Label Registry\n"
        "<!-- SOS:BLOCK id=label-canonical v=1.1.4 -->\n"
        "- Labels (user customized!)\n"
        "<!-- SOS:/BLOCK id=label-canonical -->\n"
    )
    (tmp / ".memory" / "BACKLOG_MAP.md.stratosphere-new").write_text(merged_text, encoding="utf-8")
    
    # Run update again to apply the merge. It should succeed.
    run_cmd([sys.executable, str(scaffold_script_115), "--update"], tmp)
    
    # Assert lockfile is advanced to 1.1.5 and the baseline hash is set to the template's hash H_new
    lock_115 = json.loads((tmp / ".agents" / ".stratosphere-lock.json").read_text(encoding="utf-8"))
    assert lock_115["artifacts"][".memory/BACKLOG_MAP.md"]["version"] == "1.1.5"
    assert lock_115["artifacts"][".memory/BACKLOG_MAP.md"]["blocks"]["backlog-rules"] == _versioning.block_hash(template_115, "backlog-rules")
    
    # Second update with unchanged 1.1.5 bundle. The file must not be modified or overwritten.
    p.write_text(merged_text, encoding="utf-8")
    import time
    mtime_before = p.stat().st_mtime
    time.sleep(0.02)
    res = subprocess.run([sys.executable, str(scaffold_script_115), "--update"], cwd=str(tmp), capture_output=True, text=True)
    assert res.returncode == 0
    assert "UPDATED" not in res.stdout
    assert p.stat().st_mtime == mtime_before
    
    # Third update: bump the bundle to 1.1.6, changing the backlog-rules block:
    template_116 = (
        "---\n"
        "type: backlog\n"
        "title: Backlog Map\n"
        "version: \"1.1.6\"\n"
        "---\n"
        "# BACKLOG MAP\n\n"
        "## Rules\n"
        "<!-- SOS:BLOCK id=backlog-rules v=1.1.6 -->\n"
        "- Operational rules\n"
        "- Framework improvements!\n"
        "- Version 1.1.5 framework improvements!\n"
        "- Version 1.1.6 framework improvements!\n"
        "<!-- SOS:/BLOCK id=backlog-rules -->\n\n"
        "## Label Registry\n"
        "<!-- SOS:BLOCK id=label-canonical v=1.1.6 -->\n"
        "- Labels\n"
        "<!-- SOS:/BLOCK id=label-canonical -->\n"
    )
    scaffold_script_116 = setup_mock_plugin(tmp, template_116, version="1.1.6")
    
    # Run update. It must be classified as CONFLICT, not pristine swap, because the user's block
    # was customized/merged (which does not match the 1.1.5 template hash)!
    res = subprocess.run([sys.executable, str(scaffold_script_116), "--update"], cwd=str(tmp), capture_output=True, text=True)
    assert res.returncode != 0
    assert "BACKLOG_MAP.md needs merge/review" in res.stdout or "BACKLOG_MAP.md needs merge/review" in res.stderr
    
    shutil.rmtree(tmp, ignore_errors=True)
    print("Customization survives second update test passed!")

def test_dr016_backref_restored():
    print("--- Test: DR-016 Back-Reference Restored ---")
    # Read build template
    template_rules = (REPO_ROOT / "src" / "memory-templates" / "DESIGN_RULES.md").read_text(encoding="utf-8")
    assert "version: \"1.0.6\"" in template_rules
    assert "one display/serif + one neutral/sans ([[DR-011]])." in template_rules
    print("DR-016 backref test passed!")

def test_canonical_marker_parsing():
    print("--- Test: Canonical Marker Parsing & Edge Cases ---")
    from _versioning import CANONICAL_MARKER_PATTERN, block_hash
    import scaffold
    
    orig_known = set(scaffold.KNOWN_BLOCK_IDS)
    scaffold.KNOWN_BLOCK_IDS.add("backlog")
    try:
        from scaffold import parse_file_blocks
        
        text = (
            "# BACKLOG\n\n"
            "<!-- SOS:BLOCK   id=backlog   v=1.0.0   -->\n"
            "This is the backlog block.\n"
            "<!--   SOS:/BLOCK   id=backlog   -->\n\n"
            "<!-- SOS:BLOCK id=backlog-rules -->\n"
            "This is backlog-rules.\n"
            "<!-- SOS:/BLOCK id=backlog-rules -->\n"
        )
        
        matches = list(CANONICAL_MARKER_PATTERN.finditer(text))
        assert len(matches) == 4
        
        assert matches[0].group(1) == "BLOCK"
        assert matches[0].group(2) == "backlog"
        assert matches[0].group(3) == "1.0.0"
        
        assert matches[1].group(1) == "/BLOCK"
        assert matches[1].group(2) == "backlog"
        assert matches[1].group(3) is None
        
        assert matches[2].group(1) == "BLOCK"
        assert matches[2].group(2) == "backlog-rules"
        assert matches[2].group(3) is None
        
        hash_backlog = block_hash(text, "backlog")
        hash_rules = block_hash(text, "backlog-rules")
        assert hash_backlog != hash_rules
        
        segments = parse_file_blocks(text, raw=True)
        assert len(segments) == 5
        assert segments[1]["id"] == "backlog"
        assert segments[3]["id"] == "backlog-rules"
        print("Canonical marker parsing test passed!")
    finally:
        scaffold.KNOWN_BLOCK_IDS = orig_known

def test_known_block_ids_drift_guard():
    print("--- Test: KNOWN_BLOCK_IDS Drift Guard ---")
    import scaffold
    from _versioning import CANONICAL_MARKER_PATTERN
    
    templates_dir = REPO_ROOT / "src" / "memory-templates"
    template_block_ids = set()
    
    for p in templates_dir.glob("*.md"):
        text = p.read_text(encoding="utf-8")
        for m in CANONICAL_MARKER_PATTERN.finditer(text):
            if m.group(1) == "BLOCK":
                template_block_ids.add(m.group(2))
                
    # Compare with scaffold.KNOWN_BLOCK_IDS
    diff1 = template_block_ids - scaffold.KNOWN_BLOCK_IDS
    diff2 = scaffold.KNOWN_BLOCK_IDS - template_block_ids
    
    if diff1 or diff2:
        msg = []
        if diff1:
            msg.append(f"Block IDs present in templates but missing from KNOWN_BLOCK_IDS: {diff1}")
        if diff2:
            msg.append(f"Block IDs present in KNOWN_BLOCK_IDS but missing from templates: {diff2}")
        raise AssertionError("KNOWN_BLOCK_IDS drift detected!\n" + "\n".join(msg))
        
    print("KNOWN_BLOCK_IDS drift guard verified green!")

def test_legacy_lockfile():
    print("--- Test: Legacy Lockfile (whole-file hash matching) ---")
    tmp = REPO_ROOT / ".tmp" / "test_legacy_lockfile"
    if tmp.exists():
        shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True, exist_ok=True)
    
    (tmp / ".memory").mkdir(parents=True, exist_ok=True)
    (tmp / ".agents").mkdir(parents=True, exist_ok=True)
    
    backlog_content = (
        "---\n"
        "version: 1.1.3\n"
        "timestamp: 2026-06-01\n"
        "---\n"
        "<!-- SOS:BLOCK id=backlog-rules v=1.1.3 -->\n"
        "Legacy rules\n"
        "<!-- SOS:/BLOCK id=backlog-rules -->\n"
    )
    
    import _versioning
    h_body = _versioning.body_hash(backlog_content)
    
    lock_data = {
        "installed_plugin_version": "1.0.0",
        "artifacts": {
            ".memory/BACKLOG_MAP.md": {
                "version": "1.1.3",
                "sha256_at_install": h_body,
                "blocks": {}
            }
        }
    }
    (tmp / ".agents" / ".stratosphere-lock.json").write_text(json.dumps(lock_data, indent=2), encoding="utf-8")
    (tmp / ".memory" / "BACKLOG_MAP.md").write_text(backlog_content, encoding="utf-8")
    
    template_content = (
        "---\n"
        "version: 1.1.4\n"
        "timestamp: 2026-07-08\n"
        "---\n"
        "<!-- SOS:BLOCK id=backlog-rules v=1.1.4 -->\n"
        "Upgraded rules\n"
        "<!-- SOS:/BLOCK id=backlog-rules -->\n"
    )
    
    scaffold_script = setup_mock_plugin(tmp, template_content, version="1.1.4")
    run_cmd([sys.executable, str(scaffold_script), "--update"], cwd=tmp)
    
    updated_content = (tmp / ".memory" / "BACKLOG_MAP.md").read_text(encoding="utf-8")
    if "Upgraded rules" not in updated_content:
        raise AssertionError("Expected rules to be auto-updated")
    print("Legacy Lockfile fallback test passed!")

def test_version_downgrade():
    print("--- Test: Version Downgrade Skipped ---")
    tmp = REPO_ROOT / ".tmp" / "test_version_downgrade"
    if tmp.exists():
        shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True, exist_ok=True)
    
    (tmp / ".memory").mkdir(parents=True, exist_ok=True)
    (tmp / ".agents").mkdir(parents=True, exist_ok=True)
    
    backlog_content = (
        "---\n"
        "version: 1.1.5\n"
        "timestamp: 2026-07-08\n"
        "---\n"
        "<!-- SOS:BLOCK id=backlog-rules v=1.1.5 -->\n"
        "Current rules\n"
        "<!-- SOS:/BLOCK id=backlog-rules -->\n"
    )
    (tmp / ".memory" / "BACKLOG_MAP.md").write_text(backlog_content, encoding="utf-8")
    
    import _versioning
    h_rules = _versioning.block_hash(backlog_content, "backlog-rules")
    lock_data = {
        "installed_plugin_version": "1.0.0",
        "artifacts": {
            ".memory/BACKLOG_MAP.md": {
                "version": "1.1.5",
                "sha256_at_install": _versioning.body_hash(backlog_content),
                "blocks": {
                    "backlog-rules": h_rules
                }
            }
        }
    }
    (tmp / ".agents" / ".stratosphere-lock.json").write_text(json.dumps(lock_data, indent=2), encoding="utf-8")
    
    template_content = (
        "---\n"
        "version: 1.1.4\n"
        "timestamp: 2026-07-01\n"
        "---\n"
        "<!-- SOS:BLOCK id=backlog-rules v=1.1.4 -->\n"
        "Older rules\n"
        "<!-- SOS:/BLOCK id=backlog-rules -->\n"
    )
    scaffold_script = setup_mock_plugin(tmp, template_content, version="1.1.4")
    run_cmd([sys.executable, str(scaffold_script), "--update"], cwd=tmp)
    
    final_content = (tmp / ".memory" / "BACKLOG_MAP.md").read_text(encoding="utf-8")
    if "Current rules" not in final_content:
        raise AssertionError("Downgrade should have skipped updating BACKLOG_MAP.md")
    print("Version downgrade test passed!")

def test_managed_file_refresh():
    print("--- Test: Managed File Refresh ---")
    tmp = REPO_ROOT / ".tmp" / "test_managed_refresh"
    if tmp.exists():
        shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True, exist_ok=True)
    
    (tmp / ".agents" / "workflows").mkdir(parents=True, exist_ok=True)
    (tmp / ".agents").mkdir(parents=True, exist_ok=True)
    
    wf_path = tmp / ".agents" / "workflows" / "3b_create-issue.md"
    wf_path.write_text("Old workflow content", encoding="utf-8")
    
    lock_data = {
        "installed_plugin_version": "1.0.0",
        "artifacts": {
            ".agents/workflows/3b_create-issue.md": {
                "version": "1.0.0",
                "sha256_at_install": "different"
            }
        }
    }
    (tmp / ".agents" / ".stratosphere-lock.json").write_text(json.dumps(lock_data, indent=2), encoding="utf-8")
    
    mock_plugin = tmp / ".agents" / "plugins" / "stratosphere-os"
    if mock_plugin.exists():
        shutil.rmtree(mock_plugin)
    shutil.copytree(REPO_ROOT / "dist" / "antigravity", mock_plugin)
    
    (mock_plugin / "workflows").mkdir(parents=True, exist_ok=True)
    (mock_plugin / "workflows" / "3b_create-issue.md").write_text("New workflow content", encoding="utf-8")
    
    versions_data = {
        "artifacts": {
            "workflows/3b_create-issue.md": {
                "version": "1.0.1",
                "timestamp": "2026-07-09",
                "sha256": "dummy"
            }
        }
    }
    (mock_plugin / "versions.json").write_text(json.dumps(versions_data, indent=2), encoding="utf-8")
    
    scaffold_script = mock_plugin / "scripts" / "scaffold.py"
    run_cmd([sys.executable, str(scaffold_script), "--update"], cwd=tmp)
    
    refreshed_content = wf_path.read_text(encoding="utf-8")
    if refreshed_content != "New workflow content":
        raise AssertionError("Expected managed workflow file to be refreshed/updated")
    print("Managed file refresh test passed!")

def test_constitution_needs_review():
    print("--- Test: Constitution Needs Review ---")
    tmp = REPO_ROOT / ".tmp" / "test_constitution"
    if tmp.exists():
        shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True, exist_ok=True)
    
    (tmp / ".agents").mkdir(parents=True, exist_ok=True)
    (tmp / "AGENT.md").write_text("Old constitution", encoding="utf-8")
    
    lock_data = {
        "installed_plugin_version": "1.0.0",
        "artifacts": {
            "AGENT.md": {
                "version": "1.0.0",
                "sha256_at_install": "different"
            }
        }
    }
    (tmp / ".agents" / ".stratosphere-lock.json").write_text(json.dumps(lock_data, indent=2), encoding="utf-8")
    
    mock_plugin = tmp / ".agents" / "plugins" / "stratosphere-os"
    if mock_plugin.exists():
        shutil.rmtree(mock_plugin)
    shutil.copytree(REPO_ROOT / "dist" / "antigravity", mock_plugin)
    
    (mock_plugin / "assets" / "templates" / "constitution").mkdir(parents=True, exist_ok=True)
    (mock_plugin / "assets" / "templates" / "constitution" / "AGENT.md").write_text("New constitution", encoding="utf-8")
    
    versions_data = {
        "artifacts": {
            "assets/templates/constitution/AGENT.md": {
                "version": "1.0.1",
                "timestamp": "2026-07-09",
                "sha256": "dummy"
            }
        }
    }
    (mock_plugin / "versions.json").write_text(json.dumps(versions_data, indent=2), encoding="utf-8")
    
    scaffold_script = mock_plugin / "scripts" / "scaffold.py"
    run_cmd([sys.executable, str(scaffold_script), "--update", "--dry-run"], cwd=tmp)
    
    # Read worklist and verify AGENT.md is in needs_review_constitution
    worklist_data = json.loads((tmp / ".tmp" / "stratosphere-update-worklist.json").read_text(encoding="utf-8"))
    if "AGENT.md" not in worklist_data["needs_review_constitution"]:
        raise AssertionError("Expected AGENT.md to be in needs_review_constitution")
        
    # Simulate user review acceptance by manually creating .stratosphere-new file
    new_file = tmp / "AGENT.md.stratosphere-new"
    new_file.write_text("Accepted constitution updates", encoding="utf-8")
    
    # Run update (non-dry-run should commit it)
    run_cmd([sys.executable, str(scaffold_script), "--update"], cwd=tmp)
    
    committed_content = (tmp / "AGENT.md").read_text(encoding="utf-8")
    if committed_content != "Accepted constitution updates":
        raise AssertionError("Expected constitution to be committed")
    print("Constitution review and merge test passed!")

def test_malformed_template_skip():
    print("--- Test: Malformed Template Skipped Gracefully ---")
    tmp = REPO_ROOT / ".tmp" / "test_malformed_skip"
    if tmp.exists():
        shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True, exist_ok=True)
    
    (tmp / ".memory").mkdir(parents=True, exist_ok=True)
    (tmp / ".agents").mkdir(parents=True, exist_ok=True)
    
    backlog_content = (
        "---\n"
        "version: 1.1.4\n"
        "timestamp: 2026-07-08\n"
        "---\n"
        "<!-- SOS:BLOCK id=backlog-rules v=1.1.4 -->\n"
        "Current rules\n"
        "<!-- SOS:/BLOCK id=backlog-rules -->\n"
    )
    (tmp / ".memory" / "BACKLOG_MAP.md").write_text(backlog_content, encoding="utf-8")
    
    import _versioning
    h_rules = _versioning.block_hash(backlog_content, "backlog-rules")
    lock_data = {
        "installed_plugin_version": "1.0.0",
        "artifacts": {
            ".memory/BACKLOG_MAP.md": {
                "version": "1.1.4",
                "sha256_at_install": _versioning.body_hash(backlog_content),
                "blocks": {
                    "backlog-rules": h_rules
                }
            }
        }
    }
    (tmp / ".agents" / ".stratosphere-lock.json").write_text(json.dumps(lock_data, indent=2), encoding="utf-8")
    
    malformed_template = (
        "---\n"
        "version: 1.1.5\n"
        "timestamp: 2026-07-09\n"
        "---\n"
        "<!-- SOS:BLOCK id=backlog-rules v=1.1.5 -->\n"
        "Upgraded rules without close marker!\n"
    )
    scaffold_script = setup_mock_plugin(tmp, malformed_template, version="1.1.5")
    run_cmd([sys.executable, str(scaffold_script), "--update"], cwd=tmp)
    
    final_content = (tmp / ".memory" / "BACKLOG_MAP.md").read_text(encoding="utf-8")
    if "Current rules" not in final_content:
        raise AssertionError("Malformed template should have been skipped")
    print("Malformed template skip test passed!")

def test_template_adds_block():
    print("--- Test: Template Adds New Block ---")
    tmp = REPO_ROOT / ".tmp" / "test_template_adds"
    if tmp.exists():
        shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True, exist_ok=True)
    
    (tmp / ".memory").mkdir(parents=True, exist_ok=True)
    (tmp / ".agents").mkdir(parents=True, exist_ok=True)
    
    backlog_content = (
        "---\n"
        "version: 1.1.4\n"
        "timestamp: 2026-07-08\n"
        "---\n"
        "Text 1\n"
        "<!-- SOS:BLOCK id=backlog-rules v=1.1.4 -->\n"
        "Content A\n"
        "<!-- SOS:/BLOCK id=backlog-rules -->\n"
        "Text 2\n"
    )
    (tmp / ".memory" / "BACKLOG_MAP.md").write_text(backlog_content, encoding="utf-8")
    
    import _versioning
    h_a = _versioning.block_hash(backlog_content, "backlog-rules")
    lock_data = {
        "installed_plugin_version": "1.0.0",
        "artifacts": {
            ".memory/BACKLOG_MAP.md": {
                "version": "1.1.4",
                "sha256_at_install": _versioning.body_hash(backlog_content),
                "blocks": {
                    "backlog-rules": h_a
                }
            }
        }
    }
    (tmp / ".agents" / ".stratosphere-lock.json").write_text(json.dumps(lock_data, indent=2), encoding="utf-8")
    
    template_content = (
        "---\n"
        "version: 1.1.5\n"
        "timestamp: 2026-07-09\n"
        "---\n"
        "Text 1\n"
        "<!-- SOS:BLOCK id=backlog-rules v=1.1.5 -->\n"
        "Content A\n"
        "<!-- SOS:/BLOCK id=backlog-rules -->\n"
        "Text 2\n"
        "<!-- SOS:BLOCK id=label-canonical v=1.1.5 -->\n"
        "Content B\n"
        "<!-- SOS:/BLOCK id=label-canonical -->\n"
        "Text 3\n"
    )
    scaffold_script = setup_mock_plugin(tmp, template_content, version="1.1.5")
    run_cmd([sys.executable, str(scaffold_script), "--update"], cwd=tmp)
    
    final_content = (tmp / ".memory" / "BACKLOG_MAP.md").read_text(encoding="utf-8")
    if "Content B" not in final_content:
        raise AssertionError("Expected label-canonical to be added/merged into BACKLOG_MAP.md")
    if "<!-- SOS:BLOCK id=label-canonical v=1.1.5 -->" not in final_content:
        raise AssertionError("Expected label-canonical markers to be present")
    print("Template adds new block test passed!")

if __name__ == "__main__":
    test_pristine_update()
    test_conflict_update()
    test_invariant_trips()
    test_crlf_bom_preservation()
    test_unchanged_but_bumped()
    test_atomicity_crash_recovery()
    test_unmarked_file_skipped()
    test_project_version_preserved()
    test_frontmatter_never_written_even_when_bundle_higher()
    test_content_based_scope_catches_stale_block_at_equal_version()
    test_repair_lock_does_not_inflate_or_read_frontmatter()
    test_repair_then_update_pristine()
    test_customization_survives_second_update()
    test_dr016_backref_restored()
    test_canonical_marker_parsing()
    test_known_block_ids_drift_guard()
    test_legacy_lockfile()
    test_version_downgrade()
    test_managed_file_refresh()
    test_constitution_needs_review()
    test_malformed_template_skip()
    test_template_adds_block()
    print("All update E2E tests passed successfully.")
