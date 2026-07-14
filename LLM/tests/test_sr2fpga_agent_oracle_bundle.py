import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from LLM.src.sr2fpga_agent.models import ProjectRequest
from LLM.src.sr2fpga_agent.oracles import (
    REFERENCE_BUILDERS,
    OracleBundle,
    OracleField,
    OracleScenarioSpec,
    build_oracle_bundle_for_request,
    load_oracle_bundle,
    sanitize_oracle_profile,
    write_oracle_bundle,
)


def _scenario(
    *,
    scenario_id: str = "public_smoke_001",
    scenario_class: str = "public_smoke",
    seed: int = 7,
    input_fields: tuple[OracleField, ...] | None = None,
    expected_fields: tuple[OracleField, ...] | None = None,
    input_records: tuple[int, ...] = (0x05, 0xFC),
    expected_records: tuple[int, ...] = (0x00F, 0xFEA),
) -> OracleScenarioSpec:
    return OracleScenarioSpec(
        scenario_id=scenario_id,
        scenario_class=scenario_class,
        seed=seed,
        input_record_width_bits=8,
        expected_record_width_bits=12,
        input_fields=input_fields or (OracleField("sample", 7, 0, True),),
        expected_fields=expected_fields or (OracleField("result", 11, 0, True),),
        input_records=input_records,
        expected_records=expected_records,
    )


def _write_bundle(tmp_path: Path, scenarios: tuple[OracleScenarioSpec, ...] | None = None) -> OracleBundle:
    return write_oracle_bundle(
        root=tmp_path / "oracle",
        family_id="fir_filter",
        reference_model="numeric.fir_filter",
        reference_version="1",
        task_parameters={"width": 8},
        scenarios=scenarios or (_scenario(),),
    )


def test_bundle_round_trip_uses_relative_paths_and_fixed_width_memh(tmp_path):
    bundle = _write_bundle(tmp_path)

    loaded = load_oracle_bundle(bundle.root)

    assert loaded.manifest["schema_version"] == "sr2fpga-oracle-bundle-v1"
    assert loaded.manifest["family_id"] == "fir_filter"
    assert loaded.scenarios[0].input_path == "public/public_smoke_001/input.memh"
    assert loaded.scenarios[0].expected_path == "public/public_smoke_001/expected.memh"
    assert (bundle.root / loaded.scenarios[0].input_path).read_text(encoding="ascii") == "05\nfc\n"
    assert (bundle.root / loaded.scenarios[0].expected_path).read_text(encoding="ascii") == "00f\nfea\n"
    assert loaded.scenarios[0].input_sha256
    assert loaded.scenarios[0].expected_sha256
    assert loaded.bundle_sha256 == bundle.bundle_sha256


def test_oracle_types_are_immutable():
    field = OracleField("sample", 7, 0, True)

    with pytest.raises(FrozenInstanceError):
        field.name = "changed"


@pytest.mark.parametrize(
    ("scenario_class", "directory"),
    (
        ("public_smoke", "public"),
        ("hidden_deterministic", "hidden"),
        ("randomized_fixed_seed", "randomized"),
        ("stress", "stress"),
    ),
)
def test_bundle_maps_supported_scenario_classes_to_stable_directories(
    tmp_path,
    scenario_class,
    directory,
):
    scenario = _scenario(
        scenario_id=f"{scenario_class}_001",
        scenario_class=scenario_class,
    )

    bundle = _write_bundle(tmp_path, (scenario,))

    assert bundle.scenarios[0].input_path == f"{directory}/{scenario.scenario_id}/input.memh"


def test_write_rejects_unsupported_scenario_class(tmp_path):
    with pytest.raises(ValueError, match="unsupported oracle scenario class"):
        _write_bundle(tmp_path, (_scenario(scenario_class="private"),))


def test_write_rejects_duplicate_scenario_ids(tmp_path):
    with pytest.raises(ValueError, match="duplicate oracle scenario id"):
        _write_bundle(
            tmp_path,
            (
                _scenario(),
                _scenario(scenario_class="stress", seed=11),
            ),
        )


def test_write_rejects_overlapping_field_ranges(tmp_path):
    fields = (
        OracleField("low", 5, 0, False),
        OracleField("high", 7, 4, False),
    )

    with pytest.raises(ValueError, match="overlapping oracle field ranges"):
        _write_bundle(tmp_path, (_scenario(input_fields=fields),))


