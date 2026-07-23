from __future__ import annotations

import json
from pathlib import Path
import shutil

import pytest

from sr2fpga_agent.failure_injector import oracle_mutation_projects
from sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest
from sr2fpga_agent.oracle_runner import run_oracle_scenarios
from sr2fpga_agent.oracles import REFERENCE_BUILDERS
from sr2fpga_agent.oracles.image import (
    IMAGE_HEIGHT,
    IMAGE_THRESHOLD,
    IMAGE_WIDTH,
    build_sobel_threshold_bundle,
    build_vision_defect_bundle,
    sobel_frame,
    vision_defect_frame,
)
from sr2fpga_agent.project_generator import ProjectGenerator
from sr2fpga_agent.tool_runner import CommandRunner


SCENARIO_CLASSES = {
    "public_smoke",
    "hidden_deterministic",
    "randomized_fixed_seed",
    "stress",
}


def _flat_frame(level: int = 0) -> list[list[int]]:
    return [[level] * IMAGE_WIDTH for _ in range(IMAGE_HEIGHT)]


def _vertical_step_frame(level: int) -> list[list[int]]:
    return [[0 if x < 2 else level for x in range(IMAGE_WIDTH)] for _ in range(IMAGE_HEIGHT)]


def _horizontal_step_frame(level: int) -> list[list[int]]:
    return [[0 if y < 2 else level for _ in range(IMAGE_WIDTH)] for y in range(IMAGE_HEIGHT)]


def _shifted_vertical_step_frame(level: int) -> list[list[int]]:
    return [[0 if x < 3 else level for x in range(IMAGE_WIDTH)] for _ in range(IMAGE_HEIGHT)]


def test_flat_frame_has_no_edges_and_axis_tie_is_one_inside() -> None:
    result = sobel_frame(_flat_frame(), threshold=255)

    assert sum(result.edges) == 0
    assert result.axes[6:9] == (1, 1, 1)
    assert result.axes[11:14] == (1, 1, 1)
    assert result.axes[16:19] == (1, 1, 1)
    assert all(result.axes[index] == 0 for index in _border_indices())


def test_vertical_and_horizontal_edges_use_row_major_zero_border() -> None:
    vertical = sobel_frame(_vertical_step_frame(255), threshold=IMAGE_THRESHOLD)
    horizontal = sobel_frame(_horizontal_step_frame(255), threshold=IMAGE_THRESHOLD)

    assert _set_indices(vertical.edges) == {6, 7, 11, 12, 16, 17}
    assert all(vertical.axes[index] == 1 for index in range(25) if index not in _border_indices())
    assert _set_indices(horizontal.edges) == {6, 7, 8, 11, 12, 13}
    assert all(horizontal.axes[index] == 0 for index in {6, 7, 8, 11, 12, 13})
    assert all(horizontal.edges[index] == 0 for index in _border_indices())


def test_threshold_is_inclusive_and_maximum_pixels_do_not_overflow() -> None:
    exact = sobel_frame(_vertical_step_frame(25), threshold=100)
    above = sobel_frame(_vertical_step_frame(25), threshold=101)
    maximum = sobel_frame(_vertical_step_frame(255), threshold=2040)

    assert _set_indices(exact.edges) == {6, 7, 11, 12, 16, 17}
    assert sum(above.edges) == 0
    assert sum(maximum.edges) == 0


def test_vision_defect_uses_first_row_major_thresholded_coordinate() -> None:
    result = vision_defect_frame(_vertical_step_frame(255), threshold=255)

    assert result.defect_present is True
    assert (result.first_x, result.first_y) == (1, 1)
    assert _set_indices(result.edges) == {6, 7, 11, 12, 16, 17}


def test_vision_defect_first_coordinate_is_not_assumed_to_be_one_one_or_diagonal() -> None:
    result = vision_defect_frame(_shifted_vertical_step_frame(255), threshold=255)

    assert result.defect_present is True
    assert (result.first_x, result.first_y) == (2, 1)
    assert result.first_x != result.first_y


