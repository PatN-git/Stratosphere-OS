#!/usr/bin/env python3
"""BT-148: scripts/release.py stamps the jules-dispatch pack pin (src/external-skills.json `ref` and the
"Pinned to the vX release tag" description text) with the new release version, so a VERSION bump can
never leave the pin on an older tag.
"""
import importlib.util
import inspect
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("release", ROOT / "scripts" / "release.py")
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)

SAMPLE = """{
  "skills": [
    {
      "name": "other",
      "ref": "c30d329f5814647c1e2f071020c1e8c1c9893ef1",
      "description": "Pinned to the v1.0.0 release tag."
    },
    {
      "name": "jules-dispatch",
      "default": false,
      "ref": "v4.5.0",
      "description": "EXPERIMENTAL. Pinned to the v4.5.0 release tag."
    }
  ]
}
"""


def _jules(text):
    return next(s for s in json.loads(text)["skills"] if s["name"] == "jules-dispatch")


def test_stamp_moves_the_pin_and_its_description_to_the_new_version():
    out = release.stamp_pack_pin(SAMPLE, "4.6.0")
    e = _jules(out)
    assert e["ref"] == "v4.6.0"
    assert e["description"] == "EXPERIMENTAL. Pinned to the v4.6.0 release tag."
    # nothing else moves: the other entry (same wording, other pack) and all layout stay byte-identical
    assert out == SAMPLE.replace("v4.5.0", "v4.6.0")


def test_stamp_accepts_a_v_prefixed_version():
    assert _jules(release.stamp_pack_pin(SAMPLE, "v4.6.0"))["ref"] == "v4.6.0"


def test_stamp_fails_loud_when_the_entry_or_its_fields_are_missing():
    for bad in (SAMPLE.replace("jules-dispatch", "renamed"),
                SAMPLE.replace('"ref": "v4.5.0"', '"sha": "v4.5.0"'),
                SAMPLE.replace("Pinned to the v4.5.0 release tag", "pinned somewhere")):
        try:
            release.stamp_pack_pin(bad, "4.6.0")
        except ValueError:
            continue
        raise AssertionError("expected ValueError for a registry the stamp cannot update")


def test_stamp_is_a_noop_on_the_current_tree():
    """release.py must leave a consistent tree untouched (nothing to recompile)."""
    text = (ROOT / "src" / "external-skills.json").read_bytes().decode("utf-8")
    version = re.search(r'VERSION\s*=\s*"([^"]+)"', (ROOT / "build" / "build.py").read_text(encoding="utf-8")).group(1)
    assert release.stamp_pack_pin(text, version) == text


def test_main_writes_the_stamped_registry_before_recompiling():
    src = inspect.getsource(release.main)
    assert "stamp_pack_pin(" in src and "external-skills.json" in src
    assert src.index("stamp_pack_pin(") < src.index("Recompiling with new version")
