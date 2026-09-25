#!/usr/bin/env python3
"""design_theme.py Tailwind major-version targeting.

v4 (default) emits `@custom-variant dark` + `@theme inline`; v3 has neither directive,
so v3 output keeps every token in `:root` and appends `.dark`. The version is detected
from the nearest package.json declaring `tailwindcss`, overridable with --tailwind.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DESIGN_DIR = REPO_ROOT / "src" / "scripts" / "design"
SCRIPT = DESIGN_DIR / "design_theme.py"
FIXTURE = DESIGN_DIR / "test" / "fixtures" / "skycast.DESIGN.md"

sys.path.insert(0, str(DESIGN_DIR))
import design_theme  # noqa: E402

V4_DIRECTIVES = ("@custom-variant dark", "@theme inline")


def skycast_data():
    text = FIXTURE.read_text(encoding="utf-8")
    return design_theme.parse_yaml(design_theme.extract_frontmatter(text))


def write_pkg(d: Path, section: str, deps: dict):
    d.mkdir(parents=True, exist_ok=True)
    (d / "package.json").write_text(json.dumps({section: deps}), encoding="utf-8")


def test_v4_default_unchanged():
    css, _ = design_theme.generate_css(skycast_data())
    golden = (DESIGN_DIR / "test" / "fixtures" / "skycast.globals.css").read_text(encoding="utf-8")
    assert css.replace("\r\n", "\n") == golden.replace("\r\n", "\n")


def test_v3_output_shape():
    css, _ = design_theme.generate_css(skycast_data(), tailwind=3)
    for directive in V4_DIRECTIVES:
        assert directive not in css
    root = css.index(":root {")
    dark = css.index(".dark {")
    assert root < dark
    root_block = css[root:css.index("}", root)]
    # every token lives in :root: colors, radius scale, typography/spacing
    for token in ("--background:", "--radius-md: var(--radius);", "--radius-sm:", "--radius-lg:"):
        assert token in root_block, token
    assert "--color-" not in css  # v4-only color aliases
    assert css.count(".dark {") == 1


@pytest.mark.parametrize("section,version,expected", [
    ("dependencies", "3.4", 3),
    ("devDependencies", "^3.4.1", 3),
    ("devDependencies", "~3.3.0", 3),
    ("dependencies", "^4.0.0", 4),
    ("dependencies", "latest", 4),
])
def test_detect_from_package_json(tmp_path, section, version, expected):
    write_pkg(tmp_path, section, {"tailwindcss": version})
    assert design_theme.detect_tailwind_major(str(tmp_path)) == expected


def test_detect_ignores_lookalike_packages(tmp_path):
    # tailwind-merge ^3 must not be read as Tailwind 3
    write_pkg(tmp_path, "dependencies", {"tailwind-merge": "^3.6.0", "tailwindcss-animate": "^1.0.7"})
    assert design_theme.detect_tailwind_major(str(tmp_path)) == 4


def test_detect_walks_up_to_nearest_declaring_manifest(tmp_path):
    write_pkg(tmp_path, "devDependencies", {"tailwindcss": "3.4"})
    write_pkg(tmp_path / "apps" / "web", "dependencies", {"react": "^19"})  # no tailwindcss -> keep walking
    nested = tmp_path / "apps" / "web" / "src" / "styles"
    nested.mkdir(parents=True)
    assert design_theme.detect_tailwind_major(str(nested)) == 3


def test_cli_auto_detects_from_out_dir_and_flag_overrides(tmp_path):
    write_pkg(tmp_path, "devDependencies", {"tailwindcss": "^3.4.0"})
    out = tmp_path / "src" / "theme.tokens.css"
    subprocess.run([sys.executable, str(SCRIPT), "--design", str(FIXTURE), "--out", str(out)], check=True)
    css = out.read_text(encoding="utf-8")
    assert all(d not in css for d in V4_DIRECTIVES)

    # --check stays green with the same detection
    res = subprocess.run([sys.executable, str(SCRIPT), "--design", str(FIXTURE), "--check", str(out)])
    assert res.returncode == 0

    forced = subprocess.run([sys.executable, str(SCRIPT), "--design", str(FIXTURE), "--tailwind", "4"],
                            capture_output=True, text=True, cwd=tmp_path, check=True).stdout
    assert all(d in forced for d in V4_DIRECTIVES)
