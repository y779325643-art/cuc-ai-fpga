from __future__ import annotations

import json
from pathlib import Path
import shutil

import pytest

from sr2fpga_agent.failure_injector import oracle_mutation_projects
from sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest
from sr2fpga_agent.oracle_runner import run_oracle_scenarios
from sr2fpga_agent.oracles import REFERENCE_BUILDERS
from sr2fpga_agent.oracles.signal import (
    MATCHED_TEMPLATE,
    build_matched_filter_bundle,
    build_peak_detector_bundle,
    build_pulse_radar_bundle,
    detect_peak,
    matched_filter_outputs,
    pulse_radar,
)
from sr2fpga_agent.project_generator import ProjectGenerator
from sr2fpga_agent.tool_runner import CommandRunner


SCENARIO_CLASSES = {
    "public_smoke",
    "hidden_deterministic",
    "randomized_fixed_seed",
    "stress",
}


def test_matched_filter_known_reversed_pulse_and_negative_correlation() -> None:
    assert MATCHED_TEMPLATE == (-1, 2, -3, 4)
    assert matched_filter_outputs([4, -3, 2, -1], width=8) == [-4, 11, -20, 30]
    assert matched_filter_outputs([4], width=8) == [-4]


def test_peak_detector_threshold_first_tie_empty_and_final_sample() -> None:
    assert detect_peak([11, 16, 16, 14], threshold=10) == (1, 16, 1)
    assert detect_peak([-3, 0, 9], threshold=10) == (0, 0, 0)
    assert detect_peak([9, 10], threshold=10) == (1, 10, 1)
    assert detect_peak([11, 14, 19], threshold=10) == (1, 19, 2)


def test_pulse_radar_correlates_every_sample_before_frame_peak() -> None:
    assert pulse_radar([4, -3, 2, -1], width=8, threshold=10) == (1, 30, 3)
    assert pulse_radar([4], width=8, threshold=10) == (0, 0, 0)
    assert pulse_radar([-10], width=8, threshold=10) == (1, 10, 0)


@pytest.mark.parametrize(
    ("family_id", "builder", "input_width", "expected_width", "input_layout", "expected_layout"),
    [
        (
            "matched_filter",
            build_matched_filter_bundle,
            11,
            18,
            [
                ("sample", 7, 0, True),
                ("reset_before", 8, 8, False),
                ("stall_cycles", 10, 9, False),
            ],
            [("correlation", 17, 0, True)],
        ),
        (
            "peak_detector",
            build_peak_detector_bundle,
            12,
            18,
            [
                ("sample", 7, 0, True),
                ("in_last", 8, 8, False),
                ("reset_before", 9, 9, False),
                ("stall_cycles", 11, 10, False),
            ],
            [
                ("value", 7, 0, True),
                ("index", 15, 8, False),
                ("found", 16, 16, False),
                ("expect_output", 17, 17, False),
            ],
        ),
        (
            "p_pulse_radar_signal",
            build_pulse_radar_bundle,
            12,
            38,
            [
                ("sample", 7, 0, True),
                ("in_last", 8, 8, False),
                ("reset_before", 9, 9, False),
                ("stall_cycles", 11, 10, False),
            ],
            [
                ("value", 17, 0, True),
                ("index", 35, 18, False),
                ("found", 36, 36, False),
                ("expect_output", 37, 37, False),
            ],
        ),
    ],
)
def test_signal_bundle_has_four_classes_and_exact_layout(
    tmp_path: Path,
    family_id: str,
    builder,
    input_width: int,
    expected_width: int,
    input_layout: list[tuple[str, int, int, bool]],
    expected_layout: list[tuple[str, int, int, bool]],
) -> None:
    bundle = builder(8, tmp_path / family_id)

    assert bundle.family_id == family_id
    assert bundle.reference_model == "python_signal_reference"
    assert {scenario.scenario_class for scenario in bundle.scenarios} == SCENARIO_CLASSES
    assert len(bundle.scenarios) == 4
    for scenario in bundle.scenarios:
        assert scenario.transaction_count > 0
        assert scenario.input_record_width_bits == input_width
        assert scenario.expected_record_width_bits == expected_width
        assert [
            (field.name, field.msb, field.lsb, field.signed)
            for field in scenario.input_fields
        ] == input_layout
        assert [
            (field.name, field.msb, field.lsb, field.signed)
            for field in scenario.expected_fields
        ] == expected_layout


