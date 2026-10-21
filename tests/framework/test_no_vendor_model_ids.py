"""BT-204: workflows name a model tier (`small`), never a vendor model ID; the per-host mapping lives in a shipped reference."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = sorted((ROOT / "src" / "workflows").glob("*.md"))
VENDOR_MODEL_ID = re.compile(r"\bclaude-(?:opus|sonnet|haiku|fable)-\d|\bgpt-\d|\bgemini-\d|\bo[134]-mini\b", re.I)


def test_the_pattern_catches_vendor_ids_and_spares_tier_names():
    for bad in ("claude-opus-5-5", "Claude-Sonnet-4", "gpt-5", "gemini-3-pro", "o3-mini"):
        assert VENDOR_MODEL_ID.search(bad), bad
    for ok in ("auditor_model: small", "claude-design", "the Claude Code host", "Gemini CLI"):
        assert not VENDOR_MODEL_ID.search(ok), ok


# md-crosscheck: workflow bodies are scanned for vendor model IDs; the tier names live in references/auditor-model-tiers.md
def test_no_workflow_body_names_a_vendor_model_id():
    assert WORKFLOWS, "no workflows found"
    hits = [f"{p.name}: {m.group(0)}" for p in WORKFLOWS for m in VENDOR_MODEL_ID.finditer(p.read_text(encoding="utf-8"))]
    assert hits == [], f"a workflow names a vendor model; use a tier from references/auditor-model-tiers.md: {hits}"
