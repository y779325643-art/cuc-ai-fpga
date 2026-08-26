"""Provider-neutral Paper-1 method adapters and paired initial artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Mapping, Protocol, runtime_checkable

from sr2fpga_agent.artifact_store import ArtifactRef, ArtifactStore
from sr2fpga_agent.frozen_context import FrozenRequirementContext
from sr2fpga_agent.method_contract import MethodConditionId, MethodContract, method_contract
from sr2fpga_agent.models import GeneratedProject
from sr2fpga_agent.project_contract import project_package_sha256


class PlanningArtifactKind(str, Enum):
    UNTYPED_PLAN = "untyped_plan"
    SYSTEM_HIS = "system_his"


@dataclass(frozen=True)
class PlanningArtifactEmission:
    kind: PlanningArtifactKind
    artifact_ref: ArtifactRef


@dataclass(frozen=True)
class ProjectCandidateEmission:
    artifact_ref: ArtifactRef
    project_package_sha256: str


@dataclass(frozen=True)
class MethodStageFailure:
    stage: str
    error_type: str
    message: str


MethodEmission = PlanningArtifactEmission | ProjectCandidateEmission | MethodStageFailure


@dataclass(frozen=True)
class SharedArtifactRefs:
    initial_project: ProjectCandidateEmission | None = None
    system_his: PlanningArtifactEmission | None = None


@dataclass(frozen=True)
class PairingKey:
    paired_block_id: str
    requirement_revision_id: str
    semantic_instance_id: str
    decoding_seed: int
    model_provenance_sha256: str

    def digest(self) -> str:
        return _sha256_json(
            {
                "paired_block_id": self.paired_block_id,
                "requirement_revision_id": self.requirement_revision_id,
                "semantic_instance_id": self.semantic_instance_id,
                "decoding_seed": self.decoding_seed,
                "model_provenance_sha256": self.model_provenance_sha256,
            }
        )


class DirectGenerationFacade(Protocol):
    def emit_project(self, context: FrozenRequirementContext) -> GeneratedProject: ...


class UntypedPlanFacade(Protocol):
    def emit_plan(self, context: FrozenRequirementContext) -> Mapping[str, Any]: ...

    def emit_project(
        self,
        context: FrozenRequirementContext,
        plan: Mapping[str, Any],
    ) -> GeneratedProject: ...


class SystemHisFacade(Protocol):
    def emit_his(self, context: FrozenRequirementContext) -> Mapping[str, Any]: ...

    def emit_free_project(
        self,
        context: FrozenRequirementContext,
        system_his: Mapping[str, Any],
    ) -> GeneratedProject: ...

    def emit_skeleton_project(
        self,
        context: FrozenRequirementContext,
        system_his: Mapping[str, Any],
    ) -> GeneratedProject: ...


class SystemHisValidationFacade(Protocol):
    def validate_his(
        self,
        context: FrozenRequirementContext,
        system_his: Mapping[str, Any],
    ) -> Mapping[str, Any]: ...


class RepairFacade(Protocol):
    def correct_his(
        self,
        context: FrozenRequirementContext,
        system_his: Mapping[str, Any],
        diagnosis: Mapping[str, Any],
    ) -> Mapping[str, Any]: ...

    def repair_project(
        self,
        context: FrozenRequirementContext,
        project: GeneratedProject,
        diagnosis: Mapping[str, Any],
    ) -> GeneratedProject: ...


class MethodArtifactGateway:
    """Narrow adapter-facing artifact facade; it never exposes store paths."""

    def __init__(self, store: ArtifactStore) -> None:
        self.__store = store
        self.__event_refs: dict[str, list[ArtifactRef]] = {}

    def put_planning(
        self,
        key: str,
        kind: PlanningArtifactKind,
        payload: Mapping[str, Any],
    ) -> PlanningArtifactEmission:
        ref = self.__store.put_blob(key, _canonical_json(payload), media_type="application/json")
        return PlanningArtifactEmission(kind, ref)

    def read_planning(self, emission: PlanningArtifactEmission) -> dict[str, Any]:
        payload = json.loads(self.__store.read_verified(emission.artifact_ref))
        if not isinstance(payload, dict):
            raise ValueError("planning artifact must contain a JSON object")
        return payload

    def put_project(self, key: str, project: GeneratedProject) -> ProjectCandidateEmission:
        payload = {"project_name": project.project_name, "files": project.files}
        ref = self.__store.put_blob(key, _canonical_json(payload), media_type="application/json")
        return ProjectCandidateEmission(ref, project_package_sha256(project))

    def read_project(self, emission: ProjectCandidateEmission) -> GeneratedProject:
        payload = json.loads(self.__store.read_verified(emission.artifact_ref))
        project = GeneratedProject(str(payload["project_name"]), dict(payload["files"]))
        if project_package_sha256(project) != emission.project_package_sha256:
            raise ValueError("shared project package digest mismatch")
        return project

    def append_event(self, episode_id: str, event_type: str, payload: Mapping[str, Any]) -> ArtifactRef:
        reference = self.__store.append_event(episode_id, event_type, payload)
        self.__event_refs.setdefault(episode_id, []).append(reference)
        return reference

    def event_refs(self, episode_id: str) -> tuple[ArtifactRef, ...]:
        return tuple(self.__event_refs.get(episode_id, ()))


@dataclass(frozen=True)
class GenerationServices:
    artifacts: MethodArtifactGateway
    episode_id: str
    direct: DirectGenerationFacade | None = None
    untyped: UntypedPlanFacade | None = None
    system_his: SystemHisFacade | None = None
    his_validation: SystemHisValidationFacade | None = None
    repair: RepairFacade | None = None


class MethodAdapter(Protocol):
    contract: MethodContract

    def emit_initial(
        self,
        context: FrozenRequirementContext,
        services: GenerationServices,
        shared_artifacts: SharedArtifactRefs,
    ) -> MethodEmission: ...


class _AdapterBase:
    contract: MethodContract

    def _key(self, context: FrozenRequirementContext, suffix: str) -> str:
        return f"method-emissions/{context.revision_id}/{self.contract.method_condition.value}/{suffix}"


class DirectMethodAdapter(_AdapterBase):
    def __init__(self, condition: MethodConditionId) -> None:
        if condition not in {MethodConditionId.M0, MethodConditionId.M1}:
            raise ValueError("Direct adapter only supports M0/M1")
        self.contract = method_contract(condition)

    def emit_initial(self, context, services, shared_artifacts) -> MethodEmission:
        if shared_artifacts.initial_project is not None:
            services.artifacts.read_project(shared_artifacts.initial_project)
            services.artifacts.append_event(
                services.episode_id,
                "shared_artifact_consumed",
                {
                    "method_condition_id": self.contract.method_condition.value,
                    "artifact_kind": "initial_project",
                    "artifact_sha256": shared_artifacts.initial_project.artifact_ref.sha256,
                },
            )
            return shared_artifacts.initial_project
        if services.direct is None:
            return _failure("direct_generation", "missing direct generation facade")
        try:
            project = services.direct.emit_project(context)
            return services.artifacts.put_project(self._key(context, "initial-project"), project)
        except Exception as exc:
            return _exception_failure("direct_generation", exc)


class DirectRepairMethodAdapter(DirectMethodAdapter):
    def __init__(self) -> None:
        super().__init__(MethodConditionId.M1)

    def repair_project(self, context, candidate, diagnosis, services) -> ProjectCandidateEmission:
        if services.repair is None:
            raise RuntimeError("missing project repair facade")
        project = services.artifacts.read_project(candidate)
        repaired = services.repair.repair_project(context, project, diagnosis)
        suffix = (
            f"project-repair-{candidate.artifact_ref.sha256[:16]}-"
            f"{_sha256_json(diagnosis)[:16]}"
        )
        return services.artifacts.put_project(self._key(context, suffix), repaired)


class StructuredDirectMethodAdapter(_AdapterBase):
    contract = method_contract(MethodConditionId.M2)

    def emit_initial(self, context, services, shared_artifacts) -> MethodEmission:
        if services.untyped is None:
            return _failure("untyped_plan", "missing untyped planning facade")
        try:
            plan = services.untyped.emit_plan(context)
            return services.artifacts.put_planning(
                self._key(context, "untyped-plan"), PlanningArtifactKind.UNTYPED_PLAN, plan
            )
        except Exception as exc:
            return _exception_failure("untyped_plan", exc)

    def emit_project_from_validated_planning(self, context, planning, services, shared_artifacts):
        if services.untyped is None:
            return _failure("project_from_untyped_plan", "missing untyped planning facade")
        try:
            plan = services.artifacts.read_planning(planning)
            project = services.untyped.emit_project(context, plan)
            return services.artifacts.put_project(self._key(context, "initial-project"), project)
        except Exception as exc:
            return _exception_failure("project_from_untyped_plan", exc)


class HisMethodAdapter(_AdapterBase):
    def __init__(self, condition: MethodConditionId) -> None:
        if condition not in {MethodConditionId.M3, MethodConditionId.M4, MethodConditionId.M5}:
            raise ValueError("HIS adapter only supports M3/M4/M5")
        self.contract = method_contract(condition)

    def emit_initial(self, context, services, shared_artifacts) -> MethodEmission:
        if shared_artifacts.system_his is not None:
            services.artifacts.read_planning(shared_artifacts.system_his)
            services.artifacts.append_event(
                services.episode_id,
                "shared_artifact_consumed",
                {
                    "method_condition_id": self.contract.method_condition.value,
                    "artifact_kind": "system_his",
                    "artifact_sha256": shared_artifacts.system_his.artifact_ref.sha256,
                },
            )
            return shared_artifacts.system_his
        if services.system_his is None:
            return _failure("system_his", "missing System-HIS generation facade")
        try:
            payload = services.system_his.emit_his(context)
            return services.artifacts.put_planning(
                self._key(context, "system-his"), PlanningArtifactKind.SYSTEM_HIS, payload
            )
        except Exception as exc:
            return _exception_failure("system_his", exc)

    def emit_project_from_validated_planning(self, context, planning, services, shared_artifacts):
        if shared_artifacts.initial_project is not None:
            services.artifacts.read_project(shared_artifacts.initial_project)
            services.artifacts.append_event(
                services.episode_id,
                "shared_artifact_consumed",
                {
                    "method_condition_id": self.contract.method_condition.value,
                    "artifact_kind": "initial_project",
                    "artifact_sha256": shared_artifacts.initial_project.artifact_ref.sha256,
                },
            )
            return shared_artifacts.initial_project
        if services.system_his is None:
            return _failure("project_from_system_his", "missing System-HIS generation facade")
        try:
            payload = services.artifacts.read_planning(planning)
            if self.contract.uses_deterministic_skeleton:
                project = services.system_his.emit_skeleton_project(context, payload)
            else:
                project = services.system_his.emit_free_project(context, payload)
            return services.artifacts.put_project(self._key(context, "initial-project"), project)
        except Exception as exc:
            return _exception_failure("project_from_system_his", exc)


class HisRepairMethodAdapter(HisMethodAdapter):
    def __init__(self) -> None:
        super().__init__(MethodConditionId.M5)

    def correct_his(self, context, planning, diagnosis, services) -> PlanningArtifactEmission:
        if services.repair is None:
            raise RuntimeError("missing System-HIS repair facade")
        payload = services.artifacts.read_planning(planning)
        corrected = services.repair.correct_his(context, payload, diagnosis)
        suffix = (
            f"system-his-repair-{planning.artifact_ref.sha256[:16]}-"
            f"{_sha256_json(diagnosis)[:16]}"
        )
        return services.artifacts.put_planning(
            self._key(context, suffix), PlanningArtifactKind.SYSTEM_HIS, corrected
        )

    def repair_project(self, context, candidate, diagnosis, services) -> ProjectCandidateEmission:
        if services.repair is None:
            raise RuntimeError("missing project repair facade")
        project = services.artifacts.read_project(candidate)
        repaired = services.repair.repair_project(context, project, diagnosis)
        suffix = (
            f"project-repair-{candidate.artifact_ref.sha256[:16]}-"
            f"{_sha256_json(diagnosis)[:16]}"
        )
        return services.artifacts.put_project(self._key(context, suffix), repaired)


@runtime_checkable
class HisCorrectionCapable(Protocol):
    def correct_his(self, context, planning, diagnosis, services) -> PlanningArtifactEmission: ...


@runtime_checkable
class ProjectRepairCapable(Protocol):
    def repair_project(self, context, candidate, diagnosis, services) -> ProjectCandidateEmission: ...


class RepairController:
    def correct_his(self, adapter, context, planning, diagnosis, services):
        if not adapter.contract.allows_his_correction or not isinstance(adapter, HisCorrectionCapable):
            raise PermissionError("method contract does not allow System-HIS correction")
        return adapter.correct_his(context, planning, diagnosis, services)

    def repair_project(self, adapter, context, candidate, diagnosis, services):
        if not adapter.contract.allows_project_repair or not isinstance(adapter, ProjectRepairCapable):
            raise PermissionError("method contract does not allow project repair")
        return adapter.repair_project(context, candidate, diagnosis, services)


class MethodAdapterRegistry:
    def create(self, condition: MethodConditionId | str) -> MethodAdapter:
        key = condition if isinstance(condition, MethodConditionId) else MethodConditionId(condition)
        if key is MethodConditionId.M0:
            return DirectMethodAdapter(key)
        if key is MethodConditionId.M1:
            return DirectRepairMethodAdapter()
        if key is MethodConditionId.M2:
            return StructuredDirectMethodAdapter()
        if key in {MethodConditionId.M3, MethodConditionId.M4}:
            return HisMethodAdapter(key)
        return HisRepairMethodAdapter()


class PairedArtifactCoordinator:
    """Materialize each paired initial artifact exactly once."""

    def __init__(self, store: ArtifactStore) -> None:
        self._store = store
        self._artifacts = MethodArtifactGateway(store)

    def materialize_initial_project(
        self,
        pairing: PairingKey,
        factory: Callable[[], GeneratedProject],
    ) -> ProjectCandidateEmission:
        key = f"paired/{pairing.digest()}/initial-project"
        existing = self._store.reference(key)
        if existing is None:
            emission = self._artifacts.put_project(key, factory())
            self._store.append_event(pairing.paired_block_id, "shared_project_generated", {
                "pairing_sha256": pairing.digest(),
                "artifact_sha256": emission.artifact_ref.sha256,
                "project_package_sha256": emission.project_package_sha256,
            })
            return emission
        payload = json.loads(self._store.read_verified(existing))
        project = GeneratedProject(str(payload["project_name"]), dict(payload["files"]))
        return ProjectCandidateEmission(existing, project_package_sha256(project))

    def materialize_system_his(
        self,
        pairing: PairingKey,
        factory: Callable[[], Mapping[str, Any]],
    ) -> PlanningArtifactEmission:
        key = f"paired/{pairing.digest()}/system-his"
        existing = self._store.reference(key)
        if existing is None:
            emission = self._artifacts.put_planning(
                key, PlanningArtifactKind.SYSTEM_HIS, factory()
            )
            self._store.append_event(pairing.paired_block_id, "shared_his_generated", {
                "pairing_sha256": pairing.digest(),
                "artifact_sha256": emission.artifact_ref.sha256,
            })
            return emission
        return PlanningArtifactEmission(PlanningArtifactKind.SYSTEM_HIS, existing)


def _failure(stage: str, message: str) -> MethodStageFailure:
    return MethodStageFailure(stage, "UnavailableCapability", message)


def _exception_failure(stage: str, exc: Exception) -> MethodStageFailure:
    return MethodStageFailure(stage, type(exc).__name__, str(exc))


def _canonical_json(payload: Any) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _sha256_json(payload: Any) -> str:
    return hashlib.sha256(_canonical_json(payload).rstrip(b"\n")).hexdigest()
