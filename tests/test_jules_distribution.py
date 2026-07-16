#!/usr/bin/env python3
"""Distribution + update-safety tests for the jules-dispatch pack (P5).

Proves: (a) experimental source never leaks into dist, (b) the external-skills.json
entry is present and opt-in, (c) scaffold --update never targets .agents/skills/, so
a fetched pack survives updates byte-identical.

Run: python tests/test_jules_distribution.py
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src" / "scripts"))
import scaffold  # noqa: E402


def test_no_experimental_in_dist():
    print("--- test_no_experimental_in_dist ---")
    for plat in ("dist/claude-code", "dist/antigravity"):
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
    # flows into both dist copies
    for plat in ("dist/claude-code", "dist/antigravity"):
        assert _entry(f"{plat}/external-skills.json") is not None, f"entry missing in {plat}"
    print("PASS"); return True


def test_update_never_targets_skills_dir():
    print("--- test_update_never_targets_skills_dir ---")
    versions = json.loads((REPO_ROOT / "dist/antigravity/versions.json").read_text(encoding="utf-8"))
    artifacts = versions.get("artifacts", {})
    assert artifacts, "expected a non-empty bundled manifest"
    for rel in artifacts:
        proj = scaffold.map_bundled_to_project(rel)
        if proj:
            assert not proj.startswith(".agents/skills"), \
                f"bundled artifact {rel} maps to {proj} — would collide with the on-demand pack"
    print("PASS (no bundled artifact maps into .agents/skills/)"); return True


TESTS = [test_no_experimental_in_dist, test_external_skills_entry_opt_in, test_update_never_targets_skills_dir]

if __name__ == "__main__":
    ok = True
    for t in TESTS:
        try:
            ok = t() and ok
        except AssertionError as e:
            print(f"FAIL: {t.__name__}: {e}"); ok = False
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
    sys.exit(0 if ok else 1)
