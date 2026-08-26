"""Load and apply the registered System-HIS compatibility envelope."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import json
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any

from sr2fpga_agent.repository_paths import RepositoryPaths


CONTRACT_KEY = "system_his_compatibility"
CONTRACT_VERSION = "system-his-compatibility-v1"
_TOP_LEVEL_KEYS = frozenset(
    {
        "contract_version",
        "canonical_system_his_version",
        "representations",
        "unknown_representation",
    }
)
_POLICY_KEYS = frozenset(
    {
        "status",
        "registered_h_stage_policy",
        "common_l0_policy",
        "training_partition",
        "positive_system_his_view_policy",
    }
)
_REPRESENTATION_KEYS = _POLICY_KEYS | {"representation_id"}
_EXPECTED_REPRESENTATIONS = frozenset(
    {"system-his-v1.2", "system-his-v1.1", "not_applicable"}
)


class SystemHisCompatibilityError(ValueError):
    """The registered compatibility envelope is missing or inconsistent."""


@dataclass(frozen=True, slots=True)
class SystemHisCompatibilityDisposition:
    representation_id: str
    status: str
    registered_h_stage_policy: str
    common_l0_policy: str
    training_partition: str
    positive_system_his_view_policy: str


@dataclass(frozen=True, slots=True)
class SystemHisCompatibilityEnvelope:
    contract_version: str
    canonical_system_his_version: str
    representations: Mapping[str, SystemHisCompatibilityDisposition]
    unknown_representation: SystemHisCompatibilityDisposition

    def __post_init__(self) -> None:
        object.__setattr__(self, "representations", MappingProxyType(dict(self.representations)))

    def classify(self, representation_id: str) -> SystemHisCompatibilityDisposition:
        normalized = representation_id.strip() if isinstance(representation_id, str) else ""
        disposition = self.representations.get(normalized)
        if disposition is not None:
            return disposition
        unknown = self.unknown_representation
        return SystemHisCompatibilityDisposition(
            representation_id=normalized or "unknown",
            status=unknown.status,
            registered_h_stage_policy=unknown.registered_h_stage_policy,
            common_l0_policy=unknown.common_l0_policy,
            training_partition=unknown.training_partition,
            positive_system_his_view_policy=unknown.positive_system_his_view_policy,
        )


def load_system_his_compatibility_envelope(
    repository_paths: RepositoryPaths | None = None,
) -> SystemHisCompatibilityEnvelope:
    """Load the manifest-registered compatibility policy and reject drift."""

    paths = repository_paths or RepositoryPaths.discover()
    manifest = _load_object(paths.contracts_dir / "manifest.json", "contract manifest")
    contracts = _require_object(manifest.get("contracts"), "manifest.contracts")
    record = _contract_record(contracts, CONTRACT_KEY)
    registered_version = _require_string(record.get("version"), "registered version")
    if registered_version != CONTRACT_VERSION:
        raise SystemHisCompatibilityError("registered compatibility version is unsupported")

    contract_path = _resolve_contract_path(paths.root, record.get("path"))
    payload = _load_object(contract_path, "System-HIS compatibility envelope")
    _require_exact_keys(payload, _TOP_LEVEL_KEYS, "compatibility envelope")
    if payload.get("contract_version") != registered_version:
        raise SystemHisCompatibilityError("compatibility version does not match manifest")

    canonical_version = _require_string(
        payload.get("canonical_system_his_version"),
        "canonical_system_his_version",
    )
    system_his_record = _contract_record(contracts, "system_his")
    if canonical_version != _require_string(system_his_record.get("version"), "System-HIS version"):
        raise SystemHisCompatibilityError(
            "canonical System-HIS version does not match the registered schema"
        )

    raw_representations = payload.get("representations")
    if not isinstance(raw_representations, list):
        raise SystemHisCompatibilityError("representations must be an array")
    representations: dict[str, SystemHisCompatibilityDisposition] = {}
    for index, raw in enumerate(raw_representations):
        value = _require_object(raw, f"representations[{index}]")
        _require_exact_keys(value, _REPRESENTATION_KEYS, f"representations[{index}]")
        disposition = _parse_disposition(value)
        if disposition.representation_id in representations:
            raise SystemHisCompatibilityError("representations contain a duplicate id")
        representations[disposition.representation_id] = disposition
    if set(representations) != _EXPECTED_REPRESENTATIONS:
        raise SystemHisCompatibilityError("compatibility envelope representation set is incomplete")

    canonical = representations[canonical_version]
    if (
        canonical.status != "canonical"
        or canonical.registered_h_stage_policy != "required"
        or canonical.training_partition != "clean"
        or canonical.positive_system_his_view_policy != "condition_eligible"
    ):
        raise SystemHisCompatibilityError("canonical representation must require registered H stages")
    legacy = representations["system-his-v1.1"]
    if (
        legacy.status != "legacy_quarantine"
        or legacy.registered_h_stage_policy != "reject"
        or legacy.training_partition != "quarantine"
        or legacy.positive_system_his_view_policy != "forbidden"
    ):
        raise SystemHisCompatibilityError("legacy System-HIS must remain quarantined")
    direct = representations["not_applicable"]
    if (
        direct.status != "method_not_applicable"
        or direct.registered_h_stage_policy != "not_applicable"
        or direct.common_l0_policy != "eligible"
        or direct.training_partition != "quarantine"
        or direct.positive_system_his_view_policy != "method_neutral_only"
    ):
        raise SystemHisCompatibilityError("method-inapplicable HIS must preserve common L0 eligibility")

    unknown_value = _require_object(payload.get("unknown_representation"), "unknown_representation")
    _require_exact_keys(unknown_value, _POLICY_KEYS, "unknown_representation")
    unknown = _parse_disposition({"representation_id": "unknown", **unknown_value})
    if (
        unknown.status != "unknown_quarantine"
        or unknown.training_partition != "quarantine"
        or unknown.registered_h_stage_policy != "reject"
        or unknown.positive_system_his_view_policy != "forbidden"
    ):
        raise SystemHisCompatibilityError("unknown representations must fail closed into quarantine")

    return SystemHisCompatibilityEnvelope(
        contract_version=registered_version,
        canonical_system_his_version=canonical_version,
        representations=representations,
        unknown_representation=unknown,
    )


def _parse_disposition(value: Mapping[str, Any]) -> SystemHisCompatibilityDisposition:
    representation_id = _require_string(value.get("representation_id"), "representation_id")
    status = _require_choice(
        value.get("status"),
        "status",
        {"canonical", "legacy_quarantine", "method_not_applicable", "unknown_quarantine"},
    )
    h_policy = _require_choice(
        value.get("registered_h_stage_policy"),
        "registered_h_stage_policy",
        {"required", "reject", "not_applicable"},
    )
    l0_policy = _require_choice(value.get("common_l0_policy"), "common_l0_policy", {"eligible"})
    partition = _require_choice(
        value.get("training_partition"),
        "training_partition",
        {"clean", "quarantine"},
    )
    view_policy = _require_choice(
        value.get("positive_system_his_view_policy"),
        "positive_system_his_view_policy",
        {"condition_eligible", "forbidden", "method_neutral_only"},
    )
    return SystemHisCompatibilityDisposition(
        representation_id=representation_id,
        status=status,
        registered_h_stage_policy=h_policy,
        common_l0_policy=l0_policy,
        training_partition=partition,
        positive_system_his_view_policy=view_policy,
    )


def _load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as handle:
            payload = json.load(handle, object_pairs_hook=_reject_duplicate_keys)
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemHisCompatibilityError(f"could not load {label}: {path}") from exc
    return _require_object(payload, label)


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SystemHisCompatibilityError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _contract_record(contracts: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    record = _require_object(contracts.get(key), f"manifest.contracts.{key}")
    _require_exact_keys(record, frozenset({"version", "path"}), f"manifest.contracts.{key}")
    return record


def _resolve_contract_path(root: Path, raw_path: Any) -> Path:
    text = _require_string(raw_path, "compatibility contract path")
    posix = PurePosixPath(text)
    if "\\" in text or posix.is_absolute() or ".." in posix.parts or posix.as_posix() != text:
        raise SystemHisCompatibilityError("compatibility contract path must be repository-relative POSIX")
    resolved_root = root.resolve()
    resolved = resolved_root.joinpath(*posix.parts).resolve()
    if not resolved.is_relative_to(resolved_root):
        raise SystemHisCompatibilityError("compatibility contract path escapes repository root")
    return resolved


def _require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SystemHisCompatibilityError(f"{label} must be an object")
    return value


def _require_exact_keys(value: Mapping[str, Any], expected: frozenset[str], label: str) -> None:
    if set(value) != expected:
        raise SystemHisCompatibilityError(f"{label} keys do not match the versioned contract")


def _require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise SystemHisCompatibilityError(f"{label} must be a non-empty trimmed string")
    return value


def _require_choice(value: Any, label: str, choices: set[str]) -> str:
    text = _require_string(value, label)
    if text not in choices:
        raise SystemHisCompatibilityError(f"{label} has unsupported value {text!r}")
    return text