def test_vision_all_zero_frame_has_no_coordinate_or_cca_claim() -> None:
    result = vision_defect_frame(_flat_frame(), threshold=IMAGE_THRESHOLD)

    assert result.defect_present is False
    assert (result.first_x, result.first_y) == (0, 0)
    assert not hasattr(result, "bounding_box")
    assert not hasattr(result, "components")


@pytest.mark.parametrize(
    "frame,threshold",
    [
        ([[0] * 5 for _ in range(4)], 100),
        ([[0] * 4 for _ in range(5)], 100),
        ([[0] * 5 for _ in range(4)] + [[0, 0, 0, 0, 256]], 100),
        (_flat_frame(), -1),
    ],
)
def test_image_reference_rejects_non_5x5_u8_contract(frame, threshold: int) -> None:
    with pytest.raises(ValueError):
        sobel_frame(frame, threshold)


@pytest.mark.parametrize(
    ("family_id", "builder", "expected_width", "expected_layout"),
    [
        (
            "sobel_threshold",
            build_sobel_threshold_bundle,
            4,
            [
                ("edge", 0, 0, False),
                ("axis", 1, 1, False),
                ("out_last", 2, 2, False),
                ("expect_output", 3, 3, False),
            ],
        ),
        (
            "p_vision_defect_core",
            build_vision_defect_bundle,
            36,
            [
                ("edge", 0, 0, False),
                ("out_last", 1, 1, False),
                ("defect_present", 2, 2, False),
                ("first_x", 18, 3, False),
                ("first_y", 34, 19, False),
                ("expect_output", 35, 35, False),
            ],
        ),
    ],
)
def test_image_bundle_has_four_classes_and_exact_memh_layout(
    tmp_path: Path,
    family_id: str,
    builder,
    expected_width: int,
    expected_layout: list[tuple[str, int, int, bool]],
) -> None:
    bundle = builder(8, tmp_path / family_id)

    assert bundle.family_id == family_id
    assert bundle.reference_model == "python_image_reference"
    assert {scenario.scenario_class for scenario in bundle.scenarios} == SCENARIO_CLASSES
    assert len(bundle.scenarios) == 4
    for scenario in bundle.scenarios:
        assert scenario.transaction_count > 0
        assert scenario.input_record_width_bits == 24
        assert scenario.expected_record_width_bits == expected_width
        assert [
            (field.name, field.msb, field.lsb, field.signed)
            for field in scenario.input_fields
        ] == [
            ("pixel", 7, 0, False),
            ("in_last", 8, 8, False),
            ("reset_before", 9, 9, False),
            ("stall_cycles", 11, 10, False),
            ("drain_target", 23, 12, False),
        ]
        assert [
            (field.name, field.msb, field.lsb, field.signed)
            for field in scenario.expected_fields
        ] == expected_layout


@pytest.mark.parametrize(
    ("family_id", "builder"),
    [
        ("sobel_threshold", build_sobel_threshold_bundle),
        ("p_vision_defect_core", build_vision_defect_bundle),
    ],
)
def test_image_bundle_is_deterministic_with_withheld_seeds_reset_and_stall(
    tmp_path: Path,
    family_id: str,
    builder,
) -> None:
    first = builder(8, tmp_path / "first")
    second = builder(8, tmp_path / "second")

    assert first.bundle_sha256 == second.bundle_sha256
    assert first.manifest == second.manifest
    assert REFERENCE_BUILDERS[family_id] is builder
    for scenario in first.scenarios:
        assert len(_read_memh(first.root / scenario.input_path)) == scenario.transaction_count
        assert len(_read_memh(first.root / scenario.expected_path)) == scenario.transaction_count
    stress = next(item for item in first.scenarios if item.scenario_class == "stress")
    inputs = _read_memh(first.root / stress.input_path)
    assert any((record >> 9) & 1 for record in inputs)
    assert any((record >> 10) & 0b11 for record in inputs)
    assert stress.transaction_count == 35
    assert ((inputs[10] >> 12) & 0xFFF) == 5
    assert stress.seed.bit_length() >= 120


