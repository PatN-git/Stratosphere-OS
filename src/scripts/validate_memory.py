#!/usr/bin/env python3
"""
validate_memory.py

A deterministic memory validator for the Stratosphere OS memory protocol.
Ensures memory files follow trust tag, ID uniqueness, supersession,
cross-reference, and secret hygiene rules.

Exit Codes:
  0 - Clean
  1 - Errors (or Warnings if --warnings-as-errors is set)
  2 - Warnings (only when --warnings-as-errors is NOT set)
"""

import sys
import os
import re
import argparse
import json
from pathlib import Path

# Common Secret Signatures
SECRET_PATTERNS = {
    'OpenAI API Key': r'\bsk-[a-zA-Z0-9]{48}\b',
    'GitHub Personal Access Token (Classic)': r'\bghp_[a-zA-Z0-9]{36}\b',
    'GitHub Fine-Grained Token': r'\bgithub_pat_[a-zA-Z0-9]{82}\b',
    'AWS Access Key ID': r'\bAKIA[A-Z0-9]{16}\b',
    'Generic Private Key': r'-----BEGIN [A-Z ]+ PRIVATE KEY-----'
}

def scan_file_for_secrets(file_path):
    errors = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for idx, line in enumerate(f, 1):
                for name, pattern in SECRET_PATTERNS.items():
                    if re.search(pattern, line):
                        errors.append(f"Secret detected ({name}) in {file_path.name}:{idx}")
    except Exception as e:
        errors.append(f"Could not read {file_path.name} for secrets: {e}")
    return errors

def is_placeholder(cid):
    return not cid.rsplit('-', 1)[-1].isdigit()

