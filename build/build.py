#!/usr/bin/env python3
"""Build StratosphereOS plugins for Claude Code and Antigravity from a single src/ tree.

Run:  python build/build.py
Outputs:
  dist/claude-code/   - Claude Code plugin (.claude-plugin/plugin.json, commands/, skills/)
  dist/antigravity/   - Antigravity plugin (plugin.json, workflows/, skills/)
  .claude-plugin/marketplace.json  - repo-root marketplace so `/plugin marketplace add` works

Skills are byte-identical between platforms; only the manifest and the
workflow-vs-command directory naming differ. Project-instance content
(constitution, memory templates, rules) ships as assets/templates/
and is written into a project by the stratosphere-setup skill, not on install.
"""
import json
import os
import re
import shutil
import stat
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src" / "scripts"))
import _versioning

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
DIST = ROOT / "dist"

# --- Version Signal Propagation ---------------------------------------------
# Bumping this VERSION propagates to the following files upon running build:
# 1. dist/claude-code/.claude-plugin/plugin.json (version)
# 2. dist/antigravity/plugin.json (version)
# 3. dist/claude-code/versions.json (plugin_version)
# 4. dist/antigravity/versions.json (plugin_version)
# 5. .claude-plugin/marketplace.json (via DESCRIPTION / metadata)
#
# NOTE: The version badge in README.md (~line 4) is auto-stamped by
# scripts/release.py during the release process, and validate.py
# asserts that they remain in exact synchronization.
# ----------------------------------------------------------------------------
VERSION = "4.0.0"
DESCRIPTION = (
    "StratosphereOS: a weightless 3-layer agentic OS. Ships lifecycle workflows, "
    "a first-party skill, on-demand external skills, and a one-command project installer."
)
AUTHOR = "Gravity Technologies"


# --- frontmatter helpers ---------------------------------------------------

def split_frontmatter(text):
    """Return (frontmatter_str_or_None, body)."""
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?(.*)$", text, re.S)
    if m:
        return m.group(1), m.group(2)
    return None, text


def top_level_keys(fm):
    keys = set()
    for line in fm.splitlines():
        if line and not line[0].isspace() and ":" in line:
            keys.add(line.split(":", 1)[0].strip())
    return keys


def ensure_frontmatter(text, name=None, description=None, version=None):
    """Guarantee name/description/version exist without stripping existing keys (type, trigger...)."""
    fm, body = split_frontmatter(text)
    lines = fm.splitlines() if fm is not None else []
    keys = top_level_keys(fm) if fm is not None else set()
    if name and "name" not in keys:
        lines.insert(0, f"name: {name}")
    if description and "description" not in keys:
        lines.append(f"description: {description}")
    if version and "version" not in keys:
        lines.append(f"version: \"{version}\"")
    new_fm = "\n".join(lines)
    if fm is None:
        return f"---\n{new_fm}\n---\n\n{body}"
    return f"---\n{new_fm}\n---\n{body}"


def first_heading(text):
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("#"):
            return s.lstrip("#").strip()
    return None


def copy_md_with_frontmatter(srcfile: Path, dstfile: Path, name=None):
    text = srcfile.read_text(encoding="utf-8")
    desc = None
    fm, _ = split_frontmatter(text)
    if fm is None or "description" not in top_level_keys(fm):
        desc = first_heading(text) or srcfile.stem.replace("_", " ").replace("-", " ")
    out = ensure_frontmatter(text, name=name, description=desc, version=VERSION)
    dstfile.parent.mkdir(parents=True, exist_ok=True)
    write_lf(dstfile, out)


def write_lf(path: Path, text: str):
    """Write text with deterministic LF newlines so build output is identical on any OS."""
    path.write_text(text, encoding="utf-8", newline="\n")