@pytest.mark.parametrize(
    ("builder", "expect_bit", "out_last_bit"),
    [
        (build_sobel_threshold_bundle, 3, 2),
        (build_vision_defect_bundle, 35, 1),
    ],
)
def test_image_bundle_encodes_missing_last_and_partial_reset_output_counts(
    tmp_path: Path,
    builder,
    expect_bit: int,
    out_last_bit: int,
) -> None:
    bundle = builder(8, tmp_path / builder.__name__)
    hidden = next(item for item in bundle.scenarios if item.scenario_class == "hidden_deterministic")
    hidden_inputs = _read_memh(bundle.root / hidden.input_path)
    hidden_expected = _read_memh(bundle.root / hidden.expected_path)
    assert len(hidden_inputs) == 25
    assert ((hidden_inputs[23] >> 8) & 1) == 1
    assert ((hidden_inputs[24] >> 8) & 1) == 0
    assert sum((record >> expect_bit) & 1 for record in hidden_expected) == 20
    assert not any((record >> out_last_bit) & 1 for record in hidden_expected)

    stress = next(item for item in bundle.scenarios if item.scenario_class == "stress")
    stress_inputs = _read_memh(bundle.root / stress.input_path)
    stress_expected = _read_memh(bundle.root / stress.expected_path)
    assert len(stress_inputs) == 35
    assert ((stress_inputs[10] >> 9) & 1) == 1
    assert ((stress_inputs[10] >> 12) & 0xFFF) == 5
    stall_index = next(index for index, record in enumerate(stress_inputs) if (record >> 10) & 0b11)
    assert (stress_inputs[stall_index] & 0xFF) != (stress_inputs[stall_index + 1] & 0xFF)
    assert sum((record >> expect_bit) & 1 for record in stress_expected) == 30
    assert sum((record >> out_last_bit) & 1 for record in stress_expected) == 1


def test_image_bundle_output_order_and_final_frame_report(tmp_path: Path) -> None:
    sobel = build_sobel_threshold_bundle(8, tmp_path / "sobel")
    public = next(item for item in sobel.scenarios if item.scenario_class == "public_smoke")
    sobel_expected = _read_memh(sobel.root / public.expected_path)
    assert len(sobel_expected) >= 50
    assert all(((value >> 2) & 1) == (index % 25 == 24) for index, value in enumerate(sobel_expected))

    vision = build_vision_defect_bundle(8, tmp_path / "vision")
    public = next(item for item in vision.scenarios if item.scenario_class == "public_smoke")
    expected = _read_memh(vision.root / public.expected_path)
    reports = [_unpack_vision(value) for value in expected if (value >> 1) & 1]
    assert reports[0] == (0, 0, 0)
    assert reports[1] == (1, 2, 1)
    assert all((value & ~((1 << 35) | 0b11)) == 0 for value in expected if not ((value >> 1) & 1))


def test_generated_image_testbenches_keep_legacy_and_add_oracle_mode() -> None:
    platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
    for task_type in ("sobel_threshold", "vision_defect_core"):
        project = ProjectGenerator().generate(
            ProjectRequest(task_type=task_type, width=8, project_name=task_type),
            platform,
        )
        testbench = project.files["sim/tb_top.v"]
        assert '$value$plusargs("ORACLE_INPUT=%s"' in testbench
        assert "$readmemh(oracle_input_path" in testbench
        assert "ORACLE_EXPECTED" in testbench
        assert "ORACLE_TRANSACTION_COUNT" in testbench
        assert "SR2FPGA_MISMATCH" in testbench
        assert "emitted more than 25 pixels" in testbench
        assert "output changed under stall" in testbench
        assert "input accepted while output stalled" in testbench
        assert "oracle_expected_output_count" in testbench
        assert "oracle_frame_output_count = 0" in testbench
        assert '$display("TEST_PASS")' in testbench


