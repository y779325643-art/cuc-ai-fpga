import json
from pathlib import Path, PurePosixPath

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "contracts" / "manifest.json"


def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def test_contract_manifest_declares_required_contracts() -> None:
    manifest = load_manifest()
    assert manifest["contract_registry_version"] == "1.0"
    assert set(manifest["contracts"]) == {
        "system_his",
        "system_his_backend_capabilities",
        "system_his_well_formedness",
        "system_his_compatibility",
        "requirement_audit",
        "ambiguity_case_manifest",
        "clarification_replay",
        "ambiguity_outcome",
        "ambiguity_witness",
        "ambiguity_audit_events",
        "project_package",
        "project_envelope",
        "terminal_candidate",
        "public_evaluation_candidate",
        "public_evaluation_candidate_v2",
        "official_hidden_outcome",
        "development_hidden_conformance_outcome",
        "training_qualification_outcome",
        "full_pack_smoke_report",
        "full_pack_runner_reconciliation",
        "full_pack_runner_reconciliation_v2",
        "development_public_evaluation",
        "development_public_l2_harness",
        "development_terminal_public_outcome",
        "development_attempt_public_outcome",
        "development_authoritative_attempt_public_outcome",
        "development_terminal_selection",
        "development_oracle_run_evidence",
        "development_tool_environment",
        "development_l4_qor_provenance",
        "development_l4_tool_environment",
        "pilot_target_profile_pair_manifest",
        "development_target_profile_pair_outcome",
        "development_pre_candidate_stop_outcome",
            "development_pre_candidate_stop_outcome_v2",
            "development_his_correction_outcome",
            "development_episode_outcome",
        "full_pack_outcome_reconciliation",
        "full_pack_outcome_reconciliation_v2",
        "attempt_event",
        "cost_summary",
        "development_block_preparation_event",
        "model_gateway_provenance",
        "development_provider_seed_capability",
        "training_eligibility",
        "training_view_eligibility_sidecar",
        "training_pool_manifest",
        "training_release_manifest",
        "episode_pack",
        "paired_block",
        "development_shared_checkpoint_manifest",
        "trajectory",
        "trajectory_v2",
        "training_view_row_legacy",
        "training_view_row",
        "task_catalog",
    }


def test_registered_contract_paths_are_repository_relative() -> None:
    for record in load_manifest()["contracts"].values():
        path = record["path"]
        posix_path = PurePosixPath(path)
        assert path
        assert not Path(path).is_absolute()
        assert not posix_path.is_absolute()
        assert ".." not in posix_path.parts
        assert (REPO_ROOT / path).resolve().is_relative_to(REPO_ROOT)


def test_all_registered_contracts_exist() -> None:
    for name, record in load_manifest()["contracts"].items():
        assert (REPO_ROOT / record["path"]).is_file(), name
