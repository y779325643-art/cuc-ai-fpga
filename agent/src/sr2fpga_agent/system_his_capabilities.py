"""Load the versioned System-HIS backend capability contract."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import json
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any

from .repository_paths import RepositoryPaths


_MANIFEST_CONTRACT_KEY = "system_his_backend_capabilities"
_REGISTRY_KEYS = frozenset(
    {
        "capability_registry_version",
        "system_his_version",
        "component_semantic_kinds",
        "data_flow_protocols",
        "verification",
    }
)


class SystemHisCapabilityRegistryError(ValueError):
    """The registered backend capability contract is missing or invalid."""


@dataclass(frozen=True, slots=True)
class SystemHisBackendCapabilities:
    """Immutable capabilities advertised by the current System-HIS lowerer."""

    registry_version: str
    system_his_version: str
    supported_component_semantic_kinds: frozenset[str]
    component_semantic_kind_aliases: Mapping[str, str]
    supported_data_flow_protocols: frozenset[str]
    data_flow_protocol_aliases: Mapping[str, str]
    supported_verification_scenarios: frozenset[str]
    canonical_testbench: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "supported_component_semantic_kinds",
            frozenset(self.supported_component_semantic_kinds),
        )
        object.__setattr__(
            self,
            "component_semantic_kind_aliases",
            MappingProxyType(dict(self.component_semantic_kind_aliases)),
        )
        object.__setattr__(
            self,
            "supported_data_flow_protocols",
            frozenset(self.supported_data_flow_protocols),
        )
        object.__setattr__(
            self,
            "data_flow_protocol_aliases",
            MappingProxyType(dict(self.data_flow_protocol_aliases)),
        )
        object.__setattr__(
            self,
            "supported_verification_scenarios",
            frozenset(self.supported_verification_scenarios),
        )


def load_system_his_backend_capabilities(
    repository_paths: RepositoryPaths | None = None,
) -> SystemHisBackendCapabilities:
    """Load the manifest-registered capability profile and reject drift."""

    paths = repository_paths or RepositoryPaths.discover()
    manifest_path = paths.contracts_dir / "manifest.json"
    manifest = _load_json_object(manifest_path, "contract manifest")
    contracts = _require_object(manifest.get("contracts"), "manifest.contracts")

    capability_record = _contract_record(contracts, _MANIFEST_CONTRACT_KEY)
    registry_path = _resolve_registered_path(
        paths.root,
        _require_string(capability_record.get("path"), "capability contract path"),
    )
    payload = _load_json_object(registry_path, "System-HIS capability registry")
    _require_exact_keys(payload, _REGISTRY_KEYS, "capability registry")

    registry_version = _require_string(
        payload.get("capability_registry_version"),
        "capability_registry_version",
    )
    registered_version = _require_string(
        capability_record.get("version"),
        "manifest capability contract version",
    )
    if registry_version != registered_version:
        raise SystemHisCapabilityRegistryError(
            "capability registry version does not match contracts/manifest.json"
        )

    system_his_version = _require_string(
        payload.get("system_his_version"),
        "system_his_version",
    )
    system_his_record = _contract_record(contracts, "system_his")
    registered_system_his_version = _require_string(
        system_his_record.get("version"),
        "manifest System-HIS contract version",
    )
    if system_his_version != registered_system_his_version:
        raise SystemHisCapabilityRegistryError(
            "capability registry System-HIS version does not match contracts/manifest.json"
        )

    semantic_kinds, semantic_aliases = _load_named_capabilities(
        payload.get("component_semantic_kinds"),
        "component_semantic_kinds",
    )
    protocols, protocol_aliases = _load_named_capabilities(
        payload.get("data_flow_protocols"),
        "data_flow_protocols",
    )
    verification = _require_object(payload.get("verification"), "verification")
    _require_exact_keys(
        verification,
        frozenset({"supported_scenarios", "canonical_testbench"}),
        "verification",
    )
    scenarios = _require_unique_strings(
        verification.get("supported_scenarios"),
        "verification.supported_scenarios",
    )
    canonical_testbench = _require_string(
        verification.get("canonical_testbench"),
        "verification.canonical_testbench",
    )
    _validate_relative_posix_path(canonical_testbench, "verification.canonical_testbench")

    return SystemHisBackendCapabilities(
        registry_version=registry_version,
        system_his_version=system_his_version,
        supported_component_semantic_kinds=frozenset(semantic_kinds),
        component_semantic_kind_aliases=semantic_aliases,
        supported_data_flow_protocols=frozenset(protocols),
        data_flow_protocol_aliases=protocol_aliases,
        supported_verification_scenarios=frozenset(scenarios),
        canonical_testbench=canonical_testbench,
    )


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as handle:
            payload = json.load(handle, object_pairs_hook=_object_without_duplicate_keys)
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemHisCapabilityRegistryError(f"could not load {label}: {path}") from exc
    return _require_object(payload, label)


def _object_without_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key, value in pairs:
        if key in payload:
            raise SystemHisCapabilityRegistryError(f"duplicate JSON key: {key}")
        payload[key] = value
    return payload


def _contract_record(contracts: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    record = _require_object(contracts.get(name), f"manifest.contracts.{name}")
    _require_exact_keys(record, frozenset({"version", "path"}), f"manifest.contracts.{name}")
    return record


def _resolve_registered_path(root: Path, relative_path: str) -> Path:
    posix_path = _validate_relative_posix_path(relative_path, "capability contract path")
    resolved_root = root.resolve()
    resolved_path = resolved_root.joinpath(*posix_path.parts).resolve()
    if not resolved_path.is_relative_to(resolved_root):
        raise SystemHisCapabilityRegistryError(
            "capability contract path escapes the repository root"
        )
    return resolved_path


def _validate_relative_posix_path(value: str, label: str) -> PurePosixPath:
    posix_path = PurePosixPath(value)
    if (
        "\\" in value
        or posix_path.is_absolute()
        or posix_path.as_posix() != value
        or value in {"", "."}
        or ".." in posix_path.parts
    ):
        raise SystemHisCapabilityRegistryError(
            f"{label} must be a normalized repository-relative POSIX path"
        )
    return posix_path


def _load_named_capabilities(
    value: Any,
    label: str,
) -> tuple[frozenset[str], Mapping[str, str]]:
    section = _require_object(value, label)
    _require_exact_keys(section, frozenset({"supported", "aliases"}), label)
    supported = _require_unique_strings(section.get("supported"), f"{label}.supported")
    aliases = _require_string_mapping(section.get("aliases"), f"{label}.aliases")
    overlapping_names = supported.intersection(aliases)
    if overlapping_names:
        raise SystemHisCapabilityRegistryError(
            f"{label}.aliases overlap canonical names: {sorted(overlapping_names)}"
        )
    unsupported_targets = set(aliases.values()).difference(supported)
    if unsupported_targets:
        raise SystemHisCapabilityRegistryError(
            f"{label}.aliases target unsupported names: {sorted(unsupported_targets)}"
        )
    return supported, aliases


def _require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SystemHisCapabilityRegistryError(f"{label} must be an object")
    return value


def _require_exact_keys(
    value: Mapping[str, Any],
    expected: frozenset[str],
    label: str,
) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected.difference(actual))
        unexpected = sorted(actual.difference(expected))
        raise SystemHisCapabilityRegistryError(
            f"{label} keys do not match versioned contract; "
            f"missing={missing}, unexpected={unexpected}"
        )


def _require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise SystemHisCapabilityRegistryError(f"{label} must be a non-empty trimmed string")
    return value


def _require_unique_strings(value: Any, label: str) -> frozenset[str]:
    if not isinstance(value, list) or not value:
        raise SystemHisCapabilityRegistryError(f"{label} must be a non-empty array")
    strings = tuple(_require_string(item, f"{label} item") for item in value)
    if len(strings) != len(set(strings)):
        raise SystemHisCapabilityRegistryError(f"{label} contains duplicate entries")
    return frozenset(strings)


def _require_string_mapping(value: Any, label: str) -> Mapping[str, str]:
    mapping = _require_object(value, label)
    normalized = {
        _require_string(key, f"{label} key"): _require_string(target, f"{label}.{key}")
        for key, target in mapping.items()
    }
    return MappingProxyType(normalized)