@pytest.mark.skipif(
    not shutil.which("iverilog") or not shutil.which("vvp"),
    reason="iverilog/vvp are not installed",
)
@pytest.mark.parametrize(
    ("task_type", "family_id", "builder"),
    [
        ("sobel_threshold", "sobel_threshold", build_sobel_threshold_bundle),
        ("vision_defect_core", "p_vision_defect_core", build_vision_defect_bundle),
    ],
)
def test_image_reference_and_all_declared_mutations_are_scoreable(
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
    not shutil.which("iverilog") or not shutil.which("vvp"),
    reason="iverilog/vvp are not installed",
)
@pytest.mark.parametrize(
    ("task_type", "family_id", "builder", "mutation_name"),
    [
        ("sobel_threshold", "sobel_threshold", build_sobel_threshold_bundle, "input_backpressure_error"),
        ("sobel_threshold", "sobel_threshold", build_sobel_threshold_bundle, "ignore_in_last"),
        ("sobel_threshold", "sobel_threshold", build_sobel_threshold_bundle, "ignore_subsequent_reset"),
        (
            "vision_defect_core",
            "p_vision_defect_core",
            build_vision_defect_bundle,
            "hardcoded_first_coordinate",
        ),
        (
            "vision_defect_core",
            "p_vision_defect_core",
            build_vision_defect_bundle,
            "input_backpressure_error",
        ),
        ("vision_defect_core", "p_vision_defect_core", build_vision_defect_bundle, "ignore_in_last"),
        (
            "vision_defect_core",
            "p_vision_defect_core",
            build_vision_defect_bundle,
            "ignore_subsequent_reset",
        ),
    ],
)
def test_reviewer_control_mutations_are_declared_scoreable_and_killed(
    tmp_path: Path,
    task_type: str,
    family_id: str,
    builder,
    mutation_name: str,
) -> None:
    platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
    reference = ProjectGenerator().generate(
        ProjectRequest(task_type=task_type, width=8, project_name=task_type),
        platform,
    )
    bundle = builder(8, tmp_path / "oracle" / family_id)
    mutation = oracle_mutation_projects(reference, family_id).get(mutation_name)

    assert mutation is not None, mutation_name
    assert _lint_project(
        mutation,
        tmp_path / "lint" / family_id / mutation_name,
    ) == "passed", mutation_name
    compile_status, evidence_status = _compile_and_run(
        mutation,
        tmp_path / "mutations" / family_id / mutation_name,
        bundle,
    )
    assert (compile_status, evidence_status) != ("passed", "passed"), mutation_name


def _border_indices() -> set[int]:
    return {
        index
        for index in range(IMAGE_WIDTH * IMAGE_HEIGHT)
        if index // IMAGE_WIDTH in {0, IMAGE_HEIGHT - 1} or index % IMAGE_WIDTH in {0, IMAGE_WIDTH - 1}
    }


def _set_indices(values: tuple[int, ...]) -> set[int]:
    return {index for index, value in enumerate(values) if value}


def _read_memh(path: Path) -> list[int]:
    return [int(line, 16) for line in path.read_text(encoding="ascii").splitlines()]


def _unpack_vision(record: int) -> tuple[int, int, int]:
    defect_present = (record >> 2) & 1
    first_x = (record >> 3) & 0xFFFF
    first_y = (record >> 19) & 0xFFFF
    return defect_present, first_x, first_y


def _compile_and_run(
    project: GeneratedProject,
    project_dir: Path,
    bundle,
) -> tuple[str, str]:
    _write_project(project, project_dir)
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
    _write_project(project, project_dir)
    manifest = json.loads(project.files["manifest.json"])
    result = CommandRunner().run(
        ["verilator", "--lint-only", "-Wall", *manifest["sources"]],
        cwd=project_dir,
        stage="lint",
    )
    return result.status


def _write_project(project: GeneratedProject, project_dir: Path) -> None:
    project_dir.mkdir(parents=True, exist_ok=True)
    for relative_path, source in project.files.items():
        destination = project_dir / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(source, encoding="utf-8")
