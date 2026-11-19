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
HOSTS = ["dist"]  # one canonical bundle: dist/skills
NAME_RE = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')

# a citation is either skill-relative (bare or <skill-dir>/) or, at a subagent boundary, absolute
REL_CITE = re.compile(r'(?:(?<![\w/.>])|<skill-dir>/)references/([A-Za-z0-9_.-]+\.md)')
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


def test_rel_cite_recognizes_skill_dir_without_double_match():
    sample = (
        "Read <skill-dir>/references/alpha.md, "
        ".agents/skills/other/references/beta.md, "
        "and references/gamma.md (ignore custom/references/delta.md)."
    )
    assert REL_CITE.findall(sample) == ["alpha.md", "gamma.md"]


def test_every_cited_reference_ships_validates_skill_dir_in_skill_and_references(tmp_path, monkeypatch):
    demo = tmp_path / "dist" / "skills" / "demo"
    refs = demo / "references"
    refs.mkdir(parents=True)
    (demo / "SKILL.md").write_text(
        "---\nname: demo\ndescription: demo\nversion: \"1.0.0\"\n---\n"
        "See <skill-dir>/references/parent.md and <skill-dir>/references/missing-from-skill.md\n",
        encoding="utf-8",
    )
    (refs / "parent.md").write_text(
        "---\nversion: \"1.0.0\"\n---\n"
        "See <skill-dir>/references/missing-from-ref.md\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(sys.modules[__name__], "REPO_ROOT", tmp_path)

    with pytest.raises(AssertionError) as exc:
        test_every_cited_reference_ships("dist")
    msg = str(exc.value)
    assert "demo -> references/missing-from-skill.md" in msg
    assert "demo/references/parent.md -> missing-from-ref.md" in msg

    (refs / "missing-from-skill.md").write_text("---\nversion: \"1.0.0\"\n---\n", encoding="utf-8")
    (refs / "missing-from-ref.md").write_text("---\nversion: \"1.0.0\"\n---\n", encoding="utf-8")
    test_every_cited_reference_ships("dist")


@pytest.mark.parametrize("host", HOSTS)
def test_self_contained_execution_skills_anchor_paths_to_skill_dir(host):
    """plan-html and concept-brainstorm must anchor assets/ and references/ to <skill-dir>,
    never bare relative paths or <workspace>/skills/... that fail in plugin mode (BT-275)."""
    skills = {d.name: d for d in skill_dirs(host)}
    plan_dir = skills["plan-html"]
    plan_skill = (plan_dir / "SKILL.md").read_text(encoding="utf-8")
    assert "`<skill-dir>/assets/templates/index.md`" in plan_skill
    assert "`<skill-dir>/assets/templates/`" in plan_skill
    assert "`<skill-dir>/references/html-patterns.md`" in plan_skill
    assert "directory containing this `SKILL.md`" in plan_skill
    assert "never the workspace root" in plan_skill
    assert "<workspace>/skills/" not in plan_skill
    assert (plan_dir / "assets" / "templates" / "index.md").is_file()
    assert (plan_dir / "references" / "html-patterns.md").is_file()

    plan_index = (plan_dir / "assets" / "templates" / "index.md").read_text(encoding="utf-8")
    assert "`<skill-dir>/references/html-patterns.md`" in plan_index
    assert "never the workspace root" in plan_index

    brainstorm_dir = skills["concept-brainstorm"]
    brainstorm = (brainstorm_dir / "SKILL.md").read_text(encoding="utf-8")
    assert "`<skill-dir>/references/techniques.md`" in brainstorm
    assert "directory containing this `SKILL.md`" in brainstorm
    assert "never the workspace root" in brainstorm
    assert "<workspace>/skills/" not in brainstorm
    assert (brainstorm_dir / "references" / "techniques.md").is_file()


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


def test_no_second_host_tree_exists():
    """C3: one canonical skill set, no content fork. Byte-identity used to be diffed between
    dist/claude-code and dist/antigravity; BT-118 made the fork structurally impossible."""
    assert not (REPO_ROOT / "dist" / "claude-code").exists()
    assert not (REPO_ROOT / "dist" / "antigravity").exists()


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
    assert targets == [".agents/skills"], \
        "every host reads .agents/skills (Copilot included); a second copy would double-list skills"


def test_fresh_scaffold_places_skills_under_agents_only(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    scaffold = REPO_ROOT / "dist" / "skills" / "stratosphere-setup" / "scripts" / "scaffold.py"
    r = subprocess.run([sys.executable, str(scaffold)], cwd=tmp_path, capture_output=True)
    assert r.returncode == 0, r.stdout.decode("utf-8", "replace")[-500:]
    assert (tmp_path / ".agents" / "skills" / "micro-tdd" / "SKILL.md").is_file()
    assert not (tmp_path / ".agents" / "skills" / "stratosphere-setup" / "scripts").exists(), \
        "scaffolder payload stays in the bundle; it is not a project skill file"
    assert not (tmp_path / ".github" / "copilot").exists(), "no host reads .github/copilot/skills; scaffold must not create it"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
