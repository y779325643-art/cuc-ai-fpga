"""Evaluator-owned trusted public L2 harness loading and commitments."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.path_safety import validate_project_relative_path


class PublicL2HarnessError(ValueError):
    pass


@dataclass(frozen=True)
class TrustedPublicL2HarnessFile:
    path: str
    content: str
    sha256: str


@dataclass(frozen=True)
class DevelopmentTrustedPublicL2Harness:
    harness_id: str
    testbench_top: str
    language_standard: str
    files: tuple[TrustedPublicL2HarnessFile, ...]
    timeout_seconds: int
    manifest_sha256: str
    bundle_sha256: str

    def public_evidence(self) -> dict[str, str | None]:
        return {
            "status": "available",
            "harness_id": self.harness_id,
            "manifest_sha256": self.manifest_sha256,
            "bundle_sha256": self.bundle_sha256,
            "reason": None,
        }


def load_development_public_l2_harness(
    manifest_path: Path,
    *,
    registry: ContractRegistry | None = None,
) -> DevelopmentTrustedPublicL2Harness:
    """Load and hash-check one development/excluded evaluator-owned harness."""

    path = Path(manifest_path).resolve()
    try:
        raw_bytes = path.read_bytes()
    except OSError as exc:
        raise PublicL2HarnessError("public L2 harness manifest is unavailable") from exc
    try:
        payload = json.loads(raw_bytes)
    except json.JSONDecodeError as exc:
        raise PublicL2HarnessError("public L2 harness manifest is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise PublicL2HarnessError("public L2 harness manifest must be an object")
    errors = (registry or ContractRegistry()).load_schema(
        "development_public_l2_harness"
    ).validate(payload)
    if errors:
        raise PublicL2HarnessError(
            "invalid public L2 harness manifest: " + "; ".join(errors)
        )

    root = path.parent.resolve()
    files: list[TrustedPublicL2HarnessFile] = []
    seen: set[str] = set()
    for item in payload["files"]:
        relative = validate_project_relative_path(str(item["path"]))
        if relative in seen:
            raise PublicL2HarnessError("duplicate public L2 harness file path")
        seen.add(relative)
        source = (root / Path(*relative.split("/"))).resolve()
        try:
            source.relative_to(root)
        except ValueError as exc:
            raise PublicL2HarnessError("public L2 harness file escapes manifest root") from exc
        try:
            content_bytes = source.read_bytes()
        except OSError as exc:
            raise PublicL2HarnessError("public L2 harness file is unavailable") from exc
        digest = hashlib.sha256(content_bytes).hexdigest()
        if digest != item["sha256"]:
            raise PublicL2HarnessError("public L2 harness file hash mismatch")
        try:
            content = content_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise PublicL2HarnessError("public L2 harness file must be UTF-8 text") from exc
        files.append(TrustedPublicL2HarnessFile(relative, content, digest))

    manifest_sha256 = hashlib.sha256(raw_bytes).hexdigest()
    bundle_sha256 = hashlib.sha256(
        _canonical_json(
            {
                "harness_id": payload["harness_id"],
                "testbench_top": payload["testbench_top"],
                "language_standard": payload["language_standard"],
                "timeout_seconds": payload["timeout_seconds"],
                "pass_rule": payload["pass_rule"],
                "files": [
                    {"path": item.path, "sha256": item.sha256} for item in files
                ],
            }
        )
    ).hexdigest()
    return DevelopmentTrustedPublicL2Harness(
        harness_id=payload["harness_id"],
        testbench_top=payload["testbench_top"],
        language_standard=payload["language_standard"],
        files=tuple(files),
        timeout_seconds=payload["timeout_seconds"],
        manifest_sha256=manifest_sha256,
        bundle_sha256=bundle_sha256,
    )


def unavailable_public_l2_harness_evidence() -> dict[str, str | None]:
    return {
        "status": "unavailable",
        "harness_id": None,
        "manifest_sha256": None,
        "bundle_sha256": None,
        "reason": "needs_oracle",
    }


def _canonical_json(payload: Any) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
