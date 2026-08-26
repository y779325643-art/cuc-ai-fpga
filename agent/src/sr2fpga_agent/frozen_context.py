"""Immutable ready requirement context and visibility-safe episode pack."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.method_contract import MethodConditionId
from sr2fpga_agent.models import PlatformProfile, ProjectRequest
from sr2fpga_agent.requirement_boundary import RequirementBoundaryDecision


EPISODE_PACK_CONTRACT_KEY = "episode_pack"
_ORIGIN_MAP = {
    "explicit": "user_explicit",
    "default": "platform_default",
    "assumption": "system_assumption",
    "unknown": "unresolved",
}


@dataclass(frozen=True)
class RequirementFactRecord:
    fact_id: str
    value: Any
    provenance: str
    source_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "fact_id": self.fact_id,
            "value": _json_value(self.value),
            "provenance": self.provenance,
            "source_ids": list(self.source_ids),
        }


@dataclass(frozen=True)
class FrozenRequirementContext:
    requirement_id: str
    revision_id: str
    public_text: str
    fact_records: tuple[RequirementFactRecord, ...]
    platform_profile_id: str
    platform_profile_sha256: str
    capability_profile_id: str
    capability_profile_sha256: str
    disposition: str
    public_projection_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "requirement_id": self.requirement_id,
            "revision_id": self.revision_id,
            "public_text": self.public_text,
            "fact_records": [record.to_dict() for record in self.fact_records],
            "platform_profile_id": self.platform_profile_id,
            "platform_profile_sha256": self.platform_profile_sha256,
            "capability_profile_id": self.capability_profile_id,
            "capability_profile_sha256": self.capability_profile_sha256,
            "disposition": self.disposition,
            "public_projection_sha256": self.public_projection_sha256,
        }


@dataclass(frozen=True)
class FrozenEpisodePack:
    pack_id: str
    context: FrozenRequirementContext
    episode_id: str
    analysis_population: str
    method_condition: MethodConditionId
    evaluator_metadata_sha256: str
    private_ref_ids: tuple[str, ...]
    pack_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": "episode-pack-v1",
            "pack_id": self.pack_id,
            "pack_sha256": self.pack_sha256,
            "public_context": self.context.to_dict(),
            "audit_only": {
                "episode_id": self.episode_id,
                "analysis_population": self.analysis_population,
                "method_condition_id": self.method_condition.value,
                "evaluator_metadata_sha256": self.evaluator_metadata_sha256,
                "private_ref_ids": list(self.private_ref_ids),
            },
        }

    def generation_visible(self) -> dict[str, Any]:
        """Return the only projection adapters may receive."""

        return self.context.to_dict()


def freeze_ready_requirement_context(
    decision: RequirementBoundaryDecision,
    platform: PlatformProfile,
) -> FrozenRequirementContext:
    if decision.disposition != "ready":
        raise ValueError("only a ready requirement boundary can be frozen")
    records: list[RequirementFactRecord] = []
    for fact in decision.envelope.facts:
        # task_type is evaluator/catalog metadata when supplied as a caller
        # default. The original public text remains available if the user
        # explicitly named a task.
        if fact.key == "declared_task_type" and fact.origin == "default":
            continue
        records.append(
            RequirementFactRecord(
                fact_id=fact.key,
                value=_freeze(fact.value),
                provenance=_ORIGIN_MAP[fact.origin],
                source_ids=tuple(fact.evidence),
            )
        )
    platform_payload = asdict(platform)
    platform_id = platform_profile_id(platform)
    base = {
        "requirement_id": decision.requirement_id,
        "revision_id": "rev-" + _sha256(
            {
                "requirement_id": decision.requirement_id,
                "envelope_sha256": decision.envelope_sha256,
                "platform": platform_payload,
            }
        ),
        "public_text": decision.envelope.raw_requirement,
        "fact_records": [record.to_dict() for record in records],
        "platform_profile_id": platform_id,
        "platform_profile_sha256": _sha256(platform_payload),
        "capability_profile_id": capability_profile_id(
            decision.capability_profile_id
        ),
        "capability_profile_sha256": decision.capability_profile_sha256,
        "disposition": "ready",
    }
    projection_sha256 = _sha256(base)
    return FrozenRequirementContext(
        requirement_id=base["requirement_id"],
        revision_id=base["revision_id"],
        public_text=base["public_text"],
        fact_records=tuple(records),
        platform_profile_id=base["platform_profile_id"],
        platform_profile_sha256=base["platform_profile_sha256"],
        capability_profile_id=base["capability_profile_id"],
        capability_profile_sha256=base["capability_profile_sha256"],
        disposition="ready",
        public_projection_sha256=projection_sha256,
    )


def platform_profile_sha256(platform: PlatformProfile) -> str:
    return _sha256(asdict(platform))


def platform_profile_id(platform: PlatformProfile) -> str:
    return _identifier("platform", platform.name)


def capability_profile_id(registry_version: str) -> str:
    return _identifier("capability", registry_version)


def frozen_requirement_trace_template(
    context: FrozenRequirementContext,
) -> dict[str, Any]:
    origin_map = {
        "user_explicit": "explicit",
        "platform_default": "default",
        "system_assumption": "assumption",
    }
    required_facts = {
        record.fact_id: {
            "value": _json_value(record.value),
            "origin": origin_map[record.provenance],
        }
        for record in context.fact_records
        if record.provenance in origin_map
    }
    return {
        "requirement_id": context.requirement_id,
        "required_facts": required_facts,
        "fact_to_his": {key: [] for key in required_facts},
        "unresolved_facts": [],
    }


def frozen_public_project_request(
    context: FrozenRequirementContext,
) -> ProjectRequest:
    """Build the metadata-neutral request bridge required by legacy lowerers."""

    width = next(
        (
            record.value
            for record in context.fact_records
            if record.fact_id == "data_width_bits"
        ),
        None,
    )
    if not isinstance(width, int) or isinstance(width, bool) or width < 1:
        raise ValueError("frozen context requires a positive integer data_width_bits fact")
    return ProjectRequest(
        task_type="unclassified",
        width=width,
        project_name=frozen_project_name(context),
        description=context.public_text,
    )


def frozen_project_name(context: FrozenRequirementContext) -> str:
    suffix = context.requirement_id.replace("req-", "")[:24]
    return f"frozen_{suffix}"


def build_development_episode_pack(
    context: FrozenRequirementContext,
    *,
    episode_id: str,
    analysis_population: str,
    method_condition: MethodConditionId | str,
    evaluator_metadata: Mapping[str, Any],
    private_ref_ids: tuple[str, ...] = (),
) -> FrozenEpisodePack:
    if analysis_population not in {"development", "excluded"}:
        raise ValueError(
            "development episode-pack builder cannot create official packs; "
            "official packs require a signed G4b loader"
        )
    condition = (
        method_condition
        if isinstance(method_condition, MethodConditionId)
        else MethodConditionId(method_condition)
    )
    audit_only = {
        "episode_id": episode_id,
        "analysis_population": analysis_population,
        "method_condition_id": condition.value,
        "evaluator_metadata_sha256": _sha256(evaluator_metadata),
        "private_ref_ids": list(private_ref_ids),
    }
    without_hash = {
        "contract_version": "episode-pack-v1",
        "pack_id": "pack-" + _sha256(
            {
                "episode_id": episode_id,
                "public_projection_sha256": context.public_projection_sha256,
                "method_condition_id": condition.value,
            }
        ),
        "public_context": context.to_dict(),
        "audit_only": audit_only,
    }
    pack = FrozenEpisodePack(
        pack_id=without_hash["pack_id"],
        context=context,
        episode_id=episode_id,
        analysis_population=analysis_population,
        method_condition=condition,
        evaluator_metadata_sha256=audit_only["evaluator_metadata_sha256"],
        private_ref_ids=private_ref_ids,
        pack_sha256=_sha256(without_hash),
    )
    errors = validate_episode_pack(pack.to_dict())
    if errors:
        raise ValueError("invalid episode pack: " + "; ".join(errors))
    return pack


def validate_episode_pack(payload: Any) -> tuple[str, ...]:
    contract = ContractRegistry().load_schema(EPISODE_PACK_CONTRACT_KEY)
    errors = list(contract.validate(payload))
    if not isinstance(payload, dict):
        return tuple(errors)
    public = payload.get("public_context")
    if isinstance(public, dict):
        expected_public = _sha256(
            {key: value for key, value in public.items() if key != "public_projection_sha256"}
        )
        if public.get("public_projection_sha256") != expected_public:
            errors.append("$.public_context.public_projection_sha256: digest mismatch")
    expected_pack = _sha256(
        {key: value for key, value in payload.items() if key != "pack_sha256"}
    )
    if payload.get("pack_sha256") != expected_pack:
        errors.append("$.pack_sha256: digest mismatch")
    return tuple(errors)


def context_from_validated_episode_pack(payload: Mapping[str, Any]) -> FrozenRequirementContext:
    """Rehydrate only the public context after verifying the complete pack."""

    errors = validate_episode_pack(payload)
    if errors:
        raise ValueError("invalid episode pack: " + "; ".join(errors))
    public = payload["public_context"]
    records = tuple(
        RequirementFactRecord(
            fact_id=str(record["fact_id"]),
            value=_freeze(record["value"]),
            provenance=str(record["provenance"]),
            source_ids=tuple(str(item) for item in record["source_ids"]),
        )
        for record in public["fact_records"]
    )
    return FrozenRequirementContext(
        requirement_id=str(public["requirement_id"]),
        revision_id=str(public["revision_id"]),
        public_text=str(public["public_text"]),
        fact_records=records,
        platform_profile_id=str(public["platform_profile_id"]),
        platform_profile_sha256=str(public["platform_profile_sha256"]),
        capability_profile_id=str(public["capability_profile_id"]),
        capability_profile_sha256=str(public["capability_profile_sha256"]),
        disposition="ready",
        public_projection_sha256=str(public["public_projection_sha256"]),
    )


def _identifier(prefix: str, value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._:-]+", "-", value.strip()).strip("-")
    return f"{prefix}:{normalized or _sha256(value)[:16]}"


def _sha256(value: Any) -> str:
    encoded = json.dumps(
        _json_value(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return tuple(sorted((str(key), _freeze(item)) for key, item in value.items()))
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


def _json_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        if value and all(
            isinstance(item, tuple) and len(item) == 2 and isinstance(item[0], str)
            for item in value
        ):
            return {item[0]: _json_value(item[1]) for item in value}
        return [_json_value(item) for item in value]
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    return value
