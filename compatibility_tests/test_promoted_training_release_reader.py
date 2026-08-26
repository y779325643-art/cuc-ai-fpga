import hashlib
import json

import pytest

from sr2fpga_agent.repository_paths import RepositoryPaths
from sr2fpga_agent.training_pool import build_training_pool_manifest
from sr2fpga_agent.training_release import (
    MANIFEST_FILENAME,
    ReleaseLeakagePolicy,
    build_candidate_training_release,
)
from sr2fpga_training.contracts import TrainingContractError
from sr2fpga_training.release_bundle import (
    PromotionAuthorizationExpectation,
    TrainingLeakagePolicyExpectation,
    inspect_promoted_release,
)


def _sha256(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _certificate():
    checks = {
        "training_split_member": True,
        "requirement_ready": True,
        "initial_snapshot_serializable": True,
        "initial_snapshot_pre_feedback": True,
        "qualification_completed_pass": True,
        "trusted_edit_surface_intact": True,
        "method_applicable_h_pass": True,
        "provenance_complete": True,
        "budget_compliant": True,
        "hidden_material_redacted": True,
        "leakage_audit_pass": True,
        "source_policy_allowed": True,
    }
    payload = {
        "contract_version": "training-eligibility-v1",
        "visibility_class": "release_internal",
        "episode_id": "episode-001",
        "method_condition_id": "M0",
        "training_split_id": "train-split-dev",
        "source_class": "model_generated",
        "failure_origin": "natural_llm",
        "policy_id": "eligibility-policy",
        "policy_sha256": "a" * 64,
        "episode_pack_sha256": "b" * 64,
        "initial_snapshot_id": "snapshot-initial",
        "initial_snapshot_sha256": "c" * 64,
        "terminal_candidate_sha256": "d" * 64,
        "project_envelope_sha256": "e" * 64,
        "qualification_outcome_sha256": "f" * 64,
        "evidence_bundle_sha256": "0" * 64,
        "checks": checks,
        "official_hidden_outcome_ref_count": 0,
        "eligibility_status": "eligible",
        "exclusion_reason_ids": [],
    }
    return {**payload, "artifact_sha256": _sha256(payload)}


def _row_and_sidecar(treatment, certificate):
    snapshot_id = "snapshot-initial" if treatment == "M6U" else "snapshot-final"
    payload = {
        "contract_version": "training-view-row-v2",
        "row_id": f"row-{treatment.lower()}",
        "source_episode_id": "episode-001",
        "snapshot_id": snapshot_id,
        "treatment": treatment,
        "payload": {
            "prompt_messages": [{"role": "user", "content": "Generate a counter."}],
            "assistant_target": {
                "kind": "project_files",
                "files": [
                    {
                        "path": "src/design.v",
                        "role": "rtl",
                        "content": "module top; endmodule",
                    }
                ],
            },
        },
    }
    row = {**payload, "row_sha256": _sha256(payload)}
    sidecar_payload = {
        "contract_version": "training-view-eligibility-sidecar-v1",
        "visibility_class": "release_internal",
        "row_id": row["row_id"],
        "row_sha256": row["row_sha256"],
        "source_episode_id": "episode-001",
        "snapshot_id": snapshot_id,
        "treatment": treatment,
        "eligibility_artifact_sha256": certificate["artifact_sha256"],
        "eligibility_evidence_bundle_sha256": certificate["evidence_bundle_sha256"],
        "snapshot_envelope_sha256": (
            certificate["initial_snapshot_sha256"]
            if treatment == "M6U"
            else certificate["project_envelope_sha256"]
        ),
    }
    sidecar = {**sidecar_payload, "artifact_sha256": _sha256(sidecar_payload)}
    return row, sidecar, certificate


def _candidate(tmp_path):
    certificate = _certificate()
    exports = {
        "M6U": [_row_and_sidecar("M6U", certificate)],
        "M6F": [_row_and_sidecar("M6F", certificate)],
        "M6T": [],
        "M6F_E_TRAJ": [],
    }
    pool = build_training_pool_manifest(
        exports=exports,
        family_by_episode={"episode-001": "counter"},
    )
    agent_policy = ReleaseLeakagePolicy.create(
        policy_id="release-leakage-policy",
        forbidden_canaries=("CANARY-PROMOTION-PRIVATE",),
    )
    release = build_candidate_training_release(
        tmp_path / "artifacts/releases",
        pool_manifest=pool,
        exports=exports,
        leakage_policy=agent_policy,
        paths=RepositoryPaths(root=tmp_path),
    )
    training_policy = TrainingLeakagePolicyExpectation.create(
        policy_id="release-leakage-policy",
        forbidden_canaries=("CANARY-PROMOTION-PRIVATE",),
    )
    authorization = PromotionAuthorizationExpectation(
        campaign_freeze_sha256="1" * 64,
        training_plan_sha256="2" * 64,
        promotion_record_sha256="3" * 64,
    )
    return release, training_policy, authorization


def _promote(release, authorization):
    manifest_path = release / MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["release_state"] = "promoted"
    manifest["training_authorized"] = True
    manifest["authorization"] = {
        "campaign_freeze_sha256": authorization.campaign_freeze_sha256,
        "training_plan_sha256": authorization.training_plan_sha256,
        "promotion_record_sha256": authorization.promotion_record_sha256,
    }
    without_hash = {
        key: value for key, value in manifest.items() if key != "artifact_sha256"
    }
    manifest["artifact_sha256"] = _sha256(without_hash)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def test_training_rejects_candidate_and_inspects_bound_promoted_release(tmp_path) -> None:
    release, leakage_policy, authorization = _candidate(tmp_path)
    with pytest.raises(TrainingContractError, match="candidate_unpromoted"):
        inspect_promoted_release(
            release,
            authorization=authorization,
            leakage_policy=leakage_policy,
        )

    _promote(release, authorization)
    inspected = inspect_promoted_release(
        release,
        authorization=authorization,
        leakage_policy=leakage_policy,
    )

    assert inspected.manifest["training_authorized"] is True
    assert inspected.treatment_path("M6U") == release / "views/M6U.jsonl"
    assert inspected.treatment_path("M6T").read_bytes() == b""


def test_training_rejects_authorization_leakage_and_pool_binding_mismatch(tmp_path) -> None:
    release, leakage_policy, authorization = _candidate(tmp_path)
    _promote(release, authorization)

    wrong_authorization = PromotionAuthorizationExpectation(
        campaign_freeze_sha256="4" * 64,
        training_plan_sha256=authorization.training_plan_sha256,
        promotion_record_sha256=authorization.promotion_record_sha256,
    )
    with pytest.raises(TrainingContractError, match="authorization mismatch"):
        inspect_promoted_release(
            release,
            authorization=wrong_authorization,
            leakage_policy=leakage_policy,
        )

    wrong_policy = TrainingLeakagePolicyExpectation.create(policy_id="wrong-policy")
    with pytest.raises(TrainingContractError, match="leakage policy mismatch"):
        inspect_promoted_release(
            release,
            authorization=authorization,
            leakage_policy=wrong_policy,
        )

    manifest_path = release / MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["pool_id"] = "pool-forged"
    without_hash = {
        key: value for key, value in manifest.items() if key != "artifact_sha256"
    }
    manifest["artifact_sha256"] = _sha256(without_hash)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with pytest.raises(TrainingContractError, match="pool binding mismatch"):
        inspect_promoted_release(
            release,
            authorization=authorization,
            leakage_policy=leakage_policy,
        )


def test_training_rejects_release_checksum_and_inventory_tampering(tmp_path) -> None:
    release, leakage_policy, authorization = _candidate(tmp_path)
    _promote(release, authorization)
    view = release / "views/M6F.jsonl"
    view.write_bytes(view.read_bytes() + b"\n")
    with pytest.raises(TrainingContractError, match="size mismatch|checksum mismatch"):
        inspect_promoted_release(
            release,
            authorization=authorization,
            leakage_policy=leakage_policy,
        )

    (release / "unexpected.txt").write_text("unexpected", encoding="utf-8")
    with pytest.raises(TrainingContractError, match="inventory mismatch"):
        inspect_promoted_release(
            release,
            authorization=authorization,
            leakage_policy=leakage_policy,
        )
