"""Development-only paired-block identity and balanced execution order."""

from __future__ import annotations

import hashlib
import json
import random
from collections.abc import Sequence
from typing import Any

from sr2fpga_agent.models import canonical_json_bytes as _canonical_json
from sr2fpga_agent.artifact_store import ArtifactRef, ArtifactStore
from sr2fpga_agent.contract_registry import ContractRegistry


METHODS = ("M0", "M1", "M2", "M3", "M4", "M5")
_WILLIAMS_BASE = (0, 1, 5, 2, 4, 3)


def build_balanced_method_orders(
    execution_schedule_seed: int,
) -> tuple[tuple[str, ...], ...]:
    """Return one independently seeded six-row balanced Williams design."""

    if (
        isinstance(execution_schedule_seed, bool)
        or not isinstance(execution_schedule_seed, int)
        or execution_schedule_seed < 0
    ):
        raise ValueError("execution_schedule_seed must be a non-negative integer")

    randomizer = random.Random(execution_schedule_seed)
    labels = list(METHODS)
    randomizer.shuffle(labels)
    orders = [
        tuple(labels[(index + shift) % len(labels)] for index in _WILLIAMS_BASE)
        for shift in range(len(labels))
    ]
    randomizer.shuffle(orders)
    return tuple(orders)


def write_development_paired_block(
    store: ArtifactStore,
    *,
    paired_block_id: str,
    semantic_instance_id: str,
    replicate_id: str,
    public_projection_sha256: str,
    model_provenance_sha256: str,
    decoding_control_mode: str,
    requested_decoding_seed: int | None,
    execution_schedule_seed: int,
    method_order: Sequence[str],
) -> ArtifactRef:
    """Validate and persist one non-authoritative development paired block."""

    payload = build_development_paired_block(
        paired_block_id=paired_block_id,
        semantic_instance_id=semantic_instance_id,
        replicate_id=replicate_id,
        public_projection_sha256=public_projection_sha256,
        model_provenance_sha256=model_provenance_sha256,
        decoding_control_mode=decoding_control_mode,
        requested_decoding_seed=requested_decoding_seed,
        execution_schedule_seed=execution_schedule_seed,
        method_order=method_order,
    )
    expected = development_paired_block_reference(payload)
    reference = store.put_validated_json(
        expected.key,
        payload,
        contract_key="paired_block",
    )
    if reference != expected:
        raise RuntimeError("paired-block materialization does not match pure plan")
    return reference


def build_development_paired_block(
    *,
    paired_block_id: str,
    semantic_instance_id: str,
    replicate_id: str,
    public_projection_sha256: str,
    model_provenance_sha256: str,
    decoding_control_mode: str,
    requested_decoding_seed: int | None,
    execution_schedule_seed: int,
    method_order: Sequence[str],
) -> dict[str, Any]:
    """Build one validated block payload without filesystem side effects."""

    payload = {
        "contract_version": "paired-block-v1",
        "evaluation_scope": "excluded_development_conformance_only",
        "paired_block_id": paired_block_id,
        "semantic_instance_id": semantic_instance_id,
        "replicate_id": replicate_id,
        "public_projection_sha256": public_projection_sha256,
        "model_provenance_sha256": model_provenance_sha256,
        "decoding_control_mode": decoding_control_mode,
        "requested_decoding_seed": requested_decoding_seed,
        "execution_schedule_seed": execution_schedule_seed,
        "method_order": list(method_order),
        "official_outcome": False,
        "official_authority": False,
        "pass_credit_authority": False,
        "g3_accepted": False,
        "g4b_authorized": False,
    }
    _validate_paired_block(payload)
    return payload


def development_paired_block_reference(payload: dict[str, Any]) -> ArtifactRef:
    """Predict the exact immutable reference for a validated block payload."""

    _validate_paired_block(payload)
    content = _canonical_json(payload)
    key_digest = hashlib.sha256(
        f"paired-block-v1:{payload['paired_block_id']}".encode("utf-8")
    ).hexdigest()
    return ArtifactRef(
        key=f"paired-blocks/block-{key_digest}",
        sha256=hashlib.sha256(content).hexdigest(),
        size_bytes=len(content),
        media_type="application/json",
    )


def load_development_paired_block(
    store: ArtifactStore,
    key_or_ref: str | ArtifactRef,
) -> dict[str, Any]:
    """Read and revalidate one content-addressed development paired block."""

    try:
        payload = json.loads(store.read_verified(key_or_ref))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("development paired block is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("development paired block must be a JSON object")
    _validate_paired_block(payload)
    return payload


def _validate_paired_block(payload: dict[str, Any]) -> None:
    errors = ContractRegistry().load_schema("paired_block").validate(payload)
    if errors:
        raise ValueError("invalid development paired block: " + "; ".join(errors))
    allowed = build_balanced_method_orders(payload["execution_schedule_seed"])
    if tuple(payload["method_order"]) not in allowed:
        raise ValueError(
            "paired block method_order is not a balanced order derived from "
            "execution_schedule_seed"
        )


