"""Development-only model-gateway provenance artifacts."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from sr2fpga_agent.artifact_store import ArtifactRef, ArtifactStore
from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.provider_seed_capability import read_verified_provider_seed_capability


def write_model_gateway_provenance(
    store: ArtifactStore,
    *,
    episode_id: str,
    analysis_population: str,
    method_condition: str,
    event: dict[str, Any],
    seed_control_evidence_ref: ArtifactRef | None = None,
) -> ArtifactRef | None:
    """Persist one completed or failed provider call when provenance exists."""

    if event.get("event") not in {"model_call_finished", "model_call_failed"}:
        return None
    provider = event.get("provider_response_provenance")
    if not isinstance(provider, dict):
        return None
    identity = {
        "episode_id": episode_id,
        "call_id": event.get("call_id"),
        "stage": event.get("stage"),
        "operation": event.get("operation"),
    }
    digest = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    provenance_id = f"mgp-{digest[:32]}"
    payload = {
        "contract_version": "model-gateway-provenance-v1",
        "provenance_id": provenance_id,
        "analysis_population": analysis_population,
        "episode_id": episode_id,
        "method_condition": method_condition,
        "call_id": event.get("call_id"),
        "stage": event.get("stage"),
        "operation": event.get("operation"),
        "call_status": event.get("status"),
        "provider_adapter": provider.get("provider_adapter"),
        "provider_model": provider.get("provider_model"),
        "gateway_base_url_sha256": provider.get("gateway_base_url_sha256"),
        "requested_decoding_seed": provider.get("requested_decoding_seed"),
        "seed_forwarding_status": provider.get("seed_forwarding_status"),
        "deterministic_seed_control": provider.get("deterministic_seed_control"),
        "seed_control_evidence_ref": (
            seed_control_evidence_ref.to_dict() if seed_control_evidence_ref else None
        ),
        "provider_system_fingerprint": provider.get("provider_system_fingerprint"),
        "system_fingerprint_status": provider.get("system_fingerprint_status"),
        "pass_credit_authority": False,
        "official_authority": False,
        "g3_accepted": False,
        "g4b_authorized": False,
    }
    _validate_seed_binding(store, payload)
    return store.put_validated_json(
        f"model-gateway-provenance/{provenance_id}",
        payload,
        contract_key="model_gateway_provenance",
    )


def read_verified_model_gateway_provenance(
    store: ArtifactStore, reference: ArtifactRef,
) -> dict[str, Any]:
    """Verify both call provenance and any referenced capability evidence."""
    payload = json.loads(store.read_verified(reference))
    errors = ContractRegistry().load_schema("model_gateway_provenance").validate(payload)
    if errors:
        raise ValueError("invalid model gateway provenance: " + "; ".join(errors))
    identity = {field: payload[field] for field in (
        "episode_id", "call_id", "stage", "operation"
    )}
    digest = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if payload["provenance_id"] != f"mgp-{digest[:32]}":
        raise ValueError("model gateway provenance identity mismatch")
    _validate_seed_binding(store, payload)
    return payload


def _validate_seed_binding(store: ArtifactStore, payload: dict[str, Any]) -> None:
    raw = payload["seed_control_evidence_ref"]
    if raw is None:
        if payload["deterministic_seed_control"] == "supported":
            raise ValueError("supported seed control requires capability evidence")
        return
    capability = read_verified_provider_seed_capability(store, ArtifactRef(**raw))
    for field in ("provider_adapter", "provider_model", "gateway_base_url_sha256"):
        if payload[field] != capability[field]:
            raise ValueError(f"provider seed capability binding mismatch: {field}")
    if payload["deterministic_seed_control"] == "supported":
        if capability["paired_confirmatory_eligible"] is not True:
            raise ValueError("supported seed control requires eligible capability")
        if payload["seed_forwarding_status"] != "forwarded":
            raise ValueError("supported seed control requires seed forwarding")
        if payload["system_fingerprint_status"] != "reported" or (
            payload["provider_system_fingerprint"] not in capability["system_fingerprints"]
        ):
            raise ValueError("supported seed control requires qualified backend fingerprint")
