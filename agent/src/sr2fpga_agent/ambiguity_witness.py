"""Evaluator-only witness, adjudication, and visibility checks for OASA."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from sr2fpga_agent.ambiguity_audit_runner import validate_ambiguity_case_manifest
from sr2fpga_agent.contract_registry import ContractRegistry


AMBIGUITY_WITNESS_VERSION = "ambiguity-witness-v1"


def build_ambiguity_witness_artifact(
    manifest: dict[str, Any],
    *,
    private_canary: str,
    cases: list[dict[str, Any]],
) -> dict[str, Any]:
    validate_ambiguity_case_manifest(manifest)
    payload = {
        "contract_version": AMBIGUITY_WITNESS_VERSION,
        "audit_run_id": manifest["audit_run_id"],
        "manifest_sha256": manifest["manifest_sha256"],
        "visibility_class": "evaluator_only",
        "private_canary": private_canary,
        "cases": cases,
    }
    artifact = {**payload, "artifact_sha256": _sha256(payload)}
    validate_ambiguity_witness_artifact(artifact)
    validate_witness_manifest_binding(manifest, artifact)
    return artifact


def load_ambiguity_witness_artifact(path: Path | str) -> dict[str, Any]:
    artifact_path = Path(path)
    if not artifact_path.is_file():
        raise ValueError(f"ambiguity witness artifact does not exist or is not a file: {artifact_path}")
    try:
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"ambiguity witness artifact is not readable JSON: {artifact_path}: {error}") from error
    if not isinstance(artifact, dict):
        raise ValueError("ambiguity witness artifact must be a JSON object")
    validate_ambiguity_witness_artifact(artifact)
    return artifact


def validate_ambiguity_witness_artifact(artifact: dict[str, Any]) -> None:
    contract = ContractRegistry().load_schema("ambiguity_witness")
    errors = contract.validate(artifact)
    if errors:
        raise ValueError("invalid ambiguity witness artifact: " + "; ".join(errors))
    payload = {key: value for key, value in artifact.items() if key != "artifact_sha256"}
    if artifact["artifact_sha256"] != _sha256(payload):
        raise ValueError("ambiguity witness SHA-256 does not match its canonical payload")
    cases = _case_map(artifact["cases"], "ambiguity witness artifact")
    for case_id, case in cases.items():
        commitment_ids = [item["commitment_id"] for item in case["annotator_commitments"]]
        if len(set(commitment_ids)) != len(commitment_ids):
            raise ValueError(f"annotator commitments must be independent for case: {case_id}")
        witness_ids = [
            item["witness_id"] for item in case["material_interpretation_witnesses"]
        ]
        if len(set(witness_ids)) != len(witness_ids):
            raise ValueError(f"duplicate material witness ID for case: {case_id}")


def validate_witness_manifest_binding(
    manifest: dict[str, Any],
    witness_artifact: dict[str, Any],
) -> None:
    validate_ambiguity_case_manifest(manifest)
    validate_ambiguity_witness_artifact(witness_artifact)
    if (
        witness_artifact["audit_run_id"] != manifest["audit_run_id"]
        or witness_artifact["manifest_sha256"] != manifest["manifest_sha256"]
    ):
        raise ValueError("ambiguity witness is not bound to the sealed case manifest")
    manifest_cases = _case_map(manifest["cases"], "sealed manifest")
    witness_cases = _case_map(witness_artifact["cases"], "ambiguity witness artifact")
    if set(manifest_cases) != set(witness_cases):
        raise ValueError("ambiguity witness case set does not match sealed manifest")
    for case_id, sealed_case in manifest_cases.items():
        gold = sealed_case["evaluator_only"]
        witness = witness_cases[case_id]
        if witness["base_requirement_cluster_id"] != sealed_case[
            "base_requirement_cluster_id"
        ]:
            raise ValueError(f"witness cluster mismatch for case: {case_id}")
        if witness["expected_disposition"] != gold["disposition"]:
            raise ValueError(f"witness disposition mismatch for case: {case_id}")
        if set(witness["critical_fact_ids"]) != set(gold["fact_ids"]):
            raise ValueError(f"witness critical fact IDs mismatch for case: {case_id}")
        if set(witness["capability_ids"]) != set(gold["capability_ids"]):
            raise ValueError(f"witness capability IDs mismatch for case: {case_id}")
        if (
            gold["audit_stratum"] == "ready_permitted_default"
            and not witness["permitted_default_ids"]
        ):
            raise ValueError(
                f"ready_permitted_default case needs at least one permitted default: {case_id}"
            )
        if witness["unknown_family_counterexample"] and gold["disposition"] != "ready":
            raise ValueError(
                f"unknown-family counterexample must have ready gold disposition: {case_id}"
            )
    assert_private_canary_not_exposed(manifest, witness_artifact)


def assert_private_canary_not_exposed(
    manifest: dict[str, Any],
    witness_artifact: dict[str, Any],
    *runtime_artifacts: dict[str, Any],
) -> None:
    canary = witness_artifact["private_canary"]
    public_projections = [case["public_projection"] for case in manifest["cases"]]
    for label, value in (
        ("sealed public projection", public_projections),
        *(("runtime artifact", artifact) for artifact in runtime_artifacts),
    ):
        if canary in json.dumps(value, ensure_ascii=False, sort_keys=True):
            raise ValueError(f"private ambiguity canary leaked into {label}")


def write_ambiguity_witness_artifact(path: Path, artifact: dict[str, Any]) -> None:
    validate_ambiguity_witness_artifact(artifact)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _case_map(items: list[dict[str, Any]], label: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in items:
        case_id = item["ambiguity_case_id"]
        if case_id in result:
            raise ValueError(f"duplicate ambiguity_case_id in {label}: {case_id}")
        result[case_id] = item
    return result


def _sha256(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
