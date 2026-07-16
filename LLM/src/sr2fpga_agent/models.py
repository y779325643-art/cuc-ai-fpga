"""Shared data models for the SR2FPGA data generation agent."""

from __future__ import annotations

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
        }


JsonObject = dict[str, Any]