@pytest.mark.parametrize(
    ("family_id", "builder"),
    [
        ("matched_filter", build_matched_filter_bundle),
        ("peak_detector", build_peak_detector_bundle),
        ("p_pulse_radar_signal", build_pulse_radar_bundle),
    ],
)
def test_signal_bundle_is_deterministic_and_contains_reset_stall_and_withheld_seeds(
    tmp_path: Path,
    family_id: str,
    builder,
) -> None:
    first = builder(8, tmp_path / "first")
    second = builder(8, tmp_path / "second")

    assert first.bundle_sha256 == second.bundle_sha256
    assert first.manifest == second.manifest
    assert REFERENCE_BUILDERS[family_id] is builder
    stress = next(item for item in first.scenarios if item.scenario_class == "stress")
    records = _read_memh(first.root / stress.input_path)
    reset_bit = 8 if family_id == "matched_filter" else 9
    stall_lsb = 9 if family_id == "matched_filter" else 10
    assert any((record >> reset_bit) & 1 for record in records)
    assert any((record >> stall_lsb) & 0b11 for record in records)
    assert stress.seed.bit_length() >= 120


def test_signal_bundles_encode_reset_history_final_sample_and_first_tie(tmp_path: Path) -> None:
    matched = build_matched_filter_bundle(8, tmp_path / "matched")
    matched_stress = next(item for item in matched.scenarios if item.scenario_class == "stress")
    matched_inputs = _read_memh(matched.root / matched_stress.input_path)
    matched_expected = _read_memh(matched.root / matched_stress.expected_path)
    reset_positions = [index for index, record in enumerate(matched_inputs) if (record >> 8) & 1]
    assert len(reset_positions) >= 2
    for index in reset_positions:
        sample = _signed(matched_inputs[index] & 0xFF, 8)
        assert _signed(matched_expected[index], 18) == -sample

    peak = build_peak_detector_bundle(8, tmp_path / "peak")
    public = next(item for item in peak.scenarios if item.scenario_class == "public_smoke")
    peak_expected = _read_memh(peak.root / public.expected_path)
    outputs = [_unpack_peak(record, 8) for record in peak_expected]
    qualified = [tuple(value) for expected, *value in outputs if expected]
    assert (1, 16, 1) in qualified
    assert (1, 19, 2) in qualified
    assert (0, 0, 0) in qualified

    radar = build_pulse_radar_bundle(8, tmp_path / "radar")
    radar_public = next(item for item in radar.scenarios if item.scenario_class == "public_smoke")
    radar_outputs = [
        _unpack_peak(record, 18)
        for record in _read_memh(radar.root / radar_public.expected_path)
    ]
    assert (1, 30, 3) in [tuple(value) for expected, *value in radar_outputs if expected]


def test_pulse_radar_stall_probe_participates_once_in_followup_frame(tmp_path: Path) -> None:
    radar = build_pulse_radar_bundle(8, tmp_path / "radar")
    stress = next(item for item in radar.scenarios if item.scenario_class == "stress")
    expected = [
        _unpack_peak(record, 18)
        for record in _read_memh(radar.root / stress.expected_path)
    ]

    assert expected[3] == (1, 1, 18, 1)


def test_generated_signal_testbenches_keep_legacy_and_add_oracle_mode() -> None:
    platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
    for task_type in ("matched_filter", "peak_detector", "pulse_radar_signal"):
        project = ProjectGenerator().generate(
            ProjectRequest(task_type=task_type, width=8, project_name=task_type),
            platform,
        )
        testbench = project.files["sim/tb_top.v"]
        assert '$value$plusargs("ORACLE_INPUT=%s"' in testbench
        assert '$readmemh(oracle_input_path' in testbench
        assert "ORACLE_EXPECTED" in testbench
        assert "ORACLE_TRANSACTION_COUNT" in testbench
        assert "SR2FPGA_MISMATCH" in testbench
        assert "result changed under backpressure" in testbench or "correlation changed under backpressure" in testbench
        assert '$display("TEST_PASS")' in testbench


@pytest.mark.skipif(
    not shutil.which("iverilog") or not shutil.which("vvp"),
    reason="iverilog/vvp are not installed",
)
@pytest.mark.parametrize(
    ("task_type", "family_id", "builder"),
    [
        ("matched_filter", "matched_filter", build_matched_filter_bundle),
        ("peak_detector", "peak_detector", build_peak_detector_bundle),
        ("pulse_radar_signal", "p_pulse_radar_signal", build_pulse_radar_bundle),
    ],
)
def test_signal_reference_and_all_declared_mutations_are_scoreable(
    tmp_path: Path,
    task_type: str,
    family_id: str,
    builder,
) -> None:
    platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
    reference = ProjectGenerator().generate(
        ProjectRequest(task_type=task_type, width=8, project_name=task_type),
        platform,
    )
    bundle = builder(8, tmp_path / "oracle" / family_id)

    reference_compile, reference_evidence = _compile_and_run(
        reference,
        tmp_path / "reference" / family_id,
        bundle,
    )
    assert reference_compile == "passed"
    assert reference_evidence == "passed"

    mutations = oracle_mutation_projects(reference, family_id)
    assert mutations
    for mutation_name, mutation in mutations.items():
        assert mutation is not None, mutation_name
        compile_status, evidence_status = _compile_and_run(
            mutation,
            tmp_path / "mutations" / family_id / mutation_name,
            bundle,
        )
        assert (compile_status, evidence_status) != ("passed", "passed"), mutation_name


