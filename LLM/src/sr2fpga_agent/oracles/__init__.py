"""Public API and family registry for independent Python-reference oracles."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from LLM.src.sr2fpga_agent.models import ProjectRequest
from LLM.src.sr2fpga_agent.oracles.bundle import (
    load_oracle_bundle,
    sanitize_oracle_profile,
    write_oracle_bundle,
)
from LLM.src.sr2fpga_agent.oracles.types import (
    SCENARIO_CLASSES,
    OracleBundle,
    OracleField,
    OracleScenarioManifest,
    OracleScenarioSpec,
)


REFERENCE_BUILDERS: dict[str, Callable[[int, Path], OracleBundle]] = {}


def build_oracle_bundle_for_request(
    family_id: str,
    request: ProjectRequest,
    output_root: Path,
) -> OracleBundle | None:
    builder = REFERENCE_BUILDERS.get(family_id)
    return None if builder is None else builder(request.width, output_root)


__all__ = [
    "REFERENCE_BUILDERS",
    "SCENARIO_CLASSES",
    "OracleBundle",
    "OracleField",
    "OracleScenarioManifest",
    "OracleScenarioSpec",
    "build_oracle_bundle_for_request",
    "load_oracle_bundle",
    "sanitize_oracle_profile",
    "write_oracle_bundle",
]
