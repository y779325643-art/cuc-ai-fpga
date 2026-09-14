"""Paper/display names change without migrating the serialized PC contract."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "docs/specs/2026-09-08-sr2fpga-terminology.md"


def test_terminology_ledger_preserves_object_and_compatibility_boundaries():
    text = LEDGER.read_text(encoding="utf-8")
    for term in (
        "Design-Space Contract", "Design Point", "Project Contract",
        "FPGA Project Package", "DSC", "DP", "PC", "FPP",
        "System-HIS v1.2", "system_his", "project-package-v1",
    ):
        assert term in text
    assert "不是整个空间" in text
    assert "不回写历史记录" in text


def test_project_contract_serialization_name_is_unchanged():
    manifest = json.loads((ROOT / "contracts/manifest.json").read_text(encoding="utf-8"))
    contract = manifest["contracts"]["system_his"]
    assert contract["version"] == "system-his-v1.2"
    assert contract["path"] == "contracts/system-his/system-his-v1.2.schema.json"


def test_ui_uses_pc_and_fpp_without_legacy_paper_label():
    html = (ROOT / "app/index.html").read_text(encoding="utf-8")
    script = (ROOT / "app/app.js").read_text(encoding="utf-8")
    assert "Project Contract (PC)" in html
    assert "FPGA 工程包（FPP）" in html
    assert "工程包交付约束" in html
    assert "PC（工程契约）解析" in script
    assert "System-HIS" not in html + script
    assert "Deterministic HIS" not in html + script
    assert "Deterministic PC" in html


def test_active_naming_entries_link_to_the_ledger():
    for relative in (
        "README.md", "agent/README.md", "contracts/README.md", "app/README.md",
        "docs/README.md", "docs/current-status.md", "docs/specs/README.md",
        "docs/specs/2026-08-14-sr2fpga-paper1-research-program-design.md",
        "docs/specs/2026-08-14-sr2fpga-paper1-research-program-design.zh.md",
        "docs/specs/2026-08-18-sr2fpga-paper1-code-architecture-development-spec.md",
        "docs/research-program/paper1-v1/README.md",
        "docs/research-program/paper1-v1/writing/style_guide.md",
        "docs/research-program/paper1-v1/writing/argument_map.md",
        "docs/research-program/paper1-v1/writing/section_contracts.md",
        "docs/research-program/paper1-v1/writing/contract-guided-evolutionary-dse-v1.9-candidate.md",
    ):
        assert LEDGER.name in (ROOT / relative).read_text(encoding="utf-8"), relative