@pytest.mark.skipif(
    not shutil.which("iverilog") or not shutil.which("vvp") or not shutil.which("verilator"),
    reason="iverilog/vvp/verilator are not installed",
)
def test_pulse_radar_top_ready_stuck_high_mutation_is_killed(tmp_path: Path) -> None:
    platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
    reference = ProjectGenerator().generate(
        ProjectRequest(
            task_type="pulse_radar_signal",
            width=8,
            project_name="pulse_radar_ready_stuck_high",
        ),
        platform,
    )
    mutation = oracle_mutation_projects(reference, "p_pulse_radar_signal").get(
        "top_in_ready_stuck_high"
    )
    assert mutation is not None
    assert _lint_project(mutation, tmp_path / "mutation") == "passed"

    bundle = build_pulse_radar_bundle(8, tmp_path / "oracle")
    compile_status, evidence_status = _compile_and_run(
        mutation,
        tmp_path / "mutation",
        bundle,
    )

    assert compile_status == "passed"
    assert evidence_status == "failed"


@pytest.mark.skipif(
    not shutil.which("iverilog") or not shutil.which("vvp") or not shutil.which("verilator"),
    reason="iverilog/vvp/verilator are not installed",
)
def test_pulse_radar_history_update_while_stalled_mutation_is_killed(tmp_path: Path) -> None:
    platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
    reference = ProjectGenerator().generate(
        ProjectRequest(
            task_type="pulse_radar_signal",
            width=8,
            project_name="pulse_radar_history_stall",
        ),
        platform,
    )
    mutation = oracle_mutation_projects(reference, "p_pulse_radar_signal").get(
        "history_updates_while_stalled"
    )
    assert mutation is not None
    assert _lint_project(mutation, tmp_path / "mutation") == "passed"

    bundle = build_pulse_radar_bundle(8, tmp_path / "oracle")
    compile_status, evidence_status = _compile_and_run(
        mutation,
        tmp_path / "mutation",
        bundle,
    )

    assert compile_status == "passed"
    assert evidence_status == "failed"


def _read_memh(path: Path) -> list[int]:
    return [int(line, 16) for line in path.read_text(encoding="ascii").splitlines()]


def _signed(value: int, width: int) -> int:
    value &= (1 << width) - 1
    return value - (1 << width) if value & (1 << (width - 1)) else value


def _unpack_peak(record: int, value_width: int) -> tuple[int, int, int, int]:
    value = _signed(record, value_width)
    index = (record >> value_width) & ((1 << value_width) - 1)
    found = (record >> (2 * value_width)) & 1
    expect_output = (record >> (2 * value_width + 1)) & 1
    return expect_output, found, value, index


def _compile_and_run(
    project: GeneratedProject,
    project_dir: Path,
    bundle,
) -> tuple[str, str]:
    project_dir.mkdir(parents=True, exist_ok=True)
    for relative_path, source in project.files.items():
        destination = project_dir / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(source, encoding="utf-8")
    manifest = json.loads(project.files["manifest.json"])
    runner = CommandRunner()
    compile_result = runner.run(
        [
            "iverilog",
            "-g2012",
            "-o",
            "sim.out",
            *manifest["sources"],
            manifest["simulation"]["testbench"],
        ],
        cwd=project_dir,
        stage="sim_compile",
    )
    if compile_result.status != "passed":
        return compile_result.status, "not_run"
    evidence, _ = run_oracle_scenarios(runner, project_dir, bundle)
    return compile_result.status, evidence.status


def _lint_project(project: GeneratedProject, project_dir: Path) -> str:
    project_dir.mkdir(parents=True, exist_ok=True)
    for relative_path, source in project.files.items():
        destination = project_dir / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(source, encoding="utf-8")
    manifest = json.loads(project.files["manifest.json"])
    return CommandRunner().run(
        ["verilator", "--lint-only", "-Wall", *manifest["sources"]],
        cwd=project_dir,
        stage="lint",
    ).status
