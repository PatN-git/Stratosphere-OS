#!/usr/bin/env python3
"""Distribution + update-safety tests for the jules-dispatch pack (P5).

Proves: (a) experimental source never leaks into dist, (b) the external-skills.json
entry is present and opt-in, (c) scaffold --update never targets .agents/skills/, so
a fetched pack survives updates byte-identical.

Run: python tests/test_jules_distribution.py
"""
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src" / "scripts"))
import scaffold  # noqa: E402


def test_no_experimental_in_dist():
    print("--- test_no_experimental_in_dist ---")
    for plat in ("dist/skills",):
        pdir = REPO_ROOT / plat
        leaked = [p.relative_to(REPO_ROOT).as_posix() for p in pdir.rglob("*")
                  if "experimental" in p.relative_to(pdir).parts]
        assert not leaked, f"experimental path leaked into {plat}: {leaked}"
    assert (REPO_ROOT / "src/experimental/jules-dispatch/jules_api.py").exists(), "source home must exist"
    print("PASS"); return True


def test_external_skills_entry_opt_in():
    print("--- test_external_skills_entry_opt_in ---")
    def _entry(path):
        data = json.loads((REPO_ROOT / path).read_text(encoding="utf-8"))
        return next((s for s in data["skills"] if s["name"] == "jules-dispatch"), None)
    e = _entry("src/external-skills.json")
    assert e is not None, "jules-dispatch entry missing from src/external-skills.json"
    assert e["default"] is False, "must be opt-in (default: false)"
    assert e["category"] == "experimental"
    assert e["targetPath"] == ".agents/skills/jules-dispatch"
    # flows into the bundle (carried by the setup skill)
    assert _entry("dist/skills/stratosphere-setup/external-skills.json") is not None, "entry missing in dist bundle"
    print("PASS"); return True


def test_bundled_skills_are_guarded_from_packs():
    """v4: bundled skills and on-demand packs SHARE .agents/skills/.

    The old assertion (no bundled artifact may map there) was inverted by the
    migration. What must hold now is that a pack cannot overwrite a bundled
    lifecycle skill — enforced by sync_skills.assert_not_reserved().
    """
    print("--- test_bundled_skills_are_guarded_from_packs ---")
    versions = json.loads((REPO_ROOT / "dist/skills/stratosphere-setup/versions.json").read_text(encoding="utf-8"))
    artifacts = versions.get("artifacts", {})
    assert artifacts, "expected a non-empty bundled manifest"

    mapped = [scaffold.map_bundled_to_project(r) for r in artifacts]
    skills = [m for m in mapped if m and m.startswith(".agents/skills/")]
    assert skills, "expected bundled skills to map into .agents/skills/ under v4"

    src = (REPO_ROOT / "src/commands/sync-skills/scripts/sync_skills.py").read_text(encoding="utf-8")
    assert "def assert_not_reserved(" in src, "sync_skills must define the reserved-name guard"
    assert "stratos.layer: lifecycle" in src, "guard must identify bundled skills by layer"
    assert "assert_not_reserved(target_dir" in src, "guard must be called from fetch()"
    print(f"PASS ({len(skills)} bundled skills in .agents/skills/, pack guard wired)"); return True


def test_pack_pin_is_not_older_than_the_rename_release():
    """The pack is fetched at the registry's `ref`. v2.1.0 predates the v4.0.0 rename, so a project that
    synced it got /4a_verify-and-ship style commands that no longer resolve."""
    print("--- test_pack_pin_is_not_older_than_the_rename_release ---")
    data = json.loads((REPO_ROOT / "src/external-skills.json").read_text(encoding="utf-8"))
    entry = next(s for s in data["skills"] if s["name"] == "jules-dispatch")
    m = re.fullmatch(r"v(\d+)\.(\d+)\.(\d+)", entry["ref"])
    assert m, f"pin a release tag (vX.Y.Z), got {entry['ref']!r}"
    assert tuple(map(int, m.groups())) >= (4, 0, 0), f"{entry['ref']} predates the v4.0.0 skill rename"
    assert entry["ref"] in entry["description"], "the description must name the tag it is pinned to"
    print("PASS"); return True


TESTS = [test_no_experimental_in_dist, test_external_skills_entry_opt_in, test_bundled_skills_are_guarded_from_packs,
         test_pack_pin_is_not_older_than_the_rename_release]

if __name__ == "__main__":
    ok = True
    for t in TESTS:
        try:
            ok = t() and ok
        except AssertionError as e:
            print(f"FAIL: {t.__name__}: {e}"); ok = False
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
    sys.exit(0 if ok else 1)
