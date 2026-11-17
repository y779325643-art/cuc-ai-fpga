"""LLM public-case boundary and immutable preparation, without model calls."""

import json
import copy
from pathlib import Path
from uuid import uuid4

import pytest

from sr2fpga_agent.tasks import llm
from sr2fpga_agent.task_catalog import current_research_family_specs


@pytest.fixture
def output():
    # The public CLI intentionally confines output to the repository's artifacts.
    repository = Path(__file__).resolve().parents[2]
    return repository / "artifacts" / "llm-suite-tests" / uuid4().hex


def test_llm_registry_matches_current_population():
    assert set(llm.CASE_FAMILIES.values()) == {
        spec.family_id for spec in current_research_family_specs()
    }
    assert llm.RESEARCH_PLAN_VERSION == "paper1-v2.3"


@pytest.mark.parametrize("case", llm.CASE_MODULES)
def test_prepare_writes_public_inputs_without_reference_or_tool_execution(case, output, monkeypatch):
    def unexpected_tool(*args, **kwargs):
        pytest.fail("prepare must not execute a tool")
    monkeypatch.setattr(llm, "run_recorded", unexpected_tool)
    root = llm.prepare_case(case, output)
    public = llm._load_prepared(root, case)
    assert public.requirements["analysis_population"] == "development"
    assert public.asset_bytes
    public_files = {path.relative_to(root / "public").as_posix()
                    for path in (root / "public").rglob("*") if path.is_file()}
    assert public_files == {"requirements.json", "target-profile.json", "capability-profile.json",
                            *[asset["path"] for asset in public.requirements["public_assets"]]}
    assert not (root / "reference-design.json").exists()
    assert not (root / "project").exists()
    configuration = json.loads(llm.ArtifactStore(root / "store").read_verified(
        llm.ArtifactStore(root / "store").reference("configuration")))
    assert configuration["model_calls"] == 0
    assert configuration["official"] is False
    assert configuration["hidden_evaluation"] == "not_run"


def test_prepared_public_bytes_cannot_be_changed_under_old_binding(output):
    root = llm.prepare_case("qkv", output)
    path = root / "public" / "requirements.json"
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="frozen LLM public source changed"):
        llm._load_prepared(root, "qkv")


def test_prepare_preserves_existing_outputs_and_rejects_unknown_cases(output):
    root = llm.prepare_case("ffn", output)
    before = (root / "public" / "requirements.json").read_bytes()
    with pytest.raises(FileExistsError):
        llm.prepare_case("ffn", root)
    assert (root / "public" / "requirements.json").read_bytes() == before
    with pytest.raises(ValueError, match="unknown LLM case"):
        llm.prepare_case("dw_pw", output / "unknown")


def test_preparation_rejects_output_outside_artifacts():
    outside = Path(__file__).resolve().parents[1]
    with pytest.raises(ValueError, match="below artifacts"):
        llm.prepare_case("qkv", outside)


def test_preparation_cannot_be_reopened_as_another_case(output):
    root = llm.prepare_case("qkv", output)
    with pytest.raises(ValueError, match="identity mismatch"):
        llm._load_prepared(root, "attention")


def test_source_snapshot_covers_registered_contracts_and_shared_checker_dependencies():
    repository = Path(__file__).resolve().parents[2]
    files = set(llm._source_files("qkv"))
    assert repository / "contracts" / "manifest.json" in files
    assert repository / "contracts" / "pc" / "2.1" / "project-contract-2.1.schema.json" in files
    assert repository / "agent" / "src" / "sr2fpga_agent" / "contract_registry.py" in files
    assert repository / "agent" / "src" / "sr2fpga_agent" / "public_boundary.py" in files


def test_invalid_reference_is_recorded_as_static_failure_without_running_tools(output, monkeypatch):
    module = llm._case_module("qkv")
    design = copy.deepcopy(module.reference_design())
    design["entry"] = "UndefinedModule"
    monkeypatch.setattr(module, "reference_design", lambda: design)
    def unexpected_tool(*args, **kwargs):
        pytest.fail("invalid static design must not execute a tool")
    monkeypatch.setattr(llm, "run_recorded", unexpected_tool)
    result = llm.check_reference("qkv", output)
    assert result["status"] == "failed"
    assert result["static"] == "failed"
    assert result["composition"] == "not_run"
    assert result["compile"] == "not_run"
    assert "diagnostic" in result
