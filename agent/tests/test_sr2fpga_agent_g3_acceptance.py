import json
from types import SimpleNamespace

import pytest

from sr2fpga_agent.artifact_store import ArtifactStore
from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.g3_acceptance import (
    REQUIRED_SCENARIOS, read_verified_g3_acceptance, reconcile_g3_acceptance,
)
from sr2fpga_agent.g3_test_evidence import G3TestEvidenceRecorder


def test_historical_version_fields_are_runtime_registered():
    assert ContractRegistry().load_schema("system_his").version == "system-his-v1.2"
    assert ContractRegistry().load_schema("requirement_audit").version == "requirement-audit-v1"


def test_g3_empty_evidence_and_forged_positive_cannot_grant_acceptance(tmp_path):
    recorder = G3TestEvidenceRecorder(tmp_path)
    recorder.pytest_sessionfinish(None, 0)
    report, ref = reconcile_g3_acceptance(tmp_path, recorder.manifest_ref)
    assert report["g3_accepted"] is False
    assert len(report["matrix"]) == len(REQUIRED_SCENARIOS)
    assert all(row["status"] == "blocked" for row in report["matrix"])
    assert read_verified_g3_acceptance(tmp_path, ref) == report
    forged = dict(report, g3_accepted=True)
    store = ArtifactStore(tmp_path / "evidence")
    with pytest.raises(ValueError, match="invalid registered"):
        store.put_validated_json("forged", forged, contract_key="g3_acceptance")
    forged_ref = store.put_blob("forged-unvalidated", json.dumps(forged).encode())
    with pytest.raises(ValueError, match="invalid G3 acceptance"):
        read_verified_g3_acceptance(tmp_path, forged_ref)


def test_g3_test_success_booleans_without_execution_artifacts_do_not_pass(tmp_path):
    recorder = G3TestEvidenceRecorder(tmp_path)
    recorder.collected = sorted({prefix for prefix, count in REQUIRED_SCENARIOS.values()})
    for node in recorder.collected:
        for phase in ("setup", "call", "teardown"):
            recorder.pytest_runtest_logreport(SimpleNamespace(nodeid=node, when=phase, outcome="passed"))
    recorder.pytest_sessionfinish(None, 0)
    report, _ = reconcile_g3_acceptance(tmp_path, recorder.manifest_ref)
    assert report["g3_accepted"] is False
    blocked = {row["scenario_id"] for row in report["matrix"] if row["status"] == "blocked"}
    assert "gold_ready_m0_m5_and_three_cost_views" in blocked
    assert "m1_public_diagnosis_patch_rerun" in blocked
    assert "m5_public_diagnosis_patch_rerun" in blocked


def test_g3_source_snapshot_tamper_is_rejected(tmp_path):
    recorder = G3TestEvidenceRecorder(tmp_path)
    recorder.pytest_sessionfinish(None, 0)
    payload = json.loads(recorder.store.read_verified(recorder.manifest_ref))
    payload["source_fingerprints"][next(iter(payload["source_fingerprints"]))] = "0" * 64
    ref = recorder.store.put_validated_json("forged-source", payload, contract_key="g3_test_evidence")
    with pytest.raises(ValueError, match="different source snapshot"):
        reconcile_g3_acceptance(tmp_path, ref)


def test_g3_recorder_preserves_original_write_once_artifacts(tmp_path):
    recorder = G3TestEvidenceRecorder(tmp_path / "run")
    try:
        recorder.pytest_sessionstart(None)
        store = ArtifactStore(tmp_path / "fixture")
        ref = store.put_blob("candidate", b"original")
        snapshot = recorder.stores[store.root.resolve()][1]
        assert snapshot.read_verified(ref) == b"original"
        assert len(recorder.stores) == 1
    finally:
        recorder.pytest_sessionfinish(None, 0)


def test_gold_cost_and_outcome_sources_cannot_be_transplanted():
    from sr2fpga_agent.g3_acceptance import _closed_gold_block

    costs = {"reconciliation_status": "complete", "method_records": [
        {"method_condition": "M0", "trajectory_ref": {"sha256": "a" * 64}}
    ]}
    outcomes = [{"method_condition": "M0", "trajectory_ref": {"sha256": "b" * 64},
                 "development_vpp_l3": True}]
    assert not _closed_gold_block(costs, outcomes)
    outcomes[0]["trajectory_ref"] = costs["method_records"][0]["trajectory_ref"]
    assert _closed_gold_block(costs, outcomes)
