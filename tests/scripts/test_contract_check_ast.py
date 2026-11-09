#!/usr/bin/env python3
# md-crosscheck: contract_check.py TypeScript AST parsing, PRD deferred story mirroring, and Stage 2 workflow contracts
"""Tests for zero-dependency TypeScript AST parsing, PRD deferred story mirroring, and Stage 2 hardening (BT-226 / Epic BT-223)."""
import os
import sys
import subprocess
from pathlib import Path
import pytest
from conftest import REPO_ROOT, SRC, read_src

sys.path.insert(0, str(REPO_ROOT / "src" / "scripts"))
import _versioning

SCRIPT = REPO_ROOT / "src" / "scripts" / "contract_check.py"


def test_ts_parser_interface_and_types(tmp_path):
    import contract_check
    ts_file = tmp_path / "models.ts"
    ts_file.write_text("""// Single-line comment
/* Multi-line comment
   across lines */
export interface UserProfile<T> {
    id: string;
    email: string;
    nickname?: string;
    metadata: T;
}

export type AccountStatus = 'active' | 'suspended' | 'archived';

export type SystemConfig = {
    timeout: number;
    retries?: number;
};

export interface Point { x: number; y: number; }
""", encoding="utf-8")

    src = contract_check.parse_ts(ts_file)
    assert "UserProfile" in src.tables
    assert src.tables["UserProfile"] == {"id", "email", "nickname", "metadata"}

    assert "SystemConfig" in src.tables
    assert src.tables["SystemConfig"] == {"timeout", "retries"}

    assert "Point" in src.tables
    assert src.tables["Point"] == {"x", "y"}

    assert "AccountStatus" in src.enums
    assert src.enums["AccountStatus"] == {"active", "suspended", "archived"}


def test_ts_parser_directory_recursion(tmp_path):
    import contract_check
    types_dir = tmp_path / "types"
    types_dir.mkdir()
    sub_dir = types_dir / "api"
    sub_dir.mkdir()

    (types_dir / "auth.ts").write_text("""
export interface AuthToken {
    token: string;
    expires_at: number;
}
""", encoding="utf-8")

    (sub_dir / "routes.d.ts").write_text("""
export interface ApiRoutes {
    "/api/v1/auth/login": AuthToken;
    "/api/v1/auth/logout": void;
}
""", encoding="utf-8")

    (types_dir / "auth.test.ts").write_text("""
export interface ShouldBeIgnored {
    ignored: boolean;
}
""", encoding="utf-8")

    sources = contract_check.load_sources(".memory/DATABASE_SCHEMA.md", [], ts_paths=[str(types_dir)])
    all_tables = {t for s in sources for t in s.tables}
    assert "AuthToken" in all_tables
    assert "ApiRoutes" in all_tables
    assert "ShouldBeIgnored" not in all_tables


def test_prd_deferred_stories_mirroring_clean(tmp_path):
    import contract_check
    prd_file = tmp_path / "BT-999-clean.md"
    prd_file.write_text("""# PRD BT-999 Clean Feature

## 1. Problem
Core problem statement.

## 6. User Stories
### Step 1: Onboarding
1. **[BASELINE]** As a visitor, I want to sign up.
2. **[DIFFERENTIATOR]** As a visitor, I want 1-click SSO. (ODI: 9.2)
3. **[DEFERRED]** Real-time presence: As a user, I want to see live co-workers. (ODI: -)
4. **[DEFERRED]** Mobile push alerts: As a user, I want push notifications on iOS and Android.

## 7. Architecture & Boundaries
- Always: TLS 1.3
- Never: unencrypted storage

## 9. Out of Scope
- Real-time presence: live peer status indicator is deferred to v2.0.
- Mobile push alerts: mobile notification channels are deferred.
""", encoding="utf-8")

    findings = contract_check.check_prd_contracts(str(prd_file), [])
    assert len(findings) == 0, f"Expected 0 findings, got: {findings}"


def test_prd_deferred_stories_mirroring_missing(tmp_path):
    import contract_check
    prd_file = tmp_path / "BT-999-missing.md"
    prd_file.write_text("""# PRD BT-999 Missing Mirror

## 1. Problem
Core problem statement.

## 6. User Stories
1. **[BASELINE]** As a user, I want basic search.
2. **[DEFERRED]** Vector search: As a user, I want semantic embeddings. (ODI: 8.5)
3. **[DEFERRED]** Voice transcription: As a user, I want audio transcription.

## 9. Out of Scope
- Vector search: semantic search is deferred to v2.
# Second deferred story is omitted here intentionally.
""", encoding="utf-8")

    findings = contract_check.check_prd_contracts(str(prd_file), [])
    assert any("[DEFERRED] story" in f and "Voice transcription" in f for f in findings)


