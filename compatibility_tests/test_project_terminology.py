"""Current PC2.1 registration and historical serialization stay distinct."""
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


def test_current_and_historical_contracts_are_registered_separately():
    manifest = json.loads((ROOT / "contracts/manifest.json").read_text(encoding="utf-8"))
    contract = manifest["contracts"]["system_his"]
    assert contract["version"] == "system-his-v1.2"
    assert contract["path"] == "contracts/system-his/system-his-v1.2.schema.json"
    current = manifest["contracts"]["project_contract_2_1"]
    assert current["version"] == "sr2fpga-pc-2.1"
    assert current["path"] == "contracts/pc/2.1/project-contract-2.1.schema.json"


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
        "docs/research-program/paper1-v1/README.md",
        "docs/research-program/paper1-v1/writing/style_guide.md",
        "docs/research-program/paper1-v1/writing/argument_map.md",
        "docs/research-program/paper1-v1/writing/section_contracts.md",
        "docs/research-program/paper1-v1/writing/contract-guided-evolutionary-dse-v1.9-candidate.md",
    ):
        assert LEDGER.name in (ROOT / relative).read_text(encoding="utf-8"), relative


def test_old_specifications_have_an_explicit_archive_entry():
    archive = ROOT / "docs/specs/superseded"
    index = (archive / "README.md").read_text(encoding="utf-8")
    for name in (
        "2026-08-14-sr2fpga-paper1-research-program-design.md",
        "2026-08-14-sr2fpga-paper1-research-program-design.zh.md",
        "2026-08-18-sr2fpga-paper1-code-architecture-development-spec.md",
    ):
        assert (archive / name).is_file()
        assert name in index
        assert not (ROOT / "docs/specs" / name).exists()


def test_persistent_writing_state_cannot_resume_an_old_research_plan():
    state = json.loads((ROOT / "docs/research-program/paper1-v1/state.json").read_text(encoding="utf-8"))
    assert state["workspace_role"] == "historical_research_workspace"
    assert state["canonical_spec_version"] == "paper1-v2.3"
    assert (ROOT / state["canonical_spec"]).is_file()
    assert (ROOT / state["historical_state"]).is_file()
    assert state["experiment_execution_authorized"] is False
    assert "approved_candidate_version" not in state