def force_rmtree(path: Path):
    """Remove a tree, tolerating OneDrive locks and read-only files (Windows)."""
    def onexc(func, p, exc):
        try:
            os.chmod(p, stat.S_IWRITE)
            func(p)
        except OSError:
            pass
    import sys
    for _ in range(4):
        if not path.exists():
            return
        if sys.version_info >= (3, 12):
            shutil.rmtree(path, onexc=onexc)
        else:
            shutil.rmtree(path, onerror=onexc)
        if not path.exists():
            return
        time.sleep(0.4)
    if path.exists():
        raise OSError(f"could not remove {path} (locked by another process / OneDrive?)")


def copytree(src: Path, dst: Path):
    shutil.copytree(src, dst, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "test"))


# --- workflow / command naming --------------------------------------------

def command_name(stem: str) -> str:
    """Slug used as the invocable command/workflow name."""
    return stem


# Two citation forms: the relative `references/<file>.md` a skill uses for itself,
# and the absolute `.agents/skills/<name>/references/<file>.md` required wherever a
# path is handed to an isolated subagent (whose cwd is the repo root, not the skill).
REF_CITE = re.compile(
    r'\.agents/skills/[a-z0-9-]+/references/([A-Za-z0-9_.-]+\.md)'
    r'|(?<![\w/.])references/([A-Za-z0-9_.-]+\.md)')


def cited_refs(text):
    """Reference filenames cited by a body, in either citation form."""
    return {a or b for a, b in REF_CITE.findall(text)}


def closure_for(text: str, ref_dir) -> set:
    """Transitive closure: a reference may itself cite further references."""
    seen, queue = set(), list(cited_refs(text))
    while queue:
        name = queue.pop()
        if name in seen:
            continue
        src = ref_dir / name
        if not src.exists():
            print(f"  WARNING: cited reference not found: {name}")
            continue
        seen.add(name)
        queue.extend(cited_refs(src.read_text(encoding="utf-8")) - seen)
    return seen


CODEX_SIDECAR = """# Codex reads invocation policy from this fixed path, not from SKILL.md
# frontmatter. Keep in sync with `disable-model-invocation` / `triggers`.
policy:
  allow_implicit_invocation: false
"""


def emit_skill(src_md, name, skills_dir, ref_dir):
    """Emit one self-contained skill: SKILL.md + its transitive references/."""
    dst = skills_dir / name
    dst.mkdir(parents=True, exist_ok=True)
    copy_md_with_frontmatter(src_md, dst / "SKILL.md", name=name)
    body = src_md.read_text(encoding="utf-8")

    # Codex honours no frontmatter field; it reads <skill>/agents/openai.yaml by
    # fixed convention. Emit it wherever the skill declares itself manual-only.
    if re.search(r'^disable-model-invocation:\s*true\s*$', body, re.M):
        (dst / "agents").mkdir(exist_ok=True)
        write_lf(dst / "agents" / "openai.yaml", CODEX_SIDECAR)

    refs = closure_for(body, ref_dir)
    for rname in sorted(refs):
        (dst / "references").mkdir(exist_ok=True)
        shutil.copy2(ref_dir / rname, dst / "references" / rname)
    return len(refs)


# --- per-platform assembly -------------------------------------------------

