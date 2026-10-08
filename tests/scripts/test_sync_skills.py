"""BT-154: sync_skills.py fetch transforms (F6) and the other-host duplicate notice (F7). Offline."""
import importlib.util
import json
import zipfile

import pytest

from conftest import REPO_ROOT

SCRIPT = REPO_ROOT / "src" / "commands" / "sync-skills" / "scripts" / "sync_skills.py"
REGISTRY = REPO_ROOT / "src" / "external-skills.json"
SUB = "claude-plugins-official-main/plugins/code-simplifier/"
AGENT = "---\nname: code-simplifier\ndescription: Simplify code.\nmodel: opus\n---\n\nYou simplify code.\n"


@pytest.fixture
def sync(monkeypatch, tmp_path):
    spec = importlib.util.spec_from_file_location("sync_skills", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    zip_path = tmp_path / "upstream.zip"
    with zipfile.ZipFile(zip_path, "w") as z:
        z.writestr(SUB + "agents/code-simplifier.md", AGENT)
        z.writestr(SUB + ".claude-plugin/plugin.json", '{"name": "code-simplifier"}')
        z.writestr(SUB + "LICENSE", "license")
    monkeypatch.setattr(mod, "get_cached_zip", lambda url: str(zip_path))
    return mod


def entry(**extra):
    return {"name": "code-simplifier", "repoZipUrl": "https://example.invalid/archive/refs/heads/main.zip",
            "subPath": SUB, **extra}


def test_skill_file_entry_yields_a_skill_md_without_the_agent_model_key(sync, tmp_path):
    base = tmp_path / "skills"
    status, msg = sync.fetch(entry(skillFile="agents/code-simplifier.md"), base, False, base / ".lock.json")
    assert status == "ok", msg
    text = (base / "code-simplifier" / "SKILL.md").read_text(encoding="utf-8")
    assert "name: code-simplifier" in text and "model:" not in text
    assert text.endswith("You simplify code.\n")


def test_pack_without_skill_md_keeps_the_existing_copy(sync, tmp_path):
    base = tmp_path / "skills"
    (base / "code-simplifier").mkdir(parents=True)
    (base / "code-simplifier" / "SKILL.md").write_text("sentinel", encoding="utf-8")
    status, msg = sync.fetch(entry(), base, False, base / ".lock.json")
    assert status == "warn" and "no SKILL.md" in msg
    assert (base / "code-simplifier" / "SKILL.md").read_text(encoding="utf-8") == "sentinel"
    assert sorted(p.name for p in (base / "code-simplifier").iterdir()) == ["SKILL.md"]


def test_registry_code_simplifier_declares_its_skill_file():
    skills = json.loads(REGISTRY.read_text(encoding="utf-8"))["skills"]
    assert next(s for s in skills if s["name"] == "code-simplifier")["skillFile"] == "agents/code-simplifier.md"


def pack(root, files):
    for rel, data in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_bytes(data)
    return root


def test_duplicate_notice_flags_a_differing_copy(sync, tmp_path):
    synced = pack(tmp_path / "claude" / "x", {"SKILL.md": b"new\n"})
    other = pack(tmp_path / "agents" / "x", {"SKILL.md": b"old\n"})
    notice = sync.duplicate_notice(other, synced)
    assert notice.startswith("[DUPLICATE]") and other.as_posix() in notice


def test_duplicate_notice_flags_a_differing_file_set(sync, tmp_path):
    synced = pack(tmp_path / "claude" / "x", {"SKILL.md": b"same\n", "references/a.md": b"a\n"})
    other = pack(tmp_path / "agents" / "x", {"SKILL.md": b"same\n"})
    assert sync.duplicate_notice(other, synced)


def test_duplicate_notice_silent_for_identical_or_crlf_only_copy(sync, tmp_path):
    synced = pack(tmp_path / "claude" / "x", {"SKILL.md": b"a\nb\n", "logo.png": b"\x89PNG\xff"})
    other = pack(tmp_path / "agents" / "x", {"SKILL.md": b"a\r\nb\r\n", "logo.png": b"\x89PNG\xff"})
    assert sync.duplicate_notice(other, synced) is None


def test_duplicate_notice_silent_when_other_copy_absent(sync, tmp_path):
    synced = pack(tmp_path / "claude" / "x", {"SKILL.md": b"a\n"})
    assert sync.duplicate_notice(tmp_path / "agents" / "x", synced) is None
