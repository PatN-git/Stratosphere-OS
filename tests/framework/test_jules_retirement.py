#!/usr/bin/env python3
# md-crosscheck: retirement of Google Jules from dist/skills, external-skills, and build manifests
"""BT-229: Regression and invariant tests ensuring complete retirement of Google Jules from StratOS."""
import json
import re
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def read_text(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def split_frontmatter(text: str):
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?(.*)$", text, re.S)
    return m.group(1) if m else ""


def test_no_jules_files_or_directories_exist():
    assert not (REPO_ROOT / "src/experimental/jules-dispatch").exists()
    assert not (REPO_ROOT / "src/experimental").exists()
    assert not (REPO_ROOT / "src/workflows/3x-jules-dispatch.md").exists()
    assert not (REPO_ROOT / "dist/skills/3x-jules-dispatch").exists()
    assert not (REPO_ROOT / "scripts/dev/capture_jules_contract.py").exists()
    assert not (REPO_ROOT / "tests/jules").exists()
    assert not (REPO_ROOT / "tests/fixtures/jules").exists()
    assert not (REPO_ROOT / "tests/scripts/test_release_stamp.py").exists()


def test_external_skills_excludes_jules_in_src_and_dist():
    src_json = json.loads(read_text("src/external-skills.json"))
    dist_json = json.loads(read_text("dist/skills/stratosphere-setup/external-skills.json"))
    assert len(src_json["skills"]) == 9
    assert len(dist_json["skills"]) == 9
    assert "jules" not in read_text("src/external-skills.json").lower()
    assert "jules" not in read_text("dist/skills/stratosphere-setup/external-skills.json").lower()


def test_scripts_and_configs_no_dead_jules_references():
    assert "stamp_pack_pin" not in read_text("scripts/release.py")
    assert "jules" not in read_text("scripts/release.py").lower()
    assert "jules" not in read_text("build/validate.py").lower()
    assert "jules-dispatch" not in read_text("README.md")
    assert "jules-ledger" not in read_text("src/rules/okf-protocol.md")
    assert "jules" not in read_text("pytest.ini").lower()
    assert "jules" not in read_text(".github/workflows/build-guard.yml").lower()
    assert "jules" not in read_text("src/scripts/check_suite.py").lower()
    assert "jules" not in read_text("src/scripts/pr_body.py").lower()
    assert "jules" not in read_text("tests/scripts/test_pr_body.py").lower()


def test_each_lifecycle_skill_intact_and_free_of_jules():
    assert (REPO_ROOT / "dist/skills/0a-start-session/SKILL.md").is_file()
    assert "jules" not in read_text("dist/skills/0a-start-session/SKILL.md").lower()
    assert (REPO_ROOT / "dist/skills/0b-stop-session/SKILL.md").is_file()
    assert "jules" not in read_text("dist/skills/0b-stop-session/SKILL.md").lower()
    assert (REPO_ROOT / "dist/skills/0c-handoff/SKILL.md").is_file()
    assert "jules" not in read_text("dist/skills/0c-handoff/SKILL.md").lower()
    assert (REPO_ROOT / "dist/skills/0d-nightly-consolidation/SKILL.md").is_file()
    assert "jules" not in read_text("dist/skills/0d-nightly-consolidation/SKILL.md").lower()
    assert (REPO_ROOT / "dist/skills/0e-plain-english/SKILL.md").is_file()
    assert "jules" not in read_text("dist/skills/0e-plain-english/SKILL.md").lower()
    assert (REPO_ROOT / "dist/skills/1a-research/SKILL.md").is_file()
    assert "jules" not in read_text("dist/skills/1a-research/SKILL.md").lower()
    assert (REPO_ROOT / "dist/skills/1b-concept-framing/SKILL.md").is_file()
    assert "jules" not in read_text("dist/skills/1b-concept-framing/SKILL.md").lower()
    assert (REPO_ROOT / "dist/skills/1c-concept-map/SKILL.md").is_file()
    assert "jules" not in read_text("dist/skills/1c-concept-map/SKILL.md").lower()
    assert (REPO_ROOT / "dist/skills/2a-write-prd/SKILL.md").is_file()
    assert "jules" not in read_text("dist/skills/2a-write-prd/SKILL.md").lower()
    assert (REPO_ROOT / "dist/skills/2b-interface-design/SKILL.md").is_file()
    assert "jules" not in read_text("dist/skills/2b-interface-design/SKILL.md").lower()
    assert (REPO_ROOT / "dist/skills/2c-reconcile-specs/SKILL.md").is_file()
    assert "jules" not in read_text("dist/skills/2c-reconcile-specs/SKILL.md").lower()
    assert (REPO_ROOT / "dist/skills/2z-write-spec/SKILL.md").is_file()
    assert "jules" not in read_text("dist/skills/2z-write-spec/SKILL.md").lower()
    assert (REPO_ROOT / "dist/skills/3a-version-planning/SKILL.md").is_file()
    assert "jules" not in read_text("dist/skills/3a-version-planning/SKILL.md").lower()
    assert (REPO_ROOT / "dist/skills/3b-create-issue/SKILL.md").is_file()
    assert "jules" not in read_text("dist/skills/3b-create-issue/SKILL.md").lower()
    assert (REPO_ROOT / "dist/skills/3c-sprint-planning/SKILL.md").is_file()
    assert "jules" not in read_text("dist/skills/3c-sprint-planning/SKILL.md").lower()
    assert (REPO_ROOT / "dist/skills/3d-implement-issue/SKILL.md").is_file()
    assert "jules" not in read_text("dist/skills/3d-implement-issue/SKILL.md").lower()
    assert (REPO_ROOT / "dist/skills/3z-afk-loop/SKILL.md").is_file()
    assert "jules" not in read_text("dist/skills/3z-afk-loop/SKILL.md").lower()
    assert (REPO_ROOT / "dist/skills/4a-verify-and-ship/SKILL.md").is_file()
    assert "jules" not in read_text("dist/skills/4a-verify-and-ship/SKILL.md").lower()
    assert (REPO_ROOT / "dist/skills/4b-audit-architecture-drift/SKILL.md").is_file()
    assert "jules" not in read_text("dist/skills/4b-audit-architecture-drift/SKILL.md").lower()
    assert (REPO_ROOT / "dist/skills/4c-codebase-health-audit/SKILL.md").is_file()
    assert "jules" not in read_text("dist/skills/4c-codebase-health-audit/SKILL.md").lower()
    assert (REPO_ROOT / "dist/skills/stratosphere-setup/SKILL.md").is_file()
    assert "jules" not in read_text("dist/skills/stratosphere-setup/SKILL.md").lower()
    assert (REPO_ROOT / "dist/skills/stratosphere-update/SKILL.md").is_file()
    assert "jules" not in read_text("dist/skills/stratosphere-update/SKILL.md").lower()
    assert (REPO_ROOT / "dist/skills/sync-skills/SKILL.md").is_file()
    assert "jules" not in read_text("dist/skills/sync-skills/SKILL.md").lower()


def test_each_execution_skill_intact_and_free_of_jules():
    assert (REPO_ROOT / "dist/skills/load-memory/SKILL.md").is_file()
    assert "jules" not in read_text("dist/skills/load-memory/SKILL.md").lower()
    assert (REPO_ROOT / "dist/skills/micro-tdd/SKILL.md").is_file()
    assert "jules" not in read_text("dist/skills/micro-tdd/SKILL.md").lower()
    assert (REPO_ROOT / "dist/skills/plan-html/SKILL.md").is_file()
    assert "jules" not in read_text("dist/skills/plan-html/SKILL.md").lower()
    assert (REPO_ROOT / "dist/skills/concept-brainstorm/SKILL.md").is_file()
    assert "jules" not in read_text("dist/skills/concept-brainstorm/SKILL.md").lower()


def test_versions_manifest_skill_artifacts():
    manifest_path = REPO_ROOT / "dist/skills/stratosphere-setup/versions.json"
    assert manifest_path.is_file()
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "artifacts" in data
    assert "skills/3x-jules-dispatch/SKILL.md" not in data["artifacts"]
    assert "skills/0a-start-session/SKILL.md" in data["artifacts"]
    assert "skills/0b-stop-session/SKILL.md" in data["artifacts"]
    assert "skills/0c-handoff/SKILL.md" in data["artifacts"]
    assert "skills/0d-nightly-consolidation/SKILL.md" in data["artifacts"]
    assert "skills/0e-plain-english/SKILL.md" in data["artifacts"]
    assert "skills/1a-research/SKILL.md" in data["artifacts"]
    assert "skills/1b-concept-framing/SKILL.md" in data["artifacts"]
    assert "skills/1c-concept-map/SKILL.md" in data["artifacts"]
    assert "skills/2a-write-prd/SKILL.md" in data["artifacts"]
    assert "skills/2b-interface-design/SKILL.md" in data["artifacts"]
    assert "skills/2c-reconcile-specs/SKILL.md" in data["artifacts"]
    assert "skills/2z-write-spec/SKILL.md" in data["artifacts"]
    assert "skills/3a-version-planning/SKILL.md" in data["artifacts"]
    assert "skills/3b-create-issue/SKILL.md" in data["artifacts"]
    assert "skills/3c-sprint-planning/SKILL.md" in data["artifacts"]
    assert "skills/3d-implement-issue/SKILL.md" in data["artifacts"]
    assert "skills/3z-afk-loop/SKILL.md" in data["artifacts"]
    assert "skills/4a-verify-and-ship/SKILL.md" in data["artifacts"]
    assert "skills/4b-audit-architecture-drift/SKILL.md" in data["artifacts"]
    assert "skills/4c-codebase-health-audit/SKILL.md" in data["artifacts"]
    assert "skills/stratosphere-setup/SKILL.md" in data["artifacts"]
    assert "skills/stratosphere-update/SKILL.md" in data["artifacts"]
    assert "skills/sync-skills/SKILL.md" in data["artifacts"]
    assert "skills/load-memory/SKILL.md" in data["artifacts"]
    assert "skills/micro-tdd/SKILL.md" in data["artifacts"]
    assert "skills/plan-html/SKILL.md" in data["artifacts"]
    assert "skills/concept-brainstorm/SKILL.md" in data["artifacts"]


def test_marketplace_manifest_clean():
    mk_path = REPO_ROOT / ".claude-plugin/marketplace.json"
    assert mk_path.is_file()
    data = json.loads(mk_path.read_text(encoding="utf-8"))
    skills = data["plugins"][0]["skills"]
    assert len(skills) == 27
    assert "./dist/skills/3x-jules-dispatch" not in skills
    assert "./dist/skills/0a-start-session" in skills
    assert "./dist/skills/0b-stop-session" in skills
    assert "./dist/skills/0c-handoff" in skills
    assert "./dist/skills/0d-nightly-consolidation" in skills
    assert "./dist/skills/0e-plain-english" in skills
    assert "./dist/skills/1a-research" in skills
    assert "./dist/skills/1b-concept-framing" in skills
    assert "./dist/skills/1c-concept-map" in skills
    assert "./dist/skills/2a-write-prd" in skills
    assert "./dist/skills/2b-interface-design" in skills
    assert "./dist/skills/2c-reconcile-specs" in skills
    assert "./dist/skills/2z-write-spec" in skills
    assert "./dist/skills/3a-version-planning" in skills
    assert "./dist/skills/3b-create-issue" in skills
    assert "./dist/skills/3c-sprint-planning" in skills
    assert "./dist/skills/3d-implement-issue" in skills
    assert "./dist/skills/3z-afk-loop" in skills
    assert "./dist/skills/4a-verify-and-ship" in skills
    assert "./dist/skills/4b-audit-architecture-drift" in skills
    assert "./dist/skills/4c-codebase-health-audit" in skills
    assert "./dist/skills/stratosphere-setup" in skills
    assert "./dist/skills/stratosphere-update" in skills
    assert "./dist/skills/sync-skills" in skills
    assert "./dist/skills/load-memory" in skills
    assert "./dist/skills/micro-tdd" in skills
    assert "./dist/skills/plan-html" in skills
    assert "./dist/skills/concept-brainstorm" in skills
