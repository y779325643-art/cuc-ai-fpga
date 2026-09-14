"""Execute the registered System-HIS JSON Schema contract with System-HIS diagnostics.

Loading, path-safety and version-consistency rules live once in
:mod:`sr2fpga_agent.contract_registry`. This module owns only the System-HIS
diagnostic shape, whose exact strings reach H0 reports and M5 repair prompts.
"""

from __future__ import annotations

import re
from typing import Any

from jsonschema import Draft202012Validator

from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.repository_paths import RepositoryPaths


CONTRACT_KEY = "system_his"


def load_registered_system_his_schema(
    paths: RepositoryPaths | None = None,
) -> dict[str, Any]:
    """Load the manifest-registered schema and reject unsafe or inconsistent entries."""

    try:
        return ContractRegistry(paths).load_schema(CONTRACT_KEY).document
    except KeyError as exc:
        raise ValueError(f"contracts manifest is missing {CONTRACT_KEY!r}") from exc


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
