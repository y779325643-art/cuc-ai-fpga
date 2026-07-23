"""Resolve repository-owned resources without relying on the process CWD."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


REPOSITORY_MARKER = Path("contracts") / "manifest.json"
REPOSITORY_ROOT_ENV = "SR2FPGA_REPO_ROOT"


def _has_repository_marker(candidate: Path) -> bool:
    return (candidate / REPOSITORY_MARKER).is_file()


def discover_repository_root(start: str | Path | None = None) -> Path:
    """Find the repository root from an override or an explicit source path."""

    override = os.environ.get(REPOSITORY_ROOT_ENV)
    if override:
        candidate = Path(override).expanduser().resolve()
        if not _has_repository_marker(candidate):
            raise FileNotFoundError(
                f"{REPOSITORY_ROOT_ENV}={candidate} does not contain "
                f"{REPOSITORY_MARKER.as_posix()}"
            )
        return candidate

    candidate = Path(start).resolve() if start is not None else Path(__file__).resolve()
    if candidate.is_file():
        candidate = candidate.parent

    for directory in (candidate, *candidate.parents):
        if _has_repository_marker(directory):
            return directory

    raise FileNotFoundError(
        f"could not find {REPOSITORY_MARKER.as_posix()} above {candidate}"
    )


@dataclass(frozen=True)
class RepositoryPaths:
    """Canonical repository-owned paths consumed by the Agent project."""

    root: Path

    @classmethod
    def discover(cls, start: str | Path | None = None) -> "RepositoryPaths":
        return cls(root=discover_repository_root(start))

    @property
    def contracts_dir(self) -> Path:
        return self.root / "contracts"

    @property
    def task_catalog(self) -> Path:
        return (
            self.contracts_dir
            / "task-catalog"
            / "sr2fpga-task-catalog-v0.2.json"
        )

    @property
    def agent_scripts_dir(self) -> Path:
        return self.root / "agent" / "scripts"

    @property
    def artifacts_dir(self) -> Path:
        return self.root / "artifacts"

    @property
    def reports_dir(self) -> Path:
        return self.root / "reports"

    @property
    def datasets_dir(self) -> Path:
        return self.root / "datasets"
