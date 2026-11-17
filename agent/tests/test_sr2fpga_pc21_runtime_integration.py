"""Development preflight and terminal/export boundaries without model dispatch."""
from dataclasses import asdict
import copy
import io
import json
import hashlib
from pathlib import Path
import zipfile

import pytest

from sr2fpga_agent.artifact_store import ArtifactStore
from sr2fpga_agent.execution.budgets import BudgetLedger, BudgetLimits
from sr2fpga_agent.execution.development import terminal_suites
from sr2fpga_agent.execution.gateway import ModelGateway, ReplayTransport
from sr2fpga_agent.execution.integration import configured_limits, export_analysis_views, preflight
from sr2fpga_agent.execution.isolation import LocalDevelopmentBackend, ToolLimits
from sr2fpga_agent.execution.runtime import METHODS, PairedBlockRuntime, RuntimeIdentity, finalize_batch
from sr2fpga_agent.models import canonical_json_bytes
from agent.tests.test_sr2fpga_pc21_runtime_methods import public_fixture


def common_limits():
    return {"max_total_input_tokens": 2_000_000, "max_total_output_tokens": 2_000_000,
            "max_single_output_tokens": 100_000, "max_context_tokens": 500_000,
            "max_public_tool_calls": 128, "max_final_public_tool_calls": 16, "max_hidden_tool_calls": 16,
            "max_active_seconds": 1800, "max_eda_seconds": 1800, "max_cpu_seconds": 7200,
            "max_memory_bytes": 2_147_483_648}


def config(tmp_path):
    task, _, _, _ = public_fixture(tmp_path)
    directory = tmp_path / "input-public"
    for field, name in (("requirements", "requirements"), ("target_profile", "target-profile"),
                        ("capability_profile", "capability-profile")):
        (directory / (name + ".json")).write_bytes(getattr(task.sources, field).content)
    tape = tmp_path / "tape.json"
    tape.write_text(json.dumps({"contract_version": "pc21-model-replay-v1", "source_class": "synthetic_fixture", "responses": {}}))
    return {"contract_version": "pc21-runtime-config-v1", "research_plan_version": "paper1-v2.3",
        "population_id": "llm_inference_subsystems_v1", "analysis_population": "development",
        "campaign_id": "fixture-campaign", "case": "ffn", "design_cluster_id": "fixture-cluster",
        "dependency_group_id": None, "semantic_instance_id": "fixture-semantic", "replicate_id": "r0", "schedule_seed": 3,
        "public_directory": str(directory), "limits": common_limits(), "final_limits": common_limits(),
        "tool_limits": asdict(ToolLimits()), "max_model_call_seconds": 30,
        "transport": {"kind": "replay", "path": str(tape)}, "backend": {"kind": "local_development"}}


def test_formal_preflight_fails_closed_and_never_dispatches_or_loads_provider(tmp_path, monkeypatch):
    document = config(tmp_path)
    document["transport"] = {"kind": "client_factory", "factory": "missing_provider:never_import",
                             "settings": {"api_key_env": "NOT_READ_BY_PREFLIGHT"}}
    monkeypatch.setattr("sr2fpga_agent.execution.integration.resolve_executable", lambda tool: Path("fixture-tool"))
    report = preflight(document, formal=True)
    assert report["ready"] is False
    assert report["model_calls"] == 0
    assert "research_protocol_unfrozen" in report["reasons"]
    assert "task_family_not_qualified" in report["reasons"]
    assert "os_isolation_not_qualified" in report["reasons"]


def test_preflight_rejects_literal_credentials_before_transport_import(tmp_path):
    document = config(tmp_path)
    document["transport"] = {"kind": "client_factory", "factory": "missing_provider:never_import",
                             "settings": {"api_key": "synthetic-secret-not-to-be-logged"}}
    with pytest.raises(ValueError, match="environment reference"):
        preflight(document)


def test_preflight_accepts_registered_replay_with_only_public_data(tmp_path, monkeypatch):
    document = config(tmp_path)
    monkeypatch.setattr("sr2fpga_agent.execution.integration.resolve_executable", lambda tool: Path("fixture-tool"))
    report = preflight(document)
    assert report["ready"] is True and report["official"] is False
    assert report["backend"]["isolation_qualified"] is False