@pytest.mark.parametrize(
    ("input_records", "expected_records"),
    (
        ((0x100,), (0x001,)),
        ((0x01,), (0x1000,)),
    ),
)
def test_write_rejects_records_wider_than_declared_width(
    tmp_path,
    input_records,
    expected_records,
):
    with pytest.raises(ValueError, match="fit the declared unsigned bit pattern"):
        _write_bundle(
            tmp_path,
            (_scenario(input_records=input_records, expected_records=expected_records),),
        )


def test_write_rejects_zero_transactions(tmp_path):
    with pytest.raises(ValueError, match="at least one transaction"):
        _write_bundle(
            tmp_path,
            (_scenario(input_records=(), expected_records=()),),
        )


def test_write_rejects_different_input_and_expected_record_counts(tmp_path):
    with pytest.raises(ValueError, match="record counts must match"):
        _write_bundle(
            tmp_path,
            (_scenario(input_records=(0x01,), expected_records=(0x001, 0x002)),),
        )


@pytest.mark.parametrize("unsafe_path", ("../escape.memh", "C:/escape.memh", "/escape.memh"))
def test_load_rejects_paths_outside_bundle_root(tmp_path, unsafe_path):
    bundle = _write_bundle(tmp_path)
    manifest_path = bundle.root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["scenarios"][0]["input_path"] = unsafe_path
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="bundle-relative path"):
        load_oracle_bundle(bundle.root)


def test_load_rejects_missing_record_file(tmp_path):
    bundle = _write_bundle(tmp_path)
    (bundle.root / bundle.scenarios[0].expected_path).unlink()

    with pytest.raises(ValueError, match="missing oracle record file"):
        load_oracle_bundle(bundle.root)


def test_load_rejects_modified_record_file(tmp_path):
    bundle = _write_bundle(tmp_path)
    (bundle.root / bundle.scenarios[0].input_path).write_text("00\n", encoding="ascii")

    with pytest.raises(ValueError, match="oracle record hash mismatch"):
        load_oracle_bundle(bundle.root)


def test_load_rejects_modified_manifest_bundle_hash(tmp_path):
    bundle = _write_bundle(tmp_path)
    manifest_path = bundle.root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["task_parameters"]["width"] = 16
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="oracle bundle hash mismatch"):
        load_oracle_bundle(bundle.root)


def test_load_rejects_malformed_json(tmp_path):
    root = tmp_path / "oracle"
    root.mkdir()
    (root / "manifest.json").write_text("{not-json", encoding="utf-8")

    with pytest.raises(ValueError, match="malformed oracle manifest JSON"):
        load_oracle_bundle(root)


def test_sanitize_oracle_profile_hides_withheld_seed_paths_and_payloads(tmp_path):
    public = _scenario()
    hidden = _scenario(
        scenario_id="hidden_boundary_001",
        scenario_class="hidden_deterministic",
        seed=101,
    )
    bundle = _write_bundle(tmp_path, (public, hidden))

    profile = sanitize_oracle_profile(bundle)
    hidden_profile = next(
        scenario
        for scenario in profile["scenarios"]
        if scenario["scenario_id"] == "hidden_boundary_001"
    )

    assert "seed" not in hidden_profile
    assert len(hidden_profile["seed_sha256"]) == 64
    assert "input_path" not in hidden_profile
    assert "expected_path" not in hidden_profile
    assert "input_records" not in hidden_profile
    assert "expected_records" not in hidden_profile
    assert hidden_profile["transaction_count"] == 2


def test_reference_builder_registry_starts_empty_for_unknown_family(tmp_path):
    request = ProjectRequest(task_type="counter", width=8, project_name="counter_8")

    assert build_oracle_bundle_for_request("unknown_family", request, tmp_path) is None


def test_reference_builder_registry_passes_request_width_and_output_root(tmp_path):
    request = ProjectRequest(task_type="fir_filter", width=12, project_name="fir_12")
    expected = _write_bundle(tmp_path)
    calls = []

    def builder(width, output_root):
        calls.append((width, output_root))
        return expected

    REFERENCE_BUILDERS["test_family"] = builder
    try:
        actual = build_oracle_bundle_for_request("test_family", request, tmp_path / "target")
    finally:
        REFERENCE_BUILDERS.pop("test_family", None)

    assert actual is expected
    assert calls == [(12, tmp_path / "target")]
