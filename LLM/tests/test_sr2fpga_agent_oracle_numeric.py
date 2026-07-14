from __future__ import annotations

import json
from pathlib import Path
import shutil

import pytest

from LLM.src.sr2fpga_agent.failure_injector import oracle_mutation_projects
from LLM.src.sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest
from LLM.src.sr2fpga_agent.oracle_runner import run_oracle_scenarios
from LLM.src.sr2fpga_agent.oracles import REFERENCE_BUILDERS
from LLM.src.sr2fpga_agent.oracles.numeric import (
    build_fir_filter_bundle,
    build_matrix_vector_mac_bundle,
    fir_outputs,
    matrix_vector_outputs,
    signed,
)
from LLM.src.sr2fpga_agent.project_generator import ProjectGenerator
from LLM.src.sr2fpga_agent.tool_runner import CommandRunner


SCENARIO_CLASSES = {
    "public_smoke",
    "hidden_deterministic",
    "randomized_fixed_seed",
    "stress",
}


def test_fir_reference_matches_declared_coefficients() -> None:
    assert fir_outputs([5, -4, 7], width=8) == [15, -22, 34]
    assert fir_outputs([127], width=8) == [381]


def test_matrix_vector_reference_uses_fixed_rom_order() -> None:
    assert matrix_vector_outputs([1, 2, 3, 4], width=8) == [13]
    assert matrix_vector_outputs([127, -128, 127, 127], width=8) == [890]


def test_numeric_references_normalize_signed_inputs_and_reject_partial_vectors() -> None:
    assert signed(0x80, 8) == -128
    assert signed(0xFF, 8) == -1
    assert signed(0x17F, 8) == 127
    assert fir_outputs([0x80, 0x7F], width=8) == [-384, 637]
    with pytest.raises(ValueError, match="groups of four"):
        matrix_vector_outputs([1, 2, 3], width=8)


@pytest.mark.parametrize(
    ("family_id", "builder", "result_width"),
    [
        ("fir_filter", build_fir_filter_bundle, 11),
        ("matrix_vector_mac", build_matrix_vector_mac_bundle, 12),
    ],
)
def test_numeric_bundle_has_four_classes_and_exact_layout(
    tmp_path: Path,
    family_id: str,
    builder,
    result_width: int,
) -> None:
    bundle = builder(8, tmp_path / family_id)

    assert bundle.family_id == family_id
    assert bundle.reference_model == "python_numeric_reference"
    assert {scenario.scenario_class for scenario in bundle.scenarios} == SCENARIO_CLASSES
    assert len(bundle.scenarios) == 4
    for scenario in bundle.scenarios:
        assert scenario.input_record_width_bits == 11
        assert scenario.expected_record_width_bits == result_width + 1
        assert [
            (field.name, field.msb, field.lsb, field.signed)
            for field in scenario.input_fields
        ] == [
            ("sample", 7, 0, True),
            ("reset_before", 8, 8, False),
            ("stall_cycles", 10, 9, False),
        ]
        assert [
            (field.name, field.msb, field.lsb, field.signed)
            for field in scenario.expected_fields
        ] == [
            ("result", result_width - 1, 0, True),
            ("expect_output", result_width, result_width, False),
        ]


@pytest.mark.parametrize(
    ("builder", "family_id"),
    [
        (build_fir_filter_bundle, "fir_filter"),
        (build_matrix_vector_mac_bundle, "matrix_vector_mac"),
    ],
)
def test_numeric_bundle_is_deterministic_and_contains_reset_and_stall_controls(
    tmp_path: Path,
    builder,
    family_id: str,
) -> None:
    first = builder(8, tmp_path / "first")
    second = builder(8, tmp_path / "second")

    assert first.bundle_sha256 == second.bundle_sha256
    assert first.manifest == second.manifest
    assert REFERENCE_BUILDERS[family_id] is builder
    stress = next(item for item in first.scenarios if item.scenario_class == "stress")
    records = _read_memh(first.root / stress.input_path)
    assert any((record >> 8) & 1 for record in records)
    assert any((record >> 9) & 0b11 for record in records)
    assert stress.seed.bit_length() >= 120


def test_matrix_bundle_marks_only_completed_groups_as_outputs(tmp_path: Path) -> None:
    bundle = build_matrix_vector_mac_bundle(8, tmp_path / "matrix")
    stress = next(item for item in bundle.scenarios if item.scenario_class == "stress")
    expected_records = _read_memh(bundle.root / stress.expected_path)

    expect_output = [(record >> 12) & 1 for record in expected_records]
    assert 0 in expect_output
    assert 1 in expect_output
    assert sum(expect_output) >= 2


def test_generated_numeric_testbenches_keep_legacy_and_add_oracle_mode() -> None:
    platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
    for task_type in ("fir_filter", "matrix_vector_mac"):
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
        assert '$display("TEST_PASS")' in testbench


@pytest.mark.skipif(
    not shutil.which("iverilog") or not shutil.which("vvp"),
    reason="iverilog/vvp are not installed",
)
@pytest.mark.parametrize(
    ("task_type", "builder"),
    [
        ("fir_filter", build_fir_filter_bundle),
        ("matrix_vector_mac", build_matrix_vector_mac_bundle),
    ],
)
def test_numeric_reference_and_all_declared_mutations_are_scoreable(
    tmp_path: Path,
    task_type: str,
    builder,
) -> None:
    platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
    reference = ProjectGenerator().generate(
        ProjectRequest(task_type=task_type, width=8, project_name=task_type),
        platform,
    )
    bundle = builder(8, tmp_path / "oracle" / task_type)

    reference_compile, reference_evidence = _compile_and_run(
        reference,
        tmp_path / "reference" / task_type,
        bundle,
    )
    assert reference_compile == "passed"
    assert reference_evidence == "passed"

    mutations = oracle_mutation_projects(reference, task_type)
    assert mutations
    for mutation_name, mutation in mutations.items():
        assert mutation is not None, mutation_name
        compile_status, evidence_status = _compile_and_run(
            mutation,
            tmp_path / "mutations" / task_type / mutation_name,
            bundle,
        )
        assert (compile_status, evidence_status) != ("passed", "passed"), mutation_name


def _read_memh(path: Path) -> list[int]:
    return [int(line, 16) for line in path.read_text(encoding="ascii").splitlines()]


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
