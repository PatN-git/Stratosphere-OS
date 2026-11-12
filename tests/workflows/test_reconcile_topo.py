#!/usr/bin/env python3
# md-crosscheck: reconcile.py topological DAG sorter and Stage 3 implementation workflows against Prompt Report BT-227 invariants
"""Tests for topological DAG sorter and gated diagnostic reflexion (BT-227 / Epic BT-223)."""
import os
import sys
import time
import subprocess
from pathlib import Path
import pytest
from conftest import REPO_ROOT, SRC, read_src

sys.path.insert(0, str(REPO_ROOT / "src" / "scripts"))
import _versioning

SCRIPT = REPO_ROOT / "src" / "scripts" / "reconcile.py"


def test_topological_sort_linear():
    import reconcile
    # C depends on B; B depends on A; A has no blockers
    graph = {
        "BT-003": {"BT-002"},
        "BT-002": {"BT-001"},
        "BT-001": set()
    }
    order, cycle = reconcile.topological_sort(graph)
    assert cycle is None
    assert order == ["BT-001", "BT-002", "BT-003"]


def test_topological_sort_diamond():
    import reconcile
    # D depends on B and C; B and C depend on A; A has no blockers
    graph = {
        "BT-004": {"BT-002", "BT-003"},
        "BT-002": {"BT-001"},
        "BT-003": {"BT-001"},
        "BT-001": set()
    }
    order, cycle = reconcile.topological_sort(graph)
    assert cycle is None
    assert order[0] == "BT-001"
    assert set(order[1:3]) == {"BT-002", "BT-003"}
    assert order[3] == "BT-004"


def test_topological_sort_cycle_2_node():
    import reconcile
    # A depends on B; B depends on A
    graph = {
        "BT-001": {"BT-002"},
        "BT-002": {"BT-001"}
    }
    order, cycle = reconcile.topological_sort(graph)
    assert order is None
    assert cycle is not None
    assert len(cycle) >= 2
    assert "BT-001" in cycle and "BT-002" in cycle


def test_topological_sort_cycle_3_node():
    import reconcile
    # A depends on B; B depends on C; C depends on A
    graph = {
        "BT-001": {"BT-002"},
        "BT-002": {"BT-003"},
        "BT-003": {"BT-001"}
    }
    order, cycle = reconcile.topological_sort(graph)
    assert order is None
    assert cycle is not None
    assert len(cycle) >= 3


def test_topological_sort_self_loop():
    import reconcile
    # A depends on itself
    graph = {
        "BT-001": {"BT-001"}
    }
    order, cycle = reconcile.topological_sort(graph)
    assert order is None
    assert cycle is not None
    assert "BT-001" in cycle


def test_topological_sort_disconnected():
    import reconcile
    # Component 1: A -> B; Component 2: X -> Y; Isolated: Z
    graph = {
        "BT-002": {"BT-001"},
        "BT-001": set(),
        "BT-010": {"BT-009"},
        "BT-009": set(),
        "BT-099": set()
    }
    order, cycle = reconcile.topological_sort(graph)
    assert cycle is None
    assert len(order) == 5
    assert order.index("BT-001") < order.index("BT-002")
    assert order.index("BT-009") < order.index("BT-010")
    assert "BT-099" in order


def test_topological_sort_performance_under_5ms():
    import reconcile
    # Generate 100-node graph
    graph = {}
    for i in range(1, 101):
        dep = f"BT-{i:03d}"
        if i == 1:
            graph[dep] = set()
        else:
            prev = f"BT-{i-1:03d}"
            graph[dep] = {prev}

    # Warmup
    reconcile.topological_sort({"B": {"A"}, "A": set()})

    start = time.perf_counter()
    order, cycle = reconcile.topological_sort(graph)
    elapsed_ms = (time.perf_counter() - start) * 1000.0

    assert cycle is None
    assert len(order) == 100
    assert elapsed_ms < 5.0, f"Topological sort took {elapsed_ms:.3f}ms, exceeding 5ms budget"


def test_reconcile_cli_topo_sort_acyclic(tmp_path):
    edges_file = tmp_path / "edges-clean.txt"
    edges_file.write_text("""# Clean DAG edges
BT-002: BT-001
BT-003 <- BT-002
BT-004:blocked_by=BT-002,BT-003
""", encoding="utf-8")

    cmd = [
        sys.executable, str(SCRIPT),
        "--topo-sort",
        "--edges-file", str(edges_file)
    ]
    r = subprocess.run(cmd, cwd=tmp_path, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "[TOPO-ORDER" in r.stdout
    assert "BT-001" in r.stdout
    assert "BT-004" in r.stdout


def test_reconcile_cli_topo_sort_cycle(tmp_path):
    edges_file = tmp_path / "edges-cycle.txt"
    edges_file.write_text("""# Cyclic DAG edges
BT-001: BT-002
BT-002: BT-003
BT-003: BT-001
""", encoding="utf-8")

    cmd = [
        sys.executable, str(SCRIPT),
        "--topo-sort",
        "--edges-file", str(edges_file)
    ]
    r = subprocess.run(cmd, cwd=tmp_path, capture_output=True, text=True)
    assert r.returncode == 1
    assert "[CYCLE-DETECTED" in r.stdout
    assert "BT-001" in r.stdout


def test_stage3_workflow_markdown_assertions():
    text_3a = read_src("workflows/3a-version-planning.md")
    text_3b = read_src("workflows/3b-create-issue.md")
    text_3c = read_src("workflows/3c-sprint-planning.md")
    text_3d = read_src("workflows/3d-implement-issue.md")
    text_tdd = read_src("skills/micro-tdd/SKILL.md")
    text_3z = read_src("workflows/3z-afk-loop.md")

    # 3a & 3c assertions (deterministic topological sorter; rejection of voting)
    assert "reconcile.py --topo-sort" in text_3a
    assert "reconcile.py --topo-sort" in text_3b
    assert "reconcile.py --topo-sort" in text_3c

    # 3d & micro-tdd assertions (Silent execution, Gated Reflexion, Stuck Protocol)
    assert "Silent Execution Mode" in text_3d or "silent mode" in text_3d.lower()
    assert "Gated Diagnostic Reflexion" in text_3d or "diagnostic reflexion" in text_3d.lower()
    assert "Gated Diagnostic Reflexion" in text_tdd or "diagnostic reflexion" in text_tdd.lower()
    assert "Stuck Protocol" in text_3d
    assert "Stuck Protocol" in text_tdd

    # 3z assertion (pure return code control)
    assert "$? == 0" in text_3z or "exit code" in text_3z.lower()


def test_stage3_frontmatter_version_bumps():
    for rel_path, expected_v in [
        ("workflows/3a-version-planning.md", "1.8.0"),
        ("workflows/3b-create-issue.md", "2.11.0"),
        ("workflows/3c-sprint-planning.md", "2.10.0"),
        ("workflows/3d-implement-issue.md", "2.10.0"),
        ("skills/micro-tdd/SKILL.md", "1.7.0"),
        ("workflows/3z-afk-loop.md", "1.11.0"),
    ]:
        content = read_src(rel_path)
        v, _ = _versioning.read_version(content, rel_path)
        assert v == expected_v, f"{rel_path} version mismatch: expected {expected_v}, got {v}"


if __name__ == "__main__":
    pytest.main([__file__])