def apply_autofix(memory_dir, file_name, line_num, cid):
    fpath = Path(memory_dir) / file_name
    if not fpath.exists():
        return False
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        idx = line_num - 1
        if idx < 0 or idx >= len(lines):
            return False
            
        line = lines[idx]
        line_stripped = line.rstrip('\r\n')
        newline = line[len(line_stripped):]
        
        # If it's a markdown table row (typically in BACKLOG_MAP.md)
        if '|' in line:
            parts = line.split('|')
            if len(parts) >= 9:
                cell = parts[8].strip()
                if cell == '—' or cell == '-' or cell == '':
                    parts[8] = f" [[{cid}]] "
                else:
                    # If it already has references, check if we need to append
                    if f"[[{cid}]]" not in cell:
                        parts[8] = f" {cell}, [[{cid}]] "
                lines[idx] = '|'.join(parts)
            else:
                last_pipe = line.rfind('|')
                if last_pipe != -1:
                    if f"[[{cid}]]" not in line:
                        lines[idx] = line[:last_pipe].rstrip() + f", [[{cid}]] |" + line[last_pipe+1:]
        else:
            # Glossary or list item
            if f"[[{cid}]]" not in line_stripped:
                if "Refs:" in line_stripped:
                    # Find last bracket link and append reference after it
                    match = re.search(r'(\[\[[A-Za-z0-9_-]+\]\])\s*\.?$', line_stripped)
                    if match:
                        end = match.end(1)
                        lines[idx] = line_stripped[:end] + f", [[{cid}]]" + line_stripped[end:] + newline
                    else:
                        lines[idx] = line_stripped + f", [[{cid}]]" + newline
                else:
                    if line_stripped.endswith('.'):
                        lines[idx] = line_stripped.rstrip('.') + f". Refs: [[{cid}]]." + newline
                    else:
                        lines[idx] = line_stripped + f" Refs: [[{cid}]]" + newline
                    
        with open(fpath, 'w', encoding='utf-8', newline='') as f:
            f.writelines(lines)
        return True
    except Exception as e:
        print(f"Error applying autofix to {file_name}:{line_num}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Validate Stratosphere OS memory protocol compliance.")
    parser.add_argument('--path', default='.memory', help='Path to the memory directory')
    parser.add_argument('--quiet', action='store_true', help='Suppress human-readable console output')
    parser.add_argument('--warnings-as-errors', action='store_true', help='Treat warnings as exit-code errors')
    parser.add_argument('--autofix', action='store_true', help='Automatically attempt to fix one-way reference warnings in place')
    args = parser.parse_args()

    memory_dir = Path(args.path)
    
    errors = []
    warnings = []
    
    if not memory_dir.exists() or not memory_dir.is_dir():
        if not args.quiet:
            print(f"Memory directory '{args.path}' does not exist. Skipping validation.")
        print("# MACHINE")
        print(json.dumps({"clean": True, "errors": [], "warnings": []}))
        sys.exit(0)

    # 1. Scan all files in memory directory for secrets (including STATUS.md, DESIGN.md, etc.)
    for path in memory_dir.glob('*'):
        if path.is_file():
            sec_errs = scan_file_for_secrets(path)
            errors.extend(sec_errs)

    # Files to parse for IDs and protocol compliance
    target_files = [
        'LEARNINGS.md',
        'GLOSSARY.md',
        'ARCHITECTURE.md',
        'DESIGN_RULES.md',
        'BACKLOG_MAP.md'
    ]
    
    definitions = {}
    references = []
    
    # Parse target memory files
    for fname in target_files:
        fpath = memory_dir / fname
        if not fpath.exists():
            continue
            
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            errors.append(f"Could not read {fname}: {e}")
            continue
            
        in_superseded = False
        current_context_id = None
        current_list_indent = None
        
        for line_idx, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped:
                continue
                
            # Detect section transitions
            if line.startswith('#'):
                current_context_id = None
                current_list_indent = None
                heading_match = re.match(r'^(#+)\s+(.*)', line)
                if heading_match:
                    level = len(heading_match.group(1))
                    title = heading_match.group(2).strip().lower()
                    if 'superseded' in title:
                        in_superseded = True
                    elif level == 2:
                        in_superseded = False
            
            # Special Backlog Map table parsing
            if fname == 'BACKLOG_MAP.md':
                table_match = re.match(r'^\s*\|\s*([^|]+)\s*\|', line)
                if table_match:
                    cell_1 = table_match.group(1).strip()
                    # Skip separator or header
                    if not cell_1.startswith(':') and not cell_1.startswith('-') and cell_1.lower() != 'id':
                        clean_id = cell_1.replace('[[', '').replace(']]', '').strip()
                        # Strictly validate format: BT-XXX, BT-LOCAL-<slug>, or BT-[0-9]{3,}
                        if not re.match(r'^(?:BT-XXX|BT-LOCAL-[a-zA-Z0-9_-]+|BT-[0-9]{3,})$', clean_id):
                            errors.append(f"Invalid Backlog ID format '{clean_id}' in {fname}:{line_idx}. Hierarchical suffixes (e.g. BT-059-01) are forbidden. Must be a flat 3+ digit integer (e.g. BT-060) or BT-LOCAL-<slug>.")
                            continue
                        
                        def_id = clean_id
                        
                        # Register definition
                        if not is_placeholder(def_id):
                            if def_id in definitions:
                                prev = definitions[def_id]
                                errors.append(f"Duplicate ID definition: '{def_id}' defined in {prev['file']}:{prev['line_num']} and {fname}:{line_idx}")
                            else:
                                definitions[def_id] = {
                                    'id': def_id,
                                    'file': fname,
                                    'line_num': line_idx,
                                    'tag': None,
                                    'superseded_by': None,
                                    'in_superseded': in_superseded,
                                    'content': stripped
                                }
                                
                                # Validate dual-type labels for non-parent slices (non-placeholders without size:large or early-stage status)
                                parts = [p.strip() for p in line.split('|')]
                                if len(parts) >= 6:
                                    status_str = parts[3].lower()
                                    labels_str = parts[4]
                                    labels = [l.strip() for l in labels_str.split(',') if l.strip()]
                                    
                                    exempt_status = {'planned', 'status:planned', 'needs_spec', 'status:needs_spec'}
                                    if 'size:large' not in labels and status_str not in exempt_status:
                                        primary_types = {'type:bug', 'type:content', 'type:feature', 'type:improvement', 'type:maintenance', 'type:research'}
                                        execution_modes = {'type:HITL', 'type:AFK'}
                                        
                                        has_primary = [l for l in labels if l in primary_types]
                                        has_execution = [l for l in labels if l in execution_modes]
                                        
                                        if not has_primary:
                                            errors.append(f"Slice '{def_id}' in {fname}:{line_idx} is missing a Primary Type label (e.g., type:feature, type:bug, type:improvement).")
                                        elif len(has_primary) > 1:
                                            errors.append(f"Slice '{def_id}' in {fname}:{line_idx} has multiple Primary Type labels: {has_primary}.")
                                            
                                        if not has_execution:
                                            errors.append(f"Slice '{def_id}' in {fname}:{line_idx} is missing an Execution Mode label (type:HITL or type:AFK).")
                                        elif len(has_execution) > 1:
                                            errors.append(f"Slice '{def_id}' in {fname}:{line_idx} has multiple Execution Mode labels: {has_execution}.")
                            
                            # Parse references in the rest of the row
                            ref_ids = re.findall(r'\[\[([A-Za-z0-9_-]+)\]\]', line)
                            if def_id in ref_ids:
                                ref_ids.remove(def_id)
                            for rid in ref_ids:
                                if is_placeholder(rid):
                                    continue
                                references.append({
                                    'id': rid,
                                    'file': fname,
                                    'line_num': line_idx,
                                    'context_id': def_id if not is_placeholder(def_id) else None,
                                    'content': stripped
                                })
                            continue

            # Standard list/heading item parsing
            list_match = re.match(r'^(\s*)([-*+])\s+(.*)', line)
            is_list_item = list_match is not None
            
            id_matches = re.findall(r'\[\[([A-Za-z0-9_-]+)\]\]', line)
            
            DEF_RE = re.compile(r'^\s*[-*+]\s+\**\s*\[\[([A-Za-z0-9_-]+)\]\]')
            def_match = DEF_RE.search(line)
            is_heading_def = line.startswith('#') and id_matches and line.lstrip('#').strip().startswith('[[')

            if def_match or is_heading_def:
                def_id = def_match.group(1) if def_match else id_matches[0]
                
                if is_placeholder(def_id):
                    # Placeholder definition is ignored. All valid refs on this line are just references.
                    ref_ids = [rid for rid in id_matches if not is_placeholder(rid)]
                    if is_list_item:
                        indent = len(list_match.group(1))
                        if current_list_indent is not None and indent > current_list_indent:
                            pass
                        else:
                            current_list_indent = indent
                            current_context_id = None
                else:
                    # Parse trust tag
                    tag_match = re.search(r'\[(LAW|PATTERN|ASSUMED)\]', line)
                    tag = tag_match.group(1) if tag_match else None
                    
                    # Parse superseded target
                    sup_match = re.search(r'\[SUPERSEDED BY\s+(?:\[\[)?([A-Za-z0-9_-]+)(?:\]\])?\]', line, re.IGNORECASE)
                    superseded_by = sup_match.group(1) if sup_match else None
                    
                    # Register definition
                    if def_id in definitions:
                        prev = definitions[def_id]
                        errors.append(f"Duplicate ID definition: '{def_id}' defined in {prev['file']}:{prev['line_num']} and {fname}:{line_idx}")
                    else:
                        definitions[def_id] = {
                            'id': def_id,
                            'file': fname,
                            'line_num': line_idx,
                            'tag': tag,
                            'superseded_by': superseded_by,
                            'in_superseded': in_superseded,
                            'content': stripped
                        }
                    
                    if is_list_item:
                        current_list_indent = len(list_match.group(1))
                        current_context_id = def_id
                        
                    # Remaining matches are references
                    ref_ids = [rid for rid in id_matches[1:] if not is_placeholder(rid)]
            else:
                if is_list_item:
                    indent = len(list_match.group(1))
                    if current_list_indent is not None and indent > current_list_indent:
                        # Sub-item, keep context
                        pass
                    else:
                        current_list_indent = indent
                        current_context_id = None
                else:
                    indent = len(line) - len(line.lstrip())
                    if current_list_indent is not None and indent > current_list_indent:
                        # Indented text block, keep context
                        pass
                    else:
                        current_list_indent = None
                        current_context_id = None
                ref_ids = [rid for rid in id_matches if not is_placeholder(rid)]
                
            for rid in ref_ids:
                references.append({
                    'id': rid,
                    'file': fname,
                    'line_num': line_idx,
                    'context_id': current_context_id,
                    'content': stripped
                })

    # Scan external files (e.g., docs/ directory) for references to GLOSSARY or other memory items
    docs_dir = Path('docs')
    if docs_dir.exists() and docs_dir.is_dir():
        for root, _, files in os.walk(docs_dir):
            for file in files:
                if file.endswith('.md'):
                    fpath = Path(root) / file
                    try:
                        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                            for line_idx, line in enumerate(f, 1):
                                id_matches = re.findall(r'\[\[([A-Za-z0-9_-]+)\]\]', line)
                                for rid in id_matches:
                                    references.append({
                                        'id': rid,
                                        'file': str(fpath.relative_to(Path.cwd())),
                                        'line_num': line_idx,
                                        'context_id': None,
                                        'content': line.strip()
                                    })
                    except Exception:
                        pass

    # 1.5 OKF Conformance Check (Error tier: a missing/empty type field is a validation error)
    okf_as_error = True
    okf_files_to_check = []
    if memory_dir.exists() and memory_dir.is_dir():
        for path in memory_dir.glob('**/*.md'):
            if path.name == "index.md":
                continue
            okf_files_to_check.append(path)
            
    docs_dir = Path('docs')
    if docs_dir.exists() and docs_dir.is_dir():
        for path in docs_dir.glob('**/*.md'):
            if path.name == "index.md":
                continue
            try:
                rel = path.relative_to(docs_dir)
                if rel.parts and rel.parts[0] == 'knowledge':
                    continue
            except ValueError:
                pass
            okf_files_to_check.append(path)

    for path in okf_files_to_check:
        try:
            display_path = str(path.relative_to(Path.cwd()))
        except ValueError:
            display_path = str(path)
            
        try:
            content = path.read_text(encoding='utf-8')
            m = re.match(r"^---\r?\n(.*?)\r?\n---", content, re.S)
            if not m:
                msg = f"OKF conformance: {display_path} is missing parseable frontmatter."
                if okf_as_error:
                    errors.append(msg)
                else:
                    warnings.append(msg)
                continue
            
            fm_text = m.group(1)
            fm = {}
            for line in fm_text.splitlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if ':' in line:
                    k, v = line.split(':', 1)
                    fm[k.strip()] = v.strip()
            
            if 'type' not in fm or not fm['type']:
                msg = f"OKF conformance: {display_path} is missing a non-empty 'type' field in frontmatter."
                if okf_as_error:
                    errors.append(msg)
                else:
                    warnings.append(msg)
        except Exception as e:
            msg = f"OKF conformance: Could not read {display_path} for frontmatter: {e}"
            if okf_as_error:
                errors.append(msg)
            else:
                warnings.append(msg)

    # 2. Trust Tag Rules Validation
    for def_id, info in definitions.items():
        if info['file'] == 'BACKLOG_MAP.md':
            continue  # Backlog items do not carry trust tags
            
        if info['in_superseded']:
            if not info['superseded_by']:
                errors.append(f"Supersession error: Superseded entry '{def_id}' in {info['file']}:{info['line_num']} is missing a valid [SUPERSEDED BY [[ID]]] target.")
            elif info['superseded_by'] not in definitions:
                errors.append(f"Supersession error: Superseded entry '{def_id}' in {info['file']}:{info['line_num']} points to undefined target '{info['superseded_by']}'.")
            continue
            
        # Active entries validation
        if not info['tag']:
            errors.append(f"Trust tag error: Missing trust tag for active definition '{def_id}' in {info['file']}:{info['line_num']}.")
        else:
            tag = info['tag']
            fname = info['file']
            if fname in ['ARCHITECTURE.md', 'DESIGN_RULES.md']:
                if tag != 'LAW':
                    errors.append(f"Purity error: Active entry '{def_id}' in {fname}:{info['line_num']} has trust tag '[{tag}]'. Must be '[LAW]'.")
            elif fname == 'GLOSSARY.md':
                if tag == 'LAW':
                    errors.append(f"Purity error: Glossary term '{def_id}' in {fname}:{info['line_num']} has trust tag '[LAW]'. Glossary entries cannot be '[LAW]'.")

    # 3. Cross-reference Integrity
    directed_links = set()
    for ref in references:
        rid = ref['id']
        if rid not in definitions:
            errors.append(f"Dangling reference: '{rid}' referenced in {ref['file']}:{ref['line_num']} is not defined anywhere in the memory layer.")
        else:
            if ref['context_id']:
                directed_links.add((ref['context_id'], rid))

    # 4. Bidirectional Consistency (Warning only)
    for cid, rid in directed_links:
        # Reciprocity is checked ONLY for memory-to-memory links (L/A/DR/G <-> L/A/DR/G)
        if not (any(cid.startswith(p) for p in ['L-', 'A-', 'DR-', 'G-']) and any(rid.startswith(p) for p in ['L-', 'A-', 'DR-', 'G-'])):
            continue
            
        c_info = definitions.get(cid)
        r_info = definitions.get(rid)
        if c_info and r_info:
            if not c_info['in_superseded'] and not r_info['in_superseded']:
                if (rid, cid) not in directed_links:
                    if getattr(args, 'autofix', False):
                        if apply_autofix(args.path, r_info['file'], r_info['line_num'], cid):
                            if not args.quiet:
                                print(f"[AUTO-FIXED] Added reciprocal reference to '{cid}' in {r_info['file']}:{r_info['line_num']}")
                            continue
                    warnings.append(f"One-way reference: '{cid}' references '{rid}' in {c_info['file']}:{c_info['line_num']}, but '{rid}' does not reference '{cid}' back.")

    # Print human-readable report if not quiet
    if not args.quiet:
        print("=== Stratosphere OS Memory Validator ===")
        if errors:
            print(f"\nErrors found ({len(errors)}):")
            for err in errors:
                print(f"  [ERROR] {err}")
        else:
            print("\nNo errors found.")
            
        if warnings:
            print(f"\nWarnings found ({len(warnings)}):")
            for wrn in warnings:
                print(f"  [WARNING] {wrn}")
        else:
            print("\nNo warnings found.")
        print("========================================")

    # Machine JSON block output
    is_clean = len(errors) == 0 and len(warnings) == 0
    print("# MACHINE")
    print(json.dumps({
        "clean": is_clean,
        "errors": errors,
        "warnings": warnings
    }))

    # Set exit status
    if errors:
        sys.exit(1)
    elif warnings:
        sys.exit(1 if args.warnings_as_errors else 2)
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()