def test_gateway_closed_generation_allows_old_receipt_but_no_new_dispatch(tmp_path):
    store = ArtifactStore(tmp_path / "store")
    ledger = BudgetLedger(store, "fixture-closed", {"M1": BudgetLimits.for_method("M1", **common_limits())})
    transport = ReplayTransport({"stage": ["first-response", "forbidden-second-response"]})
    gateway = ModelGateway(store, ledger, transport)
    first = gateway.call("one", "stage", ("M1",), {"public_text": "fixture"}, output_format="text")
    store.put_blob("generation-closed", b"{}")
    assert gateway.call("one", "stage", ("M1",), {"public_text": "fixture"}, output_format="text") == first
    with pytest.raises(PermissionError, match="sealed"):
        gateway.call("two", "stage", ("M1",), {"public_text": "fixture"}, output_format="text")
    assert len(transport.requests) == 1


def test_synthetic_terminal_inputs_are_distinct_and_not_public_projection(tmp_path):
    task, _, _, _ = public_fixture(tmp_path)
    private = terminal_suites({"ffn": task})["ffn"]
    from sr2fpga_agent.execution.evaluation import TrustedSuite
    public = TrustedSuite.for_development_case("ffn")
    assert private.testbench_sha256 != public.testbench_sha256
    assert private.commitment_sha256 != public.commitment_sha256


def test_terminal_null_full_barrier_export_rederives_scores_and_preserves_budget(tmp_path):
    task, _, _, _ = public_fixture(tmp_path)
    block = PairedBlockRuntime(task, case="ffn", identity=RuntimeIdentity("fixture", "llm_gated_ffn", "c", None, "s", "r"),
        output_root=tmp_path / "control", evaluator_root=tmp_path / "private" / "b0", transport=ReplayTransport({}),
        limits=configured_limits(common_limits()), final_limits=configured_limits(common_limits(), final=True),
        tool_limits=ToolLimits(), backend=LocalDevelopmentBackend())
    # Explicit fixture for planned no-candidate outcomes. No model or tool runs.
    generation = {"official": False, "identity": asdict(block.identity), "source_class": "synthetic_fixture",
        "budget": block.ledger.snapshot(), "schedule": [], "terminals": {method: {
            "candidate": None, "public_evaluation": None, "infrastructure": False,
            "reason": {"reason": "fixture_invalid_proposals"}, "repairs": []} for method in METHODS}}
    block.store.put_blob("generation-closed", canonical_json_bytes(generation), media_type="application/json")
    final = finalize_batch([block], private_root=tmp_path / "private" / "authority", private_suites=terminal_suites({"ffn": task}))
    assert final["barrier"]["slots"] == 6
    assert all(row["value"] == 0 for row in final["records"])
    assert all(row["candidate_sha256"] is None for row in final["records"])
    assert all(state["actual"]["observed"]["hidden_tool_calls"] == 0 for state in final["terminal_costs"].values())
    forged = copy.deepcopy(final)
    forged["records"][0]["value"] = 1
    export_analysis_views([block], forged, tmp_path / "analysis")
    rows = json.loads((tmp_path / "analysis" / "results.json").read_text())["results"]
    assert all(row["value"] == 0 for row in rows)


def test_runtime_preparation_archives_actual_uncommitted_source_bytes(tmp_path):
    task, _, _, _ = public_fixture(tmp_path)
    block = PairedBlockRuntime(task, case="ffn", identity=RuntimeIdentity("fixture", "llm_gated_ffn", "c", None, "s", "r"),
        output_root=tmp_path / "control", evaluator_root=tmp_path / "private", transport=ReplayTransport({}),
        limits=configured_limits(common_limits()), final_limits=configured_limits(common_limits(), final=True),
        tool_limits=ToolLimits())
    bindings = json.loads(block.store.read_verified("source-bindings"))
    code_state = json.loads(block.store.read_verified("code-state"))
    with zipfile.ZipFile(io.BytesIO(block.store.read_verified(code_state["source_archive"]["key"]))) as archive:
        for relative, expected in bindings.items():
            assert hashlib.sha256(archive.read(Path(relative).as_posix())).hexdigest() == expected
        assert "agent/src/sr2fpga_agent/execution/runtime.py" in archive.namelist()
        assert "contracts/manifest.json" in archive.namelist()
