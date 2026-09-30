#!/usr/bin/env python3
"""
okf_view.py

A wrapper script to generate the OKF visualizer dashboard for a StratosphereOS project.
Optionally rewrites internal [[ID]] links into standard markdown links in a temp directory
before generating the visualization, enabling dependency edge rendering for internal concepts.
"""

import sys
import os
import re
import shutil
import tempfile
import argparse
from pathlib import Path

# Add the script's directory to the Python path to import okf_viewer
sys.path.insert(0, str(Path(__file__).parent.resolve()))

try:
    from okf_viewer.generator import generate_visualization
except ImportError as e:
    print(f"Error: Could not import okf_viewer. Ensure okf_viewer folder is present. {e}")
    sys.exit(1)


def scan_definitions(project_root: Path) -> dict[str, str]:
    """Scans the memory layer for [[ID]] definitions, returning id -> relative_file_path."""
    definitions = {}
    memory_dir = project_root / ".memory"
    if not memory_dir.is_dir():
        return definitions

    target_files = [
        "LEARNINGS.md",
        "GLOSSARY.md",
        "ARCHITECTURE.md",
        "DESIGN_RULES.md",
        "BACKLOG_MAP.md"
    ]

    DEF_RE = re.compile(r"^\s*(?:[-*+]\s+\**|#+\s+)?\[\[([A-Za-z0-9_-]+)\]\]")
    TABLE_RE = re.compile(r"^\s*\|\s*(?:\[\[)?([A-Za-z0-9_-]+)(?:\]\])?\s*\|")

    for fname in target_files:
        fpath = memory_dir / fname
        if not fpath.is_file():
            continue

        try:
            content = fpath.read_text(encoding="utf-8")
            for line in content.splitlines():
                # Check Backlog Map table rows
                if fname == "BACKLOG_MAP.md":
                    m = TABLE_RE.match(line)
                    if m:
                        def_id = m.group(1)
                        if not def_id.endswith("-x") and not def_id.endswith("-ID"):  # Skip placeholders
                            definitions[def_id] = f".memory/{fname}"
                    continue

                # Check standard list or heading item definitions
                m = DEF_RE.match(line)
                if m:
                    def_id = m.group(1)
                    if not def_id.endswith("-x") and not def_id.endswith("-ID"):
                        definitions[def_id] = f".memory/{fname}"
        except Exception as e:
            print(f"Warning: Could not scan definitions in {fname}: {e}")

    return definitions


def rewrite_content(content: str, source_rel_path: str, id_map: dict[str, str]) -> str:
    """Replaces [[ID]] links in the content with standard markdown links relative to the source file."""
    # Find all [[ID]] patterns
    ID_PATTERN = re.compile(r"\[\[([A-Za-z0-9_-]+)\]\]")
    
    def repl(match):
        ref_id = match.group(1)
        target_rel_path = id_map.get(ref_id)
        if not target_rel_path:
            return match.group(0)  # Keep as-is if undefined

        # Compute relative path from source_rel_path's parent directory to target_rel_path
        src_parent = os.path.dirname(source_rel_path)
        try:
            rel_path = os.path.relpath(target_rel_path, src_parent)
            # Ensure POSIX style separators for markdown links
            rel_path = rel_path.replace(os.path.sep, "/")
            return f"[{ref_id}]({rel_path})"
        except Exception:
            return match.group(0)

    return ID_PATTERN.sub(repl, content)


def main():
    parser = argparse.ArgumentParser(description="Generate OKF visualization for StratosphereOS.")
    parser.add_argument("--project-root", default=".", help="Path to the project root directory")
    parser.add_argument("--out", default="docs/okf-view.html", help="Path to write the visualization HTML")
    parser.add_argument("--no-rewrite", action="store_true", help="Disable [[ID]] internal reference rewriting")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    out_path = Path(args.out).resolve()

    if not (project_root / ".memory").is_dir() and not (project_root / "docs").is_dir():
        print(f"Error: Directory does not look like a StratosphereOS project: {project_root}")
        print("Could not find '.memory' or 'docs' directory.")
        sys.exit(1)

    # Gather files to copy/visualize
    items_to_copy = []
    
    # Root index.md
    root_index = project_root / "index.md"
    if root_index.is_file():
        items_to_copy.append(("index.md", root_index))

    # .memory directory
    memory_dir = project_root / ".memory"
    if memory_dir.is_dir():
        for p in memory_dir.rglob("*.md"):
            rel_path = p.relative_to(project_root)
            items_to_copy.append((str(rel_path), p))

    # docs directory
    docs_dir = project_root / "docs"
    if docs_dir.is_dir():
        for p in docs_dir.rglob("*.md"):
            # Exclude docs/knowledge/ subfolders if they are foreign, but let's copy docs/knowledge/index.md
            rel_path = p.relative_to(project_root)
            parts = rel_path.parts
            if len(parts) > 2 and parts[0] == "docs" and parts[1] == "knowledge" and parts[2] != "index.md":
                # Foreign knowledge concept file, skip copying/rewriting
                continue
            items_to_copy.append((str(rel_path), p))

    id_map = {} if args.no_rewrite else scan_definitions(project_root)

    # Create temporary directory to generate visualization from
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_root = Path(temp_dir_str)

        # Copy and optionally rewrite files
        for rel_path_str, src_path in items_to_copy:
            dest_path = temp_root / rel_path_str
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            try:
                if args.no_rewrite or not rel_path_str.endswith(".md"):
                    shutil.copy2(src_path, dest_path)
                else:
                    content = src_path.read_text(encoding="utf-8")
                    rewritten = rewrite_content(content, rel_path_str, id_map)
                    dest_path.write_text(rewritten, encoding="utf-8")
            except Exception as e:
                print(f"Warning: Failed to process {rel_path_str}: {e}")
                # Fallback to copy
                try:
                    shutil.copy2(src_path, dest_path)
                except Exception:
                    pass

        # Generate visualization
        try:
            print(f"Generating OKF visualizer from bundle...")
            stats = generate_visualization(
                bundle_root=temp_root,
                out_path=out_path,
                bundle_name=project_root.name
            )
            print(f"Success! Generated '{out_path.relative_to(project_root) if out_path.is_relative_to(project_root) else out_path}'")
            print(f"Stats: {stats['concepts']} concepts, {stats['edges']} edges, {stats['bytes']} bytes")
        except Exception as e:
            print(f"Error generating visualization: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
