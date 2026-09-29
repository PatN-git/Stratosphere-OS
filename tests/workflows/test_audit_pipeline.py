#!/usr/bin/env python3
"""Unified audit pipeline contract (4b + 4c -> proposal -> 3b audit-sourced intake).

Guards the wiring that the L3 lifecycle harness does not drive:
  - producers and consumers cite the shared audit-to-slices contract
  - the retired single-proposal path is gone
  - 3b never ships a report template (audit-to-slices must not cite them)
  - report templates carry the generated-doc version stamp
"""
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HOSTS = ["dist/antigravity", "dist/claude-code"]
CONTRACT = "audit-to-slices.md"
PROPOSAL = ".tmp/refactor-proposal-<report-stem>.md"


def skills(host: str) -> Path:
    base = REPO_ROOT / host / "skills"
    if not base.is_dir():
        pytest.skip(f"{host}/skills not built")
    return base


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


@pytest.mark.parametrize("host", HOSTS)
def test_producers_and_consumers_cite_contract(host):
    base = skills(host)
    for name in ("4b-audit-architecture-drift", "4c-codebase-health-audit", "3b-create-issue"):
        assert CONTRACT in read(base / name / "SKILL.md"), f"{name} does not cite {CONTRACT}"
    faa = base / "4a-verify-and-ship" / "references" / "feature-acceptance-audit.md"
    assert CONTRACT in read(faa), "feature-acceptance-audit.md does not cite the contract"


@pytest.mark.parametrize("host", HOSTS)
def test_retired_proposal_path_absent(host):
    hits = [str(p.relative_to(REPO_ROOT)) for p in skills(host).rglob("*.md")
            if ".tmp/refactor-proposal.md" in read(p)]
    assert not hits, f"retired path still present: {hits}"


@pytest.mark.parametrize("host", HOSTS)
def test_audits_write_report_and_proposal(host):
    base = skills(host)
    for name in ("4b-audit-architecture-drift", "4c-codebase-health-audit"):
        body = read(base / name / "SKILL.md")
        assert "docs/audits/" in body, name
        assert PROPOSAL in body, name


@pytest.mark.parametrize("host", HOSTS)
def test_contract_tokens(host):
    body = read(skills(host) / "3b-create-issue" / "references" / CONTRACT)
    for token in ("[UNCOVERED]", "[OPPORTUNISTIC]", "Resolves: docs/audits/",
                  "Source: docs/audits/", "(standalone)"):
        assert token in body, f"{CONTRACT} missing {token!r}"


@pytest.mark.parametrize("host", HOSTS)
def test_3b_ships_no_report_template(host):
    refs = skills(host) / "3b-create-issue" / "references"
    for tpl in ("health-audit-report-template.md", "arch-drift-report-template.md"):
        assert not (refs / tpl).exists(), f"3b ships {tpl} — {CONTRACT} must not cite report templates"


@pytest.mark.parametrize("host", HOSTS)
def test_report_templates_stamp_version(host):
    base = skills(host)
    for name, tpl in (("4c-codebase-health-audit", "health-audit-report-template.md"),
                      ("4b-audit-architecture-drift", "arch-drift-report-template.md")):
        assert "version: <plugin version>" in read(base / name / "references" / tpl), tpl
