"""Training-owned readers for repository contract metadata."""

from __future__ import annotations

from functools import lru_cache
import json
import os
from pathlib import Path, PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator


class TrainingContractError(ValueError):
    """Raised when a training row violates a repository contract."""


def discover_repository_root(start: Path | None = None) -> Path:
    configured_root = os.environ.get("SR2FPGA_REPO_ROOT", "").strip()
    if configured_root:
        return _require_repository_root(Path(configured_root))

    candidate = (start or Path(__file__)).resolve()
    if candidate.is_file():
        candidate = candidate.parent
    for directory in (candidate, *candidate.parents):
        if (directory / "contracts" / "manifest.json").is_file():
            return directory

    raise TrainingContractError(
        "Cannot locate contracts/manifest.json; set SR2FPGA_REPO_ROOT"
    )


def validate_training_view_provenance(row: dict[str, Any]) -> None:
    """Validate provenance and pass-credit rules used by Training."""

    if row.get("view_type") != "requirement_to_file":
        return

    schema = _training_view_schema()
    expected_version = schema["properties"]["contract_version"]["const"]
    if row.get("contract_version") != expected_version:
        raise TrainingContractError(
            f"contract_version must be {expected_version!r}"
        )

    source_episode_id = row.get("source_episode_id")
    if not isinstance(source_episode_id, str) or not source_episode_id.strip():
        raise TrainingContractError(
            "requirement_to_file requires a non-empty source_episode_id"
        )

    if row.get("official_eval_unit") is not False:
        raise TrainingContractError(
            "requirement_to_file official_eval_unit must be false"
        )

    if row.get("standalone_pass_credit") is not False:
        raise TrainingContractError(
            "requirement_to_file standalone_pass_credit must be false"
        )


def _require_repository_root(candidate: Path) -> Path:
    resolved = candidate.expanduser().resolve()
    if not (resolved / "contracts" / "manifest.json").is_file():
        raise TrainingContractError(
            f"SR2FPGA_REPO_ROOT does not contain contracts/manifest.json: "
            f"{resolved}"
        )
    return resolved


@lru_cache(maxsize=1)
def _training_view_schema() -> dict[str, Any]:
    return load_registered_schema("training_view_row_legacy")


@lru_cache(maxsize=None)
def load_registered_schema(key: str) -> dict[str, Any]:
    """Load and verify one manifest-registered contract without importing Agent."""

    root = discover_repository_root()
    manifest_path = root / "contracts" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    contracts = manifest.get("contracts")
    registry_entry = contracts.get(key) if isinstance(contracts, dict) else None
    if not isinstance(registry_entry, dict):
        raise TrainingContractError(f"unregistered training contract: {key}")
    relative_text = registry_entry.get("path")
    if not isinstance(relative_text, str) or not relative_text:
        raise TrainingContractError(f"registered training contract {key!r} has no path")
    relative = PurePosixPath(relative_text)
    if relative.is_absolute() or ".." in relative.parts:
        raise TrainingContractError(f"registered training contract {key!r} has unsafe path")
    schema_path = (root / Path(*relative.parts)).resolve()
    contracts_root = (root / "contracts").resolve()
    if schema_path != contracts_root and contracts_root not in schema_path.parents:
        raise TrainingContractError(f"registered training contract {key!r} escapes contracts/")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    if not isinstance(schema, dict):
        raise TrainingContractError(
            f"Training contract must be a JSON object: {schema_path}"
        )
    Draft202012Validator.check_schema(schema)
    declared_version = schema.get("properties", {}).get("contract_version", {}).get("const")
    if declared_version != registry_entry.get("version"):
        raise TrainingContractError(
            f"registered training contract {key!r} version does not match schema"
        )
    return schema
