"""Canonical CD8 training-view-row-v2 exporter and eligibility sidecars."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import re
import shutil
from typing import Any, Callable, Iterable, Mapping, Sequence
import uuid

from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.models import GeneratedProject
from sr2fpga_agent.project_contract import verify_project_envelope
from sr2fpga_agent.repository_paths import RepositoryPaths
from sr2fpga_agent.training_eligibility import (
    validate_training_eligibility_certificate,
)


PROJECT_TREATMENTS = frozenset({"M6U", "M6F", "M6F_E_TRAJ"})
_GLOBAL_FORBIDDEN_TEXT_MARKERS = (
    "official_hidden_outcome",
    "hidden_raw_material",
    "private_evaluator",
    "trusted_testbench",
    "evaluator_testbench",
    "golden_model",
    "scoring_code",
)
_M6U_JSON_FIELD_PATTERN = re.compile(
    r'"(?:verdict|status|diagnosis|patch|tool_feedback|tool_output|'
    r'terminal_selection|eligibility_reasons?|verified[^"\\]*)"\s*:',
    flags=re.IGNORECASE,
)


@dataclass(frozen=True)
class PublicTransitionEvidence:
    public_failure: Mapping[str, Any]
    public_diagnosis: Mapping[str, Any]
    public_patch: str
    public_rerun: Mapping[str, Any]
    actual_rerun: bool
    targeted_failure_repaired: bool
    no_regression: bool


def build_project_training_view(
    *,
    treatment: str,
    eligibility_certificate: dict[str, Any],
    project: GeneratedProject,
    project_envelope: dict[str, Any],
    prompt_messages: Sequence[Mapping[str, str]],
    transition: PublicTransitionEvidence | None = None,
    forbidden_canaries: Iterable[str] = (),
    event_ref_resolver: Callable[[str], bool] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build M6U/M6F/M6F_E_TRAJ rows from one certificate-bound snapshot."""

    if treatment not in PROJECT_TREATMENTS:
        raise ValueError(f"project training view does not support treatment {treatment!r}")
    snapshot_id = _validate_snapshot_binding(
        treatment=treatment,
        eligibility_certificate=eligibility_certificate,
        project=project,
        project_envelope=project_envelope,
        event_ref_resolver=event_ref_resolver,
    )
    target_files = _model_visible_project_files(project, project_envelope)
    payload = {
        "prompt_messages": _prompt_messages(prompt_messages),
        "assistant_target": {"kind": "project_files", "files": target_files},
    }
    _assert_no_visibility_leak(
        payload,
        treatment=treatment,
        forbidden_canaries=tuple(forbidden_canaries),
    )
    row = _build_row(
        source_episode_id=eligibility_certificate["episode_id"],
        snapshot_id=snapshot_id,
        treatment=treatment,
        payload=payload,
    )
    transition_evidence_sha256 = None
    if treatment == "M6F_E_TRAJ":
        if transition is None:
            raise ValueError("M6F_E_TRAJ requires the matched public transition")
        _validate_transition(transition)
        transition_evidence_sha256 = _sha256(asdict(transition))
    elif transition is not None:
        raise ValueError(f"{treatment} must not carry transition evidence")
    sidecar = _build_sidecar(
        row=row,
        eligibility_certificate=eligibility_certificate,
        snapshot_envelope_sha256=project_envelope["envelope_sha256"],
        transition_evidence_sha256=transition_evidence_sha256,
    )
    validate_training_view_export(row, sidecar, eligibility_certificate)
    return row, sidecar


