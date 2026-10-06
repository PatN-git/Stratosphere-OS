"""BT-121: README documents all five install tracks (A skills.sh, B copy/paste, C Claude marketplace, D Antigravity bridge, E Antigravity plugin)."""
import re
from pathlib import Path

README = (Path(__file__).resolve().parents[2] / "README.md").read_text(encoding="utf-8")


def _track(letter: str) -> str:
    """Body of the `### Track <letter>` subsection, up to the next heading of the same or higher level."""
    m = re.search(rf"^### Track {letter}\b.*?\n(.*?)(?=^#{{2,3}} |\Z)", README, re.S | re.M)
    assert m, f"README has no '### Track {letter}' subsection"
    return m.group(1)


def test_track_a_skills_sh_uses_copy_flag_and_subpath():
    a = _track("A")
    assert "npx skills add PatN-git/Stratosphere-OS/dist/skills" in a
    assert "--copy" in a and "-y" in a
    assert re.search(r"EPERM|symlink", a), "must explain why --copy is mandatory"
    assert "-a <agent>" in a, "must show per-agent targeting"
    assert "-g" in a, "must show global install"


def test_track_b_copy_paste_covers_both_targets_on_both_shells_without_node():
    b = _track("B")
    for target in (".agents/skills", ".claude/skills"):
        assert target in b, f"missing {target}"
        assert target.replace("/", "\\") in b, f"missing PowerShell form of {target}"
    assert "cp -r <repo>/dist/skills/*" in b
    assert "Copy-Item -Recurse -Force <repo>\\dist\\skills\\*" in b
    assert "npx skills" not in b, "Track B is the zero-Node path: no npx command"
    assert re.search(r"offline|air-gapped", b, re.I)


def test_track_c_claude_marketplace():
    c = _track("C")
    assert "/plugin marketplace add PatN-git/Stratosphere-OS" in c
    assert "/plugin install stratosphere-os@stratosphere-os" in c


def test_track_d_antigravity_bridge_both_shells_and_target_flag():
    d = _track("D")
    assert "scripts/install-antigravity-bridge.sh" in d
    assert "scripts/install-antigravity-bridge.ps1" in d
    assert "--target" in d
    assert "~/.gemini/config/skills" in d


def test_track_d_records_the_cli_directory_result():
    """BT-150 spike C: on agy 1.3.0 the CLI read ~/.gemini/config/skills and not ~/.gemini/antigravity-cli/skills."""
    d = _track("D")
    assert "~/.gemini/antigravity-cli/skills" in d
    assert "agy" in d


def test_track_e_antigravity_plugin_install():
    e = _track("E")
    assert "agy plugin install dist" in e
    assert "~/.gemini/config/plugins/stratosphere-os" in e
    assert re.search(r"reinstall|again", e, re.I), "must say how to update (reinstall over it)"
    assert "/sync-skills" in e, "the plugin carries only the bundled skills; external ones come from /sync-skills"
    assert "Track D" in e, "Track D stays available"


def test_install_table_routes_antigravity_plugin_installs_to_track_e():
    assert "(#track-e--antigravity-plugin-install)" in README


def test_root_install_without_subpath_is_called_out():
    assert re.search(r"without the (?:`?/?dist/skills`? )?subpath|`?/dist/skills`? subpath", README), (
        "README must warn that omitting the /dist/skills subpath finds no skills"
    )
