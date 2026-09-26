#!/usr/bin/env python3
"""Agent Skills spec conformance for the emitted skill tree.

Coverage the v4.0.0 migration needs and nothing previously had:
  - every emitted skill satisfies the spec's name rules
  - every cited reference actually ships inside the citing skill
  - `.agents/skills/` is NOT gitignored (it holds the bundled skills)
  - lifecycle skills declare user-only invocation on every host that honours one
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HOSTS = ["dist/antigravity", "dist/claude-code"]
NAME_RE = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')

# a citation is either skill-relative or, at a subagent boundary, absolute
REL_CITE = re.compile(r'(?<![\w/.])references/([A-Za-z0-9_.-]+\.md)')
ABS_CITE = re.compile(r'\.agents/skills/([a-z0-9-]+)/references/([A-Za-z0-9_.-]+\.md)')


def skill_dirs(host: str):
    base = REPO_ROOT / host / "skills"
    if not base.is_dir():
        pytest.skip(f"{host}/skills not built")
    return sorted(d for d in base.iterdir() if d.is_dir())


def frontmatter(md: Path) -> str:
    m = re.match(r'^---\r?\n(.*?)\r?\n---', md.read_text(encoding="utf-8"), flags=re.S)
    return m.group(1) if m else ""


@pytest.mark.parametrize("host", HOSTS)
def test_skill_names_are_spec_conformant(host):
    """name matches ^[a-z0-9]+(-[a-z0-9]+)*$ AND equals the parent directory."""
    bad = []
    for d in skill_dirs(host):
        md = d / "SKILL.md"
        assert md.exists(), f"{d.name} has no SKILL.md"
        m = re.search(r'^name:[ \t]*(.+?)[ \t]*$', frontmatter(md), flags=re.M)
        name = m.group(1).strip().strip('"') if m else None
        if not name or not NAME_RE.match(name) or name != d.name:
            bad.append(f"{d.name}: name={name!r}")
    assert not bad, "spec-invalid skill names: " + "; ".join(bad)


@pytest.mark.parametrize("host", HOSTS)
def test_descriptions_within_spec_limit(host):
    over = []
    for d in skill_dirs(host):
        m = re.search(r'^description:[ \t]*(.+?)[ \t]*$', frontmatter(d / "SKILL.md"), flags=re.M)
        if m and len(m.group(1)) > 1024:
            over.append(f"{d.name} ({len(m.group(1))})")
    assert not over, "description exceeds the spec's 1024 chars: " + ", ".join(over)


@pytest.mark.parametrize("host", HOSTS)
def test_every_cited_reference_ships(host):
    """A shared reference must be present in EVERY skill that cites it.

    build.py fans references out transitively. Regressing that regex silently
    empties the closure and every skill ships dangling pointers.
    """
    base = REPO_ROOT / host / "skills"
    broken = []
    for d in skill_dirs(host):
        text = (d / "SKILL.md").read_text(encoding="utf-8")
        for fname in REL_CITE.findall(text):
            if not (d / "references" / fname).exists():
                broken.append(f"{d.name} -> references/{fname}")
        for owner, fname in ABS_CITE.findall(text):
            if not (base / owner / "references" / fname).exists():
                broken.append(f"{d.name} -> {owner}/references/{fname}")
        # a reference may cite a sibling reference
        for ref in sorted((d / "references").glob("*.md")) if (d / "references").is_dir() else []:
            for fname in REL_CITE.findall(ref.read_text(encoding="utf-8")):
                if not (d / "references" / fname).exists():
                    broken.append(f"{d.name}/references/{ref.name} -> {fname}")
    assert not broken, "dangling reference citations:\n  " + "\n  ".join(broken)


@pytest.mark.parametrize("host", HOSTS)
def test_lifecycle_skills_declare_user_only(host):
    """Every host that honours a manual-only signal must get one."""
    missing = []
    for d in skill_dirs(host):
        fm = frontmatter(d / "SKILL.md")
        if "stratos.layer: lifecycle" not in fm:
            continue
        if "disable-model-invocation: true" not in fm:
            missing.append(f"{d.name}: disable-model-invocation (Claude Code, Cursor, OpenClaw)")
        if 'triggers: ["user"]' not in fm:
            missing.append(f"{d.name}: triggers (Devin)")
        if not (d / "agents" / "openai.yaml").exists():
            missing.append(f"{d.name}: agents/openai.yaml (Codex)")
    assert not missing, "lifecycle skills missing manual-only declarations:\n  " + "\n  ".join(missing)


@pytest.mark.parametrize("host", HOSTS)
def test_execution_skills_are_not_manual_only(host):
    wrong = [d.name for d in skill_dirs(host)
             if "stratos.layer: execution" in frontmatter(d / "SKILL.md")
             and (d / "agents" / "openai.yaml").exists()]
    assert not wrong, "execution skills must stay model-invocable: " + ", ".join(wrong)


def test_hosts_are_byte_identical():
    """C3: one canonical skill set, no content fork."""
    a, b = (REPO_ROOT / h / "skills" for h in HOSTS)
    if not (a.is_dir() and b.is_dir()):
        pytest.skip("skills not built for both hosts")
    import shutil
    if shutil.which("diff"):
        res = subprocess.run(["diff", "-rq", str(a), str(b)], capture_output=True, text=True)
        assert res.returncode == 0, f"hosts diverged:\n{res.stdout}"
    else:
        import filecmp
        def _diff_dirs(d1, d2):
            cmp = filecmp.dircmp(d1, d2)
            diffs = list(cmp.left_only) + list(cmp.right_only) + list(cmp.diff_files)
            for sub in cmp.common_dirs:
                diffs.extend(_diff_dirs(d1 / sub, d2 / sub))
            return diffs
        diffs = _diff_dirs(a, b)
        assert not diffs, f"hosts diverged: {diffs}"


def test_skills_dir_is_not_gitignored():
    """`.agents/skills/` holds the bundled skills; ignoring it untracks all 22."""
    entries = (REPO_ROOT / "src" / "scripts" / "scaffold.py").read_text(encoding="utf-8")
    m = re.search(r'GITIGNORE_ENTRIES = \[(.*?)\]', entries, flags=re.S)
    assert m, "GITIGNORE_ENTRIES not found"
    assert '".agents/skills/"' not in m.group(1), \
        "`.agents/skills/` must not be gitignored - it would untrack every bundled skill"


def test_no_legacy_workflow_paths_remain():
    stale = []
    for host in HOSTS:
        for legacy in ("workflows", "commands"):
            if (REPO_ROOT / host / legacy).exists():
                stale.append(f"{host}/{legacy}")
    assert not stale, "retired output dirs still emitted: " + ", ".join(stale)


def test_placement_map_covers_every_host():
    """A new host must be a SKILL_TARGETS entry, never a content fork (C3)."""
    src = (REPO_ROOT / "src" / "scripts" / "scaffold.py").read_text(encoding="utf-8")
    m = re.search(r'SKILL_TARGETS = \[(.*?)\]', src, flags=re.S)
    assert m, "SKILL_TARGETS not found in scaffold.py"
    targets = re.findall(r'"([^"]+)"', m.group(1))
    assert ".agents/skills" in targets, "must serve Cursor, Codex, Antigravity, Devin, OpenClaw"
    assert ".github/copilot/skills" in targets, "must serve VS Code Copilot"
    assert ".github/skills" not in targets, ".github/skills is a Devin read path, not Copilot's"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
