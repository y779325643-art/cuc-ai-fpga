"""Shared data models and canonical JSON identity rules for the SR2FPGA agent.

The JSON helpers live here because artifact, event, cost and contract modules
all need them and none of them may depend on each other. Two terminations are
in use and both are load-bearing: ``canonical_json_bytes`` is what artifact
blobs and content-derived event IDs are built from, and ``compact_json_bytes``
is what cost ledgers and every ``sha256_json`` digest are built from. Choosing
the wrong one changes stored artifact identities, so callers name the
termination they mean rather than relying on one ambiguous "canonical" helper.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PlatformProfile:
    """Trusted target platform context used by the generator."""

    name: str
    vendor: str
    toolchain: str
    clock_hz: int = 100_000_000
    family: str = "generic"
    part: str = "generic"
    board: str = "generic"
    reset_polarity: str = "active_low"


@dataclass(frozen=True)
class ProjectRequest:
    """A small RTL generation request."""

    task_type: str
    width: int
    project_name: str
    description: str = ""


@dataclass(frozen=True)
class GeneratedProject:
    """Generated project files keyed by POSIX-style relative path."""

    project_name: str
    files: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ToolResult:
    """Result from one external tool invocation."""

    stage: str
    command: list[str]
    status: str
    exit_code: int | None
    stdout: str
    stderr: str
    duration_seconds: float
    skip_reason: str | None = None


@dataclass(frozen=True)
class RepairResult:
    """Project returned by a repairer plus the patch used to reach it."""

    generated_project: GeneratedProject
    patch_diff: str
    patch_metadata: PatchMetadata | None = None


@dataclass(frozen=True)
class PatchMetadata:
    """Auditable metadata for one repair patch."""

    patch_id: str
    format: str
    diagnosis_id: str
    files_touched: list[str]
    allowed_edit_regions_respected: bool
    expected_effect: str
    tool_result_before: dict[str, str]
    tool_result_after: dict[str, str]
    regressions: list[str]
    touched_trusted_artifacts: bool
    status: str
    automatic_pass_credit: bool
    repair_regression: dict[str, Any] = field(default_factory=dict)
    repair_provider_resolved: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "patch_id": self.patch_id,
            "format": self.format,
            "diagnosis_id": self.diagnosis_id,
            "files_touched": self.files_touched,
            "allowed_edit_regions_respected": self.allowed_edit_regions_respected,
            "expected_effect": self.expected_effect,
            "tool_result_before": self.tool_result_before,
            "tool_result_after": self.tool_result_after,
            "regressions": self.regressions,
            "touched_trusted_artifacts": self.touched_trusted_artifacts,
            "status": self.status,
            "automatic_pass_credit": self.automatic_pass_credit,
            "repair_regression": self.repair_regression,
            "repair_provider_resolved": self.repair_provider_resolved,
        }


JsonObject = dict[str, Any]


def compact_json_text(value: Any) -> str:
    """Return sorted, separator-compact JSON text with no trailing newline."""

    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def compact_json_bytes(value: Any) -> bytes:
    """Return :func:`compact_json_text` encoded as UTF-8."""

    return compact_json_text(value).encode("utf-8")


def canonical_json_bytes(value: Any) -> bytes:
    """Return compact JSON plus the trailing newline used by stored artifacts."""

    return (compact_json_text(value) + "\n").encode("utf-8")


def sha256_json(value: Any) -> str:
    """Return the SHA-256 hex digest of the newline-free canonical encoding."""

    return hashlib.sha256(compact_json_bytes(value)).hexdigest()
