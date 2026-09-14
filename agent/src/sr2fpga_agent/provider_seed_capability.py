"""Development-only qualification of provider decoding-seed capability."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from sr2fpga_agent.models import sha256_json as _sha256_json
from sr2fpga_agent.artifact_store import ArtifactRef, ArtifactStore
from sr2fpga_agent.contract_registry import ContractRegistry


_FAILURE_CATEGORIES = {
    "authentication",
    "authorization",
    "quota",
    "rate_limit",
    "model_unavailable",
    "seed_rejected",
    "network",
    "timeout",
    "provider_error",
    "response_invalid",
    "unknown",
}
_DOCUMENTATION_STATUSES = {
    "not_checked",
    "seed_undocumented",
    "unsupported_documented",
    "best_effort_documented",
    "deterministic_documented",
}
_DOCUMENTATION_REVIEW_TYPES = {
    "self_reviewed_development",
    "independent_review",
}
_DERIVED_FIELDS = (
    "capability_profile_id",
    "probe_protocol_sha256",
    "requested_decoding_seed",
    "planned_repetitions",
    "completed_repetitions",
    "failed_repetitions",
    "failure_categories",
    "probe_status",
    "output_sha256s",
    "system_fingerprints",
    "exact_output_match",
    "fingerprint_status",
    "fingerprint_match",
    "seed_control_classification",
    "provider_token_usage_status",
    "input_tokens",
    "output_tokens",
    "cached_tokens",
    "paired_confirmatory_eligible",
    "limitations",
)


@dataclass(frozen=True)
class ProviderSeedProbeObservation:
    status: str
    output_sha256: str | None = None
    system_fingerprint: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    cached_tokens: int | None = None
    failure_category: str | None = None
    output_size_bytes: int | None = None

    def __post_init__(self) -> None:
        if self.status not in {"completed", "failed"}:
            raise ValueError("probe observation status must be completed or failed")
        if self.status == "completed":
            if not _is_sha256(self.output_sha256):
                raise ValueError("completed probe observation requires output_sha256")
            if (
                isinstance(self.output_size_bytes, bool)
                or not isinstance(self.output_size_bytes, int)
                or self.output_size_bytes < 1
            ):
                raise ValueError(
                    "completed probe observation requires positive output_size_bytes"
                )
            if self.failure_category is not None:
                raise ValueError(
                    "completed probe observation cannot carry failure_category"
                )
        else:
            if self.output_sha256 is not None or self.output_size_bytes is not None:
                raise ValueError(
                    "failed probe observation cannot carry completed output evidence"
                )
            if self.failure_category not in _FAILURE_CATEGORIES:
                raise ValueError(
                    "failed probe observation requires a known failure_category"
                )
        if self.system_fingerprint is not None and (
            not isinstance(self.system_fingerprint, str)
            or not self.system_fingerprint
            or self.system_fingerprint != self.system_fingerprint.strip()
        ):
            raise ValueError(
                "system_fingerprint must be canonical non-empty text when present"
            )
        for name in ("input_tokens", "output_tokens", "cached_tokens"):
            value = getattr(self, name)
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, int) or value < 0
            ):
                raise ValueError(f"{name} must be a non-negative integer when present")


def write_development_provider_seed_capability(
    store: ArtifactStore,
    *,
    provider_adapter: str,
    provider_model: str,
    gateway_base_url: str,
    protocol: Mapping[str, Any],
    documentation_status: str,
    documentation_snapshot_sha256: str | None,
    observations: Sequence[ProviderSeedProbeObservation],
    documentation_source_url_sha256: str | None = None,
    documentation_review: Mapping[str, Any] | None = None,
) -> ArtifactRef:
    """Derive and persist one non-authoritative provider capability profile."""

    if provider_adapter not in {"openai_compatible", "anthropic_compatible"}:
        raise ValueError("unknown provider seed capability adapter")
    if not isinstance(provider_model, str) or not provider_model.strip():
        raise ValueError("provider model must be non-empty")
    if not isinstance(gateway_base_url, str) or not gateway_base_url.rstrip("/"):
        raise ValueError("provider gateway base URL must be non-empty")
    frozen_protocol = _normalized_protocol(protocol)
    frozen_documentation_review = _normalized_documentation(
        documentation_status=documentation_status,
        documentation_snapshot_sha256=documentation_snapshot_sha256,
        documentation_source_url_sha256=documentation_source_url_sha256,
        documentation_review=documentation_review,
    )
    frozen_observations = [
        _observation_payload(index, item)
        for index, item in enumerate(observations)
    ]
    if len(frozen_observations) > frozen_protocol["repetitions"]:
        raise ValueError("probe observations exceed planned repetitions")

    payload: dict[str, Any] = {
        "contract_version": "development-provider-seed-capability-v1",
        "evaluation_scope": "excluded_development_conformance_only",
        "provider_adapter": provider_adapter,
        "provider_model": provider_model.strip(),
        "gateway_base_url_sha256": _sha256_text(gateway_base_url.rstrip("/")),
        "probe_protocol": frozen_protocol,
        "documentation_status": documentation_status,
        "documentation_snapshot_sha256": documentation_snapshot_sha256,
        "documentation_source_url_sha256": documentation_source_url_sha256,
        "documentation_review": frozen_documentation_review,
        "observations": frozen_observations,
    }
    payload.update(_derive_fields(payload))
    payload.update(
        {
            "official_outcome": False,
            "official_authority": False,
            "pass_credit_authority": False,
            "g3_accepted": False,
            "g4b_authorized": False,
        }
    )
    _validate_capability_payload(payload)
    return store.put_validated_json(
        f"provider-seed-capabilities/{payload['capability_profile_id']}",
        payload,
        contract_key="development_provider_seed_capability",
    )


def load_development_provider_seed_capability(path: str) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(
            f"provider seed capability manifest is unreadable: {path}"
        ) from exc
    _validate_capability_payload(payload)
    return payload


def read_verified_provider_seed_capability(
    store: ArtifactStore, reference: ArtifactRef,
) -> dict[str, Any]:
    """Read immutable evidence and recompute every capability summary field."""
    payload = json.loads(store.read_verified(reference))
    _validate_capability_payload(payload)
    return payload


def require_paired_confirmatory_seed_capability(
    payload: Mapping[str, Any],
    *,
    provider_adapter: str,
    provider_model: str,
    gateway_base_url: str,
) -> None:
    _validate_capability_payload(payload)
    if payload.get("provider_adapter") != provider_adapter:
        raise ValueError("provider seed capability adapter does not match source")
    if payload.get("provider_model") != provider_model:
        raise ValueError("provider seed capability model does not match source")
    if payload.get("gateway_base_url_sha256") != _sha256_text(
        gateway_base_url.rstrip("/")
    ):
        raise ValueError("provider seed capability gateway does not match source")
    review = payload.get("documentation_review")
    if not isinstance(review, Mapping) or review.get("review_type") != "independent_review":
        raise ValueError(
            "provider seed capability lacks an independent documentation review"
        )
    if payload.get("paired_confirmatory_eligible") is not True:
        classification = payload.get("seed_control_classification", "unknown")
        raise ValueError(
            "provider seed capability is not paired-confirmatory eligible: "
            + str(classification)
        )


def _validate_capability_payload(payload: Mapping[str, Any]) -> None:
    errors = ContractRegistry().load_schema(
        "development_provider_seed_capability"
    ).validate(payload)
    if errors:
        raise ValueError(
            "invalid provider seed capability manifest: " + "; ".join(errors)
        )
    normalized_protocol = _normalized_protocol(payload["probe_protocol"])
    if payload["probe_protocol"] != normalized_protocol:
        raise ValueError("provider seed capability probe_protocol is not canonical")
    normalized_review = _normalized_documentation(
        documentation_status=payload["documentation_status"],
        documentation_snapshot_sha256=payload["documentation_snapshot_sha256"],
        documentation_source_url_sha256=payload[
            "documentation_source_url_sha256"
        ],
        documentation_review=payload["documentation_review"],
    )
    if payload["documentation_review"] != normalized_review:
        raise ValueError("provider seed capability documentation review is not canonical")
    observations = payload["observations"]
    if len(observations) > normalized_protocol["repetitions"]:
        raise ValueError("probe observations exceed planned repetitions")
    for index, raw in enumerate(observations):
        normalized = _normalized_observation_payload(index, raw)
        if raw != normalized:
            raise ValueError(
                f"provider seed capability observation {index} is not canonical"
            )
    expected = _derive_fields(payload)
    for field in _DERIVED_FIELDS:
        if payload.get(field) != expected[field]:
            raise ValueError(
                f"provider seed capability derived field mismatch: {field}"
            )


def _derive_fields(payload: Mapping[str, Any]) -> dict[str, Any]:
    protocol = _normalized_protocol(payload["probe_protocol"])
    observations = [
        _normalized_observation_payload(index, raw)
        for index, raw in enumerate(payload["observations"])
    ]
    planned = protocol["repetitions"]
    completed = [item for item in observations if item["status"] == "completed"]
    failed = [item for item in observations if item["status"] == "failed"]
    if not observations:
        probe_status = "not_run"
    elif len(observations) == planned and len(completed) == planned:
        probe_status = "complete"
    elif completed:
        probe_status = "partial"
    else:
        probe_status = "infrastructure_error"

    output_hashes = [str(item["output_sha256"]) for item in completed]
    fingerprints = [
        str(item["system_fingerprint"])
        for item in completed
        if item["system_fingerprint"] is not None
    ]
    exact_output_match = (
        len(set(output_hashes)) == 1 if probe_status == "complete" else None
    )
    if probe_status != "complete":
        fingerprint_status = "not_evaluated"
        fingerprint_match = None
    elif len(fingerprints) != planned:
        fingerprint_status = "missing"
        fingerprint_match = None
    elif len(set(fingerprints)) != 1:
        fingerprint_status = "inconsistent"
        fingerprint_match = False
    else:
        fingerprint_status = "consistent"
        fingerprint_match = True

    token_axes = {
        axis: [item[axis] for item in observations]
        for axis in ("input_tokens", "output_tokens", "cached_tokens")
    }
    token_totals = {
        axis: (
            sum(values)
            if values and all(value is not None for value in values)
            else None
        )
        for axis, values in token_axes.items()
    }
    present_token_values = sum(
        value is not None for values in token_axes.values() for value in values
    )
    expected_token_values = len(observations) * len(token_axes)
    if observations and present_token_values == expected_token_values:
        token_usage_status = "provider_reported"
    elif present_token_values:
        token_usage_status = "partial"
    else:
        token_usage_status = "unavailable"

    classification, eligible, limitations = _classify(
        documentation_status=payload["documentation_status"],
        documentation_review=payload["documentation_review"],
        probe_status=probe_status,
        exact_output_match=exact_output_match,
        fingerprint_status=fingerprint_status,
    )
    identity = {
        "provider_adapter": payload["provider_adapter"],
        "provider_model": payload["provider_model"],
        "gateway_base_url_sha256": payload["gateway_base_url_sha256"],
        "probe_protocol": protocol,
        "documentation_status": payload["documentation_status"],
        "documentation_snapshot_sha256": payload[
            "documentation_snapshot_sha256"
        ],
        "documentation_source_url_sha256": payload[
            "documentation_source_url_sha256"
        ],
        "documentation_review": payload["documentation_review"],
        "observations": observations,
    }
    return {
        "capability_profile_id": "seedcap-" + _sha256_json(identity)[:32],
        "probe_protocol_sha256": _sha256_json(protocol),
        "requested_decoding_seed": protocol["seed"],
        "planned_repetitions": planned,
        "completed_repetitions": len(completed),
        "failed_repetitions": len(failed),
        "failure_categories": sorted(
            {str(item["failure_category"]) for item in failed}
        ),
        "probe_status": probe_status,
        "output_sha256s": output_hashes,
        "system_fingerprints": fingerprints,
        "exact_output_match": exact_output_match,
        "fingerprint_status": fingerprint_status,
        "fingerprint_match": fingerprint_match,
        "seed_control_classification": classification,
        "provider_token_usage_status": token_usage_status,
        **token_totals,
        "paired_confirmatory_eligible": eligible,
        "limitations": limitations,
    }


def _normalized_protocol(protocol: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(protocol, Mapping):
        raise TypeError("provider seed probe protocol must be a mapping")
    expected = {
        "prompt_sha256",
        "seed",
        "temperature",
        "max_tokens",
        "repetitions",
        "probe_implementation_sha256",
    }
    if set(protocol) != expected:
        raise ValueError("provider seed probe protocol fields do not match v1")
    seed = protocol["seed"]
    repetitions = protocol["repetitions"]
    max_tokens = protocol["max_tokens"]
    temperature = protocol["temperature"]
    if not _is_sha256(protocol["prompt_sha256"]):
        raise ValueError("probe prompt_sha256 must be lowercase SHA-256")
    if not _is_sha256(protocol["probe_implementation_sha256"]):
        raise ValueError(
            "probe implementation sha256 must be lowercase SHA-256"
        )
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("probe seed must be a non-negative integer")
    if (
        isinstance(repetitions, bool)
        or not isinstance(repetitions, int)
        or repetitions < 2
    ):
        raise ValueError("probe repetitions must be at least two")
    if (
        isinstance(max_tokens, bool)
        or not isinstance(max_tokens, int)
        or max_tokens < 1
    ):
        raise ValueError("probe max_tokens must be a positive integer")
    if isinstance(temperature, bool) or not isinstance(temperature, (int, float)):
        raise ValueError("probe temperature must be numeric")
    if not 0 <= float(temperature) <= 2:
        raise ValueError("probe temperature must be between zero and two")
    return {
        "prompt_sha256": protocol["prompt_sha256"],
        "seed": seed,
        "temperature": float(temperature),
        "max_tokens": max_tokens,
        "repetitions": repetitions,
        "probe_implementation_sha256": protocol["probe_implementation_sha256"],
    }


def _normalized_documentation(
    *,
    documentation_status: str,
    documentation_snapshot_sha256: str | None,
    documentation_source_url_sha256: str | None,
    documentation_review: Mapping[str, Any] | None,
) -> dict[str, str] | None:
    if documentation_status not in _DOCUMENTATION_STATUSES:
        raise ValueError("unknown provider seed documentation status")
    if documentation_status == "not_checked":
        if any(
            value is not None
            for value in (
                documentation_snapshot_sha256,
                documentation_source_url_sha256,
                documentation_review,
            )
        ):
            raise ValueError(
                "unchecked documentation cannot carry snapshot, URL, or review provenance"
            )
        return None
    if not _is_sha256(documentation_snapshot_sha256):
        raise ValueError("checked documentation requires snapshot SHA-256")
    if not _is_sha256(documentation_source_url_sha256):
        raise ValueError("checked documentation requires source URL SHA-256")
    if not isinstance(documentation_review, Mapping):
        raise ValueError("checked documentation requires review provenance")
    if set(documentation_review) != {
        "review_type",
        "reviewer_provenance_sha256",
    }:
        raise ValueError("documentation review provenance fields do not match v1")
    review_type = documentation_review["review_type"]
    if review_type not in _DOCUMENTATION_REVIEW_TYPES:
        raise ValueError("unknown documentation review type")
    reviewer_digest = documentation_review["reviewer_provenance_sha256"]
    if not _is_sha256(reviewer_digest):
        raise ValueError("documentation review provenance must be lowercase SHA-256")
    return {
        "review_type": review_type,
        "reviewer_provenance_sha256": reviewer_digest,
    }


def _observation_payload(
    call_index: int, observation: ProviderSeedProbeObservation
) -> dict[str, Any]:
    if not isinstance(observation, ProviderSeedProbeObservation):
        raise TypeError("probe observations must be ProviderSeedProbeObservation values")
    return {
        "call_index": call_index,
        "status": observation.status,
        "output_size_bytes": observation.output_size_bytes,
        "output_sha256": observation.output_sha256,
        "system_fingerprint": observation.system_fingerprint,
        "input_tokens": observation.input_tokens,
        "output_tokens": observation.output_tokens,
        "cached_tokens": observation.cached_tokens,
        "failure_category": observation.failure_category,
    }


def _normalized_observation_payload(
    call_index: int, raw: Mapping[str, Any]
) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise ValueError("probe observation must be an object")
    expected = {
        "call_index",
        "status",
        "output_size_bytes",
        "output_sha256",
        "system_fingerprint",
        "input_tokens",
        "output_tokens",
        "cached_tokens",
        "failure_category",
    }
    if set(raw) != expected:
        raise ValueError("probe observation fields do not match v1")
    if raw["call_index"] != call_index:
        raise ValueError("probe observation order is not contiguous")
    observation = ProviderSeedProbeObservation(
        status=raw["status"],
        output_sha256=raw["output_sha256"],
        system_fingerprint=raw["system_fingerprint"],
        input_tokens=raw["input_tokens"],
        output_tokens=raw["output_tokens"],
        cached_tokens=raw["cached_tokens"],
        failure_category=raw["failure_category"],
        output_size_bytes=raw["output_size_bytes"],
    )
    return _observation_payload(call_index, observation)


def _classify(
    *,
    documentation_status: str,
    documentation_review: Mapping[str, Any] | None,
    probe_status: str,
    exact_output_match: bool | None,
    fingerprint_status: str,
) -> tuple[str, bool, list[str]]:
    limitations: list[str] = []
    if documentation_status == "not_checked":
        limitations.append("documentation_not_hash_bound")
    elif documentation_status == "seed_undocumented":
        limitations.append("seed_not_documented")
    elif documentation_status == "best_effort_documented":
        limitations.append("best_effort_not_guaranteed")
    if (
        isinstance(documentation_review, Mapping)
        and documentation_review.get("review_type") == "self_reviewed_development"
    ):
        limitations.extend(
            [
                "documentation_self_reviewed",
                "independent_documentation_review_required",
            ]
        )
    if documentation_status == "unsupported_documented":
        classification = "unsupported"
        eligible = False
    elif probe_status != "complete":
        limitations.append("probe_not_complete")
        classification = "unavailable"
        eligible = False
    elif exact_output_match is not True:
        limitations.append("output_mismatch")
        classification = "nonrepeatable_observed"
        eligible = False
    elif fingerprint_status != "consistent":
        limitations.append(
            "fingerprint_missing"
            if fingerprint_status == "missing"
            else "fingerprint_inconsistent"
        )
        classification = "backend_identity_unverified"
        eligible = False
    elif documentation_status == "deterministic_documented" and (
        isinstance(documentation_review, Mapping)
        and documentation_review.get("review_type") == "independent_review"
    ):
        classification = "reproducible_frozen_candidate"
        eligible = True
    elif documentation_status == "best_effort_documented":
        classification = "best_effort_observed"
        eligible = False
    else:
        classification = "unverified"
        eligible = False
    limitations.append("development_only_no_campaign_authority")
    return classification, eligible, limitations


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _is_sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return value == value.lower()
