#!/usr/bin/env python3
"""Tests for BT-269: Dual-track link validation in src/scripts/validate_memory.py."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import REPO_ROOT, git

SRC_SCRIPTS = REPO_ROOT / "src" / "scripts"
SCRIPT = SRC_SCRIPTS / "validate_memory.py"

sys.path.insert(0, str(SRC_SCRIPTS))
import validate_memory

ARCH_FM = """---
type: architecture
title: Architecture
generated:
  by: test
  at: 2026-11-12
version: "1.0.0"
---
# ARCHITECTURE

## Structural Rules
"""

LEARN_FM = """---
type: learnings
title: Learnings
generated:
  by: test
  at: 2026-11-12
version: "1.0.0"
---
# LEARNINGS

## Active Entries
"""

DOC_FM = """---
type: prd
title: Sample
generated:
  by: test
  at: 2026-11-12
status: stable
version: "1.0.0"
---
"""


def _write(root: Path, rel: str, text: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8", newline="\n")
    return p


def _init_repo(tmp_path: Path, files: dict[str, str], untracked: dict[str, str] | None = None) -> Path:
    git(tmp_path, "init", "-b", "main")
    for rel, content in files.items():
        _write(tmp_path, rel, content)
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-m", "base")
    for rel, content in (untracked or {}).items():
        _write(tmp_path, rel, content)
    return tmp_path


def _run_validator(cwd: Path, *extra_args: str) -> tuple[int, str, dict]:
    r = subprocess.run(
        [sys.executable, str(SCRIPT), *extra_args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    out = r.stdout
    machine_idx = out.rfind("# MACHINE\n")
    payload = json.loads(out[machine_idx + len("# MACHINE\n"):].strip()) if machine_idx != -1 else {}
    return r.returncode, out, payload


def test_mask_code_and_comments_preserves_line_numbers():
    raw = (
        "Line 1 [[keep-me]]\n"
        "```markdown\n"
        "[[fenced-1]]\n"
        "[[fenced-2]]\n"
        "```\n"
        "Line 6 `[[inline-code]]` and ``[[double-inline]]``\n"
        "<!-- [[comment-1]]\n"
        "[[comment-2]] -->\n"
        "Line 9 [[keep-end]]\n"
    )
    masked = validate_memory.mask_code_and_comments(raw)
    assert len(masked.splitlines()) == len(raw.splitlines())
    lines = masked.splitlines()
    assert "[[keep-me]]" in lines[0]
    assert "[[fenced-1]]" not in masked
    assert "[[fenced-2]]" not in masked
    assert "[[inline-code]]" not in masked
    assert "[[double-inline]]" not in masked
    assert "[[comment-1]]" not in masked
    assert "[[comment-2]]" not in masked
    assert "[[keep-end]]" in lines[8]


def test_parse_wikilink_token_splits_section_and_alias():
    assert validate_memory.parse_wikilink_token("BT-233-obsidian-document-linking") == (
        "BT-233-obsidian-document-linking",
        None,
        None,
    )
    assert validate_memory.parse_wikilink_token("docs/discovery/obsidian-document-linking|Brief") == (
        "docs/discovery/obsidian-document-linking",
        None,
        "Brief",
    )
    assert validate_memory.parse_wikilink_token("ARCHITECTURE#Known Architectural Constraints") == (
        "ARCHITECTURE",
        "Known Architectural Constraints",
        None,
    )
    assert validate_memory.parse_wikilink_token(" docs/prds/foo # Sec | My Alias ") == (
        "docs/prds/foo",
        "Sec",
        "My Alias",
    )
    # Must preserve backslashes so caller rejects them instead of silently normalizing
    assert validate_memory.parse_wikilink_token(r"docs\prds\BT-233")[0] == r"docs\prds\BT-233"


def test_valid_document_wikilinks_and_memory_reciprocity_pass(tmp_path):
    _init_repo(
        tmp_path,
        {
            ".memory/ARCHITECTURE.md": (
                ARCH_FM
                + "- **[[A-005]] [LAW]** GitHub only. Refs: [[L-001]].\n\n## Superseded\n"
            ),
            ".memory/LEARNINGS.md": (
                LEARN_FM
                + "- **[[L-001]] [ASSUMED] [2026-11-12]** Lesson. Refs: [[A-005]]. Source: BT-001.\n\n## Superseded\n"
            ),
            "docs/prds/BT-233-obsidian-document-linking.md": (
                DOC_FM
                + "# PRD\nSee [[obsidian-document-linking|Brief]] and [[ARCHITECTURE#Structural Rules]].\n"
                + "Memory ref [[A-005]] and [[L-001]].\n"
            ),
            "docs/discovery/obsidian-document-linking.md": (
                DOC_FM + "# Discovery\nSee [[BT-233-obsidian-document-linking]].\n"
            ),
        },
    )
    code, out, payload = _run_validator(tmp_path)
    assert code == 0, out
    assert payload == {"clean": True, "errors": [], "warnings": []}

    # Bidirectional reciprocity check still flags one-way memory-to-memory links
    _write(
        tmp_path,
        ".memory/LEARNINGS.md",
        LEARN_FM + "- **[[L-001]] [ASSUMED] [2026-11-12]** Lesson without backlink. Source: BT-001.\n\n## Superseded\n",
    )
    code2, out2, payload2 = _run_validator(tmp_path)
    assert code2 == 2, out2
    assert any("One-way reference" in w for w in payload2["warnings"])


def test_dangling_document_link_emits_error_and_exits_1(tmp_path):
    _init_repo(
        tmp_path,
        {
            ".memory/ARCHITECTURE.md": ARCH_FM + "- **[[A-001]] [LAW]** Rule.\n\n## Superseded\n",
            "docs/prds/sample.md": DOC_FM + "# Sample\nBroken link [[missing-file]].\n",
        },
    )
    code, out, payload = _run_validator(tmp_path)
    assert code == 1, out
    assert "[ERROR] Dangling document link: '[[missing-file]]'" in out
    assert any("Dangling document link: '[[missing-file]]'" in e for e in payload["errors"])


def test_untracked_target_rejected_and_archived_targets_ignored(tmp_path):
    _init_repo(
        tmp_path,
        {
            ".memory/ARCHITECTURE.md": ARCH_FM + "\n## Superseded\n",
            "docs/proposals/active-note.md": DOC_FM + "# Active\nSee [[untracked-doc]].\n",
            "docs/archive/active-note.md": DOC_FM + "# Archived duplicate\n",
        },
        untracked={
            "docs/discovery/untracked-doc.md": DOC_FM + "# Untracked\n",
        },
    )
    code, out, _ = _run_validator(tmp_path)
    assert code == 1, out
    assert "Dangling document link: '[[untracked-doc]]'" in out

    # Linking bare [[active-note]] must resolve uniquely to docs/proposals/active-note.md
    # without colliding against docs/archive/active-note.md
    _write(tmp_path, "docs/proposals/consumer.md", DOC_FM + "# Consumer\nSee [[active-note]].\n")
    _write(tmp_path, "docs/proposals/active-note.md", DOC_FM + "# Active\nClean.\n")
    git(tmp_path, "add", "docs/proposals/consumer.md", "docs/proposals/active-note.md")
    git(tmp_path, "commit", "-m", "fix link")
    code2, out2, _ = _run_validator(tmp_path)
    assert code2 == 0, out2


def test_ambiguous_stem_collision_warns_and_escalates(tmp_path):
    _init_repo(
        tmp_path,
        {
            ".memory/ARCHITECTURE.md": ARCH_FM + "\n## Superseded\n",
            "docs/discovery/foo.md": DOC_FM + "# Discovery Foo\n",
            "docs/research/foo.md": DOC_FM + "# Research Foo\n",
            "docs/prds/consumer.md": DOC_FM + "# Consumer\nAmbiguous [[foo]].\n",
        },
    )
    code, out, payload = _run_validator(tmp_path)
    assert code == 2, out
    assert "[WARNING]" in out
    assert "docs/discovery/foo" in out and "docs/research/foo" in out
    assert len(payload["warnings"]) == 1

    # --warnings-as-errors exits 1
    code_strict, out_strict, _ = _run_validator(tmp_path, "--warnings-as-errors")
    assert code_strict == 1, out_strict

    # Qualifying with minimum vault-root prefix clears the warning
    _write(tmp_path, "docs/prds/consumer.md", DOC_FM + "# Consumer\nQualified [[docs/discovery/foo|Foo]].\n")
    code_clean, out_clean, _ = _run_validator(tmp_path)
    assert code_clean == 0, out_clean


def test_hygiene_enforcement_backslash_case_and_masking(tmp_path):
    _init_repo(
        tmp_path,
        {
            ".memory/ARCHITECTURE.md": ARCH_FM + "\n## Superseded\n",
            "docs/prds/BT-233-Obsidian.md": DOC_FM + "# Target\n",
            "docs/prds/index.md": "# PRDs\n* [[BT-233-Obsidian]]\n",
            "docs/prds/bad-backslash.md": DOC_FM + "# Backslash\n[[docs\\prds\\BT-233-Obsidian]]\n",
            "docs/prds/bad-case.md": DOC_FM + "# Case\n[[bt-233-obsidian]]\n",
            "docs/prds/bad-reserved.md": DOC_FM + "# Reserved\n[[index]]\n",
            "docs/prds/L-001.md": DOC_FM + "# Namespace Collision\n",
            "docs/prds/masked-ok.md": (
                DOC_FM
                + "# Masked\n"
                + "```md\n[[missing-in-fence]]\n```\n"
                + "Inline `[[missing-in-inline]]` and <!-- [[missing-in-comment]] -->.\n"
                + "Valid MOC [[docs/prds/index|PRDs MOC]].\n"
            ),
        },
    )
    code, out, payload = _run_validator(tmp_path)
    assert code == 1, out
    errs = "\n".join(payload["errors"])
    assert "backslash" in errs.lower(), errs
    assert "case mismatch" in errs.lower(), errs
    assert "reserved" in errs.lower() or "index" in errs.lower(), errs
    assert "L-001" in errs, errs
    assert "missing-in-fence" not in errs
    assert "missing-in-inline" not in errs
    assert "missing-in-comment" not in errs


def test_placeholder_tokens_exempt_from_dangling_errors(tmp_path):
    _init_repo(
        tmp_path,
        {
            ".memory/ARCHITECTURE.md": ARCH_FM + "- **[[A-XXX]] [LAW]** Example placeholder. Source: BT-XXX.\n\n## Superseded\n",
            ".memory/LEARNINGS.md": LEARN_FM + "- **[[L-XXX]] [ASSUMED] [YYYY-MM-DD]** Example. Source: BT-XXX.\n\n## Superseded\n",
            "docs/prds/template-doc.md": DOC_FM + "# Template\nRefers to [[A-XXX]], [[G-XXX]], [[DR-YYY]].\n",
        },
    )
    code, out, payload = _run_validator(tmp_path)
    assert code == 0, out
    assert payload["clean"] is True


def test_resolve_document_wikilink_contract_and_docs_memory_handle_check(tmp_path):
    tracked = {
        "docs/prds/BT-233-obsidian-document-linking.md",
        "docs/discovery/foo.md",
        "docs/research/foo.md",
        "docs/prds/index.md",
        ".memory/ARCHITECTURE.md",
    }
    stems = validate_memory.build_doc_index(tracked)
    assert validate_memory.resolve_document_wikilink("BT-233-obsidian-document-linking", tracked, stems) == (
        "docs/prds/BT-233-obsidian-document-linking.md",
        None,
    )
    assert validate_memory.resolve_document_wikilink("ARCHITECTURE", tracked, stems) == (
        ".memory/ARCHITECTURE.md",
        None,
    )
    assert validate_memory.resolve_document_wikilink("docs/discovery/foo", tracked, stems) == (
        "docs/discovery/foo.md",
        None,
    )
    res_coll, msg_coll = validate_memory.resolve_document_wikilink("foo", tracked, stems)
    assert res_coll is not None and "Ambiguous stem 'foo'" in msg_coll
    res_readme, msg_readme = validate_memory.resolve_document_wikilink("README", tracked, stems)
    assert res_readme is None and "Reserved stem" in msg_readme
    assert validate_memory.resolve_document_wikilink("A-XXX", tracked, stems) == (None, None)

    # Dangling memory handle in docs/ and tilde fence masking
    _init_repo(
        tmp_path,
        {
            ".memory/ARCHITECTURE.md": ARCH_FM + "\n## Superseded\n",
            "docs/prds/check.md": DOC_FM + "# Check\n~~~\n[[missing-tilde]]\n~~~\nBad memory [[L-999]].\n",
        },
    )
    code, out, payload = _run_validator(tmp_path)
    assert code == 1, out
    errs = "\n".join(payload["errors"])
    assert "Dangling reference: 'L-999'" in errs
    assert "missing-tilde" not in errs


def test_dual_track_resolution_200_docs_under_50ms():
    import time

    tracked = {f"docs/research/doc-{i:03d}.md" for i in range(200)}
    sample_doc = "\n".join(
        [
            "```md\n[[ignored-fence]]\n```",
            "Inline `[[ignored-inline]]` and <!-- [[ignored-comment]] -->.",
            "See [[doc-042|Doc 42]] and [[docs/research/doc-199#Top|Last]].",
        ]
    )
    t0 = time.perf_counter()
    stems = validate_memory.build_doc_index(tracked)
    t_lower = {p.lower(): p for p in tracked}
    s_lower = {k.lower(): v for k, v in stems.items()}
    for _ in range(200):
        masked = validate_memory.mask_code_and_comments(sample_doc)
        for raw_tok in validate_memory._WIKILINK_TOKEN_RE.findall(masked):
            stem, _, _ = validate_memory.parse_wikilink_token(raw_tok)
            res, msg = validate_memory.resolve_document_wikilink(stem, tracked, stems, t_lower, s_lower)
            assert res is not None and msg is None
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    assert elapsed_ms < 50.0, f"200-doc resolution took {elapsed_ms:.2f}ms (> 50ms)"
