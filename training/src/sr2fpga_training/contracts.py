"""Training-owned readers for repository contract metadata."""

from __future__ import annotations

from functools import lru_cache
import json
import os
from pathlib import Path
from typing import Any


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
    root = discover_repository_root()
    manifest_path = root / "contracts" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    registry_entry = manifest["contracts"]["training_view_row"]
    schema_path = root / registry_entry["path"]
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    if not isinstance(schema, dict):
        raise TrainingContractError(
            f"Training-view contract must be a JSON object: {schema_path}"
        )
    return schema