def build_platform(kind: str):
    out = DIST / ("claude-code" if kind == "claude" else "antigravity")
    force_rmtree(out)
    out.mkdir(parents=True)

    skills_dir = out / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    ref_dir = SRC / "references"

    # 1. Execution skills (self-contained by construction)
    for skill in (SRC / "skills").iterdir():
        if skill.is_dir():
            dst = skills_dir / skill.name
            copytree(skill, dst)
            sk = dst / "SKILL.md"
            if sk.exists():
                copy_md_with_frontmatter(sk, sk, name=skill.name)

    # 2. Lifecycle skills + their transitive references. One canonical shape for
    #    every host: .agents/skills/<name>/SKILL.md, invocable as /<name>.
    total_refs = 0
    for wf in sorted((SRC / "workflows").glob("*.md")):
        total_refs += emit_skill(wf, wf.stem, skills_dir, ref_dir)

    # 3. Install/upgrade/sync drivers - skills like everything else
    for dirname, name in (("stratosphere-setup", "stratosphere-setup"),
                          ("stratosphere-update", "stratosphere-update"),
                          ("sync-skills", "sync-skills")):
        src_md = SRC / "commands" / dirname / "SKILL.md"
        total_refs += emit_skill(src_md, name, skills_dir, ref_dir)
    copytree(SRC / "commands" / "sync-skills" / "scripts", out / "scripts")
    shutil.copy2(SRC / "external-skills.json", out / "external-skills.json")
    print(f"  {kind}: {len(list(skills_dir.iterdir()))} skills, {total_refs} reference copies")

    # 5. Project-instance templates (written into a project by the installer)
    assets = out / "assets" / "templates"
    copytree(SRC / "constitution", assets / "constitution")
    copytree(SRC / "rules", assets / "rules")
    copytree(SRC / "memory-templates", assets / "memory")
    copytree(SRC / "github", assets / "github")
    copytree(SRC / "scripts", out / "scripts")

    # 5.5 Post-copy pass to stamp version into asset templates
    for path in assets.rglob("*.md"):
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            fm, _ = split_frontmatter(text)
            fm_keys = top_level_keys(fm) if fm is not None else set()
            if "version" not in fm_keys:
                out_content = ensure_frontmatter(text, version=VERSION)
                write_lf(path, out_content)

    # 6. Manifest
    if kind == "claude":
        manifest_dir = out / ".claude-plugin"
        manifest_dir.mkdir(parents=True)
        manifest = {
            "name": "stratosphere-os",
            "version": VERSION,
            "description": DESCRIPTION,
            "author": {"name": AUTHOR},
        }
        write_lf(manifest_dir / "plugin.json", json.dumps(manifest, indent=2) + "\n")
    else:
        manifest = {
            "name": "stratosphere-os",
            "version": VERSION,
            "description": DESCRIPTION,
            "author": AUTHOR,
        }
        write_lf(out / "plugin.json", json.dumps(manifest, indent=2) + "\n")

    # 7. Generate versions.json
    artifacts = {}
    for root_dir, _, files in os.walk(out):
        for f in files:
            if not f.endswith(".md"): continue
            p = Path(root_dir) / f
            rel = p.relative_to(out).as_posix()
            text = p.read_text(encoding="utf-8")
            v, ts = _versioning.read_version(text, p)
            if v:
                artifacts[rel] = {
                    "version": v,
                    "sha256": _versioning.body_hash(text),
                    "timestamp": ts
                }
            else:
                raise ValueError(f"Missing versioning marker in {p}. Every .md file in the plugin MUST have a version stamp in its YAML frontmatter.")
    
    versions_manifest = {
        "plugin_version": VERSION,
        "artifacts": artifacts
    }
    write_lf(out / "versions.json", json.dumps(versions_manifest, indent=2, sort_keys=True) + "\n")

    return out


def write_marketplace():
    mk_dir = ROOT / ".claude-plugin"
    mk_dir.mkdir(parents=True, exist_ok=True)
    marketplace = {
        "name": "stratosphere-os",
        "owner": {"name": "PatN-git"},
        "plugins": [
            {
                "name": "stratosphere-os",
                "source": "./dist/claude-code",
                "description": DESCRIPTION,
            }
        ],
    }
    write_lf(mk_dir / "marketplace.json", json.dumps(marketplace, indent=2) + "\n")


def main():
    DIST.mkdir(exist_ok=True)
    for kind in ("claude", "antigravity"):
        out = build_platform(kind)
        print(f"[built] {out.relative_to(ROOT)}")
    write_marketplace()
    print("[built] .claude-plugin/marketplace.json")


if __name__ == "__main__":
    main()
