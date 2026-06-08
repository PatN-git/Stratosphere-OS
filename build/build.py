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
and is written into a project by the instantiate command, not on install.
"""
import json
import os
import re
import shutil
import stat
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
DIST = ROOT / "dist"
VERSION = "1.0.0"
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


def ensure_frontmatter(text, name=None, description=None):
    """Guarantee name/description exist without stripping existing keys (type, trigger...)."""
    fm, body = split_frontmatter(text)
    lines = fm.splitlines() if fm is not None else []
    keys = top_level_keys(fm) if fm is not None else set()
    if name and "name" not in keys:
        lines.insert(0, f"name: {name}")
    if description and "description" not in keys:
        lines.append(f"description: {description}")
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
    out = ensure_frontmatter(text, name=name, description=desc)
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
    for _ in range(4):
        if not path.exists():
            return
        shutil.rmtree(path, onexc=onexc)
        if not path.exists():
            return
        time.sleep(0.4)
    if path.exists():
        raise OSError(f"could not remove {path} (locked by another process / OneDrive?)")


def copytree(src: Path, dst: Path):
    shutil.copytree(src, dst, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))


# --- workflow / command naming --------------------------------------------

def command_name(stem: str) -> str:
    """Slug used as the invocable command/workflow name."""
    return stem


# --- per-platform assembly -------------------------------------------------

def build_platform(kind: str):
    out = DIST / ("claude-code" if kind == "claude" else "antigravity")
    force_rmtree(out)
    out.mkdir(parents=True)

    # invocable folder differs: Claude=commands/, Antigravity=workflows/
    invoke_dir = out / ("commands" if kind == "claude" else "workflows")
    invoke_dir.mkdir(parents=True)

    # 1. First-party skill(s)
    for skill in (SRC / "skills").iterdir():
        if skill.is_dir():
            dst = out / "skills" / skill.name
            copytree(skill, dst)
            sk = dst / "SKILL.md"
            if sk.exists():
                copy_md_with_frontmatter(sk, sk, name=skill.name)

    # 2. Numbered lifecycle workflows -> invocable
    for wf in sorted((SRC / "workflows").glob("*.md")):
        copy_md_with_frontmatter(wf, invoke_dir / wf.name, name=command_name(wf.stem))

    # 3. Installer entry point. Claude registers plugin commands globally, so ship
    #    it as a /command. Antigravity only surfaces skills (not plugin workflows),
    #    so ship it there as a discoverable skill instead.
    inst = SRC / "commands" / "instantiate" / "Instantiate-StratosphereOS.md"
    if kind == "claude":
        copy_md_with_frontmatter(inst, invoke_dir / "stratosphere-setup.md",
                                 name="stratosphere-setup")
    else:
        sk = out / "skills" / "stratosphere-setup" / "SKILL.md"
        sk.parent.mkdir(parents=True, exist_ok=True)
        copy_md_with_frontmatter(inst, sk, name="stratosphere-setup")

    # 4. sync-skills command + script + registry
    sync_md = SRC / "commands" / "sync-skills" / "SKILL_sync-skills.md"
    copy_md_with_frontmatter(sync_md, invoke_dir / "sync-skills.md", name="sync-skills")
    copytree(SRC / "commands" / "sync-skills" / "scripts", out / "scripts")
    shutil.copy2(SRC / "external-skills.json", out / "external-skills.json")

    # 5. Project-instance templates (written into a project by the installer)
    assets = out / "assets" / "templates"
    copytree(SRC / "constitution", assets / "constitution")
    copytree(SRC / "rules", assets / "rules")
    copytree(SRC / "memory-templates", assets / "memory")
    copytree(SRC / "references", assets / "references")
    copytree(SRC / "scripts", out / "scripts")

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
