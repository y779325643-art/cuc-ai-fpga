"""Serialization and strict validation for independent oracle bundles."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

from LLM.src.sr2fpga_agent.oracles.types import (
    SCENARIO_CLASSES,
    OracleBundle,
    OracleField,
    OracleScenarioManifest,
    OracleScenarioSpec,
)


SCHEMA_VERSION = "sr2fpga-oracle-bundle-v1"
_SCENARIO_DIRECTORIES = {
    "public_smoke": "public",
    "hidden_deterministic": "hidden",
    "randomized_fixed_seed": "randomized",
    "stress": "stress",
}
_SCENARIO_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
_WINDOWS_RESERVED_NAMES = frozenset(
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{index}" for index in range(1, 10)}
    | {f"LPT{index}" for index in range(1, 10)}
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_TOP_LEVEL_KEYS = {
    "schema_version",
    "family_id",
    "reference_model",
    "reference_version",
    "task_parameters",
    "scenarios",
    "bundle_sha256",
}
_SCENARIO_KEYS = {
    "scenario_id",
    "scenario_class",
    "seed",
    "input_path",
    "expected_path",
    "transaction_count",
    "input_record_width_bits",
    "expected_record_width_bits",
    "input_fields",
    "expected_fields",
    "input_sha256",
    "expected_sha256",
}
_FIELD_KEYS = {"name", "msb", "lsb", "signed"}


def _canonical_json(value: object) -> bytes:
    try:
        text = json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except ValueError as exc:
        raise ValueError("oracle manifest values must contain only finite JSON values") from exc
    except TypeError as exc:
        raise ValueError("oracle manifest values must be JSON serializable") from exc
    return text.encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _bundle_hash(manifest: dict[str, object]) -> str:
    payload = dict(manifest)
    payload.pop("bundle_sha256", None)
    return _sha256(_canonical_json(payload))


def _memh_text(records: tuple[int, ...], width: int) -> str:
    _validate_records(records, width)
    digits = (width + 3) // 4
    return "".join(f"{record:0{digits}x}\n" for record in records)


def _validate_records(records: tuple[int, ...], width: int) -> None:
    if not _is_int(width) or width <= 0:
        raise ValueError("oracle record width must be a positive integer")
    if not isinstance(records, tuple) or not records:
        raise ValueError("oracle scenario must contain at least one transaction")
    limit = 1 << width
    if any(not _is_int(record) or record < 0 or record >= limit for record in records):
        raise ValueError("oracle records must fit the declared unsigned bit pattern")


def _safe_bundle_path(root: Path, relative_path: str) -> Path:
    if not isinstance(relative_path, str) or not relative_path:
        raise ValueError("oracle record path must be a normalized bundle-relative path")
    if "\\" in relative_path:
        raise ValueError("oracle record path must be a normalized bundle-relative path")
    posix_path = PurePosixPath(relative_path)
    windows_path = PureWindowsPath(relative_path)
    raw_parts = relative_path.split("/")
    if (
        posix_path.is_absolute()
        or windows_path.is_absolute()
        or windows_path.drive
        or any(part in {"", ".", ".."} for part in raw_parts)
        or posix_path.as_posix() != relative_path
    ):
        raise ValueError("oracle record path must be a normalized bundle-relative path")
    candidate = (root / Path(*posix_path.parts)).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError("oracle record path must be a normalized bundle-relative path") from exc
    return candidate


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _require_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{label} must be a non-empty trimmed string")
    return value


def _validate_scenario_id(value: object) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError("oracle scenario id must be Windows-portable")
    scenario_id = value
    basename = scenario_id.split(".", 1)[0].upper()
    if (
        not _SCENARIO_ID_RE.fullmatch(scenario_id)
        or scenario_id.endswith((".", " "))
        or basename in _WINDOWS_RESERVED_NAMES
    ):
        raise ValueError("oracle scenario id must be Windows-portable")
    return scenario_id


def _validate_scenario_class(value: object) -> str:
    if value not in SCENARIO_CLASSES:
        raise ValueError(f"unsupported oracle scenario class: {value}")
    return str(value)


def _validate_width(value: object, label: str) -> int:
    if not _is_int(value) or int(value) <= 0:
        raise ValueError(f"{label} must be a positive integer")
    return int(value)


def _validate_seed(value: object) -> int:
    if not _is_int(value) or int(value) < 0:
        raise ValueError("oracle seed must be a non-negative integer")
    return int(value)


def _validate_fields(
    fields: tuple[OracleField, ...],
    record_width_bits: int,
    label: str,
) -> None:
    if not fields:
        raise ValueError(f"{label} must declare at least one oracle field")
    names: set[str] = set()
    for field in fields:
        if not isinstance(field, OracleField):
            raise ValueError(f"{label} entries must be OracleField values")
        _require_string(field.name, "oracle field name")
        if field.name in names:
            raise ValueError(f"duplicate oracle field name: {field.name}")
        names.add(field.name)
        if not _is_int(field.msb) or not _is_int(field.lsb):
            raise ValueError("oracle field bounds must be integers")
        if field.lsb < 0 or field.msb < field.lsb or field.msb >= record_width_bits:
            raise ValueError("oracle field range must fit the declared record width")
        if not isinstance(field.signed, bool):
            raise ValueError("oracle field signed flag must be boolean")
    fields_by_range = sorted(fields, key=lambda field: (field.lsb, field.msb))
    for previous, current in zip(fields_by_range, fields_by_range[1:]):
        if current.lsb <= previous.msb:
            raise ValueError("overlapping oracle field ranges")


def _field_dict(field: OracleField) -> dict[str, object]:
    return {
        "name": field.name,
        "msb": field.msb,
        "lsb": field.lsb,
        "signed": field.signed,
    }


def _field_from_dict(value: object, label: str) -> OracleField:
    if not isinstance(value, dict) or set(value) != _FIELD_KEYS:
        raise ValueError(f"{label} must contain exactly name, msb, lsb, and signed")
    return OracleField(
        name=value["name"],
        msb=value["msb"],
        lsb=value["lsb"],
        signed=value["signed"],
    )


def _validate_spec(scenario: OracleScenarioSpec) -> None:
    if not isinstance(scenario, OracleScenarioSpec):
        raise ValueError("oracle scenarios must be OracleScenarioSpec values")
    _validate_scenario_id(scenario.scenario_id)
    _validate_scenario_class(scenario.scenario_class)
    _validate_seed(scenario.seed)
    input_width = _validate_width(
        scenario.input_record_width_bits,
        "oracle input record width",
    )
    expected_width = _validate_width(
        scenario.expected_record_width_bits,
        "oracle expected record width",
    )
    _validate_fields(scenario.input_fields, input_width, "input_fields")
    _validate_fields(scenario.expected_fields, expected_width, "expected_fields")
    if not scenario.input_records or not scenario.expected_records:
        raise ValueError("oracle scenario must contain at least one transaction")
    if len(scenario.input_records) != len(scenario.expected_records):
        raise ValueError("oracle input and expected record counts must match")
    _validate_records(scenario.input_records, input_width)
    _validate_records(scenario.expected_records, expected_width)


def write_oracle_bundle(
    *,
    root: Path,
    family_id: str,
    reference_model: str,
    reference_version: str,
    task_parameters: dict[str, object],
    scenarios: tuple[OracleScenarioSpec, ...],
) -> OracleBundle:
    """Write an evaluator-local oracle bundle and return its validated form."""

    root = Path(root)
    _require_string(family_id, "oracle family_id")
    _require_string(reference_model, "oracle reference_model")
    _require_string(reference_version, "oracle reference_version")
    if not isinstance(task_parameters, dict):
        raise ValueError("oracle task_parameters must be an object")
    _canonical_json(task_parameters)
    if not isinstance(scenarios, tuple) or not scenarios:
        raise ValueError("oracle bundle must contain at least one scenario")

    scenario_ids: set[str] = set()
    for scenario in scenarios:
        _validate_spec(scenario)
        scenario_key = scenario.scenario_id.casefold()
        if scenario_key in scenario_ids:
            raise ValueError(
                f"case-insensitive duplicate oracle scenario id: {scenario.scenario_id}"
            )
        scenario_ids.add(scenario_key)

    root.mkdir(parents=True, exist_ok=True)
    scenario_entries: list[dict[str, object]] = []
    for scenario in scenarios:
        directory = _SCENARIO_DIRECTORIES[scenario.scenario_class]
        scenario_root = root / directory / scenario.scenario_id
        scenario_root.mkdir(parents=True, exist_ok=True)
        input_text = _memh_text(
            scenario.input_records,
            scenario.input_record_width_bits,
        )
        expected_text = _memh_text(
            scenario.expected_records,
            scenario.expected_record_width_bits,
        )
        input_path = f"{directory}/{scenario.scenario_id}/input.memh"
        expected_path = f"{directory}/{scenario.scenario_id}/expected.memh"
        input_bytes = input_text.encode("ascii")
        expected_bytes = expected_text.encode("ascii")
        (scenario_root / "input.memh").write_bytes(input_bytes)
        (scenario_root / "expected.memh").write_bytes(expected_bytes)
        scenario_entries.append(
            {
                "scenario_id": scenario.scenario_id,
                "scenario_class": scenario.scenario_class,
                "seed": scenario.seed,
                "input_path": input_path,
                "expected_path": expected_path,
                "transaction_count": len(scenario.input_records),
                "input_record_width_bits": scenario.input_record_width_bits,
                "expected_record_width_bits": scenario.expected_record_width_bits,
                "input_fields": [_field_dict(field) for field in scenario.input_fields],
                "expected_fields": [_field_dict(field) for field in scenario.expected_fields],
                "input_sha256": _sha256(input_bytes),
                "expected_sha256": _sha256(expected_bytes),
            }
        )

    manifest: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "family_id": family_id,
        "reference_model": reference_model,
        "reference_version": reference_version,
        "task_parameters": task_parameters,
        "scenarios": scenario_entries,
    }
    manifest["bundle_sha256"] = _bundle_hash(manifest)
    (root / "manifest.json").write_text(
        json.dumps(
            manifest,
            indent=2,
            allow_nan=False,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return load_oracle_bundle(root)


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate key in oracle manifest: {key}")
        value[key] = item
    return value


def _reject_nonfinite_number(value: str) -> object:
    raise ValueError(f"non-finite number in oracle manifest: {value}")


def _read_manifest(root: Path) -> dict[str, object]:
    try:
        raw = (root / "manifest.json").read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ValueError("missing or unreadable oracle manifest") from exc
    try:
        manifest = json.loads(
            raw,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_nonfinite_number,
        )
    except json.JSONDecodeError as exc:
        raise ValueError("malformed oracle manifest JSON") from exc
    if not isinstance(manifest, dict):
        raise ValueError("oracle manifest must be a JSON object")
    if set(manifest) != _TOP_LEVEL_KEYS:
        raise ValueError("oracle manifest has missing or unsupported top-level fields")
    return manifest


def _read_record_file(
    root: Path,
    relative_path: str,
    expected_sha256: str,
    transaction_count: int,
    record_width_bits: int,
) -> None:
    path = _safe_bundle_path(root, relative_path)
    if not path.is_file():
        raise ValueError(f"missing oracle record file: {relative_path}")
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise ValueError(f"unreadable oracle record file: {relative_path}") from exc
    if _sha256(data) != expected_sha256:
        raise ValueError(f"oracle record hash mismatch: {relative_path}")
    try:
        lines = data.decode("ascii").splitlines()
    except UnicodeDecodeError as exc:
        raise ValueError(f"oracle record file must be ASCII: {relative_path}") from exc
    digits = (record_width_bits + 3) // 4
    record_re = re.compile(rf"^[0-9a-f]{{{digits}}}$")
    if len(lines) != transaction_count or any(not record_re.fullmatch(line) for line in lines):
        raise ValueError(f"oracle record file has invalid fixed-width memh data: {relative_path}")
    limit = 1 << record_width_bits
    if any(int(line, 16) >= limit for line in lines):
        raise ValueError(f"oracle record exceeds its declared record width: {relative_path}")


def _scenario_from_dict(root: Path, value: object) -> OracleScenarioManifest:
    if not isinstance(value, dict) or set(value) != _SCENARIO_KEYS:
        raise ValueError("oracle scenario has missing or unsupported fields")
    scenario_id = _validate_scenario_id(value["scenario_id"])
    scenario_class = _validate_scenario_class(value["scenario_class"])
    seed = _validate_seed(value["seed"])
    transaction_count = value["transaction_count"]
    if not _is_int(transaction_count) or transaction_count <= 0:
        raise ValueError("oracle scenario must contain at least one transaction")
    input_width = _validate_width(value["input_record_width_bits"], "oracle input record width")
    expected_width = _validate_width(
        value["expected_record_width_bits"],
        "oracle expected record width",
    )
    if not isinstance(value["input_fields"], list) or not isinstance(value["expected_fields"], list):
        raise ValueError("oracle scenario field layouts must be arrays")
    input_fields = tuple(
        _field_from_dict(field, "input field") for field in value["input_fields"]
    )
    expected_fields = tuple(
        _field_from_dict(field, "expected field") for field in value["expected_fields"]
    )
    _validate_fields(input_fields, input_width, "input_fields")
    _validate_fields(expected_fields, expected_width, "expected_fields")

    input_path = value["input_path"]
    expected_path = value["expected_path"]
    _safe_bundle_path(root, input_path)
    _safe_bundle_path(root, expected_path)
    directory = _SCENARIO_DIRECTORIES[scenario_class]
    canonical_input_path = f"{directory}/{scenario_id}/input.memh"
    canonical_expected_path = f"{directory}/{scenario_id}/expected.memh"
    if input_path != canonical_input_path or expected_path != canonical_expected_path:
        raise ValueError("oracle scenario record path must equal its canonical path")
    input_sha256 = value["input_sha256"]
    expected_sha256 = value["expected_sha256"]
    if not isinstance(input_sha256, str) or not _SHA256_RE.fullmatch(input_sha256):
        raise ValueError("oracle input_sha256 must be a lowercase SHA-256 digest")
    if not isinstance(expected_sha256, str) or not _SHA256_RE.fullmatch(expected_sha256):
        raise ValueError("oracle expected_sha256 must be a lowercase SHA-256 digest")
    _read_record_file(root, input_path, input_sha256, transaction_count, input_width)
    _read_record_file(root, expected_path, expected_sha256, transaction_count, expected_width)

    return OracleScenarioManifest(
        scenario_id=scenario_id,
        scenario_class=scenario_class,
        seed=seed,
        input_path=input_path,
        expected_path=expected_path,
        transaction_count=transaction_count,
        input_record_width_bits=input_width,
        expected_record_width_bits=expected_width,
        input_fields=input_fields,
        expected_fields=expected_fields,
        input_sha256=input_sha256,
        expected_sha256=expected_sha256,
    )


def load_oracle_bundle(root: Path) -> OracleBundle:
    """Load a bundle only after validating its manifest, files, and hashes."""

    root = Path(root)
    manifest = _read_manifest(root)
    if manifest["schema_version"] != SCHEMA_VERSION:
        raise ValueError(f"unsupported oracle bundle schema: {manifest['schema_version']}")
    family_id = _require_string(manifest["family_id"], "oracle family_id")
    reference_model = _require_string(manifest["reference_model"], "oracle reference_model")
    reference_version = _require_string(manifest["reference_version"], "oracle reference_version")
    task_parameters = manifest["task_parameters"]
    if not isinstance(task_parameters, dict):
        raise ValueError("oracle task_parameters must be an object")
    _canonical_json(task_parameters)
    raw_scenarios = manifest["scenarios"]
    if not isinstance(raw_scenarios, list) or not raw_scenarios:
        raise ValueError("oracle bundle must contain at least one scenario")
    scenarios = tuple(_scenario_from_dict(root, item) for item in raw_scenarios)
    scenario_ids = [scenario.scenario_id.casefold() for scenario in scenarios]
    if len(scenario_ids) != len(set(scenario_ids)):
        raise ValueError("case-insensitive duplicate oracle scenario id in manifest")
    bundle_sha256 = manifest["bundle_sha256"]
    if not isinstance(bundle_sha256, str) or not _SHA256_RE.fullmatch(bundle_sha256):
        raise ValueError("oracle bundle_sha256 must be a lowercase SHA-256 digest")
    if _bundle_hash(manifest) != bundle_sha256:
        raise ValueError("oracle bundle hash mismatch")
    return OracleBundle(
        root=root,
        family_id=family_id,
        reference_model=reference_model,
        reference_version=reference_version,
        task_parameters=dict(task_parameters),
        scenarios=scenarios,
        bundle_sha256=bundle_sha256,
        manifest=manifest,
    )


def sanitize_oracle_profile(bundle: OracleBundle) -> dict[str, Any]:
    """Return publishable metadata without seeds, paths, or vector payloads."""

    scenario_counts = {scenario_class: 0 for scenario_class in sorted(SCENARIO_CLASSES)}
    scenarios: list[dict[str, object]] = []
    for scenario in bundle.scenarios:
        scenario_counts[scenario.scenario_class] += 1
        scenario_profile: dict[str, object] = {
            "scenario_id": scenario.scenario_id,
            "scenario_class": scenario.scenario_class,
            "seed_sha256": _sha256(
                f"sr2fpga-oracle-seed-v1:{scenario.seed}".encode("ascii")
            ),
            "transaction_count": scenario.transaction_count,
            "input_record_width_bits": scenario.input_record_width_bits,
            "expected_record_width_bits": scenario.expected_record_width_bits,
            "input_fields": [_field_dict(field) for field in scenario.input_fields],
            "expected_fields": [_field_dict(field) for field in scenario.expected_fields],
        }
        if scenario.scenario_class == "public_smoke":
            scenario_profile.update(
                {
                    "input_sha256": scenario.input_sha256,
                    "expected_sha256": scenario.expected_sha256,
                }
            )
        scenarios.append(scenario_profile)
    return {
        "kind": "python_reference",
        "family_id": bundle.family_id,
        "reference_model": bundle.reference_model,
        "reference_version": bundle.reference_version,
        "bundle_sha256": bundle.bundle_sha256,
        "scenario_counts": scenario_counts,
        "scenarios": scenarios,
        "hidden_vectors_exported": False,
    }