def test_prd_backticked_endpoints(tmp_path):
    import contract_check
    ts_file = tmp_path / "endpoints.ts"
    ts_file.write_text("""
export interface ApiEndpoints {
    "GET /api/v1/users": void;
    "POST /api/v1/users": void;
    "/api/v1/health": void;
}
""", encoding="utf-8")

    prd_file = tmp_path / "BT-999-endpoints.md"
    prd_file.write_text("""# PRD
## 6. User Stories
1. **[BASELINE]** Uses `GET /api/v1/users` and `POST /api/v1/users`.
2. **[BASELINE]** Health check at `/api/v1/health`.
3. **[BASELINE]** Unregistered endpoint `POST /api/v1/rogue`.

## 9. Out of Scope
None.
""", encoding="utf-8")

    src = contract_check.parse_ts(ts_file)
    findings = contract_check.check_prd_contracts(str(prd_file), [src])
    assert any("POST /api/v1/rogue" in f for f in findings)
    assert not any("GET /api/v1/users" in f for f in findings)
    assert not any("/api/v1/health" in f for f in findings)


def test_contract_check_cli_prd_and_ts(tmp_path):
    ts_file = tmp_path / "models.ts"
    ts_file.write_text("""
export interface UserSession {
    user_id: string;
    token: string;
}
""", encoding="utf-8")

    prd_clean = tmp_path / "BT-100-clean.md"
    prd_clean.write_text("""# PRD
## 6. User Stories
1. **[BASELINE]** Session check: inspects `UserSession.user_id`.
2. **[DEFERRED]** Push notifications: As a user, I want push alerts.

## 9. Out of Scope
- Push notifications: Deferred.
""", encoding="utf-8")

    # Run clean
    cmd_clean = [
        sys.executable, str(SCRIPT),
        "--prd", str(prd_clean),
        "--ts", str(ts_file)
    ]
    r_clean = subprocess.run(cmd_clean, capture_output=True, text=True)
    assert r_clean.returncode == 0, r_clean.stderr
    assert "[CONTRACT-OK]" in r_clean.stdout

    # Run missing field
    prd_bad = tmp_path / "BT-101-bad.md"
    prd_bad.write_text("""# PRD
## 6. User Stories
1. **[BASELINE]** Invalid field `UserSession.non_existent_field`.
2. **[DEFERRED]** Push notifications: As a user, I want push alerts.

## 9. Out of Scope
- Push notifications: Deferred.
""", encoding="utf-8")

    cmd_bad = [
        sys.executable, str(SCRIPT),
        "--prd", str(prd_bad),
        "--ts", str(ts_file)
    ]
    r_bad = subprocess.run(cmd_bad, capture_output=True, text=True)
    assert r_bad.returncode == 1
    assert "[CONTRACT-MISSING]" in r_bad.stdout
    assert "UserSession.non_existent_field" in r_bad.stdout


def test_stage2_workflow_markdown_assertions():
    text_2a = read_src("workflows/2a-write-prd.md")
    text_2b = read_src("workflows/2b-interface-design.md")
    text_2c = read_src("workflows/2c-reconcile-specs.md")
    text_2z = read_src("workflows/2z-write-spec.md")

    # 2a Two-Stage Macro-CoT & Mirroring
    assert "Two-Stage Macro-CoT" in text_2a or "two-stage macro-cot" in text_2a.lower()
    assert "[DEFERRED]" in text_2a and "§9" in text_2a
    assert "contract_check.py --prd" in text_2a or "contract_check.py" in text_2a

    # 2b Interface Design FSM schemas & design tokens
    assert "Finite State Machine" in text_2b or "finite state machine" in text_2b.lower() or "FSM" in text_2b
    assert "DESIGN.md" in text_2b

    # 2c Reconcile Specs AST contract diffing (rejecting dual-LLM debate)
    assert "contract_check.py" in text_2c

    # 2z Write Spec sequence
    assert "2a-write-prd" in text_2z
    assert "2b-interface-design" in text_2z
    assert "2c-reconcile-specs" in text_2z


def test_stage2_frontmatter_version_bumps():
    for rel_path, expected_v in [
        ("workflows/2a-write-prd.md", "1.9.0"),
        ("workflows/2b-interface-design.md", "1.8.0"),
        ("workflows/2c-reconcile-specs.md", "1.4.0"),
        ("workflows/2z-write-spec.md", "1.2.0"),
    ]:
        content = read_src(rel_path)
        v, _ = _versioning.read_version(content, rel_path)
        assert v == expected_v, f"{rel_path} version mismatch: expected {expected_v}, got {v}"


if __name__ == "__main__":
    pytest.main([__file__])
