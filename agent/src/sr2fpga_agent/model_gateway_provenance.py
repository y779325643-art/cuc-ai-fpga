"""Development-only model-gateway provenance artifacts."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from sr2fpga_agent.artifact_store import ArtifactRef, ArtifactStore


def write_model_gateway_provenance(
    store: ArtifactStore,
    *,
    episode_id: str,
    analysis_population: str,
    method_condition: str,
    event: dict[str, Any],
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
        "seed_control_evidence_ref": None,
        "provider_system_fingerprint": provider.get("provider_system_fingerprint"),
        "system_fingerprint_status": provider.get("system_fingerprint_status"),
        "pass_credit_authority": False,
        "official_authority": False,
        "g3_accepted": False,
        "g4b_authorized": False,
    }
    return store.put_validated_json(
        f"model-gateway-provenance/{provenance_id}",
        payload,
        contract_key="model_gateway_provenance",
    )
