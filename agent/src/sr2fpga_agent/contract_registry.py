"""Manifest-aware access to registered JSON contracts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator

from sr2fpga_agent.repository_paths import RepositoryPaths


@dataclass(frozen=True)
class RegisteredContract:
    key: str
    version: str
    path: Path
    document: dict[str, Any]

    def validate(self, payload: Any) -> tuple[str, ...]:
        validator = Draft202012Validator(self.document)
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
        self._manifest = _load_object(manifest_path)

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
        path = (self._paths.root / Path(*relative.parts)).resolve()
        contracts_root = self._paths.contracts_dir.resolve()
        if path != contracts_root and contracts_root not in path.parents:
            raise ValueError(f"registered contract {key!r} escapes contracts/")
        document = _load_object(path)
        Draft202012Validator.check_schema(document)
        declared = (
            document.get("properties", {})
            .get("contract_version", {})
            .get("const")
        )
        if declared != version:
            raise ValueError(
                f"registered contract {key!r} version {version!r} does not "
                f"match schema const {declared!r}"
            )
        return RegisteredContract(key, version, path, document)


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
