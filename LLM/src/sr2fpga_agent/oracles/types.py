"""Immutable data types for evaluator-local oracle bundles."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


SCENARIO_CLASSES = frozenset(
    {"public_smoke", "hidden_deterministic", "randomized_fixed_seed", "stress"}
)


@dataclass(frozen=True)
class OracleField:
    name: str
    msb: int
    lsb: int
    signed: bool


@dataclass(frozen=True)
class OracleScenarioSpec:
    scenario_id: str
    scenario_class: str
    seed: int
    input_record_width_bits: int
    expected_record_width_bits: int
    input_fields: tuple[OracleField, ...]
    expected_fields: tuple[OracleField, ...]
    input_records: tuple[int, ...]
    expected_records: tuple[int, ...]


@dataclass(frozen=True)
class OracleScenarioManifest:
    scenario_id: str
    scenario_class: str
    seed: int
    input_path: str
    expected_path: str
    transaction_count: int
    input_record_width_bits: int
    expected_record_width_bits: int
    input_fields: tuple[OracleField, ...]
    expected_fields: tuple[OracleField, ...]
    input_sha256: str
    expected_sha256: str


@dataclass(frozen=True)
class OracleBundle:
    root: Path
    family_id: str
    reference_model: str
    reference_version: str
    task_parameters: dict[str, object]
    scenarios: tuple[OracleScenarioManifest, ...]
    bundle_sha256: str
    manifest: dict[str, object]
