#!/usr/bin/env python3
# md-crosscheck: producer hand-off lines vs the workflows that really contain the artifact
"""BT-168 H2: a producer's hand-off line is names-only -- `Writes <path>. Read by: /x, /y.` -- and its
reader names equal, both ways, the workflows that actually contain the artifact token. The meaning of
what a reader does with the artifact lives in the reader's own body, never restated in the producer."""
import re

import pytest

from conftest import SRC, read_src

ORCHESTRATORS = {"2z-write-spec", "3z-afk-loop"}

# producer -> (artifact token, co-producers that write it rather than read it, readers that reach it only
# through a reference they apply: {reader: reference file})
HANDOFFS = {
    "1a-research": ("docs/research/", {"1c-concept-map"}, {}),  # 1c runs 1a inline and saves the result
    "2b-interface-design": ("docs/design/BT-", set(), {}),
    # 3b applies audit-to-slices.md §8, which takes the [ACTIVE] release from ROADMAP.md
    "3a-version-planning": ("docs/ROADMAP.md", set(), {"3b-create-issue": "audit-to-slices.md"}),
}
# 3c writes a GitHub milestone, not a file, so no token can derive its readers (3z reads the sprint): shape only.
SHAPE_ONLY = ["3c-sprint-planning"]


def _bodies() -> dict[str, str]:
    return {f.stem: f.read_text(encoding="utf-8") for f in sorted((SRC / "workflows").glob("*.md"))}


def _handoff_line(producer: str) -> str:
    return next(l for l in read_src(f"workflows/{producer}.md").splitlines()
                if l.startswith("**Hand-off contract:**"))


def _named_readers(line: str) -> set[str]:
    assert "Read by:" in line, line
    return set(re.findall(r"`/(\d[a-z]-[a-z0-9-]+)`", line.split("Read by:", 1)[1]))


@pytest.mark.parametrize("producer", [*HANDOFFS, *SHAPE_ONLY])
def test_handoff_line_is_names_only(producer):
    line = _handoff_line(producer)
    assert line.startswith("**Hand-off contract:** Writes "), line
    assert "§" not in line, f"{producer}: hand-off line restates section lists"


@pytest.mark.parametrize("producer", HANDOFFS)
def test_named_readers_equal_the_workflows_that_contain_the_artifact(producer):
    token, co_producers, via_reference = HANDOFFS[producer]
    bodies = _bodies()
    actual = {name for name, text in bodies.items()
              if token in text and name not in ORCHESTRATORS | co_producers | {producer}}
    for reader, ref in via_reference.items():
        assert token in read_src(f"references/{ref}"), (producer, ref)
        assert ref in bodies[reader], (producer, reader, ref)
        actual.add(reader)
    named = _named_readers(_handoff_line(producer))
    assert named == actual, (producer, "named", sorted(named), "actual", sorted(actual))


def test_named_readers_are_real_workflows():
    bodies = _bodies()
    for producer in [*HANDOFFS, *SHAPE_ONLY]:
        for name in _named_readers(_handoff_line(producer)):
            assert name in bodies, (producer, name)


def test_3c_names_3z_as_its_reader():
    assert _named_readers(_handoff_line("3c-sprint-planning")) == {"3z-afk-loop"}
