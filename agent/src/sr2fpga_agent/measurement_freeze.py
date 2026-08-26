"""Immutable measurement protocol records for frozen SR2FPGA runs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


_SECRET_FIELD_MARKERS = (
    "api_key",
    "authorization",
    "access_token",
    "client_secret",
    "password",
)


def build_measurement_freeze(
    *,
    run_id: str,
    config_fingerprint: str,
    sample_records: list[dict[str, Any]],
    source_records: list[dict[str, Any]],
    max_attempts: int,
    timeouts: dict[str, int],
    tool_versions: dict[str, str],
    l4_family_ids: list[str],
    tool_environment_ref: dict[str, Any] | None = None,
    l4_tool_environment_ref: dict[str, Any] | None = None,
) -> dict[str, Any]:
    manifest: dict[str, Any] = {
        "schema_version": "sr2fpga-phase-d-freeze-v1",
        "run_id": run_id,
        "config_fingerprint": config_fingerprint,
        "sample_count": len(sample_records),
        "samples": sample_records,
        "sources": source_records,
        "max_attempts": max_attempts,
        "timeouts": timeouts,
        "tool_versions": tool_versions,
        "l4_family_ids": sorted(l4_family_ids),
    }
    if tool_environment_ref is not None:
        manifest["tool_environment_ref"] = dict(tool_environment_ref)
    if l4_tool_environment_ref is not None:
        manifest["l4_tool_environment_ref"] = dict(l4_tool_environment_ref)
    _reject_secret_like_fields(manifest)
    return manifest


def freeze_fingerprint(manifest: dict[str, Any]) -> str:
    payload = {key: value for key, value in manifest.items() if key != "freeze_fingerprint"}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def write_or_validate_freeze(
    path: Path,
    manifest: dict[str, Any],
    *,
    resume: bool,
) -> str:
    fingerprint = freeze_fingerprint(manifest)
    frozen = {**manifest, "freeze_fingerprint": fingerprint}
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing != frozen:
            raise RuntimeError("measurement freeze mismatch; refusing to resume")
        return fingerprint
    if resume:
        raise RuntimeError("measurement freeze missing; refusing to resume")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(frozen, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return fingerprint


def _reject_secret_like_fields(value: Any, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).lower()
            if any(marker in normalized for marker in _SECRET_FIELD_MARKERS):
                raise ValueError(f"measurement freeze contains secret-like field: {path}.{key}")
            _reject_secret_like_fields(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_secret_like_fields(item, f"{path}[{index}]")