def build_transition_training_view(
    *,
    eligibility_certificate: dict[str, Any],
    terminal_project: GeneratedProject,
    terminal_project_envelope: dict[str, Any],
    prompt_messages: Sequence[Mapping[str, str]],
    transition: PublicTransitionEvidence,
    forbidden_canaries: Iterable[str] = (),
    event_ref_resolver: Callable[[str], bool] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build an M6T row only from a complete, successful public transition."""

    snapshot_id = _validate_snapshot_binding(
        treatment="M6T",
        eligibility_certificate=eligibility_certificate,
        project=terminal_project,
        project_envelope=terminal_project_envelope,
        event_ref_resolver=event_ref_resolver,
    )
    _validate_transition(transition)
    final_files = _model_visible_project_files(
        terminal_project, terminal_project_envelope
    )
    payload = {
        "prompt_messages": _prompt_messages(prompt_messages),
        "assistant_target": {
            "kind": "public_transition",
            "public_failure": dict(transition.public_failure),
            "public_diagnosis": dict(transition.public_diagnosis),
            "public_patch": transition.public_patch,
            "public_rerun": dict(transition.public_rerun),
            "final_files": final_files,
        },
    }
    _assert_no_visibility_leak(
        payload,
        treatment="M6T",
        forbidden_canaries=tuple(forbidden_canaries),
    )
    row = _build_row(
        source_episode_id=eligibility_certificate["episode_id"],
        snapshot_id=snapshot_id,
        treatment="M6T",
        payload=payload,
    )
    transition_evidence_sha256 = _sha256(asdict(transition))
    sidecar = _build_sidecar(
        row=row,
        eligibility_certificate=eligibility_certificate,
        snapshot_envelope_sha256=terminal_project_envelope["envelope_sha256"],
        transition_evidence_sha256=transition_evidence_sha256,
    )
    validate_training_view_export(row, sidecar, eligibility_certificate)
    return row, sidecar


def validate_training_view_export(
    row: dict[str, Any],
    sidecar: dict[str, Any],
    eligibility_certificate: dict[str, Any],
    *,
    forbidden_canaries: Iterable[str] = (),
) -> None:
    """Validate row, sidecar, certificate, hashes, and cross-artifact bindings."""

    validate_training_eligibility_certificate(eligibility_certificate)
    if eligibility_certificate["eligibility_status"] != "eligible":
        raise ValueError("canonical training views require an eligible certificate")
    _validate_registered("training_view_row", row)
    _validate_registered("training_view_eligibility_sidecar", sidecar)
    expected_row_sha256 = _sha256(
        {key: value for key, value in row.items() if key != "row_sha256"}
    )
    if row["row_sha256"] != expected_row_sha256:
        raise ValueError("training view row_sha256 mismatch")
    expected_sidecar_sha256 = _sha256(
        {key: value for key, value in sidecar.items() if key != "artifact_sha256"}
    )
    if sidecar["artifact_sha256"] != expected_sidecar_sha256:
        raise ValueError("training view sidecar artifact_sha256 mismatch")
    bindings = (
        (sidecar["row_id"], row["row_id"], "row_id"),
        (sidecar["row_sha256"], row["row_sha256"], "row_sha256"),
        (sidecar["source_episode_id"], row["source_episode_id"], "source episode"),
        (sidecar["snapshot_id"], row["snapshot_id"], "snapshot"),
        (sidecar["treatment"], row["treatment"], "treatment"),
        (
            sidecar["eligibility_artifact_sha256"],
            eligibility_certificate["artifact_sha256"],
            "eligibility artifact",
        ),
        (
            sidecar["eligibility_evidence_bundle_sha256"],
            eligibility_certificate["evidence_bundle_sha256"],
            "eligibility evidence bundle",
        ),
        (
            row["source_episode_id"],
            eligibility_certificate["episode_id"],
            "eligibility episode",
        ),
    )
    for actual, expected, label in bindings:
        if actual != expected:
            raise ValueError(f"training view sidecar binding mismatch: {label}")
    expected_snapshot = (
        eligibility_certificate["initial_snapshot_sha256"]
        if row["treatment"] == "M6U"
        else eligibility_certificate["project_envelope_sha256"]
    )
    if sidecar["snapshot_envelope_sha256"] != expected_snapshot:
        raise ValueError("training view sidecar binding mismatch: snapshot envelope")
    _assert_no_visibility_leak(
        row["payload"],
        treatment=row["treatment"],
        forbidden_canaries=tuple(forbidden_canaries),
    )


def write_training_view_export(
    output_root: Path | str,
    *,
    row: dict[str, Any],
    sidecar: dict[str, Any],
    eligibility_certificate: dict[str, Any],
    forbidden_canaries: Iterable[str] = (),
    paths: RepositoryPaths | None = None,
) -> Path:
    """Atomically write one validated candidate bundle under artifacts/ only."""

    validate_training_view_export(
        row,
        sidecar,
        eligibility_certificate,
        forbidden_canaries=forbidden_canaries,
    )
    repository_paths = paths or RepositoryPaths.discover()
    artifacts_root = repository_paths.artifacts_dir.resolve()
    resolved_output = Path(output_root).resolve()
    if resolved_output != artifacts_root and artifacts_root not in resolved_output.parents:
        raise ValueError("candidate training views may be written only under artifacts/")
    final_bundle = resolved_output / row["row_id"]
    if final_bundle.exists():
        raise FileExistsError(f"training view bundle already exists: {final_bundle}")
    resolved_output.mkdir(parents=True, exist_ok=True)
    staging = resolved_output / f".staging-{row['row_id']}-{uuid.uuid4().hex}"
    staging.mkdir()
    try:
        _write_json(staging / "row.json", row)
        _write_json(staging / "eligibility-sidecar.json", sidecar)
        _write_json(staging / "eligibility-certificate.json", eligibility_certificate)
        staging.rename(final_bundle)
    except BaseException:
        if staging.exists():
            shutil.rmtree(staging)
        raise
    return final_bundle


def _validate_snapshot_binding(
    *,
    treatment: str,
    eligibility_certificate: dict[str, Any],
    project: GeneratedProject,
    project_envelope: dict[str, Any],
    event_ref_resolver: Callable[[str], bool] | None,
) -> str:
    validate_training_eligibility_certificate(eligibility_certificate)
    if eligibility_certificate["eligibility_status"] != "eligible":
        raise ValueError("canonical training views require an eligible certificate")
    errors = verify_project_envelope(
        project,
        project_envelope,
        event_ref_resolver=event_ref_resolver,
    )
    if errors:
        raise ValueError("project does not match training-view envelope: " + "; ".join(errors))
    if project_envelope["episode_id"] != eligibility_certificate["episode_id"]:
        raise ValueError("training-view envelope episode does not match eligibility")
    if (
        project_envelope["method_condition_id"]
        != eligibility_certificate["method_condition_id"]
    ):
        raise ValueError("training-view envelope method does not match eligibility")
    expected_envelope_sha256 = (
        eligibility_certificate["initial_snapshot_sha256"]
        if treatment == "M6U"
        else eligibility_certificate["project_envelope_sha256"]
    )
    if project_envelope["envelope_sha256"] != expected_envelope_sha256:
        raise ValueError(f"{treatment} snapshot envelope does not match eligibility")
    snapshot_ids = {record["snapshot_id"] for record in project_envelope["files"]}
    if len(snapshot_ids) != 1:
        raise ValueError("training-view envelope must bind exactly one snapshot_id")
    snapshot_id = next(iter(snapshot_ids))
    if treatment == "M6U" and snapshot_id != eligibility_certificate["initial_snapshot_id"]:
        raise ValueError("M6U must use the outcome-blind initial snapshot")
    return snapshot_id


def _model_visible_project_files(
    project: GeneratedProject, project_envelope: dict[str, Any]
) -> list[dict[str, str]]:
    targets: list[dict[str, str]] = []
    for record in sorted(project_envelope["files"], key=lambda item: item["path"]):
        if record["file_role"] != "rtl_source":
            continue
        path = record["path"]
        if record["owner"] == "model" and record["editable"] is True:
            targets.append({"path": path, "role": "rtl", "content": project.files[path]})
            continue
        if record["owner"] != "composite":
            continue
        encoded = project.files[path].encode("utf-8")
        for region in record.get("regions", ()):
            if region["owner"] != "model" or region["editable"] is not True:
                continue
            try:
                content = encoded[region["start_byte"] : region["end_byte"]].decode("utf-8")
            except UnicodeDecodeError as error:
                raise ValueError(f"model region in {path!r} is not UTF-8 aligned") from error
            if not content:
                raise ValueError(f"model region in {path!r} is empty")
            targets.append({"path": path, "role": "model_region", "content": content})
    if not targets:
        raise ValueError("training view has no eligible model-owned RTL target")
    return targets


def _prompt_messages(messages: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    rendered: list[dict[str, str]] = []
    for index, message in enumerate(messages):
        if set(message) != {"role", "content"}:
            raise ValueError(f"prompt message {index} must contain only role and content")
        role = message["role"]
        content = message["content"]
        if role not in {"system", "user"} or not isinstance(content, str) or not content:
            raise ValueError(f"prompt message {index} is not model-visible prompt content")
        rendered.append({"role": role, "content": content})
    if not rendered:
        raise ValueError("training view requires at least one prompt message")
    return rendered


def _validate_transition(transition: PublicTransitionEvidence) -> None:
    if not transition.public_failure or not transition.public_diagnosis:
        raise ValueError("M6T requires non-empty public failure and diagnosis")
    if not transition.public_patch.strip() or not transition.public_rerun:
        raise ValueError("M6T requires a non-empty patch and actual public rerun")
    if not transition.actual_rerun:
        raise ValueError("M6T transition was not actually rerun")
    if not transition.targeted_failure_repaired:
        raise ValueError("M6T transition did not repair the targeted failure")
    if not transition.no_regression:
        raise ValueError("M6T transition introduced a regression")


def _build_row(
    *,
    source_episode_id: str,
    snapshot_id: str,
    treatment: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    identity = _sha256(
        {
            "source_episode_id": source_episode_id,
            "snapshot_id": snapshot_id,
            "treatment": treatment,
            "payload_sha256": _sha256(payload),
        }
    )
    without_hash = {
        "contract_version": "training-view-row-v2",
        "row_id": f"row-{identity}",
        "source_episode_id": source_episode_id,
        "snapshot_id": snapshot_id,
        "treatment": treatment,
        "payload": payload,
    }
    return {**without_hash, "row_sha256": _sha256(without_hash)}


def _build_sidecar(
    *,
    row: dict[str, Any],
    eligibility_certificate: dict[str, Any],
    snapshot_envelope_sha256: str,
    transition_evidence_sha256: str | None = None,
) -> dict[str, Any]:
    without_hash = {
        "contract_version": "training-view-eligibility-sidecar-v1",
        "visibility_class": "release_internal",
        "row_id": row["row_id"],
        "row_sha256": row["row_sha256"],
        "source_episode_id": row["source_episode_id"],
        "snapshot_id": row["snapshot_id"],
        "treatment": row["treatment"],
        "eligibility_artifact_sha256": eligibility_certificate["artifact_sha256"],
        "eligibility_evidence_bundle_sha256": eligibility_certificate[
            "evidence_bundle_sha256"
        ],
        "snapshot_envelope_sha256": snapshot_envelope_sha256,
    }
    if transition_evidence_sha256 is not None:
        without_hash["transition_evidence_sha256"] = transition_evidence_sha256
    return {**without_hash, "artifact_sha256": _sha256(without_hash)}


def _validate_registered(key: str, artifact: dict[str, Any]) -> None:
    errors = ContractRegistry().load_schema(key).validate(artifact)
    if errors:
        raise ValueError(f"invalid registered {key}: " + "; ".join(errors))


def _assert_no_visibility_leak(
    payload: dict[str, Any],
    *,
    treatment: str,
    forbidden_canaries: tuple[str, ...],
) -> None:
    for path, value in _walk(payload):
        if not isinstance(value, str):
            continue
        lowered = value.lower()
        if any(marker in lowered for marker in _GLOBAL_FORBIDDEN_TEXT_MARKERS):
            raise ValueError(f"forbidden audit/hidden marker in model-visible payload: {path}")
        if treatment == "M6U" and _M6U_JSON_FIELD_PATTERN.search(value):
            raise ValueError(f"forbidden M6U feedback field in model-visible payload: {path}")
        if any(canary and canary in value for canary in forbidden_canaries):
            raise ValueError(f"forbidden canary in model-visible payload: {path}")


def _walk(value: Any, path: str = "$"):
    yield path, value
    if isinstance(value, dict):
        for key, item in value.items():
            yield from _walk(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk(item, f"{path}[{index}]")


def _sha256(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _write_json(path: Path, artifact: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
