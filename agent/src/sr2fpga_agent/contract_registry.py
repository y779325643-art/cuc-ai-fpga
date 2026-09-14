"""Manifest-aware access to registered JSON contracts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator

from sr2fpga_agent.repository_paths import RepositoryPaths, file_identity


_MANIFEST_CACHE: dict[tuple[str, int, int], dict[str, Any]] = {}
_SCHEMA_CACHE: dict[tuple[str, int, int], dict[str, Any]] = {}
_VALIDATOR_CACHE: dict[tuple[str, int, int], Draft202012Validator] = {}
_RESOLVED_CACHE: dict[str, Path] = {}


@dataclass(frozen=True)
class RegisteredContract:
    key: str
    version: str
    path: Path
    document: dict[str, Any]

    def validate(self, payload: Any) -> tuple[str, ...]:
        validator = _cached_validator(self.path, self.document)
        errors = sorted(
            validator.iter_errors(payload),
            key=lambda error: (
                tuple(str(part) for part in error.absolute_path),
                error.message,
            ),
        )
        return tuple(
            f"{_json_path(error.absolute_path)}: {error.message}"
            for error in errors
        )


class ContractRegistry:
    def __init__(self, paths: RepositoryPaths | None = None) -> None:
        self._paths = paths or RepositoryPaths.discover()
        manifest_path = self._paths.contracts_dir / "manifest.json"
        self._manifest = _cached_manifest(manifest_path)

    def load_schema(self, key: str) -> RegisteredContract:
        contracts = self._manifest.get("contracts")
        entry = contracts.get(key) if isinstance(contracts, dict) else None
        if not isinstance(entry, dict):
            raise KeyError(f"unregistered contract: {key}")
        version = entry.get("version")
        relative_text = entry.get("path")
        if not isinstance(version, str) or not version:
            raise ValueError(f"registered contract {key!r} has invalid version")
        if not isinstance(relative_text, str) or not relative_text:
            raise ValueError(f"registered contract {key!r} has invalid path")
        relative = PurePosixPath(relative_text)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"registered contract {key!r} has unsafe path")
        path = _resolved(self._paths.root / Path(*relative.parts))
        contracts_root = _resolved(self._paths.contracts_dir)
        if path != contracts_root and contracts_root not in path.parents:
            raise ValueError(f"registered contract {key!r} escapes contracts/")
        document = _cached_schema(path)
        version_field = {
            "system_his": "schema_version",
            "requirement_audit": "audit_version",
        }.get(key, "contract_version")
        declared = (
            document.get("properties", {})
            .get(version_field, {})
            .get("const")
        )
        if key == "pc_decisions":
            # The decision body has no model-writable version field.
            declared = document.get("x-contract-version")
        if declared != version:
            raise ValueError(
                f"registered contract {key!r} version {version!r} does not "
                f"match schema const {declared!r}"
            )
        return RegisteredContract(key, version, path, document)


def _resolved(path: Path) -> Path:
    """Memoize Path.resolve for repository-owned contract paths."""

    key = str(path)
    resolved = _RESOLVED_CACHE.get(key)
    if resolved is None:
        resolved = path.resolve()
        _RESOLVED_CACHE[key] = resolved
    return resolved


def _cached_manifest(path: Path) -> dict[str, Any]:
    """Return the parsed contracts manifest, reparsing only when the file changes."""

    identity = file_identity(path)
    manifest = _MANIFEST_CACHE.get(identity)
    if manifest is None:
        manifest = _load_object(path)
        _MANIFEST_CACHE[identity] = manifest
    return manifest


def _cached_schema(path: Path) -> dict[str, Any]:
    """Return a metaschema-checked contract document, checking it only once per file state."""

    identity = file_identity(path)
    document = _SCHEMA_CACHE.get(identity)
    if document is None:
        document = _load_object(path)
        Draft202012Validator.check_schema(document)
        _SCHEMA_CACHE[identity] = document
    return document


def _cached_validator(path: Path, document: dict[str, Any]) -> Draft202012Validator:
    """Reuse one validator per contract file state; iter_errors does not mutate it."""

    identity = file_identity(path)
    validator = _VALIDATOR_CACHE.get(identity)
    if validator is None:
        validator = Draft202012Validator(document)
        _VALIDATOR_CACHE[identity] = validator
    return validator


def _load_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON document must be an object: {path}")
    return payload


def _json_path(parts: object) -> str:
    rendered = "$"
    for part in parts:
        rendered += f"[{part}]" if isinstance(part, int) else f".{part}"
    return rendered
