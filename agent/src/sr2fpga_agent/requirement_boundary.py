"""Method-neutral requirement disposition before project generation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from sr2fpga_agent.models import PlatformProfile, ProjectRequest
from sr2fpga_agent.requirement_envelope import (
    RequirementEnvelope,
    RequirementRouteResult,
    build_request_requirement_envelope,
    route_requirement,
)
from sr2fpga_agent.system_his_capabilities import (
    SystemHisBackendCapabilities,
    load_system_his_backend_capabilities,
)
from sr2fpga_agent.task_catalog import load_exact_task_family_aliases


REQUIREMENT_BOUNDARY_VERSION = "requirement-boundary-v1"
REQUIREMENT_ENVELOPE_VERSION = "requirement-envelope-v1"

_CAPABILITY_MECHANISMS = {
    "adc_interface": ("component", "adc_interface"),
    "clock_domain_crossing": ("component", "clock_domain_crossing"),
    "dma": ("component", "dma"),
    "external_memory": ("component", "external_memory"),
    "on_chip_memory": ("component", "memory"),
    "pcie": ("component", "pcie"),
    "axi_stream": ("protocol", "axi_stream"),
    "spi": ("component", "spi"),
    "i2c": ("component", "i2c"),
    "uart": ("component", "uart"),
    "streaming": ("protocol", "valid_ready"),
    "fifo": ("component", "fifo"),
    "dsp": ("component", "rtl_component"),
    "image_pipeline": ("component", "rtl_component"),
    "state_machine": ("component", "fsm"),
    "counter": ("component", "counter"),
}


@dataclass(frozen=True)
class RequirementBoundaryDecision:
    """Evaluator-side decision shared by every generation method."""

    boundary_version: str
    envelope_version: str
    requirement_id: str
    envelope_sha256: str
    capability_profile_id: str
    capability_profile_sha256: str
    disposition: str
    reason_codes: tuple[str, ...]
    clarification_fact_ids: tuple[str, ...]
    clarification_questions: tuple[str, ...]
    capability_gap_ids: tuple[str, ...]
    envelope: RequirementEnvelope
    route: RequirementRouteResult

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "boundary_version": self.boundary_version,
            "envelope_version": self.envelope_version,
            "requirement_id": self.requirement_id,
            "envelope_sha256": self.envelope_sha256,
            "capability_profile_id": self.capability_profile_id,
            "capability_profile_sha256": self.capability_profile_sha256,
            "disposition": self.disposition,
            "reason_codes": list(self.reason_codes),
            "clarification_fact_ids": list(self.clarification_fact_ids),
            "clarification_questions": list(self.clarification_questions),
            "capability_gap_ids": list(self.capability_gap_ids),
            "envelope": self.envelope.to_dict(),
            "route": self.route.to_dict(),
            "visibility": {
                "public": ["requirement", "platform_defaults", "capability_profile_id"],
                "evaluator_only": ["route", "disposition", "reason_codes"],
            },
        }
        payload["decision_sha256"] = _sha256(payload)
        return payload


def evaluate_requirement_boundary(
    request: ProjectRequest,
    platform: PlatformProfile,
    *,
    backend: SystemHisBackendCapabilities | None = None,
    clarification_facts: dict[str, Any] | None = None,
) -> RequirementBoundaryDecision:
    """Classify a request without consulting Family Recipe or any model."""

    envelope = build_request_requirement_envelope(
        request,
        platform,
        clarification_facts=clarification_facts,
    )
    route = route_requirement(
        envelope,
        declared_family=request.task_type,
        exact_family_aliases=load_exact_task_family_aliases(),
    )
    resolved_backend = backend or load_system_his_backend_capabilities()
    gaps = requirement_capability_gaps(envelope, resolved_backend)
    ambiguity_ids = route.critical_ambiguity_keys
    questions_by_key = {item.key: item.question for item in envelope.critical_ambiguities}
    questions = tuple(questions_by_key[key] for key in ambiguity_ids)

    # Ambiguity takes precedence: an unresolved interpretation must not be
    # guessed merely because one possible interpretation is unsupported.
    if ambiguity_ids:
        disposition = "needs_clarification"
        reasons = tuple(f"critical_fact_missing:{key}" for key in ambiguity_ids)
    elif gaps:
        disposition = "capability_gap"
        reasons = tuple(f"unsupported_capability:{key}" for key in gaps)
    else:
        disposition = "ready"
        reasons = ("ready",)

    return RequirementBoundaryDecision(
        boundary_version=REQUIREMENT_BOUNDARY_VERSION,
        envelope_version=REQUIREMENT_ENVELOPE_VERSION,
        requirement_id=envelope.requirement_id,
        envelope_sha256=_sha256(envelope.to_dict()),
        capability_profile_id=resolved_backend.registry_version,
        capability_profile_sha256=capability_profile_sha256(resolved_backend),
        disposition=disposition,
        reason_codes=reasons,
        clarification_fact_ids=ambiguity_ids,
        clarification_questions=questions,
        capability_gap_ids=gaps,
        envelope=envelope,
        route=route,
    )


def requirement_capability_gaps(
    envelope: RequirementEnvelope,
    backend: SystemHisBackendCapabilities,
) -> tuple[str, ...]:
    """Return explicit required capabilities absent from the frozen backend."""

    gaps: list[str] = []
    for label in envelope.capability_labels:
        mechanism = _CAPABILITY_MECHANISMS.get(label)
        if mechanism is None:
            gaps.append(label)
            continue
        kind, canonical_name = mechanism
        supported = (
            backend.supported_component_semantic_kinds
            if kind == "component"
            else backend.supported_data_flow_protocols
        )
        if canonical_name not in supported:
            gaps.append(label)
    return tuple(gaps)


def capability_profile_sha256(backend: SystemHisBackendCapabilities) -> str:
    return _sha256(
        {
            "registry_version": backend.registry_version,
            "system_his_version": backend.system_his_version,
            "component_semantic_kinds": sorted(backend.supported_component_semantic_kinds),
            "component_semantic_kind_aliases": dict(backend.component_semantic_kind_aliases),
            "data_flow_protocols": sorted(backend.supported_data_flow_protocols),
            "data_flow_protocol_aliases": dict(backend.data_flow_protocol_aliases),
            "verification_scenarios": sorted(backend.supported_verification_scenarios),
            "canonical_testbench": backend.canonical_testbench,
        }
    )


def _sha256(value: Any) -> str:
    canonical = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
