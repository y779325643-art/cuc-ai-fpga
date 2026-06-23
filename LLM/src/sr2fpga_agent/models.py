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


JsonObject = dict[str, Any]
