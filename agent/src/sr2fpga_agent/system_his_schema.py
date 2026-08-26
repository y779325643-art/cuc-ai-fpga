"""Load and execute the registered System-HIS JSON Schema contract."""

from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator

from sr2fpga_agent.repository_paths import RepositoryPaths


CONTRACT_KEY = "system_his"


def load_registered_system_his_schema(
    paths: RepositoryPaths | None = None,
) -> dict[str, Any]:
    """Load the manifest-registered schema and reject unsafe or inconsistent entries."""

    repository_paths = paths or RepositoryPaths.discover()
    manifest_path = repository_paths.contracts_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entry = manifest.get("contracts", {}).get(CONTRACT_KEY)
    if not isinstance(entry, dict):
        raise ValueError(f"contracts manifest is missing {CONTRACT_KEY!r}")

    version = str(entry.get("version", "")).strip()
    relative_text = str(entry.get("path", "")).strip()
    relative = PurePosixPath(relative_text)
    if not relative_text or relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"contracts manifest has unsafe {CONTRACT_KEY} path: {relative_text!r}")

    schema_path = (repository_paths.root / Path(*relative.parts)).resolve()
    contracts_root = repository_paths.contracts_dir.resolve()
    if schema_path != contracts_root and contracts_root not in schema_path.parents:
        raise ValueError(f"registered {CONTRACT_KEY} schema escapes contracts/: {relative_text!r}")

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    schema_version = schema.get("properties", {}).get("schema_version", {}).get("const")
    if version != schema_version:
        raise ValueError(
            f"registered {CONTRACT_KEY} version {version!r} does not match schema const {schema_version!r}"
        )
    return schema


def validate_registered_system_his_schema(
    payload: Any,
    paths: RepositoryPaths | None = None,
) -> list[str]:
    """Return stable, path-qualified Draft 2020-12 validation diagnostics."""

    validator = Draft202012Validator(load_registered_system_his_schema(paths))
    errors = sorted(
        validator.iter_errors(payload),
        key=lambda error: (tuple(str(part) for part in error.absolute_path), error.message),
    )
    return [_format_error(error) for error in errors]


def _format_error(error: Any) -> str:
    path = _json_path(error.absolute_path)
    if error.validator == "required":
        match = re.match(r"^'(.+)' is a required property$", error.message)
        if match:
            return f"{path}.{match.group(1)} is required"
    if error.validator == "type" and isinstance(error.validator_value, str):
        type_name = {"array": "list", "object": "object"}.get(
            error.validator_value,
            error.validator_value,
        )
        article = "an" if type_name == "object" else "a"
        return f"{path} must be {article} {type_name}"
    if error.validator == "const":
        return f"{path} must be {error.validator_value}"
    return f"{path}: {error.message}"


def _json_path(parts: Any) -> str:
    path = "system_his"
    for part in parts:
        if isinstance(part, int):
            path += f"[{part}]"
        else:
            path += f".{part}"
    return path
